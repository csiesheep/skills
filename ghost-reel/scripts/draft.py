"""A first shot list for a comic, from its board: `reels/shots.json`, to be read and edited before rendering.

    py -X utf8 draft.py <story folder> [--target 85] [--force]

What it decides, from the board alone (comic/board.json, the picked panels and the "reveal" mark):
- the cold open: the hook panel before the reveal (the same pick as ghost-comic's Threads picture), then the
  title card;
- which panels play in V3: every lettered panel in reading order, then the least needed ones dropped until the film
  fits --target seconds; the hook, the panel before the reveal, the reveal and the last panel always stay;
- per shot: seconds from the length of the line, one short subtitle (the first spoken or narrated sentence, cut at a
  comma when long), a voice-in-the-frame for "voice" lettering, the camera move from the panel's shape, "night"
  from the panel's prompt, a whisper, phone ping or heartbeat from what the panel holds;
- the reveal: a second of black, a stinger, shake, the music ducked; the last panel: darken, riser and stinger;
- H3 clips already in reels/clips (named *_<panel>.mp4) are used where they exist;
- V1: the same cold open, every panel, the reveal and the ending marked; ambience from the setting.

It never writes over an existing shots.json without --force: a shot list is hand-edited work.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

NIGHT = re.compile(r"\b(night|dark|midnight|moonlight|dim|unlit|3 ?am|at night)\b", re.I)
OUTDOOR = re.compile(r"\b(mountain|forest|bamboo|camp|tent|trail|field|road|village|river|outdoor)\b", re.I)
SENT = re.compile(r"[^。！？]*[。！？」]?")


def lettering(cell, kinds=("speech", "voice", "narration", "phone", "screen")) -> list[dict]:
    return [e for e in cell.get("text", []) if e["kind"] in kinds]


def short_line(cell, limit=20) -> tuple[str | None, str | None]:
    """(subtitle, kind): the first spoken line if there is one, else the first narrated one, one sentence, cut at a
    comma when longer than `limit` characters."""
    ents = lettering(cell, ("voice", "speech")) or lettering(cell, ("narration",))
    if not ents:
        return None, None
    e = ents[0]
    text = e["text"].replace("\n", "")
    first = next((s for s in SENT.findall(text) if s.strip()), text).strip()
    if len(first) > limit:
        parts = re.split(r"(?<=[，、：])", first)
        acc = ""
        for p in parts:
            if len(acc + p) > limit:
                break
            acc += p
        first = acc.rstrip("，、：") + "。" if acc else first[:limit]
    if e["kind"] == "speech":
        first = f"「{first.strip('「」')}」"
    return first, e["kind"]


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("--target", type=float, default=85.0, help="V3 length to aim for, seconds (Reels hold 3 min, "
                                                                    "but completion falls after about 90 s)")
    ap.add_argument("--force", action="store_true", help="replace an existing reels/shots.json")
    a = ap.parse_args()

    import reel as R
    import story

    d = Path(a.story).resolve()
    if (d / "reels" / "shots.json").exists() and not a.force:
        print(f"{d / 'reels' / 'shots.json'} exists; edit it, or pass --force to start over", file=sys.stderr)
        return 1
    mg = R.mg
    mg.set_work(d / "comic")
    b, ch = mg.load_board(), mg.load_choices()
    reveal_page, after = mg.reveal_point(b)
    if reveal_page is None:
        print("board.json marks no reveal panel (\"reveal\": true): mark it first, the draft is built around it",
              file=sys.stderr)
        return 1
    panels = [(pi, c, box) for pi, c, box in mg.all_panels(b)]
    order = [c["id"] for _, c, _ in panels]
    reveal = next(c["id"] for _, c, _ in panels if c.get("reveal"))
    before = order[order.index(reveal) - 1]
    last = order[-1]
    hook = mg.threads_panel(b, ch, None) or order[0]
    clips = {}
    for f in sorted((d / "reels" / "clips").glob("*_p*.mp4")) if (d / "reels" / "clips").exists() else []:
        clips[f.stem.rsplit("_", 1)[1]] = f.relative_to(d).as_posix()
    prompts = " ".join(c.get("prompt", "") for _, c, _ in panels)
    outdoor = bool(OUTDOOR.search(prompts))

    def options(cell, box, sub_kind):
        pid = cell["id"]
        aspect = (box[2] - box[0]) / max(1, box[3] - box[1])
        o = {}
        if pid in clips:
            o["clip"] = clips[pid]
        else:
            o["motion"] = "pan_rtl" if aspect >= 1.8 else "pan_down" if aspect < 0.75 else "push"
        fx = []
        if NIGHT.search(cell.get("prompt", "")) or cell.get("fill"):
            fx.append("night")
        sfx = []
        kinds = {e["kind"] for e in cell.get("text", [])}
        if "voice" in kinds:
            sfx.append(["whisper", 0.2, 1.0])
        if kinds & {"phone", "screen"}:
            sfx.append(["ping", 0.1, 0.6])
        if pid == before:
            fx.append("pulse")
            sfx.append(["riser", 1.2, 0.5])
        if fx:
            o["fx"] = fx
        if sfx:
            o["sfx"] = sfx
        return o

    # ------------------------------------------------------------------ V3
    shots = []
    pick = {c["id"]: (pi, c, box) for pi, c, box in panels}
    pi, c, box = pick[hook]
    line, kind = short_line(c, 14)
    o = options(c, box, kind)
    o.setdefault("sfx", []).append(["heartbeat", 0.0, 0.4])
    if kind == "voice":
        o["voice"] = True
    shots.append({"panel": hook, "sec": 3.0, "sub": line, **o})
    shots.append({"panel": "TITLE", "sec": 2.2, "sub": None, **({"clip": clips[order[0]]} if order[0] in clips else {})})
    body = []
    for pi, c, box in panels:
        pid = c["id"]
        if c.get("fill") and pid not in (reveal, last):
            continue
        has_text = bool(lettering(c))
        if not has_text and pid not in (reveal, last, before):
            continue
        line, kind = short_line(c)
        o = options(c, box, kind)
        sec = round(min(4.6, max(2.6, 1.6 + len(line or "") / 7)), 1)
        if kind == "voice":
            o["voice"] = True
        if pid == reveal:
            line, sec = None, 5.0
            o.update(black=1.0, duck=True)
            o["fx"] = [x for x in o.get("fx", []) if x != "pulse"] + ["shake"]
            o["sfx"] = [["stinger", 0.0, 1.0]]
        elif pid == last:
            sec = 5.6
            o.update(black=0.6, duck=True)
            o["fx"] = o.get("fx", []) + ["darken"]
            o["sfx"] = o.get("sfx", []) + [["riser", 1.2, 0.4], ["stinger", 3.0, 0.8]]
        score = (3 if pid in (reveal, last, before) else 0) + (1 if kind in ("speech", "voice") else 0) \
            + (1 if pid in clips else 0) + (0.5 if order.index(pid) < order.index(reveal) else 0)
        body.append((score, {"panel": pid, "sec": sec, "sub": line, **o}))
    total = sum(s["sec"] for s in shots) + sum(x[1]["sec"] for x in body) + 3.6
    while total > a.target:
        cand = [x for x in body if x[1]["panel"] not in (reveal, last, before, hook)]
        if not cand:
            break
        drop = min(cand, key=lambda x: (x[0], -order.index(x[1]["panel"])))
        body.remove(drop)
        total -= drop[1]["sec"]
    shots += [x[1] for x in body]

    # ------------------------------------------------------------------ V1
    v1_panels = {}
    for pi, c, box in panels:
        o = options(c, box, None)
        o.pop("clip", None)
        if c["id"] == reveal:
            o = {"motion": "snap", "fx": ["shake"] + (["night"] if "night" in o.get("fx", []) else []),
                 "sfx": [["stinger", 0.0, 1.0]], "black": 1.0, "hold": 2.6, "duck": True}
        elif c["id"] == last:
            o.update(motion="push", hold=2.0, black=0.6, duck=True)
            o["fx"] = o.get("fx", []) + ["darken"]
            o["sfx"] = o.get("sfx", []) + [["riser", 1.4, 0.5], ["stinger", 3.2, 0.8]]
        if o:
            v1_panels[c["id"]] = o
    beds = [{"from": order[0], "to": before, "bed": "drone", "gain": 0.3},
            {"from": order[order.index(reveal) + 1] if reveal != last else last, "to": last, "bed": "drone",
             "gain": 0.35}]
    v3_beds = [{"bed": "drone", "gain": 0.35}]
    if outdoor:
        beds.insert(0, {"from": order[0], "to": before, "bed": "wind", "gain": 0.5})
        v3_beds.insert(0, {"bed": "wind", "gain": 0.3})
    doc = {
        "_doc": "ghost-reel 分鏡初稿（draft.py 從 board.json 產生）。照 ghost-reel 的 SKILL.md 逐格看過、改字幕和節奏再渲染。"
                "sfx 是 [音效名, 第幾秒, 音量]；clip 路徑相對於故事資料夾。",
        "title": mg.board_title(b).replace("\n", ""),
        "comic": "comic",
        "music": {"v1": "m1_dark_ambient.flac", "v3": "m2_folk_horror.flac"},
        "beds": beds,
        "v3_beds": v3_beds,
        "v1": {"hook": [{"panel": hook, "sec": 2.6, "sfx": [["heartbeat", 0.3, 0.5]]}], "panels": v1_panels,
               "say": {}, "skip": []},
        "v3": shots,
    }
    p = story.save(d, doc)
    v3_len = sum(s["sec"] + s.get("black", 0) for s in shots) + 3.6
    print(f"{p}: V3 {len(shots)} shots, about {v3_len:.0f} s (cold open {hook}, reveal {reveal} on page "
          f"{reveal_page}, {len(clips)} H3 clips used); V1 {len(order)} panels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
