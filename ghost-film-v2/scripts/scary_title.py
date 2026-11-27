"""Scary title treatments from fonts already on this PC (A 標楷腐蝕斑駁, B 粗明體滴落, C 黑體錯位重影, D 標楷褪色符咒冷光).
The owner picked D for 上鋪的腳 (2026-11-07). Used as a library by title_fx.py and poster.py; run alone with a 9:16 background:
py -X utf8 scary_title.py <bg.png>  -> title_options.jpg (GF_TITLE sets the text)"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
rng = np.random.default_rng(3)
import os
T = os.environ.get("GF_TITLE", "上鋪的腳")
W, H = 1080, 1920
def mask(font, size, text=T, pad=60, weight=None):
    f = ImageFont.truetype(font, size)
    if weight:
        f.set_variation_by_name(weight)
    w = int(f.getlength(text)) + pad * 2
    m = Image.new("L", (w, size + pad * 2), 0)
    ImageDraw.Draw(m).text((pad, pad - size * 0.08), text, font=f, fill=255)
    return m
def erode(m, k=0.9):
    """ragged, corroded edges and pitted holes"""
    a = np.asarray(m).astype(np.float32) / 255
    n = rng.random(a.shape)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
    edge = np.asarray(m.filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    a = np.where(edge * (0.55 + n * k) > 0.5, a, 0)
    holes = rng.random(a.shape) < 0.012
    holes = np.asarray(Image.fromarray((holes * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    a[holes] *= 0.15
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
def drip(m, n=26, maxlen=170):
    a = np.asarray(m).copy()
    h, w = a.shape
    cols = np.where(a.max(axis=0) > 128)[0]
    for x in rng.choice(cols, n):
        ys = np.where(a[:, x] > 128)[0]
        if not len(ys): continue
        y0 = ys.max(); L = int(rng.uniform(25, maxlen)); r = int(rng.uniform(3, 7))
        for y in range(y0, min(h - 1, y0 + L)):
            rr = max(1, int(r * (1 - (y - y0) / L * 0.6)))
            a[y, max(0, x - rr):x + rr] = 255
        yy = min(h - 1, y0 + L); a[max(0, yy - r):yy + r, max(0, x - r - 1):x + r + 1] = 255
    return Image.fromarray(a)
def place(bg, m, color, y, glow=None, shadow=None, offsets=()):
    im = bg.copy().convert("RGBA")
    x = (W - m.width) // 2
    for dx, dy, col in offsets:
        layer = Image.new("RGBA", m.size, col); im.alpha_composite(Image.merge("RGBA", (*layer.split()[:3], m.point(lambda v: v * col[3] // 255))), (x + dx, y + dy))
    if glow:
        g = m.filter(ImageFilter.GaussianBlur(glow[1]))
        layer = Image.new("RGBA", m.size, glow[0]); im.alpha_composite(Image.merge("RGBA", (*layer.split()[:3], g)), (x, y))
    if shadow:
        s = m.filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.9)
        layer = Image.new("RGBA", m.size, (0, 0, 0, 255)); im.alpha_composite(Image.merge("RGBA", (*layer.split()[:3], s)), (x + 6, y + 8))
    layer = Image.new("RGBA", m.size, color); im.alpha_composite(Image.merge("RGBA", (*layer.split()[:3], m)), (x, y))
    return im
if __name__ == "__main__":
    import sys
    bg = Image.open(sys.argv[1]).convert("RGB").resize((W, H), Image.LANCZOS)
    r, g, b = bg.split(); bg = Image.merge("RGB", (r.point(lambda v: v * 0.85), g.point(lambda v: v * 0.93), b.point(lambda v: min(255, v * 1.1))))
    Y = 1230
    opts = {}
    m = erode(mask("C:/Windows/Fonts/kaiu.ttf", 190)); opts["A 標楷・腐蝕斑駁"] = place(bg, m, (232, 226, 212, 255), Y, shadow=True)
    m = drip(erode(mask("C:/Windows/Fonts/NotoSerifTC-VF.ttf", 180, weight="Black"), 0.35), n=11, maxlen=140); opts["B 粗明體・滴落"] = place(bg, m, (165, 20, 18, 255), Y, glow=((0, 0, 0, 255), 10))
    m = mask("C:/Windows/Fonts/msjhbd.ttc", 175)
    opts["C 黑體・錯位重影"] = place(bg, erode(m, 0.4), (240, 240, 236, 255), Y, offsets=[(-14, 0, (200, 20, 30, 170)), (12, 4, (40, 160, 200, 150))])
    m = erode(mask("C:/Windows/Fonts/kaiu.ttf", 200), 0.6); opts["D 標楷・褪色符咒冷光"] = place(bg, m, (214, 230, 236, 235), Y, glow=((120, 190, 220, 255), 18))
    # try the variable serif at its heaviest weight for B
    tiles = []
    for name, im in opts.items():
        t = im.convert("RGB").crop((0, 1000, W, 1700)).resize((540, 350), Image.LANCZOS)
        d = ImageDraw.Draw(t); d.text((10, 8), name, font=ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 30), fill=(255, 230, 80))
        tiles.append(t); im.convert("RGB").save(f"cover_{name[0]}.jpg", quality=90)
    s = Image.new("RGB", (1090, 710), "#222")
    for k, t in enumerate(tiles): s.paste(t, (5 + (k % 2) * 545, 5 + (k // 2) * 355))
    s.save("title_options.jpg", quality=90)
