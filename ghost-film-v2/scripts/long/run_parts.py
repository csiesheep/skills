"""Render the long film in four parallel pieces (one pass took 1 h 50 m alone), join the silent pictures, then mix the sound once over the whole film.
py -X utf8 run_parts.py shots_long.json s16a s29a s52a   (the shot ids where parts 2.. start; 3 ids = 4 parts)
If one part fails with a PermissionError in sfx.read_raw (two parts reading one wav), rerun that part alone:
py -X utf8 <skill>/scripts/render.py shots_pN.json, then this script with --join-only."""
import json
import subprocess
import sys
import time
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
RENDER = str(Path(__file__).resolve().parents[1] / "render.py")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
spec_file, splits = args[0], args[1:]
JOIN_ONLY = "--join-only" in sys.argv
S = json.load(open(spec_file, encoding="utf8"))
ids = [x["id"] for x in S["shots"]]
cuts = [0] + [ids.index(k) for k in splits] + [len(ids)]
N = len(cuts) - 1
t0 = time.time()
procs, names = [], []
for i in range(N):
    T = dict(S)
    T["out"] = f"{S['out']}_p{i + 1}"
    T["shots"] = S["shots"][cuts[i]: cuts[i + 1]]
    f = f"shots_p{i + 1}.json"
    json.dump(T, open(f, "w", encoding="utf8"), ensure_ascii=False)
    names.append(T["out"])
    if not JOIN_ONLY:
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
