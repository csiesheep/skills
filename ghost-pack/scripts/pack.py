"""Pack one finished story for posting: give it its number, stamp the number on the two covers, write every
platform's caption.

    py -X utf8 pack.py <story folder> --brand-file <brand.json> [--number N] [--logline "..."] [--title "..."]

1. Number: `ledger.py reserve` by title (the same title asked again keeps its number; --number asks for a specific
   one, e.g. to put a story ahead of another).
2. Stamp: posts/ig/01.jpg gets the brand's cover strip (「鬼唱詩｜第 N 首」) in ghost-comic's font and place; the
   unstamped original is kept as 01_nonumber.jpg and every run stamps from it, so a new number is a rerun.
   posts/pinterest/00_cover.jpg is rebuilt from the stamped 01.jpg (the old one kept as 00_cover_nonumber.jpg).
3. Captions, all from the brand file's templates: posts/ig/caption.txt; the first line of posts/threads/hook.txt
   and attachment.txt; posts/threads/link.txt (the third Threads post); posts/pinterest/pins.txt; and
   posts/cross_caption.txt (YouTube title and description, TikTok, Facebook). The Instagram post's link does not
   exist yet, so captions carry an {ig_link} slot that ghost-post fills after posting on Instagram.
4. README.md: heading 「第 N 首〈title〉」, status, the logline.

Folder contract: C:/Users/sheep/Pictures/gui_chang_shi/README.md. Needs Pillow and ghost-comic next to this skill
(its manga.py draws the strip, so the stamp matches what ghost-comic's export draws with --number).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
LIMITS = {"threads": 500, "attachment": 10000, "ig_caption": 2200, "pin_title": 100, "pin_text": 500,
          "youtube_title": 100, "youtube_text": 5000, "tiktok": 2200}
TAG = re.compile(r"^\s*\[(經驗|真實|翻譯|創作)\]\s*")

# Used when the brand file has no block of its own. 鬼唱詩's brand.json carries the same blocks, so edit them there.
DEFAULTS = {
    "threads": {"link_post": "全篇漫畫和影片在 IG：{ig_link}"},
    "pinterest": {
        "board": "{name}｜台灣怪談漫畫",
        "title_cover": "台灣怪談漫畫｜{number} {title}",
        "title_page": "台灣怪談漫畫｜{title}（{k}/{pages}）",
        "lines": ["{logline}", "{disclosure}。全篇在 IG {handle}。"],
        "tags": ["#台灣怪談", "#鬼故事", "#恐怖漫畫", "#漫畫", "#鬼唱詩"],
    },
    "cross": {
        "title": "{number}｜{title}",
        "youtube_lines": ["{logline}", "", "{disclosure}", "全篇漫畫：{ig_link}", "傳給那個說自己不怕的朋友。"],
        "tiktok_lines": ["{number}｜{title}", "{logline}", "{disclosure}", "全篇漫畫在 IG {handle}"],
        "facebook_lines": ["{number}｜{title}", "", "{logline}", "", "{disclosure}", "全篇漫畫：{ig_link}",
                           "傳給那個說自己不怕的朋友。"],
    },
}


def manga_module():
    """ghost-comic's manga.py, from the skill folder next to this one (the repo and ~/.claude/skills alike)."""
    d = HERE.parent.parent / "ghost-comic" / "scripts"
    if not (d / "manga.py").exists():
        raise SystemExit(f"ghost-comic not found at {d}: ghost-pack draws the cover strip with its code")
    sys.path.insert(0, str(d))
    old, sys.argv = sys.argv, [sys.argv[0]]
    try:
        import manga
    finally:
        sys.argv = old
    return manga


def fill(template: str, v: dict) -> str:
    return template.format(**v)


def block(br: dict, name: str) -> dict:
    return {**DEFAULTS[name], **br.get(name, {})}


