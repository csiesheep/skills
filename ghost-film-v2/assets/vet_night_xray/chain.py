"""Chained clips inside a shot. The owner: 「連續的段落中，後面的段落應該要用前段落的尾幾幀當成頭幾幀」 - every segment that follows a moving
segment in the same shot is generated from the last frame the previous segment shows, so the action carries on instead of jumping back to the shared still.

py -X utf8 chain.py plan     -> chain_todo.json (what needs a chained clip, round by round)
py -X utf8 chain.py round    -> generates the next segment of every shot whose predecessor is ready (one polite.py call), checks it, retries a flagged
                               take once with the next seed, records chain_map.json {segment id: {"file", "src"}}
Run `round` until it prints "all done". make_long.py then plays chain_map clips for those segments."""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
S = "C:/Users/sheep/.claude/skills/ghost-film-v2/scripts"
HERE = Path.cwd()
REEL = HERE.parents[1] / "reel"
TALK = json.load(open(REEL / "talk_final.json", encoding="utf8"))
WHO = {"me": "穿灰色連帽外套的年輕男生", "dean": "穿白袍戴眼鏡的老醫生", "bin": "穿黑T恤的胖男生", "her": "穿透明雨衣的女生"}
LOOK = ("水墨淡彩漫畫風格的角色動畫，畫面維持跟第一幀完全一樣的筆觸、色調、房間、家具、人物長相和衣服。"
        "鏡頭完全固定不動，不推近、不拉遠、不移動，人物在畫面中的大小從頭到尾不變，同一個鏡頭從頭到尾不切換。"
        "人物的腳一直在原地，身體只有很小的動作，桌上的東西一直在原地。畫面乾淨，沒有字幕、沒有對話框、沒有任何文字或符號。")
END = "\noverall_soundscape: 日光燈很輕的嗡嗡聲，衣服摩擦的聲音。\nnon_diegetic_music: N/A\n"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 110
MAP = HERE / "chain_map.json"


def timeline():
    d = {}
    for l in open("out/long_v3/_timeline.txt", encoding="utf8"):
        m = l.split()
        if len(m) == 3 and m[0].replace(".", "").isdigit():
            d[m[2]] = float(m[1])
    return d


def segments():
    """Shots with their segments in order: (id, kind T/M/S, lines, plate or still, who)."""
    out = {}
    for s in json.load(open("shots_long.json", encoding="utf8"))["shots"]:
        if not re.match(r"s\d\d[a-z]$", s["id"]) or s["id"][:3] in ("s31", "s32", "s54"):
            continue
        clip = s.get("clip", "")
        kind = "T" if "_tk_" in clip or "_tk2_" in clip or "_tk3_" in clip else ("M" if clip else "S")
        who = None
        if kind == "T":
            who = next(v["who"] for k, v in TALK.items() if v["shot"] == s["id"][:3] and (v["ids"][0] == s.get("lines", [""])[0] or (v["shot"] == "s56" and s["lines"][0] == "L121")))
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
    import wave
    tot = 0
    for i in lines:
        f = Path(json.load(open("../vo/picks_long.json", encoding="utf8"))[i])
        with wave.open(str(f)) as w:
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
        L = 5  # 7 s chained clips pushed in (s45b); longer lines ping-pong
        if t["who"]:
            speak = min(L - 1, max(1, round(voice_len(seg["lines"]) + .3)))
            beat = (f"[0s-{speak}s] {WHO[t['who']]}正在講話，嘴巴連續清楚地一開一合。畫面中其他人嘴巴一直閉著，安靜看著他。"
                    f"[{speak}s-{L}s] 講完，嘴巴閉上，大家安靜站著。")
        else:
            beat = f"[0s-{L}s] 畫面中的人安靜地維持原來的姿勢，輕輕呼吸、偶爾眨眼，嘴巴一直閉著。"
        (REEL / "prompts" / f"{name}.txt").write_text(LOOK + "\n" + beat + END, encoding="utf8")
        args[t["id"]] = (name, L)
    for attempt, seed in enumerate((SEED, SEED + 1)):
        want = [f"{n}:{L}:{seed}" for k, (n, L) in args.items() if k not in chain]
        if not want:
            break
        subprocess.run(["py", "-X", "utf8", f"{S}/polite.py", "clips"] + want, cwd=REEL)
        for k, (n, L) in args.items():
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
    subprocess.run(["py", "-X", "utf8", f"{S}/strips.py", "sheet", f"strips/tk/chain_{len(chain):02d}.jpg"] + [chain[k]["file"] for k in args if k in chain], cwd=REEL)
    print("round done:", len(args), "clips;", len(chain), "/", len(todo), "chained")


if __name__ == "__main__":
    {"plan": plan, "round": run_round}[sys.argv[1]]()
