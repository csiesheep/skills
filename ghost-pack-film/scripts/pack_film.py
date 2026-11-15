"""Pack one finished ghost-film video for posting: its own number in the film ledger (「鬼唱詩劇場｜第 N 部」, apart from
the comics' 「第 N 首」), the number stamped on the film poster (and on each part's cover), every platform's caption.

    py -X utf8 pack_film.py <story folder> --brand-file <brand.json> --cover <poster.jpg> --full <full.mp4>
        [--parts <part1.mp4>,<part2.mp4>] [--logline "..."] [--title "..."] [--number N] [--ledger <copy>] [--ig-link URL]

1. Number: ghost-pack's ledger.py, on the brand file's "film_ledger" (kind film). The same title asked again keeps
   its number, so a rerun is safe.
2. Covers: posts/film/cover.jpg is the poster with the label line under the brand line; cover_part1.jpg and
   cover_part2.jpg add 「（上）」「（下）」. The poster itself is never changed.
3. Captions from the brand file's "film" block: caption_ig_part1/2.txt (or caption_ig.txt without parts),
   caption_full.txt (YouTube title and description, TikTok, Facebook), threads.txt and pins.txt. A link that
   does not exist yet stays as {ig_link} for ghost-post to fill.
4. posts/film/files.txt lists the video files to upload (absolute paths, never copied: the masters are ~450 MB);
   posts/film/README.md has the heading, status and logline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LEDGER_PY = HERE.parent.parent / "ghost-pack" / "scripts" / "ledger.py"
TAG = re.compile(r"^\s*\[(經驗|真實|翻譯|創作)\]\s*")
LIMITS = {"ig": 2200, "youtube_title": 100, "youtube_text": 5000, "tiktok": 2200, "threads": 500, "pin_title": 100}
FONT_L = "C:/Windows/Fonts/msjhl.ttc"
FFMPEG = "C:/Users/sheep/ffbin/ffmpeg.exe"
PIN_MAX_S = 300


def seconds(p: Path) -> float | None:
    """A video's length from ffmpeg's header read (there is no ffprobe here)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None


def write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip("\n") + "\n").encode("utf-8"))
    return text


