"""The long film with its 12 s end card, and four shorts under 3:00: opener (extras), a stretch of the long film, a 12 s card.
Short 3 is 2:56 before its card, so it keeps only the card's first seconds and fades the last 2 s (owner: 「第三篇，就放片尾的前幾秒，最後2秒漸弱」).
py -X utf8 cut_shorts.py out/long_v3 out/extras_v2 out/endcard_v1 -> out/long_v8/long_v8.mp4, out/shorts_v4/short{1..4}.mp4"""
import subprocess
import sys
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
LONG, EXTRA, ENDC = (Path(a) for a in sys.argv[1:4])
LIMIT = 179.8


def starts(d):
    t = {}
    for l in open(d / "_timeline.txt", encoding="utf8"):
        m = l.split()
        if len(m) == 3 and m[0].replace(".", "").isdigit():
            t[m[2]] = float(m[0])
    return t


TL, TE = starts(LONG), starts(EXTRA)
SRC = [LONG / f"{LONG.name}.mp4", EXTRA / f"{EXTRA.name}.mp4", ENDC / f"{ENDC.name}.mp4"]


def join(pieces, out, fade_end=0.0):
    fc, labels = [], []
    for k, (src, a, b) in enumerate(pieces):
        last = k == len(pieces) - 1
        v = f"[{src}:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS"
        au = f"[{src}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.08"
        if last and fade_end:
            v += f",fade=t=out:st={b - a - fade_end:.3f}:d={fade_end}"
            au += f",afade=t=out:st={b - a - fade_end:.3f}:d={fade_end}"
        else:
            au += f",afade=t=out:st={b - a - .12:.3f}:d=0.12"
        fc += [v + f"[v{k}]", au + f"[a{k}]"]
        labels.append(f"[v{k}][a{k}]")
    fc.append("".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[v][a0];[a0]alimiter=limit=0.89:level=0[a]")  # true peak under -1 dB
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [FF, "-y", "-v", "error"]
    for s in SRC:
        args += ["-i", str(s)]
    subprocess.run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(out, round(sum(b - a for _, a, b in pieces), 1), "s", flush=True)


join([(0, 0, TL["end"]), (2, 0, 12)], Path("out/long_v8/long_v8.mp4"))
PLAN = {1: (("h1a", "h2"), ("s02a", "s16a"), "c1"), 2: (("h2", "h3"), ("s16a", "s29a"), "c2"), 3: (("h3", "h4"), ("s29a", "s52a"), "c3"), 4: (("h4", "c1"), ("s52a", "end"), None)}
for n, (op, body, card) in PLAN.items():
    pieces = [(1, TE[op[0]], TE[op[1]]), (0, TL[body[0]], TL[body[1]])]
    used = sum(b - a for _, a, b in pieces)
    card_len = min(12.0, LIMIT - used)
    pieces.append((1, TE[card], TE[card] + card_len) if card else (2, 0, card_len))
    join(pieces, Path(f"out/shorts_v4/short{n}.mp4"), fade_end=2.0 if card_len < 12 else 0.0)
