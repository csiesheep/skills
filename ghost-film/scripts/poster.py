"""Film-poster cover (1080x1920): a graded still, a tagline at the top, the title in the D treatment (標楷, worn, cold glow) and
under it one line only, the brand icon and 鬼唱詩 (owner, 2026-11-07: 「上鋪的腳 下方，只用一行 鬼唱詩 icon 鬼唱詩」).
py -X utf8 poster.py <bg.png> <out.jpg> --title 上鋪的腳 --tagline 每天半夜，它都垂下來。 [--focus 0.5,0.4] [--lift 1.15]
The grade: teal shadows and warm highlights, crushed blacks, film grain, vignette, a dark fade at the bottom, a few faint
scratches."""
import argparse, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ap = argparse.ArgumentParser()
ap.add_argument("bg"); ap.add_argument("out"); ap.add_argument("--title", default="上鋪的腳"); ap.add_argument("--tagline", default="")
ap.add_argument("--focus", default="0.5,0.4"); ap.add_argument("--lift", type=float, default=1.15); ap.add_argument("--title-y", type=int, default=1240)
a = ap.parse_args()
os.environ["GF_TITLE"] = a.title
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scary_title as st  # noqa: E402
W, H = 1080, 1920
rng = np.random.default_rng(11)
FONT_B = "C:/Windows/Fonts/msjhbd.ttc"; FONT_L = "C:/Windows/Fonts/msjhl.ttc"; KAI = "C:/Windows/Fonts/kaiu.ttf"
ICON = "C:/Users/sheep/Pictures/gui_chang_shi/brand/avatar/final/avatar_circle_1024.png"

def cover_fit(im, focus):
    r = W / H; w, h = im.size
    if w / h > r: nw = h * r; box = ((w - nw) * focus[0], 0, (w - nw) * focus[0] + nw, h)
    else: nh = w / r; box = (0, (h - nh) * focus[1], w, (h - nh) * focus[1] + nh)
    return im.crop(tuple(map(round, box))).resize((W, H), Image.LANCZOS)

def grade(im, lift):
    x = np.clip(np.asarray(im).astype(np.float32) / 255 * lift, 0, 1) ** 1.12
    lum = x.mean(axis=2, keepdims=True)
    x = x * (np.array([0.80, 0.95, 1.12]) * (1 - lum) + np.array([1.08, 1.0, 0.9]) * lum)
    x = lum + (x - lum) * 0.85
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.42) / (H / 2)) ** 2)
    x *= np.clip(1.15 - 0.62 * d ** 1.6, 0.18, 1)[..., None]
    g = rng.normal(0, 0.035, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g + 0.5) * 255).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32)[..., None] / 255 - 0.5
    x = x + g * 0.9
    t = np.clip((np.arange(H) / H - 0.5) / 0.5, 0, 1) ** 1.3
    x *= (1 - 0.88 * t)[:, None, None]
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))

def spaced(d, text, font, y, fill, spacing):
    ws = [font.getlength(c) for c in text]; gap = font.size * spacing
    x = (W - sum(ws) - gap * (len(text) - 1)) / 2
    for c, w_ in zip(text, ws):
        d.text((x, y), c, font=font, fill=fill); x += w_ + gap

im = grade(cover_fit(Image.open(a.bg).convert("RGB"), tuple(map(float, a.focus.split(",")))), a.lift).convert("RGBA")
d = ImageDraw.Draw(im, "RGBA")
for _ in range(5):
    x = rng.uniform(0, W); y0 = rng.uniform(0, H * 0.6); L = rng.uniform(40, 220)
    d.line([(x, y0), (x + rng.uniform(-4, 4), y0 + L)], fill=(255, 255, 255, int(rng.uniform(6, 13))), width=1)
if a.tagline:
    spaced(d, a.tagline, ImageFont.truetype(FONT_L, 44), 150, (225, 222, 214), 0.45)
size = 232   # 上鋪的腳 (4 characters) at 232; a longer title shrinks to fit, and erodes less so thin strokes survive
while size > 90 and st.mask(KAI, size, text=a.title).width > W - 20:
    size -= 6
m = st.erode(st.mask(KAI, size, text=a.title), min(0.9, 0.32 * (232 / size) ** 2))
x = (W - m.width) // 2; y = a.title_y
for col, mm in (((110, 180, 215, 255), m.filter(ImageFilter.GaussianBlur(22))), ((226, 236, 240, 255), m)):
    layer = Image.new("RGBA", m.size, col); im.alpha_composite(Image.merge("RGBA", (*layer.split()[:3], mm)), (x, y))
f2 = ImageFont.truetype(FONT_B, 60); ic = Image.open(ICON).convert("RGBA").resize((96, 96), Image.LANCZOS)
rw = 96 + 24 + f2.getlength("鬼唱詩"); x0 = (W - rw) / 2; yb = y + m.height - 45
im.alpha_composite(ic, (round(x0), yb)); d.text((x0 + 120, yb + 8), "鬼唱詩", font=f2, fill=(232, 236, 238), stroke_width=4, stroke_fill=(0, 0, 0))
im.convert("RGB").save(a.out, quality=93); print(a.out)
