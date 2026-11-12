"""Cover feet that are half alive: the normal still where the light falls, the ghost still in the shadows (owner, 2026-11-07:
「亮的部分更正常，暗的部分更鬼腳」). The two stills must share their framing: draw the normal one as a same-framing edit of the
ghost one. py -X utf8 blend.py <ghost.png> <normal.png> <mode 1|2|3> <out.png>
1 柔光過渡 (smooth by brightness), 2 光束 (a cold beam from above: normal inside, ghost outside; the owner's pick for 上鋪的腳),
3 腐蝕蔓延 (ragged rot spreading from the shadows)."""
import sys
import numpy as np
from PIL import Image, ImageFilter
G = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32)
N = np.asarray(Image.open(sys.argv[2]).convert("RGB").resize((G.shape[1], G.shape[0]))).astype(np.float32)
mode, out = int(sys.argv[3]), sys.argv[4]
h, w = G.shape[:2]
lum = N.mean(axis=2) / 255
def blur(a, r): return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
gain = 1.0
if mode == 1:
    m = blur(ss(lum, 0.40, 0.78), 8)
elif mode == 2:
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    beam = ss(1 - np.abs(xx - (0.36 + 0.10 * yy)) / (0.10 + 0.22 * yy), 0.0, 0.5)
    m = blur(beam * ss(lum, 0.18, 0.5), 5)
    gain = (0.72 + 0.45 * blur(beam, 30))[..., None] * np.array([0.97, 1.0, 1.05])
else:
    rng = np.random.default_rng(8)
    def noise(k): return np.asarray(Image.fromarray((rng.random((h // k, w // k)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    m = blur(ss(lum + (noise(40) - 0.5) * 0.55 + (noise(12) - 0.5) * 0.18, 0.40, 0.56), 3)
img = (N * m[..., None] + G * (1 - m[..., None])) * gain
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)
print(out)
