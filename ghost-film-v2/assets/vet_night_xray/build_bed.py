"""Music and room tone for the long film, sections anchored to shot ids in the timeline. The clips are muted, so the fluorescent hum and the far rain live here.
py -X utf8 build_bed.py out/long_v1/_timeline.txt bed.wav"""
import subprocess
import sys
import wave

import numpy as np

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
LIB = "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/"
SR = 44100
XF = 2.0
TL, END = {}, 0
for l in open(sys.argv[1], encoding="utf8"):
    m = l.split()
    if len(m) == 3 and m[0].replace(".", "").isdigit():
        TL[m[2]] = float(m[0]); END = float(m[0]) + float(m[1])
# (first shot of the section, track, level)
SECTIONS = [("s01a", "leberch-horror-creepy-255685.mp3", 1.0), ("s02a", "leberch-quiet-piano-313742.mp3", .6), ("s14a", "leberch-slowly-to-darkness-piano-mysterious-611752.mp3", .6),
            ("s24a", "leberch-quiet-piano-313742.mp3", .5), ("s26a", "leberch-slowly-to-darkness-piano-mysterious-611752.mp3", .7), ("s29a", "leberch-tension-585268.mp3", .75),
            ("s34a", "universfield-dark-mystery-piano-161660.mp3", .55), ("s35a", "leberch-investigation-piano-611639.mp3", .6), ("s47a", "alex-morgan-ambient-horror-creepy-atmosphere-dark-587402.mp3", .8),
            ("s52a", "leberch-tension-585268.mp3", .85), ("s57a", "universfield-dark-mystery-piano-161660.mp3", .6), ("s60a", "back_drop-dark-piano-ambient-concrete-forest-208256.mp3", .6),
            ("s63a", "universfield-dark-mystery-piano-161660.mp3", .5)]


def load(n):
    raw = subprocess.run([FF, "-v", "error", "-i", LIB + n, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


N = int((END + 1) * SR)
bed = np.zeros((N, 2))
for k, (sid, track, g) in enumerate(SECTIONS):
    a = TL[sid]
    b = TL[SECTIONS[k + 1][0]] + XF / 2 if k + 1 < len(SECTIONS) else TL["end"]
    x = load(track)
    n = int((b - a) * SR)
    seg = np.tile(x, (n // len(x) + 1, 1))[:n]
    seg = seg * (.1 / (np.sqrt((seg ** 2).mean()) + 1e-9)) * g
    f = min(int(XF * SR), n // 2)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
    bed[int(a * SR): int(a * SR) + n] += seg

t = np.arange(N) / SR
hum = (np.sin(2 * np.pi * 120 * t) + .4 * np.sin(2 * np.pi * 240 * t) + .15 * np.sin(2 * np.pi * 360 * t)) * .006
bed += np.stack([hum, hum], axis=1)
rng = np.random.default_rng(3)
noise = rng.normal(0, 1, N)
c = np.cumsum(noise); rain = noise - (c - np.concatenate([np.zeros(40), c[:-40]])) / 40  # a soft high-passed hiss
env = np.zeros(N)
for sid, end, level in (("s61a", "s62a", .016), ("s68a", "end", .010)):
    i, j = int(TL[sid] * SR), int(TL[end] * SR)
    f = min(int(1.2 * SR), (j - i) // 2)
    e = np.full(j - i, level); e[:f] *= np.linspace(0, 1, f); e[-f:] *= np.linspace(1, 0, f)
    env[i:j] = e
bed += np.stack([rain * env, rain * env], axis=1)
bed = bed / (np.abs(bed).max() + 1e-9) * .9
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((bed * 32767).astype("<i2").tobytes())
print("bed", round(END, 1), "s")
