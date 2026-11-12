"""One GPU job at a time, only when ComfyUI's queue is empty (another session draws Qwen stills on the same GPU; H3 and
Qwen must never interleave). From <story>/film/reel:
    py -X utf8 polite.py speech <jobs.json>          one speak.py job per submit, waits for each to finish
    py -X utf8 polite.py clips name:sec:seed ...     h3_i2v.py per clip (src/<name>.png + prompts/<name>.txt)
A finished output is skipped. Prints start/end per job and the GPU minutes at the end."""
import json, subprocess, sys, time, urllib.request
from pathlib import Path
HOST = "http://127.0.0.1:8188"
SK = Path.home() / ".claude/skills"
OUT = Path("C:/Users/sheep/code/ComfyUI/output")


def q():
    return json.load(urllib.request.urlopen(HOST + "/queue", timeout=20))


def busy():
    d = q()
    return bool(d["queue_running"] or d["queue_pending"])


def wait_clear():
    quiet = 0
    while quiet < 1:
        try:
            quiet = 0 if busy() else quiet + 1
        except Exception as e:
            print("queue read failed", e, flush=True); quiet = 0; time.sleep(20)
        time.sleep(0.7)


def wait_done(pid):
    while True:
        h = json.load(urllib.request.urlopen(f"{HOST}/history/{pid}", timeout=20))
        if pid in h:
            st = h[pid].get("status", {})
            return st.get("status_str", "?")
        time.sleep(5)


gpu = 0.0
mode = sys.argv[1]
if mode == "speech":
    jobs = json.load(open(sys.argv[2], encoding="utf8"))
    for j in jobs:
        if list((OUT / "ghost_film_vo").glob(j["name"] + "_*.flac")):
            continue
        wait_clear()
        t0 = time.time()
        tmp = Path("_one_job.json"); tmp.write_text(json.dumps([j], ensure_ascii=False), encoding="utf8")
        r = subprocess.run([sys.executable, "-X", "utf8", str(SK / "ghost-film/scripts/speak.py"), str(tmp)], capture_output=True, text=True, encoding="utf8")
        try:
            pid = json.loads(r.stdout.split(" ", 1)[1])["prompt_id"]
            st = wait_done(pid)
        except Exception:
            st = "ERR " + r.stdout[-300:] + r.stderr[-300:]
        dt = time.time() - t0; gpu += dt
        print(time.strftime("%H:%M:%S"), j["name"], st, f"{dt:.0f}s", flush=True)
elif mode == "music":   # music name seed seconds
    wait_clear()
    t0 = time.time()
    r = subprocess.run([sys.executable, "-X", "utf8", str(SK / "ghost-film/scripts/music.py")] + sys.argv[2:5], capture_output=True, text=True, encoding="utf8")
    st = wait_done(json.loads(r.stdout)["prompt_id"])
    gpu += time.time() - t0
    print(time.strftime("%H:%M:%S"), "music", sys.argv[2], st, flush=True)
elif mode == "clips":
    Path("clips").mkdir(exist_ok=True)
    for spec in sys.argv[2:]:
        n, s, seed = spec.split(":")
        out = Path(f"clips/{n}_s{seed}.mp4")
        if out.exists():
            continue
        wait_clear()
        t0 = time.time()
        with open(f"clips/{n}_s{seed}.log", "w", encoding="utf8") as lg:
            subprocess.run([sys.executable, "-X", "utf8", str(SK / "h3-image-to-video/h3_i2v.py"), "--image", f"src/{n}.png",
                            "--prompt-file", f"prompts/{n}.txt", "--seconds", s, "--seed", seed, "--out-dir", "clips",
                            "--prefix", f"{n}_s{seed}"], stdout=lg, stderr=subprocess.STDOUT)
        got = sorted(Path("clips").glob(f"{n}_s{seed}*.mp4"), key=lambda p: p.stat().st_mtime)
        if got and got[-1] != out:
            got[-1].rename(out)
        dt = time.time() - t0; gpu += dt
        print(time.strftime("%H:%M:%S"), n, seed, "ok" if out.exists() else "FAILED", f"{dt:.0f}s", flush=True)
print(f"ALLDONE gpu_min={gpu/60:.1f}", flush=True)
