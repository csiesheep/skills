"""Moving panels for the Reel: pick the panels worth animating, crop them 9:16, draft an H3 prompt for each, and run
them through the local H3 image-to-video workflow one at a time.

    py -X utf8 clips.py plan <story folder> [--count 6 | --panels p1,p8] [--prefix tb]  images and prompt drafts
    py -X utf8 clips.py run  <story folder> [--seconds 5] [--only p8,p29] queues H3, one clip after another

`plan` reads the shot list (reels/shots.json) and the board: it takes the cold open, the establishing panel under
the title, the panel before the reveal, the reveal and the last panel, then the widest remaining V3 panels, up to
--count. For each it writes reels/clips/src/<prefix>_<panel>.png (the picked panel, cropped 9:16 around its focus)
and reels/clips/<prefix>_<panel>_prompt.txt, a draft H3 prompt built from the panel's prompt on the board. **Read
and rewrite every prompt before `run`**: say what moves (wind in the bamboo, a curtain, breath, a slow push), keep
"black-and-white manga line art" and keep faces still; a drafted prompt only knows the panel's description.

`run` needs ComfyUI up (127.0.0.1:8188). It calls the h3-image-to-video skill's h3_i2v.py for each planned panel
that has no reels/clips/<prefix>_<panel>.mp4 yet, so a run cut short by a crash resumes where it stopped. About
3 minutes per 5-second clip. Afterwards put "clip": "reels/clips/<prefix>_<panel>.mp4" on those shots in
shots.json (plan prints the lines) and look at each clip: a melted face or a drawing gone realistic is redone
with another seed or left static.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
H3 = Path.home() / ".claude" / "skills" / "h3-image-to-video" / "h3_i2v.py"

PROMPT = """integrated_multimodal_description:
黑白日式恐怖漫畫線稿風格，畫面全程維持黑白線稿與網點質感，不要變成寫實或彩色，人物的臉保持不變。{scene}
[0s-2s] 鏡頭極慢往前推；{move}
[2s-4s] {move2}
[4s-5s] 動作慢慢停下，畫面恢復安靜。

overall_soundscape:
{sound}

non_diegetic_music:
N/A
"""


def plan(a) -> int:
    import reel as R
    import story
    d = Path(a.story).resolve()
    S = story.load(d)
    mg = R.mg
    mg.set_work(Path(S.COMIC))
    b, ch = mg.load_board(), mg.load_choices()
    _, after = mg.reveal_point(b)
    order = [c["id"] for _, c, _ in mg.all_panels(b)]
    boxes = {c["id"]: (c, box) for _, c, box in mg.all_panels(b)}
    reveal = next((p for p in order if boxes[p][0].get("reveal")), None)
    v3 = [p for p, *_ in S.V3 if p != "TITLE"]
    want = []
    for p in [v3[0] if v3 else None, order[0], order[order.index(reveal) - 1] if reveal else None, reveal, order[-1]]:
        if p and p not in want and p in ch["panels"]:
            want.append(p)
    rest = sorted((p for p in v3 if p not in want and p in ch["panels"]),
                  key=lambda p: -((boxes[p][1][2] - boxes[p][1][0]) / max(1, boxes[p][1][3] - boxes[p][1][1])))
    want += rest[: max(0, a.count - len(want))]
    if a.panels:  # the panels named by hand win over the pick
        want = [x for x in a.panels.split(",") if x in ch["panels"]]
    out = d / "reels" / "clips"
    (out / "src").mkdir(parents=True, exist_ok=True)
    items = []
    for p in want:
        cell, _ = boxes[p]
        img = mg.panel_source(cell, ch)
        img = img.resize((img.width * 2, img.height * 2))
        tall = mg.cover(img, 720, 1280, tuple(cell.get("focus", (0.5, 0.5))))
        src = out / "src" / f"{a.prefix}_{p}.png"
        tall.save(src)
        pf = out / f"{a.prefix}_{p}_prompt.txt"
        if not pf.exists():
            scene = cell.get("prompt", "").split(". ")[0][:200]
            night = "night" in cell.get("prompt", "").lower() or p in after
            pf.write_bytes(PROMPT.format(
                scene=f"畫面內容：{scene}",
                move="光影輕微晃動。" if not night else "黑暗中光線微微閃爍。",
                move2="背景的細節輕輕動（風、布、煙、光），人物只有呼吸般的微小動作。",
                sound="安靜的環境音。").encode("utf-8"))
        items.append({"panel": p, "image": src.relative_to(d).as_posix(), "prompt": pf.relative_to(d).as_posix(),
                      "out": f"reels/clips/{a.prefix}_{p}.mp4"})
    (out / "plan.json").write_bytes((json.dumps(items, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"{out / 'plan.json'}: {len(items)} panels — " + ", ".join(i["panel"] for i in items))
    print("Rewrite each prompt (reels/clips/*_prompt.txt), then `clips.py run`. In shots.json, per shot:")
    for i in items:
        print(f'  {i["panel"]}: "clip": "{i["out"]}"')
    return 0


def run(a) -> int:
    d = Path(a.story).resolve()
    items = json.loads((d / "reels" / "clips" / "plan.json").read_text(encoding="utf-8"))
    only = set(a.only.split(",")) if a.only else None
    for i in items:
        if only and i["panel"] not in only:
            continue
        dest = d / i["out"]
        if dest.exists():
            print(f"{i['panel']}: {dest.name} exists, skipped")
            continue
        tmp = d / "reels" / "clips" / "_h3"
        tmp.mkdir(exist_ok=True)
        cmd = [sys.executable, "-X", "utf8", str(H3), "--image", str(d / i["image"]), "--prompt-file",
               str(d / i["prompt"]), "--seconds", str(a.seconds), "--out-dir", str(tmp), "--prefix", dest.stem]
        if a.seed is not None:
            cmd += ["--seed", str(a.seed)]
        print(f"{i['panel']}: running H3 ({a.seconds:g} s)…", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print(r.stdout[-800:], r.stderr[-800:], file=sys.stderr)
            return 1
        made = sorted(tmp.glob(f"{dest.stem}*.mp4"), key=lambda f: f.stat().st_mtime)
        if not made:
            print(f"{i['panel']}: H3 finished but no mp4 in {tmp}", file=sys.stderr)
            return 1
        made[-1].replace(dest)
        info = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        print(f"{i['panel']}: {dest.name} {info[:160]}", flush=True)
    return 0


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("story")
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--panels", default=None, help="comma-separated panels to animate instead of the pick")
    p.add_argument("--prefix", default=None, help="file prefix (default: the story folder's initials, e.g. nc, tb)")
    r = sub.add_parser("run")
    r.add_argument("story")
    r.add_argument("--seconds", type=float, default=5.0, help="H3's trained range is 5 to 15")
    r.add_argument("--only", default=None, help="comma-separated panels")
    r.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "plan" and not a.prefix:
        a.prefix = "".join(w[0] for w in Path(a.story).resolve().name.split("_"))
    return plan(a) if a.cmd == "plan" else run(a)


if __name__ == "__main__":
    sys.exit(main())
