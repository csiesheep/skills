"""After spans.py / spans2.py: make picked takes sound like where they come from, and point picks.json at the result
(spans stay: these filters keep the timing). Run in <story>/film/vo.

py -X utf8 voice_fx.py phone=P1,P2,P3 door=Q4,Q5        -> fx/<line>.wav

phone  a caller on a phone (band-pass, compressed, a little grit)
door   a voice behind a closed door (muffled, a short room echo)
A line already pointing into fx/ is skipped. Do not lay a sound effect on a filtered line: it hides it."""
import json, subprocess, sys
from pathlib import Path
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
FX = {"phone": "highpass=f=380,lowpass=f=3200,acompressor=threshold=0.1:ratio=4,volume=1.6,alimiter=limit=0.7",
      "door": "lowpass=f=1500,aecho=0.8:0.6:18:0.25,volume=1.3"}
P = json.loads(Path("picks.json").read_text(encoding="utf8"))
Path("fx").mkdir(exist_ok=True)
for arg in sys.argv[1:]:
    kind, ids = arg.split("=")
    for k in ids.split(","):
        if "/fx/" in P[k]:
            print("skip", k); continue
        out = Path("fx") / f"{k}.wav"
        subprocess.run([FF, "-y", "-v", "error", "-i", P[k], "-af", FX[kind], "-ar", "44100", str(out)], check=True)
        P[k] = str(out.resolve()).replace("\\", "/")
        print(k, kind, "->", out)
Path("picks.json").write_text(json.dumps(P, ensure_ascii=False, indent=1), encoding="utf8")
