"""Pause/resume the clip loop without losing the job in flight: `pause` touches an empty placeholder for every
not-yet-made clip in plan lists 0 and 1 (polite.py skips existing files); `resume` deletes the placeholders it made."""
import json, subprocess, sys
from pathlib import Path
P = Path("pause_placeholders.json")
if sys.argv[1] == "pause":
    specs = sum((subprocess.run(["py", "-X", "utf8", "plan.py", "list", r], capture_output=True, text=True).stdout.split() for r in "01"), [])
    busy = set(sys.argv[2:])   # names whose job is in flight: no placeholder (the rename would fail)
    made = []
    for s in specs:
        n, sec, seed = s.split(":")
        f = Path(f"clips/{n}_s{seed}.mp4")
        if not f.exists() and f"{n}_s{seed}" not in busy:
            f.touch(); made.append(f.name)
    P.write_text(json.dumps(made, indent=1)); print("paused", len(made))
else:
    keep = set(json.loads(Path("door_placeholders.json").read_text()))
    n = 0
    for f in json.loads(P.read_text()):
        p = Path("clips") / f
        if f not in keep and p.exists() and p.stat().st_size == 0:
            p.unlink(); n += 1
    print("resumed", n)
