"""Three full-comic Reel versions from one ghost-comic folder (prototype engine).

    py -X utf8 reel.py <version v1|v2|v3> <out dir> [--music file] [--preview]
"""
import argparse, importlib.util, math, random, re, subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import sfx as SFX
import story_name_call as STORY

spec = importlib.util.spec_from_file_location("manga", Path.home() / ".claude/skills/ghost-comic/scripts/manga.py")
mg = importlib.util.module_from_spec(spec); spec.loader.exec_module(mg)

W, H, FPS = 1080, 1920, 30
RED = (184, 50, 42)
PAPER = (242, 237, 228)
random.seed(5); np.random.seed(5)
ease = mg.ease

# ---------------------------------------------------------------- assets
mg.set_work(Path(STORY.COMIC))
BOARD, CH = mg.load_board(), mg.load_choices()
_cache = {}


def panel(pid, diegetic=True):
    key = (pid, diegetic)
    if key not in _cache:
        cell = mg.find_panel(BOARD, pid)
        if cell.get("fill"):
            im = Image.new("RGB", (1280, 832), cell["fill"])
        else:
            im = mg.panel_source(cell, CH)
            im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 70, 2))
        _cache[key] = (cell, im)
        # text that is part of the picture (a phone or monitor screen) is drawn back into it
        scr = [e for e in cell.get("text", []) if e["kind"] in ("screen", "phone")]
        if scr and diegetic:
            im = im.convert("RGB")
            box = (int(im.width * 0.08), int(im.height * 0.06), int(im.width * 0.92), int(im.height * 0.94))
            for e in scr:
                mg.draw_entry(im, e, box, round(im.width / 22))
            _cache[key] = (cell, im)
    return _cache[key]


def font(size, kind="serif", weight="SemiBold"):
    return mg.reel_font(size, kind, weight)


# ---------------------------------------------------------------- camera
def frame_crop(img, ow, oh, t, motion="push", focus=(0.5, 0.5), amt=0.06, start=0.0):
    Wp, Hp = img.size
    r = ow / oh
    bw, bh = (Hp * r, Hp) if Wp / Hp > r else (Wp, Wp / r)
    if motion == "pull":
        s = 1 + amt * (1 - t)
    elif motion == "snap":
        s = 1 + 0.22 * min(1, t * 8) + 0.04 * t
    elif motion == "static":
        s = 1.0
    else:
        s = 1 + start + amt * t
    bw, bh = bw / s, bh / s
    cx, cy = Wp * focus[0], Hp * focus[1]
    if tuple(focus) == (0.5, 0.5) and Wp / Hp < r * 1.05:
        cy = Hp * 0.38          # a tall picture: keep the upper part, where the faces are
    if motion == "pan_rtl":
        cx = Wp - bw / 2 - (Wp - bw) * t
    elif motion == "pan_down":
        cy = bh / 2 + (Hp - bh) * t
    cx = min(max(cx, bw / 2), Wp - bw / 2); cy = min(max(cy, bh / 2), Hp - bh / 2)
    return img.transform((ow, oh), Image.Transform.EXTENT, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2),
                         Image.Resampling.BICUBIC)


# ---------------------------------------------------------------- effects (numpy, on a picture)
_vig = {}


def vignette(w, h, k):
    key = (w, h, k)
    if key not in _vig:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        _vig[key] = np.clip(1 - k * np.clip(d - 0.42, 0, None) ** 1.5, 0, 1)[..., None].astype(np.float32)
    return _vig[key]


