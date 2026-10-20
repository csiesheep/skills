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
    slides = [s_ for s_ in slides if "_nonumber" not in s_.name]
    if slides and not (ig / "01_nonumber.jpg").exists():
        notes.append("01.jpg 還沒蓋號（ghost-pack）")
    add("IG 輪播 posts/ig", True, len(slides) >= 2 and bool(cap) and not notes,
        (f"{len(slides)} 張；" if slides else "沒有圖；") + ("；".join(notes) if notes else ("caption OK" if cap else "沒有 caption.txt")))

    # Reel full
    main_reel = d / "reels" / "full_v3_cinema" / "full_v3_cinema.mp4"
    add("Reel full reels/full_v3_cinema", True, main_reel.exists(),
        f"{main_reel.stat().st_size / 1e6:.0f} MB" if main_reel.exists() else "missing (ghost-reel)")

    # teasers (optional)
    teasers = [p for p in (d / "reels").glob("teaser_*") if p.is_dir() and list(p.glob("*.mp4"))] if (d / "reels").exists() else []
    add("預告 Reel A、B reels/teaser_*", False, len(teasers) >= 1, ", ".join(t.name for t in teasers) or "none (optional)")

    # Threads: hook.txt, attachment.txt, image.jpg
    th = d / "posts" / "threads"
    hook_t, att_t = read(th / "hook.txt"), read(th / "attachment.txt")
    notes = []
    if hook_t and len(hook_t) > LIMITS["threads"]:
        notes.append(f"hook.txt {len(hook_t)} 字超過 500")
    if "[經驗]" in hook_t + att_t:
        notes.append("有 [經驗]")
    if hook_t and num not in hook_t:
        notes.append(f"hook.txt 沒有「{num}」（ghost-pack）")
    if len(att_t) > LIMITS["attachment"]:
        notes.append("attachment.txt 超過 10,000 字")
    link_t = read(th / "link.txt")
    if link_t and "{ig_link}" not in link_t and "instagram.com" not in link_t:
        notes.append("link.txt 沒有 {ig_link} 也沒有 IG 連結")
    missing = [n for n, ok in (("hook.txt", hook_t), ("attachment.txt", att_t), ("image.jpg", (th / "image.jpg").exists()),
                               ("link.txt（ghost-pack）", link_t)) if not ok]
    add("Threads posts/threads", True, not missing and not notes,
        "；".join(([("缺 " + "、".join(missing))] if missing else []) + notes) or "OK")

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
    if pins and not (pin / "00_cover_nonumber.jpg").exists():
        notes.append("封面還沒蓋號（ghost-pack）")
    pins = [p_ for p_ in pins if "_nonumber" not in p_.name]
    reveal_page = None
    bj = d / "comic" / "board.json"
    if bj.exists():
        board = json.loads(bj.read_text(encoding="utf-8"))
        for k, page in enumerate(board.get("pages", []), 1):
            cells = [x for row in page.get("rows", []) for c in row.get("cells", []) for x in c.get("stack", [c])] + page.get("insets", [])
            if any(x.get("reveal") for x in cells):
                reveal_page = k; break
    if reveal_page:
        late = [p_.name for p_ in pins if re.match(r"(\d+)_page", p_.name) and int(re.match(r"(\d+)_page", p_.name).group(1)) >= reveal_page]
        if late:
            notes.append(f"揭露在第 {reveal_page} 頁，這些不能釘：{'、'.join(late)}")
    txt = read(pin / "pins.txt")
    for t in re.findall(r"標題[^：]*：(.+)", txt):
        if len(t.strip()) > LIMITS["pin_title"]:
            notes.append(f"標題超過 100 字：{t[:20]}…")
    add("Pinterest posts/pinterest", True, bool(pins) and bool(txt) and not notes,
        f"{len(pins)} 張" + ("；pins.txt OK" if txt else "；沒有 pins.txt") + ("；" + "；".join(notes) if notes else ""))

    # captions for YouTube / TikTok / Facebook
    # Before the Instagram post the link is an {ig_link} slot (ghost-pack writes it, ghost-post fills it): that is
    # ready, not missing. Only a caption with neither the slot nor a link is wrong.
    cross = read(d / "posts" / "cross_caption.txt")
    notes, info = [], []
    if cross and num not in cross:
        notes.append(f"沒有「{num}」")
    if cross and "{ig_link}" in cross:
        info.append("IG 連結留 {ig_link}，發完 IG 後填")
    elif cross and "instagram.com" not in cross:
        notes.append("沒有 {ig_link} 也沒有 IG 連結")
    add("YouTube、TikTok、FB 文案 posts/cross_caption.txt", True, bool(cross) and not notes,
        "；".join(notes + info) if notes or info else ("OK" if cross else "missing（ghost-pack）"))

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
