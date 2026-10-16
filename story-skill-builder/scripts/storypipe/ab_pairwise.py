"""用兩兩比較評審判新舊對照的 10 對（每對 A、B 對調各判一次），結果存 data/ab/pairwise.jsonl。
不印哪版贏，等盲讀完再看：py -m storypipe.ab_pairwise --reveal
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .llm import make_backend
from .pairwise import judge_pair

AB = Path("data/ab")
OUT = AB / "pairwise.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reveal", action="store_true")
    a = ap.parse_args()
    key = json.loads((AB / "blind" / "key.json").read_text(encoding="utf-8"))
    if not OUT.exists():
        backend = make_backend("cli")
        jobs = []
        for pid, k in sorted(key.items()):
            v1 = json.loads((AB / f"{k['seed']}_v1.json").read_text(encoding="utf-8"))["final"]
            v2 = json.loads((AB / f"{k['seed']}_v2.json").read_text(encoding="utf-8"))["final"]
            jobs += [(pid, "v1_first", v1, v2), (pid, "v2_first", v2, v1)]

        def work(j):
            pid, order, a_text, b_text = j
            r = judge_pair(backend, a_text, b_text)
            first = order.split("_")[0]
            other = "v2" if first == "v1" else "v1"
            return {"pair": pid, "order": order, "popular": first if r.popular == "A" else other,
                    "scary": first if r.scary == "A" else other, "confidence": r.confidence, "reason": r.reason}

        with ThreadPoolExecutor(max_workers=8) as pool:
            recs = list(pool.map(work, jobs))
        OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
        print(f"判完 {len(recs)} 次 → {OUT}（結果封存，盲讀完用 --reveal 看）")
    if a.reveal:
        recs = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
        for q in ("scary", "popular"):
            print(q, "v2 勝", sum(r[q] == "v2" for r in recs), "/", len(recs))


if __name__ == "__main__":
    main()
