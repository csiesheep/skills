"""Which files of a ghost-film video's posting set (ghost-pack-film's posts/film/) are ready, missing or wrong.

    py -X utf8 check_film.py <story folder> --number N [--brand-file <brand.json>]

Checks the film ledger has 第 N 部 for this folder, the stamped covers, every caption (label heading, disclosure,
lengths), and that every video in files.txt and its 720p upload copy exist (the copy within 10 MB, Claude in
Chrome's file_upload limit). An {ig_link} slot counts as ready. Exit code 1 if anything required is missing or wrong.
"""
import argparse
import json
import re
import sys
from pathlib import Path

LIMITS = {"ig": 2200, "youtube_title": 100, "threads": 500, "upload_mb": 10}


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    for s in (sys.stdout,):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--brand-file", default=None)
    a = ap.parse_args()
    d = Path(a.story).resolve()
    bf = Path(a.brand_file) if a.brand_file else Path("C:/Users/sheep/Pictures/gui_chang_shi/brand/brand.json")
    br = json.loads(bf.read_text(encoding="utf-8"))
    label = br["film"]["label"].format(n=a.number)
    disc = br["disclosure"].split("｜")[0]
    led = json.loads((bf.parent / br.get("film_ledger", "film_ledger.json")).read_text(encoding="utf-8"))
    f = d / "posts" / "film"
    rows = []

    def add(item, ok, note=""):
        rows.append((item, ok, note))

    hit = [s for s in led["stories"] if s["number"] == a.number]
    add("影片編號 film_ledger.json", bool(hit) and d.as_posix().endswith(hit[0].get("folder", "?")),
        f"第 {a.number} 部〈{hit[0]['title']}〉" if hit else "沒有這一號：ghost-pack-film")
    add("海報 cover.jpg", (f / "cover.jpg").exists())
    parts = sorted(f.glob("caption_ig_part*.txt"))
    for p in parts:
        k = p.stem.rsplit("_", 1)[-1]
        add(f"IG 封面 cover_{k}.jpg", (f / f"cover_{k}.jpg").exists())
    for p in parts or [f / "caption_ig.txt"]:
        t = read(p)
        bad = [x for x, ok in (("沒有編號", label in t), ("沒有 AI 標示", disc in t), ("超過 2200", len(t) <= LIMITS["ig"])) if not ok]
        add(f"IG 文案 {p.name}", bool(t) and not bad, f"{len(t)} 字" + ("；" + "、".join(bad) if bad else "") if t else "missing")
    full = read(f / "caption_full.txt")
    m = re.search(r"== YouTube 標題（\d+）==\n(.+)", full)
    yt_ok = bool(m) and len(m.group(1)) <= LIMITS["youtube_title"] and label in m.group(1)
    add("完整版文案 caption_full.txt", bool(full) and yt_ok and disc in full and "== Facebook ==" in full,
        f"YouTube 標題「{m.group(1)}」" if m else "missing")
    th = read(f / "threads.txt")
    add("Threads threads.txt", bool(th) and len(th) <= LIMITS["threads"] and label in th, f"{len(th)} 字" if th else "missing")
    add("Pinterest pins.txt", bool(read(f / "pins.txt")))
    for ln in read(f / "files.txt").splitlines():
        mm = re.match(r"(.+?)：(.+\.mp4)$", ln.strip()) or re.match(r"\s*上傳用 720p：(.+\.mp4)（", ln)
        if not mm:
            continue
        path = Path(mm.group(mm.lastindex) if mm.lastindex == 2 else mm.group(1))
        mb = path.stat().st_size / 1e6 if path.exists() else 0
        up = "720p" in ln
        ok = path.exists() and (mb <= LIMITS["upload_mb"] if up else True)
        add(("上傳 " if up else "影片 ") + path.name, ok, f"{mb:.1f} MB" if path.exists() else "missing")
    if not read(f / "files.txt"):
        add("files.txt", False, "missing: ghost-pack-film")

    w = max(len(r[0]) for r in rows)
    for item, ok, note in rows:
        print(f"{'OK ' if ok else 'NO '} {item.ljust(w)}  {note}")
    print(f"{label}：" + ("全部就緒" if all(r[1] for r in rows) else "有缺，回 ghost-pack-film / ghost-film"))
    return 0 if all(r[1] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
