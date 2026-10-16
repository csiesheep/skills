"""看原始資料：py -m storypipe.show [N] [--raw path] [--list]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("n", type=int, nargs="?", default=None, help="第幾篇（0-based）")
    p.add_argument("--raw", default="data/raw/ptt_marvel.jsonl")
    p.add_argument("--list", action="store_true", help="只列標題和分數")
    p.add_argument("--pushes", type=int, default=15)
    a = p.parse_args()

    rows = [json.loads(l) for l in Path(a.raw).open(encoding="utf-8") if l.strip()]
    if a.list or a.n is None:
        for i, r in enumerate(rows):
            print(f"{i:>4} nrec={r.get('nrec', 0):>3} len={len(r['body']):>5} {r['title']}")
        return
    r = rows[a.n]
    print(f"ID {r['id']}\nURL {r['url']}\nTITLE {r['title']}\nNREC {r.get('nrec')}\nLEN {len(r['body'])}")
    print("---BODY---")
    print(r["body"])
    print("---PUSHES---")
    kept = [x for x in r["pushes"] if len(x["text"]) > 4][: a.pushes]
    print("\n".join(f"{x['tag']} {x['text']}" for x in kept))


if __name__ == "__main__":
    main()
