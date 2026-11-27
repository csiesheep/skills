"""The long vertical film: 68 shots from film/reel/shot_table.json, voiced with the C takes, mouths on the talking clips.
Runs in film/longcut/reel so render.py reads this cut's own vo/script.json and vo/picks_long.json and leaves the old test files alone.
py -X utf8 make_long.py -> ../vo/c/*.wav, ../vo/script.json, ../vo/picks_long.json, plates/*.mp4, labels/*.png, sfx/*.wav, shots_long.json

A talking line plays its own clip from the start. If the line is longer than the usable part, the clip plays forward then backward (same speaker, same still, no jump).
Shots whose action cannot run backward (walking, a door, a lamp, a button) are slowed instead."""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
HERE = Path.cwd()
SRC = HERE.parents[1] / "reel"
VO = HERE.parent / "vo"
for d in (VO / "c", HERE / "plates", HERE / "labels", HERE / "sfx"):
    d.mkdir(parents=True, exist_ok=True)
SR = 44100
UP = 2 ** (1 / 12)

TABLE = json.load(open(SRC / "shot_table.json", encoding="utf8"))["shots"]
PICKS = json.load(open(SRC / "long_picks.json", encoding="utf8"))
TALK = json.load(open(SRC / "talk_final.json", encoding="utf8"))
MOTION = json.load(open(SRC / "motion_final.json", encoding="utf8"))
SCRIPT = json.load(open(HERE.parents[1] / "vo" / "full_script.json", encoding="utf8"))
TAKES = json.load(open(HERE.parents[1] / "vo" / "picks_c.json", encoding="utf8"))
BY_ID = {x["id"]: x for x in SCRIPT}

CHAIN = json.load(open("chain_map.json", encoding="utf8")) if Path("chain_map.json").exists() else {}
PINGPONG = set("s04 s14 s17 s19 s21 s28 s29 s34 s35 s36 s38 s42 s44 s46 s55 s57".split())
CCTV = set("s37 s38 s39 s41 s42".split())
LIMIT = {"tk_s13_L032": 2.5}
OFFSET = {"tk_s24_L068": 1.5}  # the bag is already up, as at the end of L066
SWAP = {"tk_s24_L067": "clips/tk4_s24_L067_s98.mp4", "tk_s24_L069": "clips/tk4_s24_L067_s98.mp4", "tk_s24_L070": "clips/tk4_s24_L070_s98.mp4"}
DARK = {"s47": 95, "s48": 95, "s49": 95, "s50": 95, "s51": 95, "s59": 85, "s63": 85, "s64": 85, "s66": 105, "s68": 85}  # 禮拜六: half the lights are out
LABEL = {"s14": "禮拜三　02:10", "s21": "禮拜四　02:10", "s24": "禮拜五", "s26": "禮拜五　02:10", "s37": "禮拜三　02:08", "s39": "禮拜五", "s41": "禮拜三　02:14", "s47": "禮拜六"}
STILL = {"s31": "long/s32_2.png"}
MOVE = {"s01": ("push", .05), "s02": ("push", .04), "s03": ("push", .03), "s05": ("push", .05), "s12": ("push", .04), "s18": ("push", .05), "s22": ("push", .08), "s26": ("push", .05),
        "s31": ("pull", .10), "s32": ("push", .03), "s41": ("push", .03), "s48": ("push", .06), "s50": ("push", .04), "s53": ("push", .06), "s54": ("pull", .22), "s60": ("push", .04),
        "s62": ("push", .05), "s65": ("push", .05), "s66": ("push", .07), "s67": ("pull", .04), "s68": ("push", .07)}
SILENT = ("沒有聲音", "靜音", "沒有旁白", "切黑", "只有冷氣聲", "只有機器")
BLACK_AFTER = {"s40", "s56", "s61"}
GAP, LEAD, TAIL = .22, .22, .28


def voice(i):
    src = BY_ID[i].get("same_as", i)
    t = TAKES[src]
    out = VO / "c" / f"{src}.wav"
    if not out.exists():
        af = f"aresample={SR},asetrate={int(SR * UP)},aresample={SR},atempo={1.15 / UP:.5f},afade=t=in:d=0.012"
        subprocess.run([FF, "-y", "-v", "error", "-ss", f"{max(0, t['start'] - .08):.3f}", "-to", f"{t['end'] + .22:.3f}", "-i", t["file"], "-af", af, "-ac", "2", str(out)], check=True)
    return out


