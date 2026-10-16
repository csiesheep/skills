"""兩套規則對照：同一副骨架（同一個 seed），兩套規則（預設 genre.json 的前兩套）各寫一篇。

輸出 data/ab/：
- <seed>_<rules>.json：完整結果（骨架、每輪稿子、評分）
- cross.jsonl：每篇最終稿再用兩版評審各打一次分（交叉評分）
- annot.jsonl：每篇最終稿用標註模型標一次，看寫法有沒有照規則改變
- blind/pair01_A.md、pair01_B.md…：盲讀檔，A／B 是哪一版隨機決定
- blind/key.json：答案，讀完再打開

py -m storypipe.ab --seeds 10
"""
from __future__ import annotations

import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .annotate import build_user_prompt, load_prompt
from .generate import count_chars, generate, judge_story
from .genre import GENRE
from .llm import DEFAULT_MODELS, make_backend
from .taxonomy import Annotation, Plan

AB = Path("data/ab")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--start", type=int, default=9001)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--backend", default="cli")
    ap.add_argument("--rules", nargs=2, default=list(GENRE.rule_sets)[:2], help="要對照的兩套規則")
    ap.add_argument("--weights", default="data/weights.json")
    a = ap.parse_args()
    AB.mkdir(parents=True, exist_ok=True)
    weights = json.loads(Path(a.weights).read_text(encoding="utf-8"))
    backend = make_backend(a.backend)
    seeds = list(range(a.start, a.start + a.seeds))
    lock = threading.Lock()
    R1, R2 = a.rules

    def gen(seed: int, rules: str):
        p = AB / f"{seed}_{rules}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        res = generate(backend, weights, seed=seed, max_rounds=3, log=lambda *_: None, rules=rules)
        p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        with lock:
            print(f"gen {seed} {rules}: round {res['final_round']} overall {res['final_verdict']['overall']} {res['final_chars']} 字", flush=True)
        return res

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(gen, s, r): (s, r) for s in seeds for r in (R1, R2)}
        results = {}
        for f in as_completed(futs):
            try:
                results[futs[f]] = f.result()
            except Exception as e:  # noqa: BLE001
                print("fail gen", futs[f], e, flush=True)

    # 交叉評分 + 重新標註
    cross_p, annot_p = AB / "cross.jsonl", AB / "annot.jsonl"
    done_c = {(x["seed"], x["rules"], x["judge"]) for x in map(json.loads, cross_p.read_text(encoding="utf-8").splitlines())} if cross_p.exists() else set()
    done_a = {(x["seed"], x["rules"]) for x in map(json.loads, annot_p.read_text(encoding="utf-8").splitlines())} if annot_p.exists() else set()
    ann_sys = load_prompt("annotate.md")

    def cross(seed, rules, judge_rules):
        res = results[(seed, rules)]
        plan = Plan(**{**res["plan"], "rules": judge_rules})
        v = judge_story(backend, plan, res["final"], DEFAULT_MODELS["judge"])
        return ("cross", {"seed": seed, "rules": rules, "judge": judge_rules, "verdict": v.model_dump()})

    def annot(seed, rules):
        res = results[(seed, rules)]
        title, _, body = res["final"].partition("\n")
        ann = backend.structured(ann_sys, build_user_prompt({"title": title, "body": body}), Annotation, DEFAULT_MODELS["annotate"], max_tokens=2500)
        return ("annot", {"seed": seed, "rules": rules, "annotation": ann.model_dump()})

    jobs = []
    for (s, r) in results:
        for jr in (R1, R2):
            if (s, r, jr) not in done_c:
                jobs.append((cross, (s, r, jr)))
        if (s, r) not in done_a:
            jobs.append((annot, (s, r)))
    with ThreadPoolExecutor(max_workers=a.workers) as pool, cross_p.open("a", encoding="utf-8") as fc, annot_p.open("a", encoding="utf-8") as fa:
        futs = [pool.submit(fn, *args) for fn, args in jobs]
        for f in as_completed(futs):
            try:
                kind, rec = f.result()
            except Exception as e:  # noqa: BLE001
                print("fail post", e, flush=True)
                continue
            with lock:
                (fc if kind == "cross" else fa).write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 盲讀檔
    blind = AB / "blind"
    blind.mkdir(exist_ok=True)
    rng = random.Random(20261014)
    key = {}
    for i, s in enumerate(seeds, 1):
        if (s, R1) not in results or (s, R2) not in results:
            continue
        order = [R1, R2]
        rng.shuffle(order)
        key[f"pair{i:02d}"] = {"A": order[0], "B": order[1], "seed": s}
        for label, rules in zip("AB", order):
            (blind / f"pair{i:02d}_{label}.md").write_text(results[(s, rules)]["final"] + "\n", encoding="utf-8")
    (blind / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"盲讀檔 {len(key)} 對 → {blind}", flush=True)


if __name__ == "__main__":
    main()
