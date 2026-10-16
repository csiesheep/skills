"""評審校準：拿真實的高分和低分經驗文，用 v1、v2 兩版評審打分，看哪版分得開、分數跟毛率有沒有關。

py -m storypipe.calibrate --n 20
"""
from __future__ import annotations

import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .generate import judge_story
from .llm import make_backend
from .scare import _spearman, push_index, rates
from .stats import load_units
from .taxonomy import ENDINGS, MECHANISMS, SETTINGS, BeatShare, Plan

OUT = Path("data/calibration.jsonl")


def plan_from_annotation(a: dict, chars: int, rules: str) -> Plan:
    mechs = a["mechanisms"]
    return Plan(
        setting=a["setting"], setting_label=SETTINGS[a["setting"]],
        mechanisms=mechs, mechanism_labels=[MECHANISMS[m] for m in mechs],
        ending=a["ending"], ending_label=ENDINGS[a["ending"]],
        beats=BeatShare(**a["beats"]).normalized(), ghost_explicitness=a["ghost_explicitness"],
        target_chars=chars, anchor_hints=[], structural_examples=[], seed=0, rules=rules,
    )


def auc(pos: list[float], neg: list[float]) -> float:
    """高分組的分數大於低分組分數的機率（Mann-Whitney AUC），平手算一半。0.5 是瞎猜。"""
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--backend", default="cli")
    a = ap.parse_args()

    rows, _ = load_units(Path("data/annotated.opus55.v2.jsonl"), Path("data/corpus.jsonl"))
    corpus = {}
    for line in Path("data/corpus.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            corpus[u["id"]] = u
    ok = lambda r: 600 <= r["length_chars"] <= 4000 and not corpus[r["id"]]["series_key"]  # noqa: E731
    hi = [r for r in rows if r["source"] == "經驗" and r.get("pct") is not None and r["pct"] >= 0.9 and ok(r)]
    lo = [r for r in rows if r["source"] == "經驗對照" and r.get("pct") is not None and r["pct"] <= 0.3 and ok(r)]
    rng = random.Random(a.seed)
    pick = [("high", r) for r in rng.sample(hi, a.n)] + [("low", r) for r in rng.sample(lo, a.n)]
    P = push_index()

    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                done.add((x["id"], x["rules"]))
    jobs = [(g, r, rules) for g, r in pick for rules in ("v1", "v2") if (r["id"], rules) not in done]
    backend = make_backend(a.backend)
    lock = threading.Lock()

    def work(g, r, rules):
        u = corpus[r["id"]]
        story = f"{u['title']}\n{u['body']}"
        from .generate import count_chars

        v = judge_story(backend, plan_from_annotation(r["annotation"], count_chars(story), rules), story, "claude-opus-5-5")
        s, d, n = rates([p for part in u["parts"] for p in P.get(part["id"], [])])
        return {"id": r["id"], "title": u["title"], "group": g, "pct": r["pct"], "scary": s, "doubt": d, "n_push": n,
                "rules": rules, "verdict": v.model_dump()}

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
            print(f"[{k}/{len(jobs)}] {rec['rules']} {rec['group']:<4} overall={rec['verdict']['overall']} | {rec['title'][:30]}", flush=True)

    recs = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    L = ["# 評審校準", "", f"真實經驗文：高分組（同年前 10%）{a.n} 篇、低分組（對照組，後 30%）{a.n} 篇，字數 600 到 4000、不含系列。", "",
         "| 指標 | v1 評審 | v2 評審 |", "|---|---|---|"]
    stats = {}
    for rules in ("v1", "v2"):
        R = [x for x in recs if x["rules"] == rules]
        H = [x["verdict"]["overall"] for x in R if x["group"] == "high"]
        Lo = [x["verdict"]["overall"] for x in R if x["group"] == "low"]
        stats[rules] = {
            "auc": auc(H, Lo),
            "mean_h": sum(H) / len(H) if H else 0, "mean_l": sum(Lo) / len(Lo) if Lo else 0,
            "pass_h": sum(x["verdict"]["passes"] for x in R if x["group"] == "high") / max(1, len(H)),
            "pass_l": sum(x["verdict"]["passes"] for x in R if x["group"] == "low") / max(1, len(Lo)),
            "rho_pct": _spearman([x["pct"] for x in R], [x["verdict"]["overall"] for x in R]) if len(R) > 3 else 0,
            "rho_scary": _spearman([x["scary"] for x in R], [x["verdict"]["overall"] for x in R]) if len(R) > 3 else 0,
            "ghost_auc": auc([x["verdict"]["ghost_restraint"] for x in R if x["group"] == "high"], [x["verdict"]["ghost_restraint"] for x in R if x["group"] == "low"]),
        }
    for key, name, fmt in [("auc", "總分分得開高低分組的程度（AUC，0.5 是瞎猜）", "{:.2f}"),
                           ("mean_h", "高分組平均總分", "{:.1f}"), ("mean_l", "低分組平均總分", "{:.1f}"),
                           ("pass_h", "高分組通過率", "{:.0%}"), ("pass_l", "低分組通過率", "{:.0%}"),
                           ("rho_pct", "總分跟推文百分位的等級相關", "{:+.2f}"), ("rho_scary", "總分跟毛率的等級相關", "{:+.2f}"),
                           ("ghost_auc", "「鬼的處理」分得開高低分組的程度（AUC）", "{:.2f}")]:
        L.append(f"| {name} | {fmt.format(stats['v1'][key])} | {fmt.format(stats['v2'][key])} |")
    md = "\n".join(L) + "\n"
    Path("data/calibration.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