def reserve(brand_file: str, ledger: str | None, title: str, kind: str, folder: str, number: int | None) -> int:
    cmd = [sys.executable, "-X", "utf8", str(HERE / "ledger.py"), "--brand-file", brand_file]
    cmd += ["--ledger", ledger] if ledger else []
    cmd += ["reserve", title, "--kind", kind, "--folder", folder] + (["--number", str(number)] if number is not None else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(r.stderr.strip() or r.stdout.strip())
    got = int(r.stdout.strip().splitlines()[-1])
    if number is not None and got != number:
        raise SystemExit(f"〈{title}〉 already has 第 {got} 首 in the ledger; to move it, edit the ledger first")
    return got


def stamp_cover(path: Path, br: dict, number: int, m) -> None:
    """Redraw the cover strip's big line from the unstamped backup, where ghost-comic's brand_cover draws it."""
    backup = path.with_name(path.stem + "_nonumber.jpg")
    if not backup.exists():
        shutil.copy2(path, backup)
    im = Image.open(backup).convert("RGB")
    w, h = im.size
    margin, strip = round(w * 0.05), round(h * 0.11)
    top = h - margin - strip + round(strip * 0.22)
    big = m._serif(round(w / 23))
    seal = round(strip * 0.8)
    c = br["rgb"]
    d = ImageDraw.Draw(im)
    d.rectangle([margin, top - round(big.size * 0.1), w - margin - seal - 8, top + round(big.size * 1.3)], fill=c["paper"])
    d.text((margin, top), m.brand_text(br.get("cover_strip", "{name}｜{number}"), br, number), font=big, fill=c["ink"])
    im.save(path, quality=92)


def set_heading(path: Path, heading: str, title: str) -> str:
    """Replace the first line (the bare title, or an older heading ending in it) with the numbered heading."""
    text = path.read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    if not first.strip().endswith(title):
        raise SystemExit(f"{path}: first line 「{first}」 is not the story's title; rerun ghost-story post --dest")
    out = heading + "\n" + rest
    path.write_bytes(out.encode("utf-8"))
    return out


def write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip("\n") + "\n").encode("utf-8"))
    return text


def first_sentence(hook: str) -> str:
    """The hook post's first sentence after its two heading lines: the default logline."""
    body = hook.split("\n\n", 1)[1] if "\n\n" in hook else hook
    m = re.match(r".+?[。！？」](?![」』])", body.strip().replace("\n", ""))
    return m.group(0) if m else body.strip().split("\n")[0]


