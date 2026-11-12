"""Frame strips of clips for review: strips/<clip>.jpg, one row per clip, a frame every `step` s with its time.
py -X utf8 strips.py [step=0.5] clips/a.mp4 ...   or   py -X utf8 strips.py sheet out.jpg clips/a.mp4 ... (several rows)"""
import subprocess, sys, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)


def row(clip, step=0.5, w=135, h=240):
    tmp = Path("strips/_tmp"); tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.glob("*.png"): f.unlink()
    subprocess.run([FF, "-v", "error", "-i", clip, "-vf", f"fps={1/step},scale={w}:{h}", str(tmp / "f%03d.png")])
    fs = sorted(tmp.glob("f*.png"))
    im = Image.new("RGB", (w * len(fs) + 160, h), "black")
    d = ImageDraw.Draw(im)
    d.text((4, 4), Path(clip).stem, fill="yellow", font=FONT)
    for i, f in enumerate(fs):
        im.paste(Image.open(f), (160 + i * w, 0))
        d.text((160 + i * w + 3, h - 22), f"{i*step:.1f}", fill="yellow", font=FONT)
    return im


a = sys.argv[1:]
if a[0] == "sheet":
    out, clips = a[1], a[2:]
    rows = [row(c) for c in clips]
    W = max(r.width for r in rows)
    S = Image.new("RGB", (W, sum(r.height + 4 for r in rows)), "gray")
    y = 0
    for r in rows:
        S.paste(r, (0, y)); y += r.height + 4
    S.save(out, quality=85)
else:
    step = 0.5
    if re.match(r"^[\d.]+$", a[0]):
        step = float(a[0]); a = a[1:]
    for c in a:
        row(c, step).save(f"strips/{Path(c).stem}.jpg", quality=85)
