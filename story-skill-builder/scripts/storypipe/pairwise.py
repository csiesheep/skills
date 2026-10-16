"""兩兩比較的評審：給兩篇，問哪篇推文多（popular）、哪篇比較毛（scary）。先用真實文章的配對量準確率。

兩組真實配對：
- pop：經驗文同年前 10%（高）vs 對照組後 30%（低），量 popular 的準確率
- scary：推文百分位都在 0.5 以上、推文至少 30 則的經驗文，毛率前四分之一 vs 後四分之一，量 scary 的準確率
每對 A、B 對調各判一次，抵銷位置偏好。

py -m storypipe.pairwise --pop 40 --scary 30
"""
from __future__ import annotations

import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .annotate import load_prompt
from .llm import make_backend
from .scare import push_index, rates
from .stats import load_units

OUT = Path("data/pairwise_calibration.jsonl")


class PairJudgment(BaseModel):
    popular: Literal["A", "B"]
    scary: Literal["A", "B"]
    confidence: int = Field(ge=1, le=5)
    reason: str = Field(description="一句話講判斷的關鍵差別，60 字內")


def judge_pair(backend, story_a: str, story_b: str, model: str = "claude-opus-5-5") -> PairJudgment:
    user = f"A：\n{story_a}\n\n----\n\nB：\n{story_b}"
    return backend.structured(load_prompt("pairwise_judge.md"), user, PairJudgment, model, max_tokens=3000, effort="high")


def build_pairs(n_pop: int, n_scary: int, seed: int) -> list[dict]:
    rows, _ = load_units(Path("data/annotated.opus55.v2.jsonl"), Path("data/corpus.jsonl"))
    corpus = {}
    for line in Path("data/corpus.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            corpus[u["id"]] = u
    P = push_index()
    ok = lambda r: 600 <= r["length_chars"] <= 4000 and not corpus[r["id"]]["series_key"]  # noqa: E731
    rng = random.Random(seed)

    hi = [r for r in rows if r["source"] == "經驗" and r["pct"] is not None and r["pct"] >= 0.9 and ok(r)]
    lo = [r for r in rows if r["source"] == "經驗對照" and r["pct"] is not None and r["pct"] <= 0.3 and ok(r)]
    pairs = [{"kind": "pop", "good": g["id"], "bad": b["id"], "good_pct": g["pct"], "bad_pct": b["pct"]}
             for g, b in zip(rng.sample(hi, n_pop), rng.sample(lo, n_pop))]

    cand = []
    for r in rows:
        if r["source"] != "經驗" or r["pct"] is None or r["pct"] < 0.5 or not ok(r):
            continue
        s, d, n = rates([p for part in corpus[r["id"]]["parts"] for p in P.get(part["id"], [])])
        if n >= 30:
            cand.append((s, r))
    cand.sort(key=lambda x: x[0])
    q = len(cand) // 4
    low_s, high_s = cand[:q], cand[-q:]
    for (sg, g), (sb, b) in zip(rng.sample(high_s, n_scary), rng.sample(low_s, n_scary)):
        pairs.append({"kind": "scary", "good": g["id"], "bad": b["id"], "good_scary": sg, "bad_scary": sb,
                      "good_pct": g["pct"], "bad_pct": b["pct"]})
    for i, p in enumerate(pairs):
        p["pair"] = f"{p['kind']}{i:03d}"
    return pairs, corpus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=40)
    ap.add_argument("--scary", type=int, default=30)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--backend", default="cli")
    a = ap.parse_args()
    pairs, corpus = build_pairs(a.pop, a.scary, a.seed)
    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                done.add((x["pair"], x["order"]))
    backend = make_backend(a.backend)
    lock = threading.Lock()
    text = lambda i: f"{corpus[i]['title']}\n{corpus[i]['body']}"  # noqa: E731

    def work(p, order):
        a_id, b_id = (p["good"], p["bad"]) if order == "good_first" else (p["bad"], p["good"])
        j = judge_pair(backend, text(a_id), text(b_id))
        good_label = "A" if order == "good_first" else "B"
        return {**p, "order": order, "judgment": j.model_dump(),
                "popular_correct": j.popular == good_label, "scary_correct": j.scary == good_label}

    jobs = [(p, o) for p in pairs for o in ("good_first", "bad_first") if (p["pair"], o) not in done]
    print(f"配對 {len(pairs)}（pop {a.pop}、scary {a.scary}），要判 {len(jobs)} 次", flush=True)
    with OUT.open("a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = [pool.submit(work, *j) for j in jobs]
        for k, f in enumerate(as_completed(futs), 1):
            try:
                rec = f.result()
            except Exception as e:  # noqa: BLE001
                print("fail", e, flush=True)
                continue
            with lock:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
            if k % 10 == 0:
                print(f"[{k}/{len(jobs)}]", flush=True)
    print(report(), flush=True)


def report() -> str:
    R = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    L = ["# 兩兩比較評審的校準", "", "| 配對 | 判斷次數 | 熱門度選對 | 可怕度選對 | 對調後選擇一致 |", "|---|---|---|---|---|"]
    for kind, name in (("pop", "熱門度配對（高分 vs 低分）"), ("scary", "可怕度配對（毛率高 vs 低）")):
        X = [x for x in R if x["kind"] == kind]
        if not X:
            continue
        by = {}
        for x in X:
            by.setdefault(x["pair"], {})[x["order"]] = x
        both = [v for v in by.values() if len(v) == 2]
        cons_p = sum(v["good_first"]["popular_correct"] == v["bad_first"]["popular_correct"] for v in both) / max(1, len(both))
        cons_s = sum(v["good_first"]["scary_correct"] == v["bad_first"]["scary_correct"] for v in both) / max(1, len(both))
        L.append(f"| {name} | {len(X)} | {sum(x['popular_correct'] for x in X) / len(X):.0%} | {sum(x['scary_correct'] for x in X) / len(X):.0%} "
                 f"| 熱門 {cons_p:.0%}、可怕 {cons_s:.0%} |")
    L += ["", "依信心（全部判斷）：", ""]
    for c in range(1, 6):
        X = [x for x in R if x["judgment"]["confidence"] == c]
        if X:
            tgt = lambda x: x["popular_correct"] if x["kind"] == "pop" else x["scary_correct"]  # noqa: E731
            L.append(f"- 信心 {c}：{len(X)} 次，選對 {sum(tgt(x) for x in X) / len(X):.0%}")
    first_a = sum(x["judgment"]["popular"] == "A" for x in R) / max(1, len(R))
    L += ["", f"選 A 的比例（熱門度題）：{first_a:.0%}（50% 代表沒有位置偏好）"]
    md = "\n".join(L) + "\n"
    Path("data/pairwise_calibration.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    main()
