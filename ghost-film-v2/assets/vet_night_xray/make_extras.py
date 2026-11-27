"""The pieces only the shorts have: an opener per short (hook line, corner label n/4) and the 2.5 s 下集 cards for shorts 1-3.
py -X utf8 make_extras.py -> shots_extras.json (render it, then cut_shorts.py joins openers + long film pieces + cards)"""
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path.cwd()
SRC = HERE.parents[1] / "reel"
FF, SR, UP = "C:/Users/sheep/ffbin/ffmpeg.exe", 44100, 2 ** (1 / 12)
TAKES = json.load(open(HERE.parents[1] / "vo" / "picks_c.json", encoding="utf8"))


def voice(i):  # same processing as make_long.voice (not imported: importing it rewrites shots_long.json)
    t, out = TAKES[i], HERE.parent / "vo" / "c" / f"{i}.wav"
    if not out.exists():
        af = f"aresample={SR},asetrate={int(SR * UP)},aresample={SR},atempo={1.15 / UP:.5f},afade=t=in:d=0.012"
        subprocess.run([FF, "-y", "-v", "error", "-ss", f"{max(0, t['start'] - .08):.3f}", "-to", f"{t['end'] + .22:.3f}", "-i", t["file"], "-af", af, "-ac", "2", str(out)], check=True)
    return out


def gamma(still, target):
    m = np.asarray(Image.open(still).convert("L")).mean() / 255
    return 1.0 if m * 255 <= target else float(np.log(target / 255) / np.log(m))


L = SimpleNamespace(voice=voice, gamma=gamma, BY_ID={x["id"]: x for x in json.load(open(HERE.parents[1] / "vo" / "full_script.json", encoding="utf8"))})
PICKS = json.load(open(SRC / "long_picks.json", encoding="utf8"))
S = json.load(open("shots_long.json", encoding="utf8"))
picks = json.load(open("../vo/picks_long.json", encoding="utf8"))
script = json.load(open("../vo/script.json", encoding="utf8"))
for h in ("H2", "H3", "H4"):
    picks[h] = L.voice(h).as_posix()
    script[h] = L.BY_ID[h]["text"]
json.dump(picks, open("../vo/picks_long.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
json.dump(script, open("../vo/script.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
B = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 52)


def png(name, draw):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw(ImageDraw.Draw(im))
    p = HERE / "labels" / f"{name}.png"
    im.save(p)
    return p.as_posix()


def corner(n):
    t = f"{n}/4"
    return png(f"part{n}", lambda d: d.text((1080 - 64 - B.getlength(t), 170), t, font=B, fill=(245, 243, 238, 235), stroke_width=3, stroke_fill=(0, 0, 0, 200)))


def card(name, rows):
    f = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 66)

    def draw(d):
        for i, t in enumerate(rows):
            d.text(((1080 - f.getlength(t)) / 2, 1090 + i * 92), t, font=f, fill=(245, 243, 238, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    return png(name, draw)


THEME = "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/end_theme_12s.wav"
first = {s["id"]: s for s in S["shots"]}
shots = []
for sid in ("s01a", "s01b"):
    x = dict(first[sid])
    x["id"] = "h1" + sid[-1]
    x["overlays"] = [{"png": corner(1), "at": [0, -.01], "fade": 0, "fade_out": .3}]
    shots.append(x)
for n, still, line in ((2, "s15", "H2"), (3, "s30", "H3"), (4, "s51", "H4")):
    shots.append({"id": f"h{n}", "still": str(SRC / PICKS[still]), "motion": "push", "amt": .04, "focus": [.5, .5], "lines": [line], "lead": .1, "tail": .6,
                  "lift": L.gamma(SRC / PICKS[still], 95) if still == "s51" else None, "overlays": [{"png": corner(n), "at": [0, -.01], "fade": 0, "fade_out": .3}]})
for n, rows in ((1, ["下集：", "她問的那隻貓，", "我一次都沒看過"]), (2, ["下集：", "我按下去了"]), (3, ["最後一集：", "螢幕上的東西"])):
    shots.append({"id": f"c{n}", "end": True, "dur": 12, "bg_clip": str(SRC / "clips/mo2_s25_s102.mp4"), "bg_t": 0, "theme": THEME, "theme_at": 0, "theme_gain": .9,
                  "music_cut": [0, 12], "overlays": [{"png": card(f"card{n}", rows), "at": [0, 12], "fade": 0, "fade_out": 0}]})
json.dump({**{k: v for k, v in S.items() if k != "shots"}, "out": "extras_v2", "music": "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/leberch-horror-creepy-255685.mp3",
           "end_title": " ", "end_question": " ", "shots": shots}, open("shots_extras.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
print(len(shots), "extra shots")
