"""Fresh Qwen draws with a new framing (no source picture to keep): py -X utf8 fresh_draw.py jobs.json  (in film/reel)
jobs.json: {"out": "fx", "n": 4, "size": [720,1280], "jobs": {"name": {"prompt": "...", "refs": ["../out/cast/qi_2.png"]}}}
Refs are <image1>, <image2>... One job at a time, only on an empty ComfyUI queue. Skips names that already have outputs."""
import json, random, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, "C:/Users/sheep/.claude/skills/ghost-film-v2/scripts")
import uc  # noqa: F401
import manga
spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))
HERE = Path.cwd(); OUT = HERE / spec.get("out", "fx"); OUT.mkdir(exist_ok=True)
W, H = spec.get("size", [720, 1280])
manga.set_work(HERE)


def wait_clear():
    while True:
        try:
            q = json.load(urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=20))
            if not (q["queue_running"] or q["queue_pending"]):
                return
        except Exception:
            pass
        time.sleep(15)


for name, j in spec["jobs"].items():
    if list(OUT.glob(f"{name}_*.png")):
        print("skip", name, flush=True); continue
    refs = [HERE / r for r in j.get("refs", [])]
    wait_clear(); t0 = time.time()
    manga.job("panel", name, j["prompt"] + " No text.", refs, W, H, j.get("n", spec.get("n", 4)), random.randrange(2**31), OUT)
    print(time.strftime("%H:%M:%S"), name, f"{time.time()-t0:.0f}s", flush=True)
print("ALLDONE", flush=True)
