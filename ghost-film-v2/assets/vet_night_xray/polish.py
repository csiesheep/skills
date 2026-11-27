"""Polish pass (owner: 「你再打磨一遍」). Called at the end of make_long.py, before shots_long.json is written.
s60a: the dean asleep for 17 s on a still - the phone on the nightstand now starts dark, lights up and buzzes while
L131b (「有一個女生凌晨打進來，我睡死了」) plays, and goes dark again for L131c (「早上才聽到語音信箱」)."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

FF, SR, FPS = "C:/Users/sheep/ffbin/ffmpeg.exe", 44100, 24
HERE = Path.cwd()
ON, OFF = 5.1, 10.2           # seconds into s60a: L131b starts at 5.24, L131c at 10.47
BUZZ = [(0.0, .7), (1.2, .7), (2.4, .7), (3.6, .7), (4.8, .3)]   # buzz bursts after ON (start, length)


def buzzing(t):
    r = t - ON
    return any(a <= r < a + b for a, b in BUZZ) if 0 <= r < OFF - ON else False


def s60_plate(still, dur):
    out = HERE / "plates" / "s60_phone.mp4"
    if out.exists():
        return out
    base = np.asarray(Image.open(still).convert("RGB").resize((1080, 1920), Image.LANCZOS)).astype(np.float32)
    lum = base.mean(2)
    yy, xx = np.mgrid[0:1920, 0:1080]
    near = np.exp(-(((xx - 907) / 150) ** 2 + ((yy - 738) / 110) ** 2))           # the glow the screen throws on the nightstand
    from scipy import ndimage
    from scipy.spatial import ConvexHull
    from PIL import ImageDraw
    m = np.zeros_like(lum, bool)
    m[620:860, 780:1030] = lum[620:860, 780:1030] > 170                            # the lit screen: largest bright blob next to the bed
    lab, n = ndimage.label(m)
    ys, xs = np.nonzero(lab == np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
    pts = np.c_[xs, ys]
    poly = Image.new("L", (1080, 1920), 0)
    ImageDraw.Draw(poly).polygon([tuple(map(int, pts[v])) for v in ConvexHull(pts).vertices], fill=255)
    hull = ndimage.binary_dilation(np.asarray(poly) > 0, iterations=4)
    screen = np.asarray(Image.fromarray((hull * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    dark = base * (1 - .45 * near)[..., None]                                       # the nightstand without the screen's glow
    off = np.array([30, 30, 34], np.float32) + 10 * ((yy - 680) / 140).clip(0, 1)[..., None]   # a switched-off glossy screen
    dark = dark * (1 - screen[..., None]) + off * screen[..., None]
    diff = base - dark
    p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for k in range(int(dur * FPS) + 1):
        t = k / FPS
        a = 0.0
        if ON <= t < OFF:
            a = min(1, (t - ON) / .15) * min(1, (OFF - t) / .25)
        layer = diff
        if buzzing(t):                                                             # the phone shakes 2 px while it buzzes
            layer = np.roll(diff, 2 if k % 2 else -2, axis=1)
        p.stdin.write(np.clip(dark + layer * a, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    return out


def buzz_wav():
    out = HERE / "sfx" / "buzz.wav"
    if not out.exists():
        n = int((BUZZ[-1][0] + BUZZ[-1][1] + .1) * SR)
        t = np.arange(n) / SR
        w = np.sign(np.sin(2 * np.pi * 160 * t)) * .5 + np.sin(2 * np.pi * 320 * t) * .3   # a phone motor on a wooden nightstand
        env = np.zeros(n)
        for a, b in BUZZ:
            i, j = int(a * SR), int((a + b) * SR)
            env[i:j] = np.minimum(1, np.minimum(np.arange(j - i), np.arange(j - i)[::-1]) / (.01 * SR))
        x = (w * env * .18).astype(np.float32)
        import wave
        with wave.open(str(out), "w") as f:
            f.setnchannels(2)
            f.setsampwidth(2)
            f.setframerate(SR)
            f.writeframes((np.repeat(x[:, None], 2, 1) * 32767).astype(np.int16).tobytes())
    return out


def apply(shots):
    for sh in shots:
        if sh["id"] == "s60a":
            plate = s60_plate(sh["still"], 17.6)
            sh["clip"], sh["speed"] = str(plate), 1
            sh.pop("still", None)
            sh["sfx"] = sh.get("sfx") or []
            sh["sfx"].append(["file:" + buzz_wav().as_posix(), ON, .5])
    return shots
