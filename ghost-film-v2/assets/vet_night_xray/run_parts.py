"""Render the long film in four parallel pieces (one pass took 1 h 50 m alone), join the silent pictures, then mix the sound once over the whole film.
py -X utf8 run_parts.py shots_long.json"""
import json
import subprocess
import sys
import time
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
RENDER = "C:/Users/sheep/.claude/skills/ghost-film-v2/scripts/render.py"
spec_file = sys.argv[1]
S = json.load(open(spec_file, encoding="utf8"))
ids = [x["id"] for x in S["shots"]]
cuts = [0] + [ids.index(k) for k in ("s16a", "s29a", "s52a")] + [len(ids)]
t0 = time.time()
procs, names = [], []
for i in range(4):
    T = dict(S)
    T["out"] = f"{S['out']}_p{i + 1}"
    T["shots"] = S["shots"][cuts[i]: cuts[i + 1]]
    f = f"shots_p{i + 1}.json"
    json.dump(T, open(f, "w", encoding="utf8"), ensure_ascii=False)
    names.append(T["out"])
    procs.append(subprocess.Popen(["py", "-X", "utf8", RENDER, f], stdout=open(f"p{i + 1}.log", "w", encoding="utf8"), stderr=subprocess.STDOUT))
codes = [p.wait() for p in procs]
print("parts", codes, round((time.time() - t0) / 60, 1), "min", flush=True)
if any(codes):
    sys.exit(1)
out = Path("out") / S["out"]
out.mkdir(parents=True, exist_ok=True)
lst = out / "_parts.txt"
lst.write_text("".join(f"file '{(Path('out') / n / '_silent.mp4').resolve().as_posix()}'\n" for n in names), encoding="utf8")
subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "_silent.mp4")], check=True)
r = subprocess.run(["py", "-X", "utf8", RENDER, spec_file, "--reuse"], capture_output=True, text=True, encoding="utf8", errors="ignore")
print(r.stdout[-900:], r.stderr[-400:])
print("done", round((time.time() - t0) / 60, 1), "min")
