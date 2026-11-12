"""Material for a blind review of a rendered reel: every shot as 3 frames (10/50/90 %) with its id and start, 12 shots
a sheet, plus shots.txt (id, start, length, the subtitles during the shot) and a copy of the mix ASR.
py -X utf8 review_sheets.py <story>/film/reel/out/reel_vN <dest folder>   (the dest must not be under AppData: the
Windows path limit breaks ffmpeg there). Give the dest to two fresh subagents with references/review_split.md."""
import re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
R, D = Path(sys.argv[1]), Path(sys.argv[2])
D.mkdir(parents=True, exist_ok=True)
V = next(R.glob("*_preview720.mp4"), None) or next(p for p in R.glob("*.mp4") if not p.name.startswith("_"))
shots, subs = [], []
for l in open(R / "_timeline.txt", encoding="utf8"):
    m = re.match(r"\s*([\d.]+)\s+([\d.]+)\s+(\S+)$", l)
    if m:
        shots.append((float(m[1]), float(m[2]), m[3])); continue
    m = re.match(r"\s*([\d.]+)-\s*([\d.]+)\s+(.*)$", l)
    if m:
        subs.append((float(m[1]), float(m[2]), m[3]))
f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 24)
tiles, rows, tmp = [], [], D / "_x.png"
for st, d, i in shots:
    im = Image.new("RGB", (3 * 244, 470))
    for j, frac in enumerate((0.1, 0.5, 0.9)):
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{st + d * frac:.2f}", "-i", str(V), "-frames:v", "1",
                        "-vf", "scale=240:427", str(tmp)], check=True)
        im.paste(Image.open(tmp), (j * 244, 0))
    ImageDraw.Draw(im).text((6, 436), f"{i}  {int(st // 60)}:{st % 60:04.1f}  ({d:.1f}s)", font=f, fill=(255, 255, 0))
    tiles.append(im)
    rows.append(f"{i}\t{int(st // 60)}:{st % 60:04.1f}\t{d:.1f}s\t" + " / ".join(s[2] for s in subs if st - 0.05 <= s[0] < st + d))
tmp.unlink(missing_ok=True)
for k in range(0, len(tiles), 12):
    sheet = Image.new("RGB", (732 * 4, 470 * 3))
    for j, t in enumerate(tiles[k:k + 12]):
        sheet.paste(t, ((j % 4) * 732, (j // 4) * 470))
    sheet.save(D / f"sheet{k // 12 + 1}.jpg", quality=82)
(D / "shots.txt").write_text("\n".join(rows), encoding="utf8")
if (R / "_asr.txt").exists():
    shutil.copy(R / "_asr.txt", D / "asr.txt")
print(D, len(tiles), "shots,", (len(tiles) + 11) // 12, "sheets; video:", V)