def apply_fx(pic, fxs, i, n, base_vig=0.55, grain=0.0, tint=None):
    a = np.asarray(pic).astype(np.float32)
    h, w = a.shape[:2]
    t = i / max(1, n - 1)
    for fx in fxs:
        if fx == "flicker" and random.random() < 0.14:
            a *= random.uniform(0.3, 0.65)
        elif fx == "pulse":
            ph = (i % 25) / 25
            beat = math.exp(-((ph - 0.08) / 0.05) ** 2) + 0.7 * math.exp(-((ph - 0.28) / 0.05) ** 2)
            a *= vignette(w, h, 1.0) * (1 - 0.16 * beat) + (1 - vignette(w, h, 1.0)) * 0
        elif fx == "darken":
            a *= (1 - 0.5 * t)
        elif fx == "night":
            a *= 0.78
        elif fx == "glitch" and random.random() < 0.22:
            for _ in range(random.randint(2, 5)):
                y = random.randint(0, h - 40); hh = random.randint(6, 40)
                a[y:y + hh] = np.roll(a[y:y + hh], random.randint(-50, 50), axis=1)
            a += np.random.normal(0, 18, a.shape).astype(np.float32)
        elif fx == "chroma" and i < 12:
            k = int(10 * (1 - i / 12))
            a[..., 0] = np.roll(a[..., 0], k, axis=1); a[..., 2] = np.roll(a[..., 2], -k, axis=1)
        elif fx == "fadein":
            a *= min(1, i / 18)
    if tint is not None:
        a = a * np.array(tint, dtype=np.float32)
    a *= vignette(w, h, base_vig)
    if grain:
        a += np.random.normal(0, grain, (h, w, 1)).astype(np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def shake_offset(fxs, i):
    if "shake" in fxs and i < 12:
        k = 1 - i / 12
        return (int(random.randint(-20, 20) * k), int(random.randint(-16, 16) * k))
    return (0, 0)


# ---------------------------------------------------------------- text tiles
def split_text(text, limit):
    """Split at sentence punctuation into chunks of at most `limit` characters."""
    text = text.replace("\n", "")
    parts = re.split(r"(?<=[。！？])", text)
    out, cur = [], ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) <= limit:
            cur += p
        else:
            if cur:
                out.append(cur)
            while len(p) > limit:
                cut = max([p.rfind(c, 0, limit) for c in "，、：；"] + [-1])
                cut = cut + 1 if cut > limit // 3 else limit
                out.append(p[:cut]); p = p[cut:]
            cur = p
    if cur:
        out.append(cur)
    return out


def narration_tile(text, maxw=W - 140, sizes=(46, 42, 38), lines=3):
    size, f, ls = mg.fit_lines([(c, 0) for c in text], sizes, maxw - 52, lines, "serif", "SemiBold")
    lh = round(size * 1.38)
    tw = max(round(sum(f.getlength(c) for c, _ in ln)) for ln in ls)
    pad = 26
    tile = Image.new("RGBA", (tw + 2 * pad, lh * len(ls) + 2 * pad - round(size * 0.38)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, tile.width - 1, tile.height - 1], fill=(250, 248, 242), outline="black", width=3)
    y = pad
    for ln in ls:
        d.text((pad, y), "".join(c for c, _ in ln), font=f, fill="black"); y += lh
    return tile


def bubble_tiles(cell, box, base):
    out = []
    for e in cell.get("text", []):
        if e["kind"] in ("title", "narration"):
            continue
        layer = Image.new("RGBA", (box[2] + 40, box[3] + 40), (0, 0, 0, 0))
        bx = mg.draw_entry(layer, e, box, base)
        bx = [max(0, bx[0] - 4), max(0, bx[1] - 4), bx[2] + 4, bx[3] + 4]
        out.append((e, layer.crop(bx), bx))
    return out


def kinetic_tile(text, size=84, maxw=W - 180, color=(255, 255, 255)):
    """Big centred caption; {braces} in red. Black outline for any background."""
    chars = mg.parse_accent(text)
    sz, f, ls = mg.fit_lines(chars, (size, size - 8, size - 16), maxw, 3, "serif", "Bold")
    lh = round(sz * 1.42)
    widths = [sum(f.getlength(c) for c, _ in ln) for ln in ls]
    tw, th = int(max(widths)) + 24, lh * len(ls) + 24
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    for k, ln in enumerate(ls):
        x = (tw - widths[k]) / 2; y = 12 + k * lh
        runs, cur = [], None
        for c, flag in ln:
            w_ = f.getlength(c)
            if flag:
                if cur is None:
                    cur = [x, x + w_]
                else:
                    cur[1] = x + w_
            elif cur is not None:
                runs.append(cur); cur = None
            x += w_
        if cur is not None:
            runs.append(cur)
        for x0, x1 in runs:
            d.rounded_rectangle([x0 - 8, y - 4, x1 + 8, y + sz * 1.18], radius=10, fill=RED)
        x = (tw - widths[k]) / 2
        for c, flag in ln:
            d.text((x, y), c, font=f, fill=color, stroke_width=0 if flag else 5, stroke_fill=(0, 0, 0))
            x += f.getlength(c)
    return tile


