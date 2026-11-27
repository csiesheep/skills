"""Check chained cuts: the frame just before and just after each listed segment's start, side by side on one sheet.
A pair that does not match (pose snaps back, a person jumps, the camera jumps) is a broken link in the chain.

py -X utf8 cut_pairs.py out/long_v5 s08b s13c s16b ...        (no ids: every id in chain_map.json)
    -> out/long_v5/_cut_pairs.jpg"""
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
d = Path(sys.argv[1])
ids = sys.argv[2:] or list(json.load(open("chain_map.json", encoding="utf8")))
tl = {l.split()[2]: float(l.split()[0]) for l in open(d / "_timeline.txt", encoding="utf8") if len(l.split()) == 3 and l.split()[0].replace(".", "").isdigit()}
W, H, C = 270, 480, 6
sheet = Image.new("RGB", (W * C, H * ((len(ids) * 2 + C - 1) // C)))
for i, k in enumerate(ids):
    for j, o in enumerate((-.06, .06)):
        png = subprocess.run([FF, "-v", "error", "-ss", f"{tl[k] + o:.3f}", "-i", str(d / f"{d.name}.mp4"), "-frames:v", "1", "-vf", f"scale={W}:{H}",
                              "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True).stdout
        im = Image.open(BytesIO(png)).convert("RGB")
        ImageDraw.Draw(im).text((6, 6), f"{k} {'before' if j == 0 else 'after'}", fill=(255, 255, 0))
        n = i * 2 + j
        sheet.paste(im, (n % C * W, n // C * H))
sheet.save(d / "_cut_pairs.jpg", quality=88)
print(d / "_cut_pairs.jpg", len(ids), "cuts")
