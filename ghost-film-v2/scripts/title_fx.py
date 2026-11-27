"""Three animated treatments of the poster title (D: 標楷, worn, cold glow) for the title shot of the reel.
py -X utf8 title_fx.py <clip.mp4>  -> title_fx_1.mp4 (霧中浮現), _2 (訊號干擾), _3 (垂吊搖晃) and title_fx_sheet.jpg
The title text is GF_TITLE (environment variable), default 上鋪的腳
Also importable: frame(kind, t, base_rgb) -> RGB frame, used by render.py."""
import math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scary_title as st
W, H, FPS = 1080, 1920, 30
KAI = "C:/Windows/Fonts/kaiu.ttf"; FONT_B = "C:/Windows/Fonts/msjhbd.ttc"
ICON = "C:/Users/sheep/Pictures/gui_chang_shi/brand/avatar/final/avatar_circle_1024.png"
COL = np.array([226, 236, 240], np.float32); GLOW = np.array([110, 180, 215], np.float32)
TY = 560   # top of the title box
_t = os.environ.get("GF_TITLE", "上鋪的腳")
_m = st.erode(st.mask(KAI, 200, text=_t), 0.32)
if _m.width > W - 80:   # long titles shrink to fit the frame; the wear shrinks with them, or thin strokes break apart
    _sz = int(200 * (W - 80) / _m.width)   # (社辦門上的氣窗 at 0.32 read as scattered dots: review 2, 2026-11-09)
    _m = st.erode(st.mask(KAI, _sz, text=_t), min(0.9, 0.32 * (200 / _sz) ** 2))   # erode keeps more as k grows
MASK = np.asarray(_m).astype(np.float32) / 255
MX = (W - _m.width) // 2
GLOWM = np.asarray(_m.filter(ImageFilter.GaussianBlur(22))).astype(np.float32) / 255
# per-character boxes (for the hanging treatment): split the mask into 4 columns at the gaps
cols = MASK.max(axis=0) > 0.1
xs = np.where(cols)[0]; segs = []; s0 = xs[0]
for a, b in zip(xs[:-1], xs[1:]):
    if b - a > 12: segs.append((s0, a + 1)); s0 = b