def seconds(f):
    with wave.open(str(f)) as w:
        return w.getnframes() / w.getframerate()


def probe(f):
    e = subprocess.run([FF, "-i", str(f)], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def plate(name, f, start, usable, need, grey, pingpong):
    """A clip cut to `need` seconds: forward, or forward and backward until long enough."""
    out = HERE / "plates" / f"{name}.mp4"
    g = ",hue=s=0" if grey else ""
    if pingpong and need > usable:
        n = int(usable * 24) * 2
        vf = f"[0:v]trim={start}:{start + usable},setpts=PTS-STARTPTS,fps=24{g},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1,loop=-1:size={n}:start=0[v]"
    else:
        vf = f"[0:v]trim={start}:{start + usable},setpts=PTS-STARTPTS,fps=24{g}[v]"
    t = need if pingpong else usable
    subprocess.run([FF, "-y", "-v", "error", "-i", str(f), "-filter_complex", vf, "-map", "[v]", "-t", f"{t:.2f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out.as_posix()


def label(shot, text):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((64, 170), text, font=ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 56), fill=(245, 243, 238, 235), stroke_width=3, stroke_fill=(0, 0, 0, 200))
    p = HERE / "labels" / f"{shot}.png"
    im.save(p)
    return p.as_posix()


def tone(name, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(HERE / "sfx" / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())
    return (HERE / "sfx" / f"{name}.wav").as_posix()


def bell(f, d, decay):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t)) * np.exp(-t * decay)


np.random.seed(5)
DING = tone("ding", np.concatenate([bell(880, .42, 6), bell(698, .9, 4.5)]) * .6)
ring = np.sin(2 * np.pi * 480 * np.arange(int(.9 * SR)) / SR) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 18 * np.arange(int(.9 * SR)) / SR)))
RING = tone("ring", np.concatenate([ring, np.zeros(int(.45 * SR)), ring, np.zeros(int(.25 * SR))]) * .35)
BEEP = tone("beep", np.sin(2 * np.pi * 1240 * np.arange(int(.32 * SR)) / SR) * .5)
STATIC = "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/sfx/lenspulse-80s-crt-tv-static-noise-amp-glitch-sound-effect-597768.mp3"
SOUND = {"s05": [(RING, -1.5, .5)], "s10": [(DING, .05, .55)], "s14": [(DING, -.95, .6)], "s26": [(DING, -.95, .6)], "s30": [(BEEP, -.9, .6)], "s51": [(BEEP, -.9, .7)], "s56": [("file:" + STATIC, -1.4, .25)]}

def gamma(still, target):
    m = np.asarray(Image.open(still).convert("L")).mean() / 255
    return 1.0 if m * 255 <= target else float(np.log(target / 255) / np.log(m))


def phone_card():
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bold = lambda z: ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", z)
    mid = lambda t, y, z, c: d.text((592 - bold(z).getlength(t) / 2, y), t, font=bold(z), fill=c)
    mid("通話紀錄", 500, 50, (235, 235, 235, 255))
    d.line((350, 590, 830, 590), fill=(190, 190, 190, 160), width=3)
    mid("02:10", 650, 112, (245, 245, 245, 255))
    mid("未接來電", 800, 64, (255, 86, 76, 255))
    d.line((350, 910, 830, 910), fill=(190, 190, 190, 160), width=3)
    p = HERE / "labels" / "phone.png"
    im.save(p)
    return p.as_posix()