def subtitle_tile(text, size=60):
    chars = [(c, 0) for c in text]
    sz, f, ls = mg.fit_lines(chars, (size, size - 4), W - 200, 2, "serif", "SemiBold")
    lh = round(sz * 1.45)
    widths = [sum(f.getlength(c) for c, _ in ln) for ln in ls]
    tw, th = int(max(widths)) + 20, lh * len(ls) + 20
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    for k, ln in enumerate(ls):
        x = (tw - widths[k]) / 2
        d.text((x, 10 + k * lh), "".join(c for c, _ in ln), font=f, fill=(235, 235, 235), stroke_width=3, stroke_fill=(0, 0, 0))
    return tile


def popped(tile, p, fade=1.0):
    sc = 0.84 + 0.16 * ease(min(1, p))
    t2 = tile.resize((max(1, round(tile.width * sc)), max(1, round(tile.height * sc))), Image.LANCZOS)
    a = min(1, p * 1.7) * fade
    if a < 1:
        t2.putalpha(t2.split()[3].point(lambda v: int(v * a)))
    return t2


def paste_center(canvas, tile, cx, cy):
    canvas.alpha_composite(tile, (round(cx - tile.width / 2), round(cy - tile.height / 2)))


def overlaps(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


# ---------------------------------------------------------------- cards
def title_card(sub=True):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    t = STORY.TITLE
    f = font(88, weight="Bold")
    y = 820
    tw = f.getlength(t)
    if tw > W - 120:
        f = font(int(88 * (W - 120) / tw), weight="Bold"); tw = f.getlength(t)
    d.text(((W - tw) / 2, y), t, font=f, fill=(245, 245, 245))
    s = f"鬼唱詩｜{STORY.NUMBER}" if STORY.NUMBER else "鬼唱詩"
    f2 = font(44)
    d.text(((W - f2.getlength(s)) / 2, y + 150), s, font=f2, fill=(170, 170, 170))
    f3 = font(30, "plain", None)
    dis = "AI 輔助創作｜故事純屬虛構"
    d.text(((W - f3.getlength(dis)) / 2, y + 230), dis, font=f3, fill=(120, 120, 120))
    return im


def end_card():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    lines = [("本首完", font(96, weight="Bold"), (245, 245, 245)),
             ("追蹤，聽下一首", font(52), (200, 200, 200)),
             ("@gui.chang.shi", font(46, "plain", None), RED),
             ("AI 輔助創作｜故事純屬虛構", font(30, "plain", None), (120, 120, 120))]
    y = 760
    for text, f, col in lines:
        d.text(((W - f.getlength(text)) / 2, y), text, font=f, fill=col); y += round(f.size * 1.9)
    seal = Image.open(STORY.SEAL).convert("RGBA").resize((170, 170), Image.LANCZOS)
    im.alpha_composite(seal, ((W - 170) // 2, 520))
    return im


# ---------------------------------------------------------------- render loop
def render(shots, out_mp4, preview_every=0):
    """shots: list of dicts with 'n' frames and 'draw(i)' -> RGB image."""
    frames_dir_samples = []
    total = sum(s["n"] for s in shots)
    marks = set(range(0, total, preview_every)) if preview_every else set()

    def gen():
        idx = 0
        prev = None
        for s in shots:
            for i in range(s["n"]):
                f = s["draw"](i)
                xf = s.get("xfade", 0)
                if prev is not None and i < xf:
                    f = Image.blend(prev, f, (i + 1) / (xf + 1))
                if idx in marks:
                    frames_dir_samples.append((idx, f.copy()))
                idx += 1
                yield f
            prev = f
    n = mg.write_video(gen(), out_mp4)
    return n, frames_dir_samples


def sheet(samples, path, cols=10):
    tw, th = 162, 288
    rows = math.ceil(len(samples) / cols)
    im = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 28) + 6), "#333")
    d = ImageDraw.Draw(im)
    for k, (idx, f) in enumerate(samples):
        x, y = 6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 28)
        im.paste(f.resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 4), f"{idx / FPS:.1f}s", fill="white", font=font(18, "plain", None))
    im.save(path, quality=85)


