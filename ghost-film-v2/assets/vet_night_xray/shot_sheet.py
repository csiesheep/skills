"""One labelled frame from the middle of every shot. py -X utf8 shot_sheet.py out/long_v1"""
import subprocess, sys
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
d = Path(sys.argv[1]); mp4 = d / f"{d.name}.mp4"
rows = []
for l in open(d / "_timeline.txt", encoding="utf8"):
    m = l.split()
    if len(m) == 3 and m[0].replace(".", "").isdigit():
        rows.append((float(m[0]), float(m[1]), m[2]))
    elif rows and not l.strip():
        break
F = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
W, H, C = 170, 302, 9
for p in range(0, len(rows), 36):
    part = rows[p:p + 36]
    im = Image.new("RGB", (W * C, H * ((len(part) + C - 1) // C)), "black")
    for i, (a, b, n) in enumerate(part):
        png = subprocess.run([FF, "-v", "error", "-ss", f"{a + b / 2:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True).stdout
        x, y = i % C * W, i // C * H
        im.paste(Image.open(BytesIO(png)).convert("RGB"), (x, y))
        ImageDraw.Draw(im).text((x + 3, y + 3), n, fill="yellow", font=F, stroke_width=2, stroke_fill="black")
    im.save(d / f"_shots{p // 36}.jpg", quality=88)
print(len(rows))