def reserve(brand_file: Path, ledger: Path, title: str, folder: str, number: int | None) -> int:
    cmd = [sys.executable, "-X", "utf8", str(LEDGER_PY), "--ledger", str(ledger), "reserve", title, "--kind", "film",
           "--folder", folder] + (["--number", str(number)] if number is not None else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(r.stderr.strip() or r.stdout.strip())
    got = int(r.stdout.strip().splitlines()[-1])
    if number is not None and got != number:
        raise SystemExit(f"〈{title}〉 already has 第 {got} 部 in the film ledger; edit the ledger first to move it")
    return got


def stamp(poster: Path, out: Path, text: str) -> None:
    """The label as one spaced line under the poster's brand line (y 1640 of 1920), pale on the dark fade."""
    im = Image.open(poster).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_L, round(W * 0.043))
    gap = f.size * 0.18
    ws = [f.getlength(c) for c in text]
    x = (W - sum(ws) - gap * (len(text) - 1)) / 2
    y = round(H * 0.854)
    for c, w in zip(text, ws):
        d.text((x, y), c, font=f, fill=(228, 224, 214), stroke_width=3, stroke_fill=(0, 0, 0))
        x += w + gap
    im.save(out, quality=93)


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("--brand-file", required=True)
    ap.add_argument("--cover", required=True, help="the film poster (ghost-film poster.py), unnumbered")
    ap.add_argument("--full", required=True, help="the full video (1080x1920 master)")
    ap.add_argument("--parts", default=None, help="part1.mp4,part2.mp4 for Instagram (each under 3 min)")
    ap.add_argument("--title", default=None, help="default: story.md's first line without its [經驗] tag")
    ap.add_argument("--logline", default=None, help="one or two sentences: who, where, the strange thing; never the twist")
    ap.add_argument("--number", type=int, default=None)
    ap.add_argument("--ledger", default=None, help="another film ledger (a trial run); default: the brand file's film_ledger")
    ap.add_argument("--ig-link", default=None, help="fills {ig_link} once the Instagram post is out")
    a = ap.parse_args()

    d = Path(a.story).resolve()
    bf = Path(a.brand_file).resolve()
    br = json.loads(bf.read_text(encoding="utf-8"))
    fb = br.get("film")
    if not fb:
        raise SystemExit(f"{bf} has no \"film\" block")
    ledger = Path(a.ledger).resolve() if a.ledger else (bf.parent / br.get("film_ledger", "film_ledger.json")).resolve()
    title = a.title or TAG.sub("", (d / "story.md").read_text(encoding="utf-8").split("\n", 1)[0]).strip()
    out = d / "posts" / "film"
    readme = out / "README.md"
    logline = a.logline
    if not logline and readme.exists():
        hit = re.search(r"^- 一句話：(.+)$", readme.read_text(encoding="utf-8"), re.M)
        logline = hit.group(1).strip() if hit else None
    if not logline:
        raise SystemExit("give --logline (who, where, the strange thing; never the twist)")
    folder = d.relative_to(bf.parent.parent).as_posix() if bf.parent.parent in d.parents else d.name
    n = reserve(bf, ledger, title, folder, a.number)
    label = fb["label"].format(n=n)
    heading = fb["title"].format(label=label, title=title)
    v = {"name": br["name"], "handle": br.get("handle", ""), "disclosure": br["disclosure"], "label": label,
         "title": title, "heading": heading, "logline": logline, "ig_link": a.ig_link or "{ig_link}", "part_line": ""}
    fill = lambda t, extra=None: t.format(**{**v, **(extra or {})})
    tags = " ".join(fb.get("tags", []))
    report = []

    # covers
    out.mkdir(parents=True, exist_ok=True)
    stamp(Path(a.cover), out / "cover.jpg", label)
    report.append(("封面 cover.jpg", f"「{label}」"))
    parts = [Path(p) for p in a.parts.split(",")] if a.parts else []
    for k, _ in enumerate(parts, 1):
        key = f"part{k}"
        stamp(Path(a.cover), out / f"cover_{key}.jpg", label + fb["parts"][key])
        report.append((f"封面 cover_{key}.jpg", f"「{label}{fb['parts'][key]}」"))

    # Instagram, one caption per part (or one for the whole video)
    for k in range(1, len(parts) + 1) if parts else [0]:
        key = f"part{k}" if k else ""
        h = fill(fb["title"], {"label": label + (fb["parts"][key] if key else "")})
        pl = fill(fb["part_lines"][key]) if key else ""
        body = [h, ""] + [fill(x, {"part_line": pl}) for x in fb["ig_lines"]]
        body = [x for i, x in enumerate(body) if not (x == "" and i > 0 and body[i - 1] == "")]   # no double blank where part_line is empty
        t = write(out / f"caption_ig{'_' + key if key else ''}.txt", "\n".join(body) + "\n\n" + tags)
        report.append((f"IG caption_ig{'_' + key if key else ''}.txt", f"{len(t)} 字" + ("，超過 2200！" if len(t) > LIMITS["ig"] else "")))

    # the full video: YouTube, TikTok, Facebook
    yt_title = heading
    yt = "\n".join(fill(x) for x in fb["youtube_lines"]) + "\n\n" + tags
    tk = "\n".join(fill(x) for x in fb["tiktok_lines"]) + "\n" + tags
    fbk = "\n".join(fill(x) for x in fb["facebook_lines"]) + "\n\n" + tags
    write(out / "caption_full.txt", f"== YouTube 標題（{len(yt_title)}）==\n{yt_title}\n\n== YouTube 說明 ==\n{yt}\n\n"
                                    f"== TikTok ==\n{tk}\n\n== Facebook ==\n{fbk}")
    report.append(("完整版 caption_full.txt", f"YouTube 標題 {len(yt_title)} 字，TikTok {len(tk)} 字"
                   + ("，YouTube 標題超過 100！" if len(yt_title) > LIMITS["youtube_title"] else "")))

    th = "\n".join(fill(x) for x in fb["threads_lines"]) + "\n" + tags
    write(out / "threads.txt", th)
    report.append(("Threads threads.txt", f"{len(th)} 字" + ("，超過 500！" if len(th) > LIMITS["threads"] else "")))

    pc = fb["pinterest"]
    ptext = "\n".join(fill(x) for x in pc["lines"]) + "\n" + tags
    # Pinterest refuses videos over 300 s (第 1 部, 2026-11-11): pin the full cut only when it fits, else IG part 1
    pin_video = next((p for p in [Path(a.full)] + parts[:1] if (seconds(p) or 1e9) <= PIN_MAX_S), None)
    pins = [f"板：{fill(pc['board'])}", "連結：" + v["ig_link"], "",
            "== cover.jpg ==", f"標題：{fill(pc['title_cover'])}", "說明：", ptext]
    if pin_video:
        pins += ["", f"== 影片 {pin_video.name}（{seconds(pin_video):.0f} 秒） ==", f"標題：{fill(pc['title_video'])}", "說明：", ptext]
    write(out / "pins.txt", "\n".join(pins))
    report.append(("Pinterest pins.txt", f"板「{fill(pc['board'])}」，封面＋" +
                   (f"影片 {pin_video.name}" if pin_video else f"沒有影片 pin（每支都超過 {PIN_MAX_S} 秒）")))

    def up(p: Path) -> str:   # the 720p copy is what goes up: Claude in Chrome's file_upload takes 10 MB a call
        c = p.with_name(p.stem + "_preview720.mp4")
        return f"{p.resolve()}\n  上傳用 720p：{c.resolve()}（{c.stat().st_size / 1e6:.1f} MB）" if c.exists() else f"{p.resolve()}\n  上傳用 720p：沒有（ghost-film package.py）"
    files = [f"完整版（YouTube、Facebook）：{up(Path(a.full))}"]
    files += [f"IG {fb['parts'][f'part{k}']}：{up(p)}" for k, p in enumerate(parts, 1)]
    write(out / "files.txt", "\n".join(files))
    today = dt.date.today().isoformat()
    write(readme, f"# {heading}\n\n- 狀態：{today} 已包裝（ghost-pack-film），待發\n- 一句話：{logline}\n"
                  f"- 編號以 brand/{ledger.name} 為準（影片另編，跟漫畫的第 N 首分開）\n- 檔案：files.txt\n")
    report.append(("README.md", heading))

    print(f"{heading}  ({folder})  ledger: {ledger}")
    w = max(len(r[0]) for r in report)
    for item, note in report:
        print(f"  {item.ljust(w)}  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