def mux(video, wav, out):
    # re-encode with a bitrate ceiling (grain otherwise makes a 600 MB file) and bring the sound to -14 LUFS,
    # the level Instagram, YouTube and TikTok play at
    subprocess.run([mg.ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "10M", "-bufsize", "20M",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("out")
    ap.add_argument("--music", default=None)
    ap.add_argument("--preview", type=float, default=1.5, help="seconds between sampled frames for the sheet")
    ap.add_argument("--reuse", action="store_true", help="keep the silent video if it exists; redo sound and sheet")
    a = ap.parse_args()
    import versions
    shots, events, ducks, music_gain = versions.build(a.version, sys.modules[__name__])
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    silent = out / f"{a.version}_silent.mp4"
    if a.reuse and silent.exists():
        import imageio_ffmpeg
        n, _ = imageio_ffmpeg.count_frames_and_secs(str(silent))
        samples = []
        tmpd = out / f"_frames_{a.version}"
        import shutil; shutil.rmtree(tmpd, ignore_errors=True); tmpd.mkdir()
        subprocess.run([mg.ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(silent), "-vf", f"fps=1/{a.preview}",
                        str(tmpd / "f%04d.jpg")], check=True)
        for k, fp in enumerate(sorted(tmpd.glob("f*.jpg"))):
            samples.append((int(k * a.preview * FPS), Image.open(fp).convert("RGB")))
    else:
        n, samples = render(shots, silent, int(a.preview * FPS))
    total = n / FPS
    music = SFX.read_audio(Path(a.music), mg.ffmpeg_exe()) if a.music else None
    audio = SFX.mix(total, events, music, music_gain, ducks)
    wav = out / f"{a.version}.wav"
    SFX.write_wav(wav, audio)
    mux(silent, wav, out / f"{a.version}.mp4")
    wav.unlink()
    sheet(samples, out / f"{a.version}_sheet.jpg")
    print(f"{a.version}: {n} frames, {total:.1f}s -> {out / (a.version + '.mp4')}")



# ---------------------------------------------------------------- moving panels (H3 clips)
_clip = {}


def clip_frames(path):
    """All frames of a clip at 1080x1920 (cover crop, sharpened), cached one clip at a time."""
    if path not in _clip:
        _clip.clear()
        cmd = [mg.ffmpeg_exe(), "-loglevel", "error", "-i", str(path), "-vf",
               "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,unsharp=5:5:0.7",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = len(raw) // (1080 * 1920 * 3)
        arr = np.frombuffer(raw, np.uint8)[: n * 1080 * 1920 * 3].reshape(n, 1920, 1080, 3)
        _clip[path] = arr
    return _clip[path]


def clip_frame(path, i, n, src_fps=24, offset=0.0):
    """Frame for output frame i of n: plays at natural speed from `offset` s, slowed down if the shot is longer than
    what is left of the clip."""
    arr = clip_frames(path)
    length = len(arr) / src_fps - offset
    shot = n / FPS
    speed = min(1.0, length / shot)
    k = min(len(arr) - 1, int((offset + i / FPS * speed) * src_fps))
    return Image.fromarray(arr[k])


def title_overlay():
    """The title card's words on a transparent ground, to lay over a moving establishing shot."""
    im = title_card().convert("RGBA")
    a = np.asarray(im).astype(np.uint8).copy()
    lum = a[..., :3].max(axis=2)
    a[..., 3] = np.clip(lum.astype(int) * 3, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


if __name__ == "__main__":
    main()