def card_question():
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 50)
    for t, y in (("你家的貓，每天有沒有", 1062), ("固定時間坐在門口？", 1118)):
        d.text(((1080 - f.getlength(t)) / 2, y), t, font=f, fill=(225, 222, 215, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    p = HERE / "labels" / "question.png"
    im.save(p)
    return p.as_posix()


def ease(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def camera_shot(n, ids, need):
    """X-ray film: one continuous move drawn here, so the hands and the skull come in on the words that name them."""
    out = HERE / "plates" / f"{n}_cam.mp4"
    im = Image.open(SRC / ("long/s54_2.png" if n == "s54" else "long/s32_2.png")).convert("RGB").resize((720, 1280), Image.LANCZOS)
    hidden = None
    if n == "s54":
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).ellipse((235, 475, 470, 815), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(7))
        hidden = Image.composite(Image.new("RGB", im.size, im.getpixel((340, 900))), im, mask)
    a0 = 1.0 if n == "s54" else LEAD
    da = seconds(voice(ids[0]))

    def cam(t):
        if n == "s31":
            return .525, .38, 3.4 + .12 * t / need, 1
        if n == "s32":
            k = ease(t / 1.8)
            return .525 + (.5 - .525) * k, .38 + (.5 - .38) * k, 3.5 + (1 - 3.5) * k + .02 * max(0, t - 1.8), 1
        k = ease((t - a0) / (.38 * da))
        alpha = ease((t - (a0 + .52 * da)) / .7)
        return .5, .27 + (.5 - .27) * k, 3.8 + (1 - 3.8) * k + .012 * max(0, t - a0 - da), alpha
    p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "720x1280", "-r", "24", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for i in range(int(need * 24)):
        cx, cy, s, alpha = cam(i / 24)
        src = im if hidden is None else Image.blend(hidden, im, alpha)
        w, h = 720 / s, 1280 / s
        x = min(max(cx * 720, w / 2), 720 - w / 2)
        y = min(max(cy * 1280, h / 2), 1280 - h / 2)
        p.stdin.write(src.transform((720, 1280), Image.Transform.EXTENT, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), Image.Resampling.BICUBIC).tobytes())
    p.stdin.close()
    p.wait()
    return {"clip": out.as_posix()}


shots, cast = [], {}
talk_of = {}
for k, v in TALK.items():
    ids = ["L121", "L122", "L123", "L124", "L125", "L126"] if v["shot"] == "s56" else v["ids"]
    talk_of[(v["shot"], ids[0])] = (k, v, ids)


def add_lines(ids):
    for i in ids:
        f = voice(i)
        cast[i] = f.as_posix()


def length(ids):
    return LEAD + sum(seconds(voice(i)) for i in ids) + GAP * (len(ids) - 1) + TAIL


add_lines(["H1"])
shots.append({"id": "s01a", "still": str(SRC / PICKS["s01"]), "motion": "push", "focus": [.5, .55], "amt": .025, "lines": ["H1"], "lead": .0, "tail": .35})
shots.append({"id": "s01b", "still": str(SRC / PICKS["s01"]), "zoom": .025, "motion": "push", "focus": [.5, .55], "amt": .025, "dur": 3.5, "title_fx": 1, "title_fx_dur": 3.5})

black_next = False
for row in TABLE:
    n = f"s{row['n']:02d}"
    if n == "s01":
        continue
    lines = row["lines"]
    segs, i = [], 0
    while i < len(lines):
        hit = talk_of.get((n, lines[i]))
        if hit:
            segs.append(("talk", hit, hit[2])); i += len(hit[2])
        else:
            j = i
            while j < len(lines) and (n, lines[j]) not in talk_of:
                j += 1
            segs.append(("pic", None, lines[i:j])); i = j
    pause = float(row.get("pause_after") or 0)
    note = row.get("pause_note") or ""
    for c, (kind, hit, ids) in enumerate(segs):
        add_lines(ids)
        last = c == len(segs) - 1
        sh = {"id": f"{n}{'abcdefghijkl'[c]}", "lines": ids, "lead": LEAD, "gap": GAP, "tail": TAIL + (pause if last else 0), "amb": 0, "vig": .3, "grain": 3.0}
        if n in DARK:
            sh["lift"] = gamma(SRC / PICKS[n], DARK[n])
        need = length(ids) + (pause if last else 0) + 1.2
        if sh["id"] in CHAIN:  # generated from the last frame the previous segment shows (chain.py)
            f = SRC / CHAIN[sh["id"]]["file"]
            sh.update(clip=plate(f"{sh['id']}_ch", f, 0, probe(f) - .05, need, False, True), speed=1)
        elif kind == "talk":
            k, v, _ = hit
            f = SRC / SWAP.get(k, v["file"])
            off = OFFSET.get(k, 0)
            use = min(probe(f), LIMIT.get(k, 6.0)) - off
            sh.update(clip=plate(f"{n}_{k}", f, off, use, need, n in CCTV, True), speed=1)
        elif n in ("s31", "s32", "s54"):
            sh.update(camera_shot(n, ids, need + (.8 if n == "s54" else 0)), speed=1)
            if n == "s54":
                sh["lead"] = 1.0
        elif n in MOTION:
            m = MOTION[n]
            f = SRC / m["file"]
            off = m.get("offset", 0)
            use = min(probe(f), m.get("max_t", 99)) - off
            pp = n in PINGPONG
            sh.update(clip=plate(f"{n}_{c}", f, off, use, need, n in CCTV or n == "s49", pp), motion="push", focus=[.5, .5], amt=.025)
            sh.update({"speed": 1} if pp else {"min_speed": .3 if n == "s10" else .4})
        else:
            mv, amt = MOVE.get(n, ("push", .02))
            still = SRC / STILL.get(n, PICKS[n])
            if n == "s24" and c > 0:
                still = SRC / "src/tk4_s24_L067.png"  # after L066 the bag stays up
            if n == "s05":
                g = HERE / "plates" / "s05_ink.png"
                Image.blend(Image.open(still).convert("RGB"), Image.open(still).convert("L").convert("RGB"), .75).save(g)
                still = g
            if n == "s65":
                mv, amt = "static", 0
            if n in CCTV:
                g = HERE / "plates" / f"{n}_grey.png"
                Image.open(still).convert("L").convert("RGB").save(g)
                still = g
            sh.update(still=str(still), motion=mv, amt=amt, focus=[.5, .5])
            if mv == "pull":
                sh["zoom"] = amt
        if n == "s65":
            sh["overlays"] = [{"png": phone_card(), "at": [0, -.01], "fade": 0, "fade_out": 0}]
        if c == 0 and n in LABEL:
            sh["overlays"] = [{"png": label(n, LABEL[n]), "at": [.1, 3.4 if n not in CCTV else -.05], "fade": .2, "fade_out": .3}]
        if last and pause and any(w in note for w in SILENT):
            sh["music_cut"] = [-pause, 0]
        if last and n in SOUND:
            sh["_sound"] = SOUND[n]
        shots.append(sh)
    if n in BLACK_AFTER:
        black_next = True
        continue
    if black_next:  # the cut to black sits in front of the next row's first shot
        first = next(s for s in shots if s["id"].startswith(n))
        first["black"] = .7
        black_next = False

for sh in shots:  # sound positions: negative = seconds from the end of the shot, resolved after the lines are known
    if "_sound" in sh:
        d = length(sh["lines"]) + (sh["tail"] - TAIL)
        sh["sfx"] = [[s if s.startswith("file:") else "file:" + s, a if a >= 0 else max(0, d + a), g] for s, a, g in sh.pop("_sound")]
shots.append({"id": "end", "end": True, "dur": 6, "bg_clip": str(SRC / "clips/mo2_s25_s102.mp4"), "bg_t": 0, "amb": 0, "theme": "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/end_theme_12s.wav", "theme_at": .1, "theme_gain": 1.0, "music_cut": [0, 6], "overlays": [{"png": card_question(), "at": [0, 6], "fade": 0, "fade_out": 0}]})

import polish  # 打磨 pass: s60a phone lights up and buzzes during the missed call
polish.apply(shots)

SCR = {i:("「" + BY_ID[i]["text"] + "」" if BY_ID[i]["who"] != "VO" else BY_ID[i]["text"]).replace("⋯", "…") for i in cast}  # msjhbd draws ⋯ as a box
json.dump(SCR, open(VO / "script.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
json.dump(cast, open(VO / "picks_long.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
json.dump({"out": "long_v7", "title": "動物醫院的兩點十分", "music": "bed.wav", "music_gain": .22, "duck": .45, "amb_gain": 0, "vo_gain": 1.4, "vo_speed": 1.0, "vo_picks": "picks_long.json",
           "end_title": "本首完", "end_question": " ", "shots": shots}, open("shots_long.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
print(len(shots), "shots,", len(cast), "lines")
