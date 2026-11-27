"""Silent review reels of the clips kept so far, each labelled with its shot. CPU only.
py -X utf8 make_preview.py  (in film/reel) -> preview/ready_talking.mp4, preview/ready_motion.mp4"""
import json
import subprocess
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
OUT = Path("preview")
TMP = OUT / "tmp"
TMP.mkdir(parents=True, exist_ok=True)
FONT = "C\\:/Windows/Fonts/arial.ttf"

talk, seen = [], set()
for name, v in json.load(open("talk_final.json", encoding="utf8")).items():
    if v["file"] not in seen:
        seen.add(v["file"])
        talk.append((v["shot"], f'{v["shot"]} {v["who"]}', v["file"], 0, None))
talk.sort(key=lambda r: (r[0], r[2]))

TRIM = {"s06": (0, 2.5), "s10": (0, 3.5), "s27": (0, 2.5), "s40": (1.6, 5)}
motion = [(s, s, f"clips/mo_{s}_s101.mp4", 0, None) for s in "s19 s42 s51 s61".split()]
for s in "s06 s10 s15 s17 s25 s27 s29 s30 s34 s35 s36 s37 s39 s40 s46 s47 s49 s52 s55 s57 s58".split():
    a, b = TRIM.get(s, (0, None))
    motion.append((s, s, f"clips/mo2_{s}_s102.mp4", a, b))
motion.sort()


def build(rows, out):
    parts = []
    for i, (_, label, f, a, b) in enumerate(rows):
        p = TMP / f"{out}_{i:03d}.mp4"
        cmd = [FF, "-y", "-v", "error", "-ss", str(a)] + (["-to", str(b)] if b else []) + ["-i", f, "-an", "-threads", "4", "-vf",
               f"scale=540:960,fps=24,drawtext=fontfile='{FONT}':text='{label}':x=16:y=16:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=6",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", str(p)]
        subprocess.run(cmd, check=True)
        parts.append(p)
    lst = TMP / f"{out}.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf8")
    subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(OUT / f"{out}.mp4")], check=True)
    print(out, len(rows), "clips")


build(talk, "ready_talking")
build(motion, "ready_motion")
