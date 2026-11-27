"""The long film with its end card, and shorts under 3:00 cut from it, with no second render of the film body.
Each short = an opener (rendered once in an extras spec) + a stretch of the long film + a card (12 s when it fits).
A short that would pass LIMIT keeps only the card's first seconds and fades the last 2 s (owner on 〈動物醫院的兩點十分〉:
「每一個片尾，能放12秒，就放12秒／第三篇，就放片尾的前幾秒，最後2秒漸弱」). Every output goes through a limiter (true peak about -1 dB).

py -X utf8 cut_shorts.py shorts_plan.json

shorts_plan.json:
{"long": "out/long_v7", "extras": "out/extras_v2", "endcard": "out/endcard_v1",
 "out_long": "out/long_v8/long_v8.mp4", "out_shorts": "out/shorts_v4", "limit": 179.8, "card": 12,
 "shorts": [{"opener": ["h1a", "h2"], "body": ["s02a", "s16a"], "card": "c1"},      # extras ids from..to, long ids from..to
            ...
            {"opener": ["h4", "c1"], "body": ["s52a", "end"], "card": null}]}      # null: the long film's own end card
Ids are read from each folder's _timeline.txt (start times); "end" is the long film's end shot."""
import json
import subprocess
import sys
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
P = json.load(open(sys.argv[1], encoding="utf8"))
LONG, EXTRA, ENDC = Path(P["long"]), Path(P["extras"]), Path(P["endcard"])
LIMIT, CARD = P.get("limit", 179.8), P.get("card", 12.0)


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
    fc.append("".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[v][a0];[a0]alimiter=limit=0.89:level=0[a]")
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [FF, "-y", "-v", "error"]
    for s in SRC:
        args += ["-i", str(s)]
    subprocess.run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(out, round(sum(b - a for _, a, b in pieces), 1), "s", flush=True)


join([(0, 0, TL["end"]), (2, 0, CARD)], Path(P["out_long"]))
for n, s in enumerate(P["shorts"], 1):
    pieces = [(1, TE[s["opener"][0]], TE[s["opener"][1]]), (0, TL[s["body"][0]], TL[s["body"][1]])]
    used = sum(b - a for _, a, b in pieces)
    card_len = min(CARD, LIMIT - used)
    pieces.append((1, TE[s["card"]], TE[s["card"]] + card_len) if s.get("card") else (2, 0, card_len))
    join(pieces, Path(P["out_shorts"]) / f"short{n}.mp4", fade_end=2.0 if card_len < CARD else 0.0)