segs.append((s0, xs[-1] + 1))
# brand line
_f2 = ImageFont.truetype(FONT_B, 54)
BRAND = Image.new("RGBA", (W, 110), (0, 0, 0, 0)); _d = ImageDraw.Draw(BRAND)
_ic = Image.open(ICON).convert("RGBA").resize((86, 86), Image.LANCZOS)
_rw = 86 + 20 + _f2.getlength("鬼唱詩"); _x0 = (W - _rw) / 2
BRAND.alpha_composite(_ic, (round(_x0), 10)); _d.text((_x0 + 106, 18), "鬼唱詩", font=_f2, fill=(232, 236, 238), stroke_width=4, stroke_fill=(0, 0, 0))
BY = TY + _m.height - 40
rng = np.random.default_rng(2)
NOISE = np.asarray(Image.fromarray((rng.random((MASK.shape[0] // 6 + 1, MASK.shape[1] // 6 + 1)) * 255).astype(np.uint8))
                   .resize((MASK.shape[1], MASK.shape[0]), Image.BICUBIC)).astype(np.float32) / 255

def comp(base, mask, glowm, x, y, a=1.0, col=COL, glow_a=1.0):
    out = base.astype(np.float32)
    h, w = mask.shape
    sub = out[y:y + h, x:x + w]
    g = (glowm * glow_a * a)[..., None]
    sub[:] = sub * (1 - g * 0.85) + GLOW * g * 0.85
    m = (mask * a)[..., None]
    sub[:] = sub * (1 - m) + col * m
    return out

def brand(img, a):
    if a <= 0: return img
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    b = BRAND.copy(); b.putalpha(b.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(b, (0, BY)); return np.asarray(im.convert("RGB")).astype(np.float32)

def ease(t): t = min(1, max(0, t)); return t * t * (3 - 2 * t)

def frame(kind, t, base, dur=3.5):
    """t in seconds from the title's start; base: HxWx3 uint8. Fades out over the last 0.5 s of dur."""
    out_a = min(1, max(0, (dur - t) / 0.5))
    img = base.astype(np.float32)
    if kind == 1:   # 霧中浮現: dissolves in out of noise, then the glow breathes
        thr = ease(t / 1.6)
        reveal = np.clip((thr * 1.25 - NOISE) / 0.18, 0, 1)
        m = MASK * reveal
        blur = max(0, 1 - t / 1.4)
        if blur > 0.02:
            m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6 * blur))).astype(np.float32) / 255
        breath = 0.75 + 0.35 * math.sin(t * 2 * math.pi / 1.6)
        img = comp(img, m, GLOWM * reveal, MX, TY, out_a, glow_a=breath)
        img = brand(img, ease((t - 1.3) / 0.6) * out_a)
    elif kind == 2:   # 訊號干擾: torn, split, flickering, then it settles and twitches now and then
        on = t > 0.15
        settle = ease((t - 0.2) / 1.2)
        glitchy = (1 - settle) + (0.8 if (int(t * FPS) % 37) in (0, 1) else 0)
        if on and not (glitchy > 0.5 and rng.random() < 0.18):
            m = MASK.copy()
            if glitchy > 0.05:
                for _ in range(int(3 + 8 * glitchy)):
                    y = rng.integers(0, m.shape[0] - 10); hh = rng.integers(4, 24)
                    m[y:y + hh] = np.roll(m[y:y + hh], int(rng.integers(-60, 60) * glitchy), axis=1)
            sh = int(16 * glitchy) + 3
            img = comp(img, np.roll(m, -sh, axis=1), GLOWM * 0, MX, TY, 0.55 * out_a, col=np.array([210, 30, 40], np.float32))
            img = comp(img, np.roll(m, sh, axis=1), GLOWM * 0, MX, TY, 0.5 * out_a, col=np.array([40, 170, 210], np.float32))
            img = comp(img, m, GLOWM, MX, TY, out_a, glow_a=0.8 + 0.4 * glitchy)
            if glitchy > 0.3:
                sl = slice(TY, TY + MASK.shape[0]); img[sl] += rng.normal(0, 18 * glitchy, img[sl].shape)
        img = brand(img, ease((t - 1.4) / 0.5) * out_a)
    else:   # 垂吊搖晃: the characters drop in from above one by one and hang, swaying a little like the feet
        for k, (a0, a1) in enumerate(segs):
            tk = t - k * 0.18
            if tk <= 0: continue
            drop = ease(tk / 0.55)
            bounce = math.exp(-tk * 3.2) * math.sin(tk * 14) * 18 if tk > 0.55 else 0
            dy = int(-260 * (1 - drop) + bounce)
            ang = math.sin(tk * 2.1 + k) * 2.2 * min(1, tk)
            ch = Image.fromarray((MASK[:, a0:a1] * 255).astype(np.uint8))
            pad = 40
            canvas = Image.new("L", (ch.width + 2 * pad, ch.height + 2 * pad)); canvas.paste(ch, (pad, pad))
            rot = canvas.rotate(ang, resample=Image.BICUBIC, center=(canvas.width / 2, 0))
            m = np.asarray(rot).astype(np.float32) / 255
            g = np.asarray(rot.filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
            x = MX + a0 - pad; y = TY + dy - pad
            if y < 0: m = m[-y:]; g = g[-y:]; y = 0
            # a faint thread from the top edge to each character
            thread = int(x + canvas.width / 2)
            img[0:max(0, y + pad + 10), thread:thread + 2] = img[0:max(0, y + pad + 10), thread:thread + 2] * 0.6 + 140 * 0.4 * drop * out_a
            img = comp(img, m, g, x, y, drop * out_a)
        img = brand(img, ease((t - 1.5) / 0.5) * out_a)
    return np.clip(img, 0, 255).astype(np.uint8)

def base_frames(n, clip):
    raw = subprocess.run(["C:/Users/sheep/ffbin/ffmpeg.exe", "-loglevel", "error", "-i", str(clip), "-vf",
                          f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    a = (arr.astype(np.float32) / 255) ** 0.8 * 255
    return a.astype(np.uint8)

if __name__ == "__main__":
    n = int(3.5 * FPS); bases = base_frames(n, sys.argv[1]); sheet = []   # py -X utf8 title_fx.py <clip.mp4> [title]
    for kind in (1, 2, 3):
        out = Path.cwd() / f"title_fx_{kind}.mp4"
        p = subprocess.Popen(["C:/Users/sheep/ffbin/ffmpeg.exe", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                              "-vf", "scale=720:1280", str(out)], stdin=subprocess.PIPE)
        for i in range(n):
            f = frame(kind, i / FPS, bases[min(i, len(bases) - 1)])
            p.stdin.write(f.tobytes())
            if i in (12, 30, 60): sheet.append(Image.fromarray(f).resize((270, 480)))
        p.stdin.close(); p.wait(); print(out)
    s = Image.new("RGB", (270 * 3 + 20, 480 * 3 + 20), "#111")
    for k, im in enumerate(sheet): s.paste(im, (5 + (k % 3) * 275, 5 + (k // 3) * 485))
    s.save(Path.cwd() / "title_fx_sheet.jpg", quality=88)
