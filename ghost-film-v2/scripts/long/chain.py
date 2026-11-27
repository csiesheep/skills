"""Chained clips inside a shot (owner on 〈動物醫院的兩點十分〉: 「有些連續的段落，頭幀都用同一張，看起來很怪，就像做了一些動作後，
後回到第一幀，而且動作不連續／連續的段落中，後面的段落應該要用前段落的尾幾幀當成頭幾幀吧」).

Every segment that follows a moving segment in the same shot is generated from the frame the previous segment actually
shows at its cut (after ping-pong), so the action carries on instead of snapping back to the shot's shared still.
Run from the long-film folder (the one with shots_long.json and out/), with a chain.json there:

{"reel": "../../reel",                       # the folder with src/, prompts/, clips/, strips/ (polite.py runs there)
 "talk": "../../reel/talk_final.json",       # {key: {"shot": "s13", "ids": ["L034", ...], "who": "bin"}}
 "picks": "../vo/picks_long.json",           # line id -> voice wav (for the speaking seconds)
 "timeline": "out/long_v3/_timeline.txt",    # a dry.py or render timeline of the current cut
 "who": {"me": "穿灰色連帽外套的年輕男生", "dean": "穿白袍戴眼鏡的老醫生"},
 "skip_shots": ["s31", "s32", "s54"],        # drawn camera plates, X-ray screens: never chained
 "talk_markers": ["_tk_", "_tk2_", "_tk3_"]} # a plate whose name has one of these is a talking clip

py -X utf8 chain.py plan            -> chain_todo.json (segments that need a chained clip)
py -X utf8 chain.py round [seed]    -> next link of every chain whose predecessor is ready (one polite.py call); retries a
                                       clip_check FLAG once with seed+1; records chain_map.json {id: {"file", "src", "flag"}};
                                       writes a strip sheet <reel>/strips/tk/chain_NN.jpg
Run `round` (in the background, on an empty queue) until it prints "all done". Then LOOK at every strip: clip_check
passed both push-ins on the first film. A bad link spoils every later link of its chain: delete it AND the links after
it from chain_map.json and run `round` again with a new seed. The long-film builder plays chain_map clips for those
segments (make_long.py: `if sh["id"] in CHAIN: plate(... from CHAIN[id]["file"] ...)`).
Clips are 5 s: H3 refuses under 5 s, and 7 s chained clips pushed in. Longer segments ping-pong; a clip that pushes in
first and then settles is played once and held with hold_plate.py."""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
S = str(Path(__file__).resolve().parents[1])
CFG = json.load(open("chain.json", encoding="utf8"))
REEL = Path(CFG["reel"]).resolve()
TALK = json.load(open(CFG["talk"], encoding="utf8"))
WHO = CFG["who"]
SKIP = set(CFG.get("skip_shots", []))
MARK = CFG.get("talk_markers", ["_tk_"])
L = 5
LOOK = CFG.get("look", "水墨淡彩漫畫風格的角色動畫，畫面維持跟第一幀完全一樣的筆觸、色調、房間、家具、人物長相和衣服。"
               "鏡頭完全固定不動，不推近、不拉遠、不移動，人物在畫面中的大小從頭到尾不變，同一個鏡頭從頭到尾不切換。"
               "人物的腳一直在原地，身體只有很小的動作，桌上的東西一直在原地。畫面乾淨，沒有字幕、沒有對話框、沒有任何文字或符號。")
END = CFG.get("sound", "\noverall_soundscape: 日光燈很輕的嗡嗡聲，衣服摩擦的聲音。\nnon_diegetic_music: N/A\n")
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 110
MAP = Path("chain_map.json")


def timeline():
    d = {}
    for l in open(CFG["timeline"], encoding="utf8"):
        m = l.split()
        if len(m) == 3 and m[0].replace(".", "").isdigit():
            d[m[2]] = float(m[1])
    return d


def segments():
    """Shots with their segments in order: id, kind T (talking clip) / M (motion clip) / S (still), lines, plate or still, who."""
    out = {}
    for s in json.load(open("shots_long.json", encoding="utf8"))["shots"]:
        if not re.match(r"s\d\d[a-z]$", s["id"]) or s["id"][:3] in SKIP:
            continue
        clip = s.get("clip", "")
        first = (s.get("lines") or [""])[0]   # the speaker comes from talk_final by line id (a chained plate's name has no marker)
        who = next((v["who"] for v in TALK.values() if v["shot"] == s["id"][:3] and first in v["ids"]), None)
        kind = "T" if who or any(m in clip for m in MARK) else ("M" if clip else "S")
        out.setdefault(s["id"][:3], []).append({"id": s["id"], "kind": kind, "lines": s.get("lines", []), "clip": clip, "still": s.get("still"), "who": who})
    return out