def update_readme(path: Path, heading: str, logline: str, today: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# x\n\n- 連結：還沒發\n\n編號以 ../../brand/ledger.json 為準。\n"
    lines = text.split("\n")
    lines[0] = f"# {heading}"
    found = set()
    for i, ln in enumerate(lines):
        if ln.startswith("- 狀態："):
            lines[i] = f"- 狀態：{today} 已包裝（ghost-pack），待發"
            found.add("狀態")
        elif ln.startswith("- 一句話："):
            lines[i] = f"- 一句話：{logline}"
            found.add("一句話")
    at = next((i for i, ln in enumerate(lines) if ln.startswith("- ")), 2)
    if "一句話" not in found:
        lines.insert(at, f"- 一句話：{logline}")
    if "狀態" not in found:
        lines.insert(at, f"- 狀態：{today} 已包裝（ghost-pack），待發")
    path.write_bytes("\n".join(lines).encode("utf-8"))


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", help="the story folder, e.g. .../gui_chang_shi/stories/name_call")
    ap.add_argument("--brand-file", required=True)
    ap.add_argument("--number", type=int, default=None, help="a specific number; default: the ledger's (next free)")
    ap.add_argument("--title", default=None, help="default: story.md's first line without its [經驗] tag")
    ap.add_argument("--logline", default=None,
                    help="one or two sentences for Pinterest, YouTube, TikTok and Facebook (default: the README's "
                         "「一句話」, else the hook's first sentence)")
    ap.add_argument("--ledger", default=None, help="another ledger file (for a trial run); default: the brand file's")
    a = ap.parse_args()

    m = manga_module()
    d = Path(a.story).resolve()
    br = m.load_brand(a.brand_file)
    posts = d / "posts"
    title = a.title or TAG.sub("", (d / "story.md").read_text(encoding="utf-8").split("\n", 1)[0]).strip()
    kind = "comic" if (posts / "ig" / "01.jpg").exists() else "text"
    folder = d.relative_to(Path(a.brand_file).resolve().parent.parent).as_posix() \
        if Path(a.brand_file).resolve().parent.parent in d.parents else d.name
    n = reserve(a.brand_file, a.ledger, title, kind, folder, a.number)
    num = br["number"].format(n=n)
    readme = d / "README.md"
    logline, src = a.logline, "--logline"
    if not logline and readme.exists():
        hit = re.search(r"^- 一句話：(.+)$", readme.read_text(encoding="utf-8"), re.M)
        logline, src = (hit.group(1).strip(), "README 的「一句話」") if hit else (None, "")
    hook_p, att_p = posts / "threads" / "hook.txt", posts / "threads" / "attachment.txt"
    if not logline and hook_p.exists():
        logline, src = first_sentence(hook_p.read_text(encoding="utf-8")), "鉤子第一句（沒給 --logline）"
    v = {"name": br["name"], "handle": br.get("handle", ""), "disclosure": br["disclosure"], "number": num,
         "title": title, "logline": logline or "", "ig_link": "{ig_link}"}
    report = []

    # 2. the two covers
    ig = posts / "ig"
    if kind == "comic":
        covers = sorted(p for p in ig.glob("*01.jpg") if "_nonumber" not in p.name)
        for p in covers:
            stamp_cover(p, br, n, m)
        report.append(("IG 封面", f"蓋上「{m.brand_text(br.get('cover_strip', '{name}｜{number}'), br, n)}」：" +
                       "、".join(p.name for p in covers)))
        pin_cover = posts / "pinterest" / "00_cover.jpg"
        if pin_cover.exists():
            bk = pin_cover.with_name("00_cover_nonumber.jpg")
            if not bk.exists():
                shutil.copy2(pin_cover, bk)
            m.pin_fit(Image.open(covers[0]), m.PIN_MARGIN["cover"], br["rgb"]["paper"]).save(pin_cover, quality=92)
            report.append(("Pinterest 封面", "用蓋好號的 01.jpg 重做"))

        # 3a. Instagram caption, as ghost-comic's export writes it
        cfg = br.get("caption", {})
        cap = [m.brand_text(cfg.get("title", "{number}｜{title}"), br, n, title), ""]
        cap += [m.brand_text(x, br, n, title) for x in cfg.get("lines", ["{disclosure}"])]
        cap += ["", " ".join(cfg.get("tags", []))]
        t = write(ig / "caption.txt", "\n".join(cap))
        report.append(("IG 文案 posts/ig/caption.txt", f"{len(t)} 字"))

    # 3b. Threads
    st = br.get("story", {})
    heading = st.get("title", "{number}｜{title}").format(number=num, title=title, name=br["name"])
    if hook_p.exists():
        t = set_heading(hook_p, heading, title).rstrip("\n")
        warn = f"，超過 {LIMITS['threads']}！重跑 ghost-story post --limit {LIMITS['threads'] - (len(t) - LIMITS['threads'])}" \
            if len(t) > LIMITS["threads"] else ""
        report.append(("Threads 鉤子 hook.txt", f"第一行「{heading}」，{len(t)} 字{warn}"))
    else:
        report.append(("Threads 鉤子 hook.txt", "沒有：ghost-story post --dest"))
    if att_p.exists():
        t = set_heading(att_p, heading, title).rstrip("\n")
        report.append(("Threads 附件 attachment.txt", f"{len(t)} 字"))
    t = write(posts / "threads" / "link.txt", fill(block(br, "threads")["link_post"], v))
    report.append(("Threads 第 3 則 link.txt", t))

    # 3c. Pinterest
    pdir = posts / "pinterest"
    pins = sorted(p for p in pdir.glob("*.jpg") if "_nonumber" not in p.name) if pdir.exists() else []
    if pins:
        pc = block(br, "pinterest")
        pages = len(list((d / "comic" / "out" / "pages").glob("page_*.png"))) or max(len(list(ig.glob("[0-9]*.jpg"))) - 2, 1)
        text = "\n".join(fill(x, v) for x in pc["lines"]) + "\n" + " ".join(pc["tags"])
        out = [f"板：{fill(pc['board'], v)}", "連結：{ig_link}（IG 那則輪播，ghost-post 發完 IG 後填）", ""]
        for p in pins:
            k = re.match(r"(\d+)_page", p.name)
            ttl = fill(pc["title_page"], {**v, "k": int(k.group(1)), "pages": pages}) if k else fill(pc["title_cover"], v)
            out += [f"== {p.name} ==", f"標題（{len(ttl)}）：{ttl}", f"說明（{len(text)}）：", text, ""]
            if len(ttl) > LIMITS["pin_title"]:
                report.append(("Pinterest 標題", f"{p.name} {len(ttl)} 字超過 100！"))
        write(pdir / "pins.txt", "\n".join(out))
        report.append(("Pinterest pins.txt", f"{len(pins)} 張"))

    # 3d. YouTube, TikTok, Facebook
    cc = block(br, "cross")
    tags = " ".join(br.get("reel", {}).get("tags") or br.get("caption", {}).get("tags", []))
    yt_title = fill(cc["title"], v)
    yt = "\n".join(fill(x, v) for x in cc["youtube_lines"]) + "\n\n" + tags
    tk = "\n".join(fill(x, v) for x in cc["tiktok_lines"]) + "\n" + tags
    fb = "\n".join(fill(x, v) for x in cc["facebook_lines"]) + "\n\n" + tags
    write(posts / "cross_caption.txt", f"== YouTube 標題（{len(yt_title)}）==\n{yt_title}\n\n== YouTube 說明 ==\n{yt}\n\n"
                                       f"== TikTok ==\n{tk}\n\n== Facebook ==\n{fb}")
    report.append(("YouTube、TikTok、FB posts/cross_caption.txt", f"YouTube 標題 {len(yt_title)} 字，IG 連結留 {{ig_link}}"))

    # 4. README
    update_readme(readme, f"{num}〈{title}〉", logline or "", dt.date.today().isoformat())
    report.append(("README.md", f"# {num}〈{title}〉"))

    print(f"{num}〈{title}〉  ({folder})")
    print(f"一句話（{src}）：{logline}")
    width = max(len(r[0]) for r in report)
    for item, note in report:
        print(f"  {item.ljust(width)}  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
