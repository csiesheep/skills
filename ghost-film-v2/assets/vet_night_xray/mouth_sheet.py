"""Close-up review of the speaker's head in every final talking clip: 10 evenly spaced frames per clip, one row per line.
py -X utf8 mouth_sheet.py  (in film/reel) -> strips/tk/mouth0.jpg ... (14 rows each). Head positions are fractions of the 720x1280 frame, read from the strips."""
import json
import subprocess
import sys
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
HEAD = {("s07", "me"): (.28, .33), ("s07", "dean"): (.67, .33), ("s08", "me"): (.25, .37), ("s08", "dean"): (.65, .35), ("s09", "dean"): (.17, .33), ("s11", "me"): (.48, .24),
        ("s13", "me"): (.39, .30), ("s13", "bin"): (.78, .50), ("s16", "me"): (.46, .36), ("s20", "me"): (.50, .50), ("s20", "bin"): (.73, .50), ("s23", "me"): (.34, .44),
        ("s23", "bin"): (.80, .62), ("s24", "me"): (.36, .31), ("s24", "bin"): (.62, .47), ("s33", "her"): (.75, .35), ("s43", "dean"): (.23, .37), ("s43", "me"): (.64, .34),
        ("s45", "me"): (.30, .44), ("s45", "dean"): (.52, .44), ("s56", "her"): (.52, .38), ("s59", "dean"): (.80, .49), ("s63", "me"): (.63, .38), ("s63", "dean"): (.76, .51), ("s64", "dean"): (.74, .46)}
HEAD.update({("s11", "me"): (.48, .36), ("s13", "me"): (.39, .39), ("s20", "me"): (.50, .42), ("s20", "bin"): (.73, .42), ("s23", "bin"): (.76, .54), ("s45", "me"): (.30, .36), ("s45", "dean"): (.52, .36)})
ONLY = set(sys.argv[1:])  # shots to show; none = all
BOX, CELL, N, LABEL = 200, 130, 10, 150


def dur(f):
    e = subprocess.run([FF, "-i", f], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def frame(f, t, cx, cy):
    x, y = max(0, min(720 - BOX, int(cx * 720 - BOX / 2))), max(0, min(1280 - BOX, int(cy * 1280 - BOX / 2)))
    png = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1", "-vf", f"scale=720:1280,crop={BOX}:{BOX}:{x}:{y},scale={CELL}:{CELL}", "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True).stdout
    return Image.open(BytesIO(png)).convert("RGB")


T = [(k, v) for k, v in json.load(open("talk_final.json", encoding="utf8")).items() if not ONLY or v["shot"] in ONLY]
for s in range(0, len(T), 14):
    part = T[s:s + 14]
    im = Image.new("RGB", (LABEL + CELL * N, CELL * len(part)), "black")
    d = ImageDraw.Draw(im)
    for r, (name, v) in enumerate(part):
        d.text((4, r * CELL + 4), name.replace("tk_", "") + "\n" + v["who"] + (" pp" if v["pingpong"] else ""), fill="yellow", font=FONT)
        D = dur(v["file"])
        for k in range(N):
            im.paste(frame(v["file"], .3 + k * (D - .6) / (N - 1), *HEAD[(v["shot"], v["who"])]), (LABEL + k * CELL, r * CELL))
    im.save(f"strips/tk/mouth{s // 14}.jpg", quality=88)
print("ok", len(T))
