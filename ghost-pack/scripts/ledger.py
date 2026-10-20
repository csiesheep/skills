"""The account's story ledger: which number each story has (「第 N 首」) and where it was posted.

A story keeps one number across every platform and format (Threads text, Instagram carousel, Reels, Pinterest),
and numbers run across text and comics alike, so they are handed out here and nowhere else.

    py -X utf8 ledger.py --brand-file brand.json next
    py -X utf8 ledger.py --brand-file brand.json reserve "阿嬤說我後面跟了三個人" --kind comic --folder stories/three_behind
    py -X utf8 ledger.py --brand-file brand.json reserve "關於鬼唱詩" --number 0
    py -X utf8 ledger.py --brand-file brand.json posted 1 instagram --url https://www.instagram.com/p/... --date 2026-10-31
    py -X utf8 ledger.py --brand-file brand.json show

The ledger file is the brand file's "ledger" (a path relative to the brand file), or --ledger. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def ledger_path(a) -> Path:
    if a.ledger:
        return Path(a.ledger)
    if not a.brand_file:
        raise SystemExit("give --brand-file (with a \"ledger\" entry) or --ledger")
    bf = Path(a.brand_file).resolve()
    name = json.loads(bf.read_text(encoding="utf-8")).get("ledger")
    if not name:
        raise SystemExit(f"{bf} has no \"ledger\" entry; add one or pass --ledger")
    return (bf.parent / name).resolve()


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"stories": []}


def save(p: Path, led: dict) -> None:
    led["stories"].sort(key=lambda s: s["number"])
    p.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_number(led: dict) -> int:
    used = {s["number"] for s in led["stories"]}
    n = 1
    while n in used:
        n += 1
    return n


def main() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand-file", default=None)
    ap.add_argument("--ledger", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next")
    sub.add_parser("show")
    r = sub.add_parser("reserve")
    r.add_argument("title")
    r.add_argument("--kind", choices=["text", "comic", "other"], default="text")
    r.add_argument("--number", type=int, default=None, help="a specific number (0 for an intro post); default: next free")
    r.add_argument("--folder", default=None, help="the story's folder, relative to the brand file's folder (e.g. stories/three_behind)")
    po = sub.add_parser("posted")
    po.add_argument("number", type=int)
    po.add_argument("platform", help="threads, instagram, instagram-reel, pinterest, facebook, youtube, tiktok ...")
    po.add_argument("--url", default="")
    po.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    p = ledger_path(a)
    led = load(p)

    if a.cmd == "next":
        print(next_number(led))
        return
    if a.cmd == "show":
        if not led["stories"]:
            print(f"{p}: empty")
        for s in led["stories"]:
            posts = ", ".join(f"{x['platform']} {x['date']}" for x in s.get("posts", [])) or "not posted"
            where = f"  ({s['folder']})" if s.get("folder") else ""
            print(f"{s['number']:>3}  {s['title']}  [{s['kind']}]  {posts}{where}")
        return
    if a.cmd == "reserve":
        same = [s for s in led["stories"] if s["title"] == a.title]
        if same:  # the same story asked twice keeps its number
            if a.folder and same[0].get("folder") != a.folder:
                same[0]["folder"] = a.folder
                save(p, led)
            print(same[0]["number"])
            return
        n = next_number(led) if a.number is None else a.number
        taken = [s for s in led["stories"] if s["number"] == n]
        if taken:
            raise SystemExit(f"第 {n} 首 is already 〈{taken[0]['title']}〉")
        entry = {"number": n, "title": a.title, "kind": a.kind, "reserved": dt.date.today().isoformat(), "posts": []}
        if a.folder:
            entry["folder"] = a.folder
        led["stories"].append(entry)
        save(p, led)
        print(n)
        return
    if a.cmd == "posted":
        hit = [s for s in led["stories"] if s["number"] == a.number]
        if not hit:
            raise SystemExit(f"no story has number {a.number}; reserve it first")
        hit[0].setdefault("posts", []).append({"platform": a.platform, "url": a.url, "date": a.date})
        save(p, led)
        print(f"第 {a.number} 首 〈{hit[0]['title']}〉: {a.platform} {a.date} recorded")


if __name__ == "__main__":
    main()
