"""Which files of a story's full posting set are ready, missing or wrong.

    py -X utf8 check_story.py <story folder> --number N [--brand-file <brand.json>]

Looks in the story folder for the Instagram carousel (posts/ig), the Reel full (reels/full_*), teasers
(reels/teaser_*), the Threads posts (posts/threads), the Pinterest pins (posts/pinterest) and the captions for
YouTube, TikTok and Facebook (posts/cross_caption.txt), and checks the number heading, the disclosure, lengths and
image sizes. Exit code 1 if anything required is missing or wrong. Standard library plus Pillow.
"""
import argparse
import json
import re
import sys
from pathlib import Path

LIMITS = {"threads": 500, "attachment": 10000, "ig_caption": 2200, "pin_title": 100}


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--brand-file", default=None)
    a = ap.parse_args()
    d = Path(a.story)
    bf = Path(a.brand_file) if a.brand_file else d.parent.parent / "brand" / "brand.json"
    brand = json.loads(bf.read_text(encoding="utf-8")) if bf.exists() else {}
    num = brand.get("number", "第 {n} 首").format(n=a.number)
    disclosure = brand.get("disclosure", "AI 輔助創作｜故事純屬虛構")
    rows = []          # (item, required, ok, note)

    def add(item, required, ok, note=""):
        rows.append((item, required, ok, note))

    # story text
    story = read(d / "story.md")
    add("story.md", True, bool(story), f"{len(story)} 字" if story else "missing")

    # Instagram carousel
    ig = d / "posts" / "ig"
    slides = sorted(ig.glob("*.jpg")) if ig.exists() else []
    cap = read(ig / "caption.txt")
    notes = []
    if cap and num not in cap:
        notes.append(f"caption 沒有「{num}」")
    if cap and disclosure.split("｜")[0] not in cap:
        notes.append("caption 沒有 AI 標示")
    if len(cap) > LIMITS["ig_caption"]:
        notes.append(f"caption {len(cap)} 字超過 2,200")
    add("IG 輪播 posts/ig", True, len(slides) >= 2 and bool(cap) and not notes,
        (f"{len(slides)} 張；" if slides else "沒有圖；") + ("；".join(notes) if notes else ("caption OK" if cap else "沒有 caption.txt")))

    # Reel full
    fulls = [p for p in (d / "reels").glob("full_*") if p.is_dir() and "proto" not in p.name] if (d / "reels").exists() else []
    vids = [v for f in fulls for v in f.glob("*.mp4") if "preview" not in v.name]
    add("Reel full reels/full_*", True, bool(vids),
        "；".join(f"{v.parent.name}/{v.name} {v.stat().st_size / 1e6:.0f} MB" for v in vids) or "missing")

    # teasers (optional)
    teasers = [p for p in (d / "reels").glob("teaser_*") if p.is_dir() and list(p.glob("*.mp4"))] if (d / "reels").exists() else []
    add("預告 Reel A、B reels/teaser_*", False, len(teasers) >= 1, ", ".join(t.name for t in teasers) or "none (optional)")

    # Threads
    th = d / "posts" / "threads"
    posts = sorted(th.glob("*.txt")) if th.exists() else []
    hook = [p for p in posts if "attach" not in p.name]
    att = [p for p in posts if "attach" in p.name]
    imgs = sorted(th.glob("*.jpg")) + sorted(th.glob("*.png")) if th.exists() else []
    notes = []
    for p in hook:
        t = read(p)
        if len(t) > LIMITS["threads"]:
            notes.append(f"{p.name} {len(t)} 字超過 500")
        if "[經驗]" in t:
            notes.append(f"{p.name} 有 [經驗]")
    if hook and num not in read(hook[0]):
        notes.append(f"{hook[0].name} 沒有「{num}」")
    for p in att:
        if len(read(p)) > LIMITS["attachment"]:
            notes.append(f"{p.name} 超過 10,000 字")
    add("Threads posts/threads", True, bool(hook) and bool(att) and bool(imgs) and not notes,
        f"鉤子 {len(hook)}、附件 {len(att)}、配圖 {len(imgs)}" + ("；" + "；".join(notes) if notes else ""))

    # Pinterest
    pin = d / "posts" / "pinterest"
    pins = sorted(pin.glob("*.jpg")) if pin.exists() else []
    notes = []
    try:
        from PIL import Image
        for p in pins:
            if Image.open(p).size != (1000, 1500):
                notes.append(f"{p.name} 不是 1000×1500")
    except ImportError:
        pass
    txt = read(pin / "pins.txt")
    for t in re.findall(r"標題[^：]*：(.+)", txt):
        if len(t.strip()) > LIMITS["pin_title"]:
            notes.append(f"標題超過 100 字：{t[:20]}…")
    add("Pinterest posts/pinterest", True, bool(pins) and bool(txt) and not notes,
        f"{len(pins)} 張" + ("；pins.txt OK" if txt else "；沒有 pins.txt") + ("；" + "；".join(notes) if notes else ""))

    # captions for YouTube / TikTok / Facebook
    cross = read(d / "posts" / "cross_caption.txt")
    notes = []
    if cross and num not in cross:
        notes.append(f"沒有「{num}」")
    if cross and "instagram.com" not in cross:
        notes.append("還沒有 IG 連結（IG 發出後補）")
    add("YouTube、TikTok、FB 文案 posts/cross_caption.txt", True, bool(cross) and not notes[:1],
        "；".join(notes) if notes else ("OK" if cross else "missing"))

    width = max(len(r[0]) for r in rows)
    bad = 0
    for item, req, ok, note in rows:
        mark = "✅" if ok else ("❌" if req else "－")
        if req and not ok:
            bad += 1
        print(f"{mark} {item.ljust(width)}  {note}")
    print(f"\n{num}：{'全部就緒' if not bad else f'{bad} 項要補'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
