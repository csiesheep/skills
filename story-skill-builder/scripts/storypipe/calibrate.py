"""評審校準：拿真實的高分和低分單位，用各版評審打分，看哪版分得開、分數跟第二訊號有沒有關。

py -m storypipe.calibrate --n 20 [--rules v1 v2]
"""
from __future__ import annotations

import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .generate import count_chars, judge_story
from .genre import GENRE
from .llm import make_backend
from .scare import _spearman, push_index, rates
from .stats import load_units
from .taxonomy import BeatShare, Plan


def plan_from_annotation(a: dict, chars: int, rules: str) -> Plan:
    axes = GENRE.axis_values(a)
    return Plan(
        axes=axes, axis_labels={k: [GENRE.axis(k).label_of(v) for v in vs] for k, vs in axes.items()},
        cap=a[GENRE.cap.key], beats=BeatShare(**a["beats"]).normalized().model_dump(),
        target_chars=chars, anchor_hints=[], structural_examples=[], seed=0,
        style=GENRE.default_style, style_label=GENRE.styles[GENRE.default_style].label, rules=rules,
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
    ap.add_argument("--model", default=None)
    ap.add_argument("--rules", nargs="+", default=list(GENRE.rule_sets), help="要比的規則版本，預設全部")
    ap.add_argument("--annotated", default="data/annotated.jsonl")
    ap.add_argument("--corpus", default="data/corpus.jsonl")
    ap.add_argument("--out", default="data/calibration.jsonl")
    a = ap.parse_args()
    OUT = Path(a.out)
    tag = GENRE.source.default_tag

    rows, _ = load_units(Path(a.annotated), Path(a.corpus))
    corpus = {}
    for line in Path(a.corpus).read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            corpus[u["id"]] = u
    ok = lambda r: 600 <= r["length_chars"] <= 4000 and not corpus[r["id"]].get("series_key")  # noqa: E731
    hi = [r for r in rows if r["source"] == tag and r.get("pct") is not None and r["pct"] >= 0.9 and ok(r)]
    lo = [r for r in rows if r["source"] == tag + "對照" and r.get("pct") is not None and r["pct"] <= 0.3 and ok(r)]
    rng = random.Random(a.seed)
    pick = [("high", r) for r in rng.sample(hi, min(a.n, len(hi)))] + [("low", r) for r in rng.sample(lo, min(a.n, len(lo)))]
    P = push_index()

    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                done.add((x["id"], x["rules"]))
    jobs = [(g, r, rules) for g, r in pick for rules in a.rules if (r["id"], rules) not in done]
    backend = make_backend(a.backend)
    lock = threading.Lock()

    def work(g, r, rules):
        u = corpus[r["id"]]
        story = f"{u['title']}\n{u['body']}"
        v = judge_story(backend, plan_from_annotation(r["annotation"], count_chars(story), rules), story, a.model)
        s, d, n = rates([p for part in u.get("parts", [{"id": r["id"]}]) for p in P.get(part["id"], [])])
        return {"id": r["id"], "title": u["title"], "group": g, "pct": r["pct"], "pos": s, "neg": d, "n_push": n,
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
    pn = GENRE.signal.positive_name if GENRE.signal else "第二訊號"
    cap_dim = GENRE.verdict_cap_dim
    L = ["# 評審校準", "", f"真實{GENRE.unit}：高分組（同年前 10%）{a.n} 篇、低分組（對照組，後 30%）{a.n} 篇，字數 600 到 4000、不含系列。", "",
         "| 指標 | " + " | ".join(f"{r} 評審" for r in a.rules) + " |", "|---" * (len(a.rules) + 1) + "|"]
    stats = {}
    for rules in a.rules:
        R = [x for x in recs if x["rules"] == rules]
        H = [x["verdict"]["overall"] for x in R if x["group"] == "high"]
        Lo = [x["verdict"]["overall"] for x in R if x["group"] == "low"]
        stats[rules] = {
            "auc": auc(H, Lo),
            "mean_h": sum(H) / len(H) if H else 0, "mean_l": sum(Lo) / len(Lo) if Lo else 0,
            "pass_h": sum(x["verdict"]["passes"] for x in R if x["group"] == "high") / max(1, len(H)),
            "pass_l": sum(x["verdict"]["passes"] for x in R if x["group"] == "low") / max(1, len(Lo)),
            "rho_pct": _spearman([x["pct"] for x in R], [x["verdict"]["overall"] for x in R]) if len(R) > 3 else 0,
            "rho_pos": _spearman([x.get("pos", x.get("scary", 0)) for x in R], [x["verdict"]["overall"] for x in R]) if len(R) > 3 else 0,
            "cap_auc": auc([x["verdict"][cap_dim] for x in R if x["group"] == "high"], [x["verdict"][cap_dim] for x in R if x["group"] == "low"]) if cap_dim else float("nan"),
        }
    rows_out = [("auc", "總分分得開高低分組的程度（AUC，0.5 是瞎猜）", "{:.2f}"),
                ("mean_h", "高分組平均總分", "{:.1f}"), ("mean_l", "低分組平均總分", "{:.1f}"),
                ("pass_h", "高分組通過率", "{:.0%}"), ("pass_l", "低分組通過率", "{:.0%}"),
                ("rho_pct", "總分跟推文百分位的等級相關", "{:+.2f}"), ("rho_pos", f"總分跟{pn}的等級相關", "{:+.2f}")]
    if cap_dim:
        rows_out.append(("cap_auc", f"「{cap_dim}」分得開高低分組的程度（AUC）", "{:.2f}"))
    for key, name, fmt in rows_out:
        L.append(f"| {name} | " + " | ".join(fmt.format(stats[r][key]) for r in a.rules) + " |")
    md = "\n".join(L) + "\n"
    OUT.with_suffix(".md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
