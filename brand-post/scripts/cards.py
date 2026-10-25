"""Render 4:5 slide cards (1080x1350) for an Instagram carousel / Facebook album / Threads images.

    py -X utf8 cards.py <spec.json>

spec.json:
{
  "out": "C:/.../posts/12",            # folder; writes 01.jpg, 02.jpg ... and contact.jpg
  "brand": "小羊遊戲間",                # footer left
  "series": "開發日記",                  # footer middle text after the brand (optional)
  "slides": [
    {"title": "如果投胎到中國歷史上？", "lines": ["first line (bold)", "second line"],
     "image": "C:/.../frame.jpg", "crop": [x0, y0, x1, y1]},     # image and crop optional
    {"title": "...", "lines": ["..."], "big": "42 × 49"}          # no image: a big number/phrase instead
  ]
}
Paper background, ink text, vermilion rule, the look of 生在中國's share card. Fonts: kaiu.ttf (titles),
msjh.ttc (text). A slide without image and without big gets its lines set larger in the middle.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
PAPER, INK, INK2, VERM, RULE = "#F3EBDD", "#1f1a14", "#4d4438", "#b3261e", "#c9ba9a"
FONTS = Path(r"C:/Windows/Fonts")
KAI = lambda s: ImageFont.truetype(str(FONTS / "kaiu.ttf"), s)
SANS = lambda s: ImageFont.truetype(str(FONTS / "msjh.ttc"), s)
SANSB = lambda s: ImageFont.truetype(str(FONTS / "msjhbd.ttc"), s)


def wrap(d, text, font, maxw):
    rows, cur = [], ""
    for ch in text:
        if cur and d.textlength(cur + ch, font=font) > maxw:
            rows.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        rows.append(cur)
    return rows


def fit_title(d, text, maxw, start=76):
    s = start
    while s > 40 and d.textlength(text, font=KAI(s)) > maxw:
        s -= 4
    return KAI(s)


def render(spec):
    out = Path(spec["out"])
    out.mkdir(parents=True, exist_ok=True)
    n = len(spec["slides"])
    foot = spec.get("brand", "小羊遊戲間") + (f" · {spec['series']}" if spec.get("series") else "")
    paths = []
    for i, sl in enumerate(spec["slides"], 1):
        im = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(im)
        d.rectangle([28, 28, W - 28, H - 28], outline=INK, width=4)
        d.rectangle([44, 44, W - 44, H - 44], outline=RULE, width=2)
        d.text((W / 2, 130), sl["title"], font=fit_title(d, sl["title"], W - 200), fill=INK, anchor="mm")
        d.line([W / 2 - 60, 190, W / 2 + 60, 190], fill=VERM, width=4)
        lines = sl.get("lines", [])
        if sl.get("image"):
            pic = Image.open(sl["image"]).convert("RGB")
            if sl.get("crop"):
                pic = pic.crop(tuple(sl["crop"]))
            px0, py0, px1, py1 = 90, 230, W - 90, 1000
            s = min((px1 - px0) / pic.width, (py1 - py0) / pic.height)
            pic = pic.resize((int(pic.width * s), int(pic.height * s)), Image.LANCZOS)
            x, y = px0 + (px1 - px0 - pic.width) // 2, py0 + (py1 - py0 - pic.height) // 2
            d.rectangle([x - 6, y - 6, x + pic.width + 5, y + pic.height + 5], outline=RULE, width=2)
            im.paste(pic, (x, y))
            y, f1, f2, step1, step2 = 1062, SANSB(44), SANS(36), 58, 50
        elif sl.get("big"):
            bf = KAI(150)
            while d.textlength(sl["big"], font=bf) > W - 200 and bf.size > 60:
                bf = KAI(bf.size - 10)
            d.text((W / 2, 560), sl["big"], font=bf, fill=VERM, anchor="mm")
            y, f1, f2, step1, step2 = 860, SANSB(48), SANS(40), 64, 56
        else:
            y, f1, f2, step1, step2 = 420, SANSB(54), SANS(44), 76, 66
        for j, ln in enumerate(lines):
            f, col, step = (f1, INK, step1) if j == 0 else (f2, INK2, step2)
            for r in wrap(d, ln, f, W - 180):
                d.text((W / 2, y), r, font=f, fill=col, anchor="mm")
                y += step
            y += 10
        d.text((80, H - 80), foot, font=SANS(26), fill=INK2, anchor="lm")
        d.text((W - 80, H - 80), f"{i} / {n}", font=SANS(26), fill=VERM, anchor="rm")
        p = out / f"{i:02d}.jpg"
        im.save(p, quality=92)
        paths.append(p)
    thumbs = [Image.open(p).resize((270, 338)) for p in paths]
    cols = min(4, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 285, rows * 353), "white")
    for k, t in enumerate(thumbs):
        sheet.paste(t, ((k % cols) * 285, (k // cols) * 353))
    sheet.save(out / "contact.jpg", quality=85)
    print("\n".join(str(p) for p in paths))
    print(out / "contact.jpg")


if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")))
