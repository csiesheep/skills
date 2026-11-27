"""Same-framing Qwen edits of picked stills (fix a prop, close a door, an FL2VA last frame, a ghost version), n candidates
each, one job at a time and only on an empty ComfyUI queue. Pause the H3 clip loop first (pause.py): never mix Qwen and H3.

py -X utf8 edit_stills.py <jobs.json> [--dry]      run in <story>/film/reel; writes <out>/<name>_<k>.png

jobs.json:
{"out": "fx", "n": 3, "size": [720, 1280],
 "blocks": {"DOOR": "The door is a plain dark-brown wooden room door with one coin-sized brass peephole."},
 "jobs": {"k17p": {"src": "src/k17.png", "change": "Change only the peephole: {DOOR}", "refs": ["../out/cast/qing_3.png"]}}}

The prompt is "The same picture as <image1>: ..." + change; src is <image1>, refs follow as <image2>, <image3>.
{NAME} in a change is replaced by blocks[NAME] (the set's architecture block, so every edit says the same door).
A name that already has outputs is skipped: delete them or use a new name to retry."""
import json, random, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
KEEP = ("The same picture as <image1>: the same camera, framing, light, colours, film grain and everything else. ")
spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))
dry = "--dry" in sys.argv
HERE = Path.cwd()
OUT = HERE / spec.get("out", "fx")
W, H = spec.get("size", [720, 1280])
jobs = []
for name, j in spec["jobs"].items():
    change = j["change"]
    for k, v in spec.get("blocks", {}).items():
        change = change.replace("{" + k + "}", v)
    refs = [HERE / j["src"]] + [HERE / r if not Path(r).is_absolute() else Path(r) for r in j.get("refs", [])]
    miss = [str(r) for r in refs if not r.exists()]
    if miss:
        sys.exit(f"{name}: missing {miss}")
    if "{" in change:
        sys.exit(f"{name}: unknown block in: {change}")
    jobs.append((name, KEEP + change + ("" if "No text" in change else " No text."), refs, j.get("n", spec.get("n", 3))))
if dry:
    for name, prompt, refs, n in jobs:
        print(name, n, [r.name for r in refs], "\n  ", prompt)
    sys.exit()

import uc  # noqa: E402  the uncensored Qwen 2.1 GGUF
import manga  # noqa: E402


def wait_clear():
    while True:
        try:
            q = json.load(urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=20))
            if not (q["queue_running"] or q["queue_pending"]):
                return
        except Exception:
            time.sleep(20)
        time.sleep(5)


OUT.mkdir(exist_ok=True)
manga.set_work(HERE)
for name, prompt, refs, n in jobs:
    if list(OUT.glob(f"{name}_*.png")):
        print("skip", name, flush=True); continue
    wait_clear(); t0 = time.time()
    manga.job("repaint", name, prompt, refs, W, H, n, random.randrange(2**31), OUT)
    print(time.strftime("%H:%M:%S"), name, f"{time.time()-t0:.0f}s", flush=True)
print("ALLDONE", flush=True)