def plan():
    todo = []
    for shot, segs in segments().items():
        for i in range(1, len(segs)):
            if segs[i - 1]["kind"] in "TM" or any(t["id"] == segs[i - 1]["id"] for t in todo):
                todo.append({"id": segs[i]["id"], "prev": segs[i - 1]["id"], "who": segs[i]["who"], "shot": shot})
    json.dump(todo, open("chain_todo.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(len(todo), "segments to chain")


def probe(f):
    e = subprocess.run([FF, "-i", str(f)], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def shown_time(usable, t):
    """The clip second shown at segment time t when a clip of `usable` s plays forward then backward."""
    if t <= usable:
        return t
    k = t % (2 * usable)
    return k if k <= usable else 2 * usable - k


def last_frame(seg_id, segs_by_id, dur, chain, out_png):
    seg = segs_by_id[seg_id]
    t = max(0, dur[seg_id] - 1 / 24)
    if seg_id in chain:
        f = REEL / chain[seg_id]["file"]
        t = shown_time(probe(f) - .05, t)
    elif seg["kind"] == "S":
        f, t = Path(seg["still"]), None
    else:
        f = Path(seg["clip"])   # the current plate: already cut or ping-ponged to the segment
        t = min(t, probe(f) - .05)
    vf = "scale=731:1280:force_original_aspect_ratio=increase,crop=720:1280"
    args = [FF, "-y", "-v", "error"] + (["-ss", f"{t:.3f}"] if t is not None else []) + ["-i", str(f), "-frames:v", "1", "-vf", vf, str(out_png)]
    subprocess.run(args, check=True)


def voice_len(lines):
    picks = json.load(open(CFG["picks"], encoding="utf8"))
    tot = 0
    for i in lines:
        with wave.open(str(picks[i])) as w:
            tot += w.getnframes() / w.getframerate()
    return tot


def run_round():
    todo = json.load(open("chain_todo.json", encoding="utf8"))
    chain = json.load(open(MAP, encoding="utf8")) if MAP.exists() else {}
    dur = timeline()
    segs = {x["id"]: x for v in segments().values() for x in v}
    ready = [t for t in todo if t["id"] not in chain and (t["prev"] in chain or t["prev"] not in {x["id"] for x in todo})]
    if not ready:
        print("all done" if all(t["id"] in chain for t in todo) else "blocked")
        return
    args = {}
    for t in ready:
        name = f"ch_{t['id']}"
        last_frame(t["prev"], segs, dur, chain, REEL / "src" / f"{name}.png")
        seg = segs[t["id"]]
        if t["who"]:
            speak = min(L - 1, max(1, round(voice_len(seg["lines"]) + .3)))
            beat = (f"[0s-{speak}s] {WHO[t['who']]}正在講話，嘴巴連續清楚地一開一合。畫面中其他人嘴巴一直閉著，安靜看著他。"
                    f"[{speak}s-{L}s] 講完，嘴巴閉上，大家安靜站著。")
        else:
            beat = f"[0s-{L}s] 畫面中的人安靜地維持原來的姿勢，輕輕呼吸、偶爾眨眼，嘴巴一直閉著。"
        (REEL / "prompts" / f"{name}.txt").write_text(LOOK + "\n" + beat + END, encoding="utf8")
        args[t["id"]] = name
    for attempt, seed in enumerate((SEED, SEED + 1)):
        want = [f"{n}:{L}:{seed}" for k, n in args.items() if k not in chain]
        if not want:
            break
        subprocess.run(["py", "-X", "utf8", f"{S}/polite.py", "clips"] + want, cwd=REEL)
        for k, n in args.items():
            if k in chain:
                continue
            f = REEL / "clips" / f"{n}_s{seed}.mp4"
            if not f.exists():
                continue
            r = subprocess.run(["py", "-X", "utf8", f"{S}/clip_check.py", str(f)], capture_output=True, text=True, encoding="utf8", errors="ignore")
            print(r.stdout.strip())
            if r.returncode == 0 or attempt == 1:
                chain[k] = {"file": f"clips/{n}_s{seed}.mp4", "src": f"src/{n}.png", "flag": r.returncode != 0}
        json.dump(chain, open(MAP, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    (REEL / "strips" / "tk").mkdir(parents=True, exist_ok=True)
    subprocess.run(["py", "-X", "utf8", f"{S}/strips.py", "sheet", f"strips/tk/chain_{len(chain):02d}.jpg"] + [chain[k]["file"] for k in args if k in chain], cwd=REEL)
    print("round done:", len(args), "clips;", len(chain), "/", len(todo), "chained")


if __name__ == "__main__":
    {"plan": plan, "round": run_round}[sys.argv[1]]()
