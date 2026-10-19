"""Manga pages from a story board, on the local ComfyUI (Qwen Image 2.1). Run from the work folder.

    py -X utf8 manga.py check                         # ComfyUI up and the three model files present
    py -X utf8 manga.py styles --panel p2             # gate 1: the same panel in every style option
    py -X utf8 manga.py choose style=A
    py -X utf8 manga.py sheets                        # gate 2: 3 versions of every character and scene
    py -X utf8 manga.py choose me=1 fang=3 room=2 hall=3
    py -X utf8 manga.py refs                          # single-view, grayscale references (plus :head and :bust crops)
    py -X utf8 manga.py plan                          # gate 3: every page as a wireframe with the real lettering
    py -X utf8 manga.py lint                          # the pitfall table as checks; `panels` runs it and stops on errors
    py -X utf8 manga.py panels                        # pass 1 (2 candidates each, "n" overrides)
    py -X utf8 manga.py review --page 3               # brief for an independent checker (references/qa_checklist.md)
    py -X utf8 manga.py review p5 p10 --new           # only candidates no earlier brief listed (redraws)
    py -X utf8 manga.py contact p5 p10                # candidates side by side, for picking
    py -X utf8 manga.py choose p5=2 p10=1 ...
    py -X utf8 manga.py repaint p34_1 --box 220,70,500,330 --prompt "his hair is white"   # redraw one small area
    py -X utf8 manga.py fill p11_2 --box 590,0,768,200   # solid black in the box turns white (a daytime window)
    py -X utf8 manga.py tone p16_5 --poly "48,345 140,276 215,292 92,365" --mode dots   # screentone on white paper
    py -X utf8 manga.py crop p28_10 --box 150,150,610,950   # a region enlarged to the panel: a close-up
    py -X utf8 manga.py panels --pass 2               # panels that use other panels as references
    py -X utf8 manga.py review --cast all             # each character across every picked panel, beside the sheet
    py -X utf8 manga.py pages                         # lettering, layout, PDF, overview
    py -X utf8 manga.py review --read                 # brief for a first-time reader of the pages (references/reader_check.md)
    py -X utf8 manga.py status                        # picked per page, what is missing, GPU minutes so far
    py -X utf8 manga.py export --cover p27            # Instagram carousel: cover, every page on 3:4, end card, caption
    py -X utf8 manga.py reel teaser p8 p9 p10 --handle @gui.chang.shi      # 9:16 Reel: three panels, captions, end card
    py -X utf8 manga.py reel line --text "我回頭，床上那個人還在{睡}。"     # 9:16 Reel: a one-line story typed out on black

Files in the work folder: board.json (the storyboard, see references/board_format.md), choices.json
(written by `choose`), out/ (everything generated). Lettering is drawn here, vertical, never by the model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy  # noqa: E402

WORK = Path.cwd()
OUT = WORK / "out"
BOARD = "board.json"

# ---------------------------------------------------------------------------
# fonts (Traditional Chinese with vertical punctuation forms)
# ---------------------------------------------------------------------------

_FONT_DIRS = ["C:/Windows/Fonts", "/usr/share/fonts/opentype/noto", "/usr/share/fonts/noto-cjk", "/System/Library/Fonts", "/Library/Fonts"]
_FONT_NAMES = {
    "bold": ["msjhbd.ttc", "NotoSansCJK-Bold.ttc", "NotoSansTC-VF.ttf", "PingFang.ttc"],
    "serif": ["NotoSerifTC-VF.ttf", "NotoSerifCJK-Regular.ttc", "mingliu.ttc", "Songti.ttc"],
    "plain": ["msjh.ttc", "NotoSansCJK-Regular.ttc", "NotoSansTC-VF.ttf", "PingFang.ttc"],
}


def font_path(kind: str) -> str:
    for d in _FONT_DIRS:
        for n in _FONT_NAMES[kind]:
            p = Path(d) / n
            if p.exists():
                return str(p)
    raise SystemExit(f"no CJK font found for {kind}; install Noto Sans/Serif TC")


VERT = {"，": "︐", "、": "︑", "。": "︒", "：": "︓", "；": "︔", "！": "︕", "？": "︖", "…": "︙",
        "—": "︱", "「": "﹁", "」": "﹂", "『": "﹃", "』": "﹄", "（": "︵", "）": "︶"}
NO_START = set("︐︑︒︓︔︕︖﹂﹄︶")
NO_END = set("﹁﹃︵")
BREAK_AFTER = set("︐︑︒︓︔︕︖")
PER_COL = {"speech": 8, "voice": 8, "screen": 8, "phone": 8, "narration": 11, "title": 12, "tag": 8}

# ---------------------------------------------------------------------------
# board and choices
# ---------------------------------------------------------------------------


def set_work(path: Path) -> None:
    global WORK, OUT
    WORK = path.resolve()
    OUT = WORK / "out"


def load_board() -> dict:
    return json.loads((WORK / BOARD).read_text(encoding="utf-8"))


def load_choices() -> dict:
    p = WORK / "choices.json"
    ch = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    for k in ("sheets", "refs", "panels"):
        ch.setdefault(k, {})
    return ch


def save_choices(ch: dict) -> None:
    (WORK / "choices.json").write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")


def style_text(board: dict, ch: dict, kind: str = "panel") -> str:
    """The chosen style's prompt prefix ("panel" or "sheet"); a board without options uses its own style fields."""
    opts = board.get("style_options")
    if opts and ch.get("style") in opts:
        return opts[ch["style"]][kind]
    return board["style"] if kind == "panel" else board["sheet_style"]


def log(rec: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------


def page_cells(board: dict, page: dict) -> list[tuple[dict, tuple[int, int, int, int]]]:
    """[(cell, box)] in page pixels and reading order. rtl puts a row's first cell on the right; a cell with
    "stack" is a column of panels read top to bottom before the next cell; insets come last."""
    W, H = board["page"]
    m = board["margin"]
    gx, gy = board["gutter"]
    rows = page["rows"]
    usable_h = H - 2 * m - gy * (len(rows) - 1)
    out = []
    y = m
    for r in rows:
        rh = round(usable_h * r["h"])
        cells = r["cells"]
        usable_w = W - 2 * m - gx * (len(cells) - 1)
        x = W - m if board.get("direction", "rtl") == "rtl" else m
        for c in cells:
            cw = round(usable_w * c["w"])
            if board.get("direction", "rtl") == "rtl":
                box = (x - cw, y, x, y + rh)
                x -= cw + gx
            else:
                box = (x, y, x + cw, y + rh)
                x += cw + gx
            if "stack" in c:
                subs = c["stack"]
                sh_total = rh - gy * (len(subs) - 1)
                sy = box[1]
                for i, s in enumerate(subs):
                    sh = round(sh_total * s["h"]) if i < len(subs) - 1 else box[3] - sy
                    out.append((s, (box[0], sy, box[2], sy + sh)))
                    sy += sh + gy
            else:
                out.append((c, box))
        y += rh + gy
    for ins in page.get("insets", []):
        bx = ins["box"]
        uw, uh = W - 2 * m, H - 2 * m
        out.append((ins, (round(m + bx[0] * uw), round(m + bx[1] * uh), round(m + bx[2] * uw), round(m + bx[3] * uh))))
    return out


def all_panels(board: dict):
    for pi, page in enumerate(board["pages"], 1):
        for cell, box in page_cells(board, page):
            yield pi, cell, box


def find_panel(board: dict, pid: str) -> dict:
    for _, c, _ in all_panels(board):
        if c["id"] == pid:
            return c
    raise SystemExit(f"no panel {pid} on the board")


def gen_size(box) -> tuple[int, int]:
    """Generation size for a cell: same aspect (clamped to 0.45..2.4), long side 768..1280, multiples of 32."""
    w, h = box[2] - box[0], box[3] - box[1]
    a = max(0.45, min(2.4, w / h))
    long = max(768, min(1280, round(1.25 * max(w, h))))
    gw, gh = (long, long / a) if a >= 1 else (long * a, long)
    r32 = lambda v: max(512, int(round(v / 32)) * 32)  # noqa: E731
    return r32(gw), r32(gh)


# ---------------------------------------------------------------------------
# generation
# ---------------------------------------------------------------------------


def candidates(folder: Path, jid: str) -> list[Path]:
    """Every candidate file of one panel or sheet (jid_1.png, jid_2.png, … jid_12.png), in number order."""
    rx = re.compile(re.escape(jid) + r"_(\d+)\.png$")
    found = [(int(m.group(1)), f) for f in folder.glob(f"{jid}_*.png") if (m := rx.match(f.name))]
    return [f for _, f in sorted(found)]


def next_number(folder: Path, jid: str) -> int:
    """The highest candidate number so far: a redraw must never overwrite the image already picked for the page."""
    found = candidates(folder, jid)
    return max(int(f.stem.rsplit("_", 1)[1]) for f in found) if found else 0


def prompt_key(prompt: str, ref_names: list[str]) -> str:
    """A short fingerprint of what a candidate was drawn from, so a brief can tell redraws of a rewritten prompt apart."""
    return hashlib.sha1("\n".join([prompt] + ref_names).encode("utf-8")).hexdigest()[:10]


def job(kind: str, jid: str, prompt: str, refs: list[Path], w: int, h: int, n: int, seed: int, dest_dir: Path) -> list[str]:
    names = [comfy.upload(p) for p in refs]
    graph = comfy.build_graph(prompt, names, w, h, seed, n, f"ghost_comic/{kind}/{jid}")
    pid, images, wall, exec_s = comfy.run(graph)
    start = next_number(dest_dir, jid)
    files = []
    for k, img in enumerate(images, start + 1):
        dest = dest_dir / f"{jid}_{k}.png"
        comfy.fetch(img, dest)
        files.append(dest.name)
    rec = {"kind": kind, "id": jid, "prompt_id": pid, "w": w, "h": h, "n": n, "seed": seed,
           "refs": [p.name for p in refs], "prompt_key": prompt_key(prompt, [p.name for p in refs]),
           "wall_s": wall, "exec_s": exec_s, "files": files}
    log(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return files


CROPS = ("full", "bust", "head")


def char_ref(board: dict, ref: str) -> tuple[str, str] | None:
    """(character id, crop) for a character reference such as "me", "me:head", "me:bust"; None for anything else."""
    cid, _, crop = ref.partition(":")
    if cid in board.get("characters", {}):
        crop = crop or "full"
        if crop not in CROPS:
            raise SystemExit(f"unknown crop {ref!r}; use one of {', '.join(CROPS)}")
        return cid, crop
    return None


def cast(board: dict, cell: dict) -> list[str]:
    """Characters drawn in a panel. An explicit `cast` list wins (a character described in words only, or a sheet
    used just for a pattern); otherwise the characters passed as references."""
    if "cast" in cell:
        return list(cell["cast"])
    return list(dict.fromkeys(cr[0] for r in cell.get("refs", []) if (cr := char_ref(board, r))))


def people(board: dict, cell: dict) -> list[str]:
    """The cast without animals (`"animal": true`), for head counts."""
    return [c for c in cast(board, cell) if not board["characters"].get(c, {}).get("animal")]


def _explicit_scenes(board: dict) -> bool:
    return any("scene" in c for _, c, _ in all_panels(board))


def panel_scenes(board: dict, cell: dict) -> list[str]:
    """Scene ids whose fixed layout applies to this panel. Explicit: the panel's `scene` field. A board that never
    sets `scene` falls back to the old inference from references (consistency.scene_refs), which `lint` warns about:
    a reference panel shot from a different viewpoint pulled in a layout it cannot show (tents seen from inside one)."""
    if _explicit_scenes(board):
        s = cell.get("scene")
        return [] if not s else ([s] if isinstance(s, str) else list(s))
    c = board.get("consistency", {})
    refs = cell.get("refs", [])
    return [sid for sid in c.get("scene", {}) if any(r in refs for r in c.get("scene_refs", {}).get(sid, [f"scene:{sid}"]))]


def light_text(board: dict, cell: dict) -> str:
    key = cell.get("light")
    if not key:
        return ""
    v = board.get("lights", {}).get(key)
    if v is None:
        raise SystemExit(f"{cell['id']}: no light state {key!r} in board['lights']")
    return v["text"] if isinstance(v, dict) else v


def consistency(board: dict, cell: dict) -> str:
    """Fixed scene-layout and character-scale sentences for what this panel shows (board["consistency"])."""
    c = board.get("consistency")
    if not c:
        return ""
    out = [c.get("scene", {})[sid] for sid in panel_scenes(board, cell) if sid in c.get("scene", {})]
    out += [text for cid, text in c.get("scale", {}).items() if cid in cast(board, cell)]
    return " ".join(out)


def compose_prompt(board: dict, ch: dict, cell: dict) -> str:
    """Style prefix, the panel's own prompt, its lighting state, then scene layout and character scale."""
    parts = [style_text(board, ch, "panel"), cell["prompt"], light_text(board, cell), consistency(board, cell)]
    return " ".join(p.strip() for p in parts if p and p.strip())


# ---------------------------------------------------------------------------
# lint: the pitfall table in references/prompting.md, as checks that run before any GPU time is spent
# ---------------------------------------------------------------------------

_NEG = re.compile(r"\b(no|not|without|never|nothing|nobody)\b[^.;:]*$", re.I)
_RISKY = [
    ("warn", re.compile(r"\bwall of\b", re.I), "「wall of …」 gets drawn as a real wall; describe the things themselves (thin bamboo stalks) and add 'no walls'"),
    ("warn", re.compile(r"\b(signs?|signboards?|posters?|banners?|labels?|menus?|captions?|placards?)\b", re.I), "anything that carries writing comes out as garbled text; leave it out or say 'no writing anywhere'"),
    ("warn", re.compile(r"\b(dim|dimly|lit by|glowing|soft light|cinematic|realistic lighting)\b", re.I), "light words pull a line-art style toward grey photographic shading; say 'solid flat black' and 'clean white line art' instead"),
    ("warn", re.compile(r"\b(red|pink|brown|blue|green|yellow|purple|orange|bluish|golden|beige)\b", re.I), "colour words leak into the black-and-white pages; describe tone or pattern instead"),
    ("warn", re.compile(r"\b(halfway|about to)\b", re.I), "abstract actions get misdrawn (a hero on the coffee table); write positions: standing between X and Y, knees bent"),
    ("warn", re.compile(r"\breflect(ion|ions|ed|s)?\b", re.I), "the model draws the person instead of a reflection; make the screen fill the frame and say 'nobody outside the screen'"),
]
_CROSSED = re.compile(r"\b(arms? crossed|crossed arms|folds? (his|her) arms|arms? folded|folded across)\b", re.I)
_CLOSE = re.compile(r"\b(waist-up|bust shot|close-up|head-and-shoulders|head and shoulders)\b", re.I)
_SEATED_OR_CLOSE = re.compile(r"\b(close-up|bust shot|head-and-shoulders|head and shoulders|waist-up|seated|sits|sitting|sit)\b", re.I)
_FLAT = re.compile(r"\b(solid flat black|flat black|clean (white )?line art)\b", re.I)
_HEADSHOT = re.compile(r"(close-up|head-and-shoulders|head and shoulders|bust shot)", re.I)
_ONE = re.compile(r"\b(only one person|the only person|exactly one person|nobody else)\b", re.I)
_TWO = re.compile(r"\bexactly two people\b", re.I)
_NOT_SMILING = re.compile(r"\b(scared|frightened|afraid|terrified|fear|cry|cries|crying|tears|sobbing|unsmiling|no smiles?|"
                          r"nobody smiles|frown|frowns|frowning|grim|pale|tight-lipped|lips pressed|mouth tight|mouth pulled down)\b", re.I)
_SITS_ON = re.compile(r"\b(sits?|sitting|seated)\b[^.]{0,60}?\b(sofa|couch|armchair|chair|bench|stool|bed)\b", re.I)
_WIDE = re.compile(r"\b(wide shot|establishing shot|long shot)\b", re.I)
_GAZE = re.compile(r"\b(viewer|in profile|three-quarter|head turned|turned toward|looks? (at|down|up|toward)|"
                   r"looking (at|down|up|toward)|eyes (on|fixed|lowered)|faces? turned)\b", re.I)
_SEEN_BY = re.compile(r"\b(as seen by|seen by someone|from the point of view of|through the eyes of)\b", re.I)
_PART_SHOT = re.compile(r"\b(close-up|close shot|extreme close-up|through a gap|head-and-shoulders|head and shoulders)\b", re.I)


def character_names(board: dict, cid: str) -> list[str]:
    """What the lettering may call a character: the parts of its `name` (「我（舅舅）」 is 我 and 舅舅) and its `aliases`."""
    ci = board["characters"][cid]
    parts = re.split(r"[（）()、/／\s]+", ci.get("name", ""))
    return [n for n in dict.fromkeys(parts + list(ci.get("aliases", []))) if n]


def _risky_hits(rx: re.Pattern, text: str) -> list[str]:
    hits = []
    for m in rx.finditer(text):
        before = text[max(0, m.start() - 60):m.start()]
        if not _NEG.search(before):
            hits.append(m.group(0))
    return hits


def lint(board: dict, only: list[str] | None = None) -> list[tuple[str, str, str]]:
    """[(panel id, 'error'|'warn', message)]. Errors stop `panels`; warnings are printed."""
    out: list[tuple[str, str, str]] = []
    passes = {c["id"]: c.get("pass", 1) for _, c, _ in all_panels(board)}
    lights = board.get("lights", {})
    scene_ids = set(board.get("consistency", {}).get("scene", {})) | set(board.get("scenes", {}))
    if not _explicit_scenes(board) and board.get("consistency", {}).get("scene_refs"):
        out.append(("board", "warn", "scene layouts are inferred from references (consistency.scene_refs); set `scene` on each panel instead"))
    for _, cell, box in all_panels(board):
        pid = cell["id"]
        if cell.get("fill") or (only and pid not in only):
            continue
        prompt, refs = cell.get("prompt", ""), cell.get("refs", [])
        say = lambda lvl, msg: out.append((pid, lvl, msg))  # noqa: E731
        mentioned = {int(n) for n in re.findall(r"<image(\d+)>", prompt)}
        if mentioned and max(mentioned) > len(refs):
            say("error", f"prompt mentions <image{max(mentioned)}> but the panel has {len(refs)} reference(s)")
        for i in range(1, len(refs) + 1):
            if i not in mentioned:
                say("warn", f"reference {refs[i - 1]!r} (<image{i}>) is never mentioned; an unmentioned reference still drags its composition in")
        for r in refs:
            if r.startswith("panel:"):
                src = r.split(":", 1)[1]
                if src not in passes:
                    say("error", f"{r}: no such panel")
                elif passes[src] >= cell.get("pass", 1):
                    say("error", f"{r} is drawn in pass {passes[src]}, so this panel must be in a later pass (now {cell.get('pass', 1)})")
            elif r.startswith("scene:") and r.split(":", 1)[1] not in board.get("scenes", {}):
                say("error", f"{r}: no such scene")
            elif not r.startswith(("panel:", "scene:", "file:")) and char_ref(board, r) is None:
                say("error", f"{r}: not a character, scene, panel or file reference")
        for s in ([cell["scene"]] if isinstance(cell.get("scene"), str) else cell.get("scene", []) or []):
            if s not in scene_ids:
                say("error", f"scene {s!r} is not defined")
        if cell.get("light") and cell["light"] not in lights:
            say("error", f"light state {cell['light']!r} is not in board['lights']")
        for lvl, rx, msg in _RISKY:
            if rx is _RISKY[2][1] and _FLAT.search(prompt):
                continue  # light words are fine once the flat-black wording that fixes them is there
            hits = _risky_hits(rx, prompt)
            if hits:
                say(lvl, f"{', '.join(dict.fromkeys(h.lower() for h in hits))}: {msg}")
        if _CROSSED.search(prompt) and not _CLOSE.search(prompt):
            say("error", "crossed arms in a full-body shot grew two extra hands; make it waist-up and say 'exactly two arms and two hands'")
        heads = people(board, cell)
        count = cell.get("heads", len(heads))  # `heads` counts unnamed people too (patients in a corridor)
        if isinstance(count, int) and count < len(heads):
            say("error", f"heads {count} is fewer than the {len(heads)} characters drawn in it")
        if count == 1 and not _ONE.search(prompt):
            say("warn", "one character: add 'Only one person in the frame' (character sheets carry two figures)")
        if count == 2 and not _TWO.search(prompt):
            say("warn", "two characters: add 'Exactly two people in the frame'")
        for r in refs:
            cr = char_ref(board, r)
            if cr and cr[1] == "full" and cr[0] in heads and _SEATED_OR_CLOSE.search(prompt):
                say("warn", f"{r}: a full-body standing sheet keeps the pose standing in seated and close-up panels; use {cr[0]}:head or {cr[0]}:bust")
        scene_ref = any(r.startswith("scene:") for r in refs)
        if _HEADSHOT.search(prompt) and scene_ref:
            say("warn", "a close-up with a scene reference: the sheet's furniture comes in behind the character even when the "
                        "prompt says not to (a second table behind 阿凱, six times); leave the scene out and describe the background")
        elif scene_ref and heads and not _SITS_ON.search(prompt) and not _WIDE.search(prompt):
            say("warn", "a scene sheet in a panel with people: they came out tiny or not at all (〈三個人〉 p2, p7), and the "
                        "sheet's camera came along (eye level where a CCTV view was asked, 〈電梯〉 p12); keep it only for a "
                        "wide shot from the sheet's own viewpoint (say 'wide shot'), otherwise describe the place in words")
        if len(heads) >= 2 and not _GAZE.search(prompt):
            say("warn", "two or more people and nothing says where they look: front-view sheets made everyone stare at the "
                        "reader (〈阿嬤住院〉 p3, p9, p34); write the head direction ('in profile, his head turned toward her') "
                        "and add 'Nobody looks at the viewer.'")
        bw, bh = box[2] - box[0], box[3] - box[1]
        if heads and _HEADSHOT.search(prompt) and bw > 1.7 * bh:
            say("warn", f"a close-up in a wide cell ({bw}x{bh}): the model fills the width with the whole body (p24, and p28 "
                        f"four times); make the cell taller, or draw it wider and `crop` the face out")
        if _SEEN_BY.search(prompt):
            say("warn", "'as seen by someone' draws that someone into the picture (p15, three times); describe the camera "
                        "(low angle, looking up at the window) instead of a viewer")
        layouts = board.get("consistency", {}).get("scene", {})
        if _PART_SHOT.search(prompt) and any(s in layouts for s in ([cell["scene"]] if isinstance(cell.get("scene"), str)
                                                                    else cell.get("scene", []) or [])):
            say("warn", "a close shot with a scene layout: the whole fixed layout goes into the prompt and the model draws "
                        "the whole room (p29, 8 of 8 pulled back from a curtain gap to the room); set \"scene\": [] for a "
                        "shot of one part of the place")
        if _NOT_SMILING.search(prompt):
            for r in refs:
                cr = char_ref(board, r)
                if cr and cr[1] == "head":
                    say("warn", f"{r}: a head crop brings the sheet's face along, smile included (老二 grinned in 4 of 5 "
                                f"scared panels); use {cr[0]}:bust and spell the expression out")
        if _SITS_ON.search(prompt) and any(r.startswith("scene:") for r in refs):
            say("warn", "seated on furniture with a scene reference: the character lands in the middle of the sheet, on the "
                        "coffee table (2 of 3 in 〈跟外甥玩捉迷藏〉, and in the first comic); leave the scene out and describe "
                        "the seat and its backrest")
        if "zoom" in cell and not 0.2 <= cell["zoom"] <= 1:
            say("error", f"zoom {cell['zoom']} is outside 0.2..1 (it shrinks the picture onto its own background colour)")
        for cid in cast(board, cell):
            kws = board["characters"][cid].get("keywords", [])
            if kws and not any(k.lower() in prompt.lower() for k in kws):
                say("warn", f"{cid}: none of its features ({', '.join(kws)}) is repeated in the prompt")
    # name a character where they first appear: 阿嬤 never was, and her bust beside 「那應該是恁細姑」 read as 細姑.
    # `intro` points at another panel on the same page that names them (小寶 is drawn in p2, his tag is in p4)
    where = {c["id"]: (pi, c) for pi, c, _ in all_panels(board)}
    lettering = lambda c: " ".join(e.get("text", "") for e in c.get("text", []))  # noqa: E731
    seen: set[str] = set()
    for pi, cell, _ in all_panels(board):
        if cell.get("fill"):
            continue
        new = [c for c in cast(board, cell) if c not in seen]
        seen.update(new)
        if only and cell["id"] not in only:
            continue
        for cid in new:
            if board["characters"][cid].get("ghost"):  # nobody is supposed to know who the ghost is yet
                continue
            names = character_names(board, cid)
            intro = board["characters"][cid].get("intro")
            at = where.get(intro, (None, None)) if intro else (pi, cell)
            if intro and at[0] is None:
                out.append((cell["id"], "error", f"{cid}: intro panel {intro!r} is not on the board"))
            elif names and (at[0] != pi or not any(n in lettering(at[1]) for n in names)):
                out.append((cell["id"], "warn", f"{cid}: first drawn here, but nothing on this page names them "
                                                f"({' / '.join(names)}); add a caption or tag here, or set `intro` to the "
                                                f"panel on this page that does (an unnamed 阿嬤 was read as 細姑)"))
    return out


def print_lint(issues: list[tuple[str, str, str]]) -> int:
    for pid, lvl, msg in issues:
        print(f"{pid:<6} {lvl.upper():<5} {msg}")
    errors = sum(1 for _, lvl, _ in issues if lvl == "error")
    print(f"{errors} error(s), {len(issues) - errors} warning(s)")
    return errors


def text_only(board: dict, cell: dict) -> str:
    """A panel prompt without reference images: '<imageN>' mentions dropped, the descriptions appended."""
    p = re.sub(r"\s*(?:from|as in|of|in) <image\d+>", "", cell["prompt"])
    p = re.sub(r"<image\d+>", "the reference", p)
    descs = []
    for r in cell.get("refs", []):
        if r.startswith("scene:"):
            descs.append(board["scenes"][r.split(":", 1)[1]])
        elif cr := char_ref(board, r):
            descs.append(board["characters"][cr[0]]["desc"])
    return p + (" " + " ".join(descs) if descs else "")


def cmd_check(a) -> None:
    if not comfy.alive():
        raise SystemExit(f"ComfyUI is not answering at {comfy.SERVER}; start it first")
    miss = comfy.missing_models()
    print("ComfyUI ok at", comfy.SERVER, "| missing models:", miss or "none")
    if miss:
        raise SystemExit(1)


def cmd_styles(a) -> None:
    """Gate 1: one panel (and the first scene) in every style option, text only, same seed."""
    b = load_board()
    cell = find_panel(b, a.panel)
    box = next(bx for _, c, bx in all_panels(b) if c["id"] == a.panel)
    w, h = gen_size(box)
    scene_id = next(iter(b.get("scenes", {})), None)
    out = OUT / "styles"
    for key, opt in b["style_options"].items():
        job("styles", f"{a.panel}_{key}", f"{opt['panel']} {text_only(b, cell)} Not realistic.", [], w, h, 1, a.seed, out)
        if scene_id:
            job("styles", f"scene_{key}", f"{opt['panel']} {b['scenes'][scene_id]}", [], 1536, 1024, 1, a.seed, out)
    font = ImageFont.truetype(font_path("bold"), 30)
    rows = []
    for key, opt in b["style_options"].items():
        pan = Image.open(out / f"{a.panel}_{key}_1.png").convert("RGB")
        pan = pan.resize((round(pan.width * 400 / pan.height), 400))
        parts = [pan]
        if scene_id:
            parts.append(Image.open(out / f"scene_{key}_1.png").convert("RGB").resize((600, 400)))
        row = Image.new("RGB", (sum(p.width for p in parts) + 30 * (len(parts) - 1), 450), "white")
        x = 0
        for p in parts:
            row.paste(p, (x, 50))
            x += p.width + 30
        ImageDraw.Draw(row).text((10, 8), f"{key}  {opt.get('name', '')}", fill="black", font=font)
        rows.append(row)
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 20 for r in rows)), "#bbb")
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 20
    sheet.save(OUT / "pick_style.png")
    print(OUT / "pick_style.png")


def cmd_sheets(a) -> None:
    """Gate 2: n versions of every character and scene in the chosen style, then numbered pick sheets."""
    b = load_board()
    ch = load_choices()
    sheet_style, panel_style = style_text(b, ch, "sheet"), style_text(b, ch, "panel")
    jobs = [(cid, f"{sheet_style} {c['views']} {c['desc']}") for cid, c in b["characters"].items()]
    jobs += [(f"scene_{sid}", f"{panel_style} Background art in this style, nobody in it. {p}") for sid, p in b["scenes"].items()]
    for jid, prompt in jobs:
        if a.only and jid not in a.only and jid.removeprefix("scene_") not in a.only:
            continue
        job("sheets", jid, prompt, [], 1536, 1024, a.n, a.seed or random.randrange(2**31), OUT / "sheets")
    pick_sheet(b, [c for c in b["characters"]], "pick_characters.png", {c: f"{v.get('name', c)}：{v.get('features', '')}" for c, v in b["characters"].items()})
    pick_sheet(b, [f"scene_{s}" for s in b["scenes"]], "pick_scenes.png", {f"scene_{s}": s for s in b["scenes"]})


def pick_sheet(b: dict, ids: list[str], name: str, titles: dict) -> None:
    font = ImageFont.truetype(font_path("bold"), 34)
    big = ImageFont.truetype(font_path("bold"), 40)
    cw = 600
    rows = []
    for sid in ids:
        files = candidates(OUT / "sheets", sid)
        if not files:
            continue
        rh = round(cw * 1024 / 1536)
        row = Image.new("RGB", (len(files) * (cw + 10), 60 + rh), "white")
        d = ImageDraw.Draw(row)
        d.text((10, 10), titles.get(sid, sid), fill="black", font=font)
        for k, f in enumerate(files):
            im = Image.open(f).convert("RGB").resize((cw, rh))
            x = (len(files) - 1 - k) * (cw + 10)  # version 1 on the right: reads like the pages
            row.paste(im, (x, 60))
            d.rectangle([x, 60, x + 56, 112], fill="black")
            d.text((x + 14, 62), f.stem.rsplit("_", 1)[1], fill="white", font=big)
        rows.append(row)
    if not rows:
        return
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 16 for r in rows)), "#999")
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 16
    sheet.save(OUT / name)
    print(OUT / name)


def cmd_choose(a) -> None:
    """key=value picks. style=A; a character or scene id = version number or a path under out/; a panel id = number or file."""
    b = load_board()
    ch = load_choices()
    for kv in a.picks:
        k, v = kv.split("=", 1)
        if k == "style":
            if v not in b.get("style_options", {}):
                raise SystemExit(f"no style option {v}")
            ch["style"] = v
        elif k in b.get("characters", {}) or k in b.get("scenes", {}) or k.startswith("scene_"):
            sid = k if k in b.get("characters", {}) else ("scene_" + k.removeprefix("scene_"))
            path = f"sheets/{sid}_{v}.png" if v.isdigit() else v
            if not (OUT / path).exists():
                raise SystemExit(f"{OUT / path} does not exist")
            ch["sheets"][sid] = path
            ch["refs"].pop(sid, None)  # stale until `refs` runs again
        else:
            find_panel(b, k)
            f = f"{k}_{v}.png" if v.isdigit() else v
            if not (OUT / "panels" / f).exists():
                raise SystemExit(f"{OUT / 'panels' / f} does not exist")
            ch["panels"][k] = f
    save_choices(ch)
    print(json.dumps(ch, ensure_ascii=False, indent=1))


def cmd_refs(a) -> None:
    """Reference images from the picked sheets: grayscale, and characters cropped to one view.
    A sheet with two figures side by side makes the model draw two of the same person."""
    b = load_board()
    ch = load_choices()
    dest = OUT / "refs"
    dest.mkdir(parents=True, exist_ok=True)
    for sid, path in ch["sheets"].items():
        im = Image.open(OUT / path).convert("L")
        char = b.get("characters", {}).get(sid)
        crop = char.get("ref_crop", "left") if char else "none"
        if crop == "left":
            im = im.crop((0, 0, im.width // 2, im.height))
        elif crop == "right":
            im = im.crop((im.width // 2, 0, im.width, im.height))
        im.convert("RGB").save(dest / f"{sid}.png")
        ch["refs"][sid] = f"refs/{sid}.png"
        if char:  # head and bust: identity without the sheet's standing pose
            for kind, box in figure_crops(im, char.get("ref_boxes", {})).items():
                im.crop(box).convert("RGB").save(dest / f"{sid}_{kind}.png")
                ch["refs"][f"{sid}:{kind}"] = f"refs/{sid}_{kind}.png"
    save_choices(ch)
    print(json.dumps(ch["refs"], ensure_ascii=False))


def figure_crops(im: Image.Image, override: dict | None = None) -> dict[str, tuple[int, int, int, int]]:
    """Head and bust boxes for the single figure on a light background. The figure's extent comes from the ink;
    the head is centred on the ink of the figure's top rows. `override` takes {"head": [x0, y0, x1, y1]} as fractions."""
    g = im.convert("L")
    w, h = g.size
    out: dict[str, tuple[int, int, int, int]] = {}
    for kind, fr in (override or {}).items():
        out[kind] = (round(fr[0] * w), round(fr[1] * h), round(fr[2] * w), round(fr[3] * h))
    mask = g.point(lambda v: 255 if v < 200 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return out
    x0, y0, x1, y1 = bbox
    fh = y1 - y0
    top = mask.crop((x0, y0, x1, y0 + max(1, round(fh * 0.12))))
    tb = top.getbbox()
    cx = x0 + ((tb[0] + tb[2]) / 2 if tb else (x1 - x0) / 2)

    def box(cy: float, side: float) -> tuple[int, int, int, int]:
        bx0, by0 = max(0, round(cx - side / 2)), max(0, round(cy - side / 2))
        return bx0, by0, min(w, round(bx0 + side)), min(h, round(by0 + side))

    out.setdefault("head", box(y0 + fh * 0.13, fh * 0.30))
    out.setdefault("bust", box(y0 + fh * 0.27, fh * 0.58))
    return out


def ref_path(ref: str, ch: dict, board: dict | None = None) -> Path:
    if ref.startswith("panel:"):
        return OUT / "panels" / ch["panels"][ref.split(":", 1)[1]]
    if ref.startswith("file:"):
        return OUT / ref.split(":", 1)[1]
    if ref.startswith("scene:"):
        sid = "scene_" + ref.split(":", 1)[1]
    else:
        cid, _, crop = ref.partition(":")
        sid = cid if crop in ("", "full") else f"{cid}:{crop}"
        if sid != cid and sid not in ch["refs"]:
            raise SystemExit(f"{ref}: no {crop} crop yet; run `manga.py refs` after picking the sheet")
    if sid in ch["refs"]:
        return OUT / ch["refs"][sid]
    return OUT / ch["sheets"][sid]


def cmd_panels(a) -> None:
    b = load_board()
    ch = load_choices()
    todo = [(cell, box) for _, cell, box in all_panels(b) if not cell.get("fill")
            and (cell["id"] in a.only if a.only else cell.get("pass", 1) == a.pass_)]
    issues = lint(b, [c["id"] for c, _ in todo])
    if issues:
        errors = print_lint(issues)
        if errors and not a.force:
            raise SystemExit("lint errors: fix them, or pass --force to draw anyway")
    for cell, box in todo:
        w, h = gen_size(box)
        refs = [ref_path(r, ch, b) for r in cell["refs"]]
        job("panels", cell["id"], compose_prompt(b, ch, cell), refs, w, h, cell.get("n", a.n),
            a.seed or random.randrange(2**31), OUT / "panels")


def parse_box(text: str, size: tuple[int, int]) -> tuple[int, int, int, int]:
    """'x0,y0,x1,y1' in pixels of the candidate, or as fractions of its size when any value has a decimal point."""
    vals = [v.strip() for v in text.split(",")]
    if len(vals) != 4:
        raise SystemExit(f"--box needs x0,y0,x1,y1, got {text!r}")
    if any("." in v for v in vals):
        box = tuple(round(float(v) * size[k % 2]) for k, v in enumerate(vals))
    else:
        box = tuple(int(v) for v in vals)
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
        raise SystemExit(f"box {box} is not inside the {size[0]}x{size[1]} candidate")
    return box


def feather_mask(size: tuple[int, int]) -> Image.Image:
    """Full strength inside, fading to nothing over the outer tenth of the box, so the patch has no visible seam."""
    pad = max(6, min(size) // 10)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle([pad, pad, size[0] - pad, size[1] - pad], fill=255)
    return mask.filter(ImageFilter.GaussianBlur(pad / 2))


def cmd_repaint(a) -> None:
    """Redraw one small area of a candidate: crop the box, enlarge it so the detail fills the frame, edit only the crop,
    shrink it back and paste it in with a feathered edge. An edit of the whole panel ignores small things (four tries
    could not put a radio on p29's drip stand); at crop size the model draws them (p30's collar, p34's hair, p37's hand).
    The results are new candidates numbered after the existing ones; the base file is never changed."""
    b, ch = load_board(), load_choices()
    base = OUT / "panels" / (a.candidate if a.candidate.endswith(".png") else a.candidate + ".png")
    if not base.exists():
        raise SystemExit(f"{base} does not exist")
    pid = base.stem.rsplit("_", 1)[0]
    find_panel(b, pid)
    src = Image.open(base).convert("RGB")
    box = parse_box(a.box, src.size)
    crop = src.crop(box)
    scale = max(1, min(6, round(1024 / max(crop.size))))
    w, h = (max(512, round(v * scale / 32) * 32) for v in crop.size)
    work = OUT / "repaint"
    work.mkdir(parents=True, exist_ok=True)
    tmp = work / f"{base.stem}_crop.png"
    crop.resize((w, h), Image.LANCZOS).save(tmp)
    text = a.prompt if "<image1>" in a.prompt else f"Keep this picture exactly the same as <image1>. Change only this: {a.prompt}"
    prompt = f"{style_text(b, ch, 'panel')} {text}"
    seed = a.seed or random.randrange(2**31)
    graph = comfy.build_graph(prompt, [comfy.upload(tmp)], w, h, seed, a.n, f"ghost_comic/repaint/{pid}")
    prompt_id, images, wall, exec_s = comfy.run(graph)
    mask = feather_mask(crop.size)
    files = []
    for k, img in enumerate(images, next_number(OUT / "panels", pid) + 1):
        raw = work / f"{pid}_{k}_raw.png"
        comfy.fetch(img, raw)
        out = src.copy()
        out.paste(Image.open(raw).convert("RGB").resize(crop.size, Image.LANCZOS), box[:2], mask)
        out.save(OUT / "panels" / f"{pid}_{k}.png")
        files.append(f"{pid}_{k}.png")
    rec = {"kind": "repaint", "id": pid, "prompt_id": prompt_id, "base": base.name, "box": list(box), "w": w, "h": h,
           "n": a.n, "seed": seed, "prompt": text, "wall_s": wall, "exec_s": exec_s, "files": files}
    log(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------------------
# hand fixes: what repaint cannot do. It keeps a big flat tone as it is: three edits left a daytime window solid black,
# two left a pale buzz cut paler. These change pixels directly and write new candidates, like repaint
# ---------------------------------------------------------------------------


def open_candidate(name: str) -> tuple[Path, str, Image.Image]:
    base = OUT / "panels" / (name if name.endswith(".png") else name + ".png")
    if not base.exists():
        raise SystemExit(f"{base} does not exist")
    return base, base.stem.rsplit("_", 1)[0], Image.open(base).convert("RGB")


def save_fix(kind: str, base: Path, pid: str, out: Image.Image, **extra) -> str:
    dest = f"{pid}_{next_number(OUT / 'panels', pid) + 1}.png"
    out.save(OUT / "panels" / dest)
    log({"kind": kind, "id": pid, "base": base.name, "files": [dest], "wall_s": 0, "exec_s": 0, **extra})
    print(dest)
    return dest


def fill_solid_black(im: Image.Image, box, colour=(255, 255, 255)) -> tuple[Image.Image, int]:
    """Every solid black area inside the box becomes `colour`. Solid means it covers at least 45% of its bounding box and is
    6 px or more across both ways, so outlines of a window frame or a curtain stay."""
    im = im.copy()
    x0, y0, x1, y1 = box
    filled = 0
    for y in range(y0, y1, 4):
        for x in range(x0, x1, 4):
            if sum(im.getpixel((x, y))) >= 90:
                continue
            before = im.copy()
            ImageDraw.floodfill(im, (x, y), colour, thresh=70)
            diff = ImageChops.difference(before, im).convert("L").point(lambda v: 255 if v else 0)
            bb = diff.getbbox()
            w, h = (bb[2] - bb[0], bb[3] - bb[1]) if bb else (0, 0)
            area = sum(1 for v in diff.crop(bb).getdata() if v) if bb else 0
            if not bb or min(w, h) < 6 or area < 0.45 * w * h or area < 60:
                im = before
            else:
                filled += area
    return im, filled


def cmd_fill(a) -> None:
    """Paint the solid black inside a box white: a daytime window the line-art style drew black, a black blob in a corner."""
    base, pid, src = open_candidate(a.candidate)
    box = parse_box(a.box, src.size)
    out, filled = fill_solid_black(src, box)
    if not filled:
        raise SystemExit("nothing solid and black in that box")
    save_fix("fill", base, pid, out, box=list(box), px=filled)


def add_tone(im: Image.Image, poly: list[tuple[int, int]], mode: str, seed: int = 7) -> Image.Image:
    """Screentone dots or short stubble strokes inside a polygon, on white paper only, so lines, glasses and faces stay."""
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    paper = im.convert("L").point(lambda v: 255 if v > 170 else 0)
    tex = Image.new("L", im.size, 255)
    d = ImageDraw.Draw(tex)
    rng = random.Random(seed)
    x0, y0 = min(p[0] for p in poly), min(p[1] for p in poly)
    x1, y1 = max(p[0] for p in poly), max(p[1] for p in poly)
    area = max(1, (x1 - x0) * (y1 - y0))
    if mode == "dots":
        for _ in range(int(area * 0.22)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            d.ellipse([x - 0.9, y - 0.9, x + 0.9, y + 0.9], fill=40)
    else:  # strokes pointing away from a centre below the shape, like short hair growing outward
        cx, cy = (x0 + x1) / 2, y1 + (y1 - y0)
        for _ in range(int(area * 0.05)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            ang = math.atan2(y - cy, x - cx) + rng.uniform(-0.25, 0.25)
            n = rng.uniform(4, 8)
            d.line([(x, y), (x + n * math.cos(ang), y + n * math.sin(ang))], fill=30, width=1)
    out = im.copy()
    out.paste(Image.merge("RGB", [tex] * 3), (0, 0), ImageChops.multiply(mask, paper))
    return out


def cmd_tone(a) -> None:
    """Hand-drawn texture in a polygon: a buzz cut the model left white (it read as a bald head, twice)."""
    base, pid, src = open_candidate(a.candidate)
    poly = [tuple(int(v) for v in p.split(",")) for p in a.poly.split()]
    if len(poly) < 3:
        raise SystemExit("--poly needs at least three points, 'x,y x,y x,y'")
    save_fix("tone", base, pid, add_tone(src, poly, a.mode), poly=[list(p) for p in poly], mode=a.mode)


def cmd_crop(a) -> None:
    """Cut a region out of a candidate and enlarge it to the candidate's size: the close-up the model would not draw. The
    box keeps the candidate's shape (its height follows from the width); the face in p28 came out of a wider draw."""
    base, pid, src = open_candidate(a.candidate)
    x0, y0, x1, _ = parse_box(a.box, src.size)
    h = round((x1 - x0) * src.height / src.width)
    if y0 + h > src.height:
        raise SystemExit(f"the box needs {h} px of height from y={y0}; move it up or make it narrower")
    save_fix("crop", base, pid, src.crop((x0, y0, x1, y0 + h)).resize(src.size, Image.LANCZOS), box=[x0, y0, x1, y0 + h])


def cmd_lint(a) -> None:
    raise SystemExit(1 if print_lint(lint(load_board(), a.only)) else 0)


_BRIEF_PATH = re.compile(r"^\s+- ((?:[A-Za-z]:[\\/]|/).*\.png)\s*$", re.M)  # candidate lines: a bare path


def reviewed_paths(skip: str | None = None) -> set[str]:
    """Every candidate path an earlier brief in out/review listed (the brief named `skip` is about to be rewritten)."""
    seen: set[str] = set()
    for f in (OUT / "review").glob("*.md"):
        if f.stem != skip:
            seen.update(_BRIEF_PATH.findall(f.read_text(encoding="utf-8")))
    return seen


def continuity_panels(b: dict, ch: dict, cell: dict, limit: int = 3) -> list[dict]:
    """Picked panels a candidate must match: its `continuity` list and `panel:` references first, then the nearest
    picked panels of the same scene. p21's wardrobe came out white next to p14's dark one; the checker needs p14 open."""
    order = [c for _, c, _ in all_panels(b) if not c.get("fill")]
    pos = {c["id"]: k for k, c in enumerate(order)}
    want = list(cell.get("continuity", [])) + [r.split(":", 1)[1] for r in cell.get("refs", []) if r.startswith("panel:")]
    mine = set(panel_scenes(b, cell))
    if mine:
        near = sorted((c for c in order if c["id"] != cell["id"] and mine & set(panel_scenes(b, c))),
                      key=lambda c: abs(pos[c["id"]] - pos[cell["id"]]))
        want += [c["id"] for c in near]
    picked = [i for i in dict.fromkeys(want) if i in ch["panels"] and i != cell["id"]]
    return [find_panel(b, i) for i in picked[:limit]]


def logged_keys() -> dict[str, str]:
    """{candidate file: prompt_key} for every panel job in out/log.jsonl that recorded one (repaints keep their base's)."""
    keys: dict[str, str] = {}
    if not (OUT / "log.jsonl").exists():
        return keys
    for line in (OUT / "log.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("kind") == "panels" and r.get("prompt_key"):
            keys.update({f: r["prompt_key"] for f in r.get("files", [])})
        elif r.get("kind") in ("repaint", "fill", "tone", "crop") and r.get("base") in keys:
            keys.update({f: keys[r["base"]] for f in r.get("files", [])})
    return keys


def current_key(b: dict, ch: dict, cell: dict) -> str | None:
    """The prompt_key a candidate drawn now would get; None when a reference is not ready yet."""
    try:
        return prompt_key(compose_prompt(b, ch, cell), [ref_path(r, ch, b).name for r in cell.get("refs", [])])
    except (KeyError, SystemExit):
        return None


def head_line(b: dict, cell: dict) -> str:
    """The brief's head count. `heads` on the panel counts people who are no character (patients, a crowd)."""
    named = people(b, cell)
    names = "、".join(b["characters"][c].get("name", c) for c in named)
    n = cell.get("heads")
    if isinstance(n, str):
        return f"- 人數：{n}" + (f"（有名字的：{names}）" if named else "")
    if n is not None:
        return f"- 人數：剛好 {n} 人" + (f"（其中有名字的：{names}）" if named else "")
    return f"- 人數：剛好 {len(named)} 人" + (f"（{names}）" if named else "，畫面上不該有人")


def cast_brief(b: dict, ch: dict, cids: list[str]) -> None:
    """One character across every picked panel, next to their sheet: face, hair, clothes, what they carry, size.
    The panel checks passed 阿嬤 drawn from words with a face that was not hers, and a boy with black hair on one page
    and white on the next; the owner found both. Only a look at all of a character's panels at once shows that."""
    picked = lambda cid: [(pi, c) for pi, c, _ in all_panels(b)  # noqa: E731
                          if not c.get("fill") and c["id"] in ch["panels"] and cid in cast(b, c)]
    if cids == ["all"]:
        cids = [cid for cid in b["characters"] if len(picked(cid)) >= 2]
    dest = OUT / "review"
    dest.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(font_path("bold"), 26)
    scale = b.get("consistency", {}).get("scale", {})
    for cid in cids:
        if cid not in b["characters"]:
            raise SystemExit(f"no character {cid!r} on the board")
        ci, rows = b["characters"][cid], picked(cid)
        if not rows:
            print(f"{cid}: no picked panel draws them, left out")
            continue
        sheets = [OUT / ch["refs"][k] for k in (cid, f"{cid}:head", f"{cid}:bust") if k in ch["refs"]]
        if not sheets and cid in ch["sheets"]:
            sheets = [OUT / ch["sheets"][cid]]
        L = [f"# 跨格檢查：{ci.get('name', cid)}", "",
             "照 qa_checklist.md 的「跨格檢查」，把這個角色出現的每一格都跟角色卡、也跟彼此比對。每一格都要開原圖看；"
             "總覽圖只用來找哪幾格不一樣。",
             f"要放大、調亮暗部或裁切時可以寫小程式，但程式和輸出只放在 {dest / 'work' / f'cast_{cid}'}，"
             "不要動 out/ 裡其他任何檔案。", "",
             f"- 特徵：{ci.get('features', '')}。{scale.get(cid, '')}"]
        if ci.get("ghost"):
            L.append("- 這是鬼：臉本來就可以在陰影裡，但身形、衣服、比例要每格一樣。")
        L.append("- 角色卡：")
        L += [f"  - 角色卡 {p.name}：{p}" for p in sheets] or ["  - （沒有選定的角色卡）"]
        L.append(f"- 總覽圖：{dest / f'cast_{cid}.png'}")
        L.append("- 每一格（閱讀順序）：")
        for pi, c in rows:  # a mirrored panel puts the bangle on the other wrist on the page; the checker sees the file
            note = "，".join(x for x in (c.get("label", ""), "頁面上左右翻轉（mirror）" if c.get("mirror") else "") if x)
            L.append(f"  - 第 {pi} 頁 {c['id']}（{note}）：{OUT / 'panels' / ch['panels'][c['id']]}")
            L.append(f"    畫面要的是：{c['prompt']}")
        rest = [c["id"] for _, c, _ in all_panels(b) if cid in cast(b, c) and c["id"] not in ch["panels"] and not c.get("fill")]
        if rest:
            L.append(f"- 還沒選定、這次不比：{'、'.join(rest)}")
        L.append("")
        (dest / f"cast_{cid}.md").write_text("\n".join(L), encoding="utf-8")
        th = 300
        tiles = [(p.stem, Image.open(p).convert("RGB")) for p in sheets]
        tiles += [(c["id"], Image.open(OUT / "panels" / ch["panels"][c["id"]]).convert("RGB")) for _, c in rows]
        tiles = [(t, im.resize((max(1, round(im.width * th / im.height)), th))) for t, im in tiles]
        per_row, gap = 5, 10
        lines = [tiles[i:i + per_row] for i in range(0, len(tiles), per_row)]
        sheet = Image.new("RGB", (max(sum(im.width + gap for _, im in r) for r in lines), len(lines) * (th + 40)), "#888")
        d = ImageDraw.Draw(sheet)
        for ri, r in enumerate(lines):
            x = 0
            for t, im in r:
                sheet.paste(im, (x, ri * (th + 40) + 36))
                d.text((x + 4, ri * (th + 40) + 2), t, fill="white", font=font)
                x += im.width + gap
        sheet.save(dest / f"cast_{cid}.png")
        print(dest / f"cast_{cid}.md")


def contact_sheet(tiles: list[tuple[str, Image.Image]], path: Path, th: int = 300, per_row: int = 5) -> None:
    font = ImageFont.truetype(font_path("bold"), 26)
    tiles = [(t, im.resize((max(1, round(im.width * th / im.height)), th))) for t, im in tiles]
    lines = [tiles[i:i + per_row] for i in range(0, len(tiles), per_row)]
    sheet = Image.new("RGB", (max(sum(im.width + 10 for _, im in r) for r in lines), len(lines) * (th + 40)), "#888")
    d = ImageDraw.Draw(sheet)
    for ri, r in enumerate(lines):
        x = 0
        for t, im in r:
            sheet.paste(im, (x, ri * (th + 40) + 36))
            d.text((x + 4, ri * (th + 40) + 2), t, fill="white", font=font)
            x += im.width + 10
    sheet.save(path)


def scene_brief(b: dict, ch: dict, sids: list[str]) -> None:
    """One room across every picked panel set in it, against its fixed layout (consistency.scene): where the window, the
    bed, the door and the furniture are, and which way things face. In the sixth comic the window, the bed and the photo
    frame moved from panel to panel and every panel had passed on its own; the owner saw it on the pages."""
    layouts = b.get("consistency", {}).get("scene", {})
    if sids == ["all"]:
        sids = list(layouts)
    dest = OUT / "review"
    dest.mkdir(parents=True, exist_ok=True)
    for sid in sids:
        if sid not in layouts:
            raise SystemExit(f"no fixed layout for scene {sid!r} in consistency.scene")
        rows = [(pi, c) for pi, c, _ in all_panels(b) if not c.get("fill") and c["id"] in ch["panels"] and sid in panel_scenes(b, c)]
        if not rows:
            print(f"{sid}: no picked panel is set there, left out")
            continue
        L = [f"# 場景跨格檢查：{sid}", "",
             "照 qa_checklist.md 的「場景跨格檢查」，把這個場景的每一格都跟下面的固定格局、也跟彼此比對。每一格都要開原圖看；"
             "總覽圖只用來找哪幾格不一樣。",
             f"要放大或裁切時可以寫小程式，但程式和輸出只放在 {dest / 'work' / f'scene_{sid}'}，不要動 out/ 裡其他任何檔案。", "",
             f"- 固定格局：{layouts[sid]}", f"- 總覽圖：{dest / f'scene_{sid}.png'}", "- 每一格（閱讀順序）："]
        for pi, c in rows:
            note = "，".join(x for x in (c.get("label", ""), "頁面上左右翻轉（mirror）" if c.get("mirror") else "") if x)
            L.append(f"  - 第 {pi} 頁 {c['id']}（{note}）：{OUT / 'panels' / ch['panels'][c['id']]}")
            L.append(f"    畫面要的是：{c['prompt']}")
        L.append("")
        (dest / f"scene_{sid}.md").write_text("\n".join(L), encoding="utf-8")
        contact_sheet([(c["id"], Image.open(OUT / "panels" / ch["panels"][c["id"]]).convert("RGB")) for _, c in rows],
                      dest / f"scene_{sid}.png")
        print(dest / f"scene_{sid}.md")


def read_brief(b: dict) -> None:
    """A brief for a first-time reader (references/reader_check.md): the page images in reading order and nothing else;
    beside it a key for the one who compares: who each character is, where they first appear, every line in order."""
    pages = sorted((OUT / "pages").glob("page_*.png"))
    if not pages:
        raise SystemExit("no pages yet: run `pages` first")
    rtl = b.get("direction", "rtl") == "rtl"
    dest = OUT / "review"
    dest.mkdir(parents=True, exist_ok=True)
    L = ["# 讀者檢查", "", "照 reader_check.md 讀完下面每一頁再回答。只開這些頁面，不要開資料夾裡的其他檔案。", "",
         f"- 閱讀方向：{'格子由右往左、由上往下；直書文字一欄一欄由右往左' if rtl else '格子由左往右、由上往下'}",
         "- 頁面："] + [f"  - {p}" for p in pages]
    (dest / "read.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    K = ["# 讀者檢查的對照表（不要交給讀者）", "", f"- 故事：{b.get('story', '')}", "", "## 角色", ""]
    first: dict[str, tuple[int, str]] = {}
    for pi, cell, _ in all_panels(b):
        for cid in cast(b, cell):
            first.setdefault(cid, (pi, cell["id"]))
    for cid, ci in b.get("characters", {}).items():
        where = f"第 {first[cid][0]} 頁 {first[cid][1]} 第一次出現" if cid in first else "沒畫出來"
        K.append(f"- {ci.get('name', cid)}：{ci.get('features', '')}；{where}")
    K += ["", "## 每個框（閱讀順序）", ""]
    for pi, cell, _ in all_panels(b):
        for e in cell.get("text", []):
            K.append(f"- 第 {pi} 頁 {cell['id']} {e['kind']} {e.get('pos', 'tr')}：「{e['text']}」")
    K += ["", "比對：讀者講的劇情和故事一樣嗎？每個角色都認對了嗎？每句台詞的說話的人都對嗎？結尾的轉折看懂了嗎？", ""]
    (dest / "read_key.md").write_text("\n".join(K), encoding="utf-8")
    print(dest / "read.md")
    print(dest / "read_key.md")


def cmd_review(a) -> None:
    """A brief for an independent checker (references/qa_checklist.md): for each panel, what must be in it and every
    candidate's path. The checker is a fresh subagent: the one who wrote the prompts sees what was meant, not what is there."""
    b = load_board()
    ch = load_choices()
    if getattr(a, "read", False):
        read_brief(b)
        return
    if getattr(a, "scene", None):
        scene_brief(b, ch, a.scene)
        return
    if getattr(a, "cast", None):
        cast_brief(b, ch, a.cast)
        return
    ids = list(a.ids or [])
    if a.page:
        ids += [c["id"] for c, _ in page_cells(b, b["pages"][a.page - 1])]
    if a.unpicked:
        ids += [c["id"] for _, c, _ in all_panels(b) if not c.get("fill") and c["id"] not in ch["panels"]]
    ids = list(dict.fromkeys(i for i in ids if not find_panel(b, i).get("fill")))
    if not ids:
        raise SystemExit("nothing to review")
    name = a.name or (f"page{a.page}" if a.page else ("unpicked" if a.unpicked else "_".join(ids[:4])))
    found = {pid: candidates(OUT / "panels", pid) for pid in ids}
    # candidates drawn from an earlier version of the prompt (or other references) than the board has now
    keys = logged_keys()
    now = {pid: current_key(b, ch, find_panel(b, pid)) for pid in ids}
    stale = {pid: [f for f in fs if now[pid] and keys.get(f.name, now[pid]) != now[pid]] for pid, fs in found.items()}
    if getattr(a, "new", False):  # redraws only: the checker re-judged old, already failed candidates until told not to
        seen = reviewed_paths(skip=name)
        found = {pid: [f for f in fs if str(f) not in seen and f not in stale[pid]] for pid, fs in found.items()}
        for pid in [p for p, fs in found.items() if not fs]:
            print(f"{pid}: no candidates newer than the earlier briefs from the current prompt, left out")
        ids = [p for p in ids if found[p]]
        if not ids:
            raise SystemExit("nothing new to review")
    scale = b.get("consistency", {}).get("scale", {})
    L = [f"# 格子檢查：{', '.join(ids)}", "",
         "照 qa_checklist.md 逐張檢查下面每一張候選圖，每張都要開原圖看，不要看縮圖。",
         f"要放大、調亮暗部或裁切時可以寫小程式，但程式和輸出只放在 {OUT / 'review' / 'work' / name}，"
         "不要動 out/ 裡其他任何檔案。", ""]
    for pid in ids:
        cell = find_panel(b, pid)
        files = found[pid]
        heads, everyone = people(b, cell), cast(b, cell)
        L += [f"## {pid}：{cell.get('label', '')}", ""]
        L.append(head_line(b, cell))
        animals = [c for c in everyone if c not in heads]
        if animals:
            L.append("- 動物：" + "、".join(b['characters'][c].get('name', c) for c in animals) + "，各一隻")
        for c in everyone:
            ci = b["characters"][c]
            L.append(f"- {ci.get('name', c)} 的特徵：{ci.get('features', '')}。{scale.get(c, '')}")
        if cell.get("light"):
            L.append(f"- 光線：{light_text(b, cell)}")
        for sid in panel_scenes(b, cell):
            L.append(f"- 場景：{b.get('consistency', {}).get('scene', {}).get(sid, sid)}")
        L.append(f"- 畫面要的是：{cell['prompt']}")
        match = continuity_panels(b, ch, cell)
        if match:
            L.append("- 要跟這些已選定的格子接得上（同一個場景、道具、光線，開原圖比對）：")
            L += [f"  - {m['id']}（{m.get('label', '')}）：{OUT / 'panels' / ch['panels'][m['id']]}" for m in match]
        L.append("- 候選：")
        L += [f"  - {f}" for f in files] or ["  - （還沒畫）"]
        old = [f.stem for f in files if f in stale[pid]]
        if old:
            L.append(f"- 其中 {'、'.join(old)} 是舊版 prompt 畫的；現在的 prompt 是上面「畫面要的是」，照它判")
        L.append("")
    dest = OUT / "review"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / f"{name}.md"
    p.write_text("\n".join(L), encoding="utf-8")
    print(p)


def cmd_contact(a) -> None:
    font = ImageFont.truetype(font_path("plain"), 22)
    files = []
    for jid in a.ids:
        for d in ("panels", "sheets", "styles"):
            files += candidates(OUT / d, jid)
    if not files:
        raise SystemExit("no candidates found")
    cw, cols = a.width, a.cols
    cells = []
    for f in files:
        im = Image.open(f).convert("RGB")
        cells.append((f.name, im.resize((cw, round(im.height * cw / im.width)))))
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    sheet = Image.new("RGB", (cols * (cw + 8), sum(max(c.height for _, c in r) + 30 for r in rows)), "#888")
    y = 0
    for r in rows:
        for i, (name, c) in enumerate(r):
            sheet.paste(c, (i * (cw + 8), y + 28))
            ImageDraw.Draw(sheet).text((i * (cw + 8) + 4, y + 1), name, fill="white", font=font)
        y += max(c.height for _, c in r) + 30
    dest = OUT / f"contact_{a.name}.png"
    sheet.save(dest)
    print(dest)


# ---------------------------------------------------------------------------
# lettering
# ---------------------------------------------------------------------------


def _phrases(chars: list[str]) -> list[list[str]]:
    """Split after punctuation; runs of punctuation and closing brackets stay with the phrase before."""
    out, cur = [], []
    for i, c in enumerate(chars):
        cur.append(c)
        nxt = chars[i + 1] if i + 1 < len(chars) else None
        if c in BREAK_AFTER | {"︙", "﹂", "﹄"} and (nxt is None or nxt not in NO_START | {"︙"}):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def columns(text: str, per_col: int) -> list[list[str]]:
    """Vertical columns broken at phrase ends when possible. Punctuation never starts a column (it hangs on the
    one before), an opening bracket never ends one, a long phrase splits into balanced halves, and "\\n" forces a break."""
    if "\n" in text:
        return [c for part in text.split("\n") for c in columns(part, per_col)]
    chars = [VERT.get(c, c) for c in text]
    cols: list[list[str]] = []
    for ph in _phrases(chars):
        hang = sum(1 for c in reversed(ph) if c in NO_START or c == "︙")
        if cols and len(cols[-1]) + len(ph) - hang <= per_col:
            cols[-1].extend(ph)
            continue
        body = len(ph) - hang
        k = max(1, math.ceil(body / per_col))
        size = math.ceil(body / k)
        cur: list[str] = []
        for c in ph:
            if cur and len(cur) >= size and c not in NO_START and c != "︙":
                cols.append(cur)
                cur = []
            if c in NO_END and cur and len(cur) >= size - 1:
                cols.append(cur)
                cur = []
            cur.append(c)
        cols.append(cur)
    return [c for c in cols if c]


def text_block(entry: dict, size: int, max_h: float | None = None) -> Image.Image:
    """Vertical text on a transparent tile, columns right to left. With max_h, columns shorten until it fits."""
    kind = entry["kind"]
    font = ImageFont.truetype(font_path("serif") if kind in ("narration", "title") else font_path("bold"), size)
    per = entry.get("per_col", PER_COL[kind])
    if max_h:
        per = max(3, min(per, int((max_h - size * 1.25) // round(size * 1.06)) + 1))
    cols = columns(entry["text"], per)
    step_x, step_y = round(size * 1.18), round(size * 1.06)
    tw, th = step_x * len(cols), step_y * (max(len(c) for c in cols) - 1) + round(size * 1.25)
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    for ci, col in enumerate(cols):
        x = tw - (ci + 1) * step_x + (step_x - size) // 2
        for ri, chr_ in enumerate(col):
            d.text((x, ri * step_y), chr_, font=font, fill=(0, 0, 0, 255))
    return tile


def draw_entry(page: Image.Image, entry: dict, cell_box, base: int) -> list[int]:
    """One text item. The bubble shape says where the voice comes from: speech (round) is said in the room,
    voice (round, white on black) comes from someone unseen, screen / phone (square, double outline) comes
    through a device, narration is a plain box, title and tag are white on black."""
    kind = entry["kind"]
    oval = kind in ("speech", "voice")
    size = round(base * entry.get("scale", 1.0) * {"title": 1.5, "tag": 1.25}.get(kind, 1.0))
    room = (cell_box[3] - cell_box[1]) - 28 - (size * 1.1 if not oval else size * 0.8)
    tile = text_block(entry, size, max_h=room / (1.22 if oval else 1.0))
    if oval:  # the text rectangle must fit inside the ellipse: scale by about sqrt(2)
        bw, bh = round(tile.width * 1.42 + size * 0.5), round(tile.height * 1.22 + size * 0.8)
    else:
        pad = round(size * 0.55)
        bw, bh = tile.width + 2 * pad, tile.height + 2 * pad
    pad_x, pad_y = (bw - tile.width) // 2, (bh - tile.height) // 2
    x0, y0, x1, y1 = cell_box
    mgn = 14
    pos = entry.get("pos", "tr")
    bx = x1 - mgn - bw if pos[1] == "r" else (x0 + mgn if pos[1] == "l" else (x0 + x1 - bw) // 2)
    by = y0 + mgn if pos[0] == "t" else (y1 - mgn - bh if pos[0] == "b" else (y0 + y1 - bh) // 2)
    d = ImageDraw.Draw(page)
    box = [bx, by, bx + bw, by + bh]
    if kind == "speech":
        d.ellipse(box, fill="white", outline="black", width=3)
    elif kind == "voice":
        d.ellipse(box, fill="black", outline="white", width=3)
        white = Image.new("RGBA", tile.size, (255, 255, 255, 255))
        white.putalpha(tile.split()[3])
        page.paste(white, (bx + pad_x, by + pad_y), white)
        return box
    elif kind in ("screen", "phone"):
        d.rounded_rectangle(box, radius=round(size * 0.35), fill="white", outline="black", width=3)
        g = 5
        d.rounded_rectangle([box[0] + g, box[1] + g, box[2] - g, box[3] - g], radius=round(size * 0.25), outline="black", width=1)
    elif kind in ("title", "tag"):
        d.rectangle(box, fill="black")
        white = Image.new("RGBA", tile.size, (255, 255, 255, 255))
        white.putalpha(tile.split()[3])
        page.paste(white, (bx + pad_x, by + pad_y), white)
        return box
    else:
        d.rectangle(box, fill="white", outline="black", width=2)
    page.paste(tile, (bx + pad_x, by + pad_y), tile)
    return box


def draw_sfx(page: Image.Image, sfx: dict, cell_box) -> None:
    x0, y0, x1, y1 = cell_box
    size = round(min(x1 - x0, y1 - y0) * sfx.get("size", 0.25))
    font = ImageFont.truetype(font_path("bold"), size)
    stroke = max(4, size // 12)
    # the tile is as wide as the text: a fixed two-character tile cut 「唰啦」 to 「唰吋」 and the last 「叩」 of 「叩叩叩」
    left, top, right, bottom = font.getbbox(sfx["text"], stroke_width=stroke)
    pad = stroke + 2
    tile = Image.new("RGBA", (right - left + 2 * pad, bottom - top + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad - left, pad - top), sfx["text"], font=font, fill="black", stroke_width=stroke, stroke_fill="white")
    tile = tile.rotate(sfx.get("angle", 0), resample=Image.BICUBIC, expand=True)
    cx, cy = x0 + sfx["at"][0] * (x1 - x0), y0 + sfx["at"][1] * (y1 - y0)
    page.paste(tile, (round(cx - tile.width / 2), round(cy - tile.height / 2)), tile)


# ---------------------------------------------------------------------------
# panels into cells, pages
# ---------------------------------------------------------------------------


def cover(im: Image.Image, w: int, h: int, focus=(0.5, 0.5)) -> Image.Image:
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    left = round((im.width - w) * focus[0])
    top = round((im.height - h) * focus[1])
    return im.crop((left, top, left + w, top + h))


def rounded_mask(w: int, h: int, r: int) -> Image.Image:
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m


def placeholder(page: Image.Image, cell: dict, box, label: str | None = None) -> None:
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(page)
    fill = "#a9b4bf" if cell.get("screen") else ("#e8e1d0" if cell.get("flashback") else "#cfcfcf")
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=fill, outline="black", width=4)
    f = ImageFont.truetype(font_path("bold"), 30)
    txt = label or f"{cell['id']} {cell.get('label', '')}"
    lines, cur, maxw = [], "", x1 - x0 - 40
    for chr_ in txt:
        if d.textlength(cur + chr_, font=f) > maxw:
            lines.append(cur)
            cur = chr_
        else:
            cur += chr_
    lines.append(cur)
    cy = (y0 + y1) // 2 - len(lines) * 19
    for i, l in enumerate(lines):
        d.text((x0 + 20, cy + i * 38), l, fill="#444", font=f)


def panel_source(cell: dict, ch: dict) -> Image.Image:
    """The picked candidate as the page uses it, in black and white. `mirror` flips it (the first speaker belongs on the
    right of a right-to-left page); `zoom` below 1 shrinks it onto its own background colour, anchored at `zoom_at`, to
    free room for lettering beside a close-up. Both are layout only: the candidate file is never changed."""
    src = Image.open(OUT / "panels" / ch["panels"][cell["id"]]).convert("RGB")
    if cell.get("mirror"):
        src = ImageOps.mirror(src)
    z = cell.get("zoom", 1.0)
    if z < 1:
        W, H = src.size
        corners = sorted((src.getpixel(p) for p in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1))), key=sum)
        small = src.resize((round(W * z), round(H * z)), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), corners[1])
        ax, ay = cell.get("zoom_at", (0.5, 0.5))
        canvas.paste(small, (round((W - small.width) * ax), round((H - small.height) * ay)))
        src = canvas
    return src.convert("L").convert("RGB")  # pages stay black and white


def overlap(a, b) -> float:
    """Intersection of two boxes as a share of the smaller one."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    return w * h / min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))


def place_panel(page: Image.Image, cell: dict, box, ch: dict) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(page)
    if cell.get("fill"):  # a flat panel (all black for a pause, a voice in the dark): nothing to generate
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=cell["fill"], outline="black", width=4)
        return
    if cell["id"] not in ch["panels"]:
        placeholder(page, cell, box)
        return
    src = panel_source(cell, ch)
    focus = tuple(cell.get("focus", (0.5, 0.5)))
    if cell.get("screen"):  # seen through a device: bezel, camera dot, optional picture-in-picture
        t = max(10, round(min(w, h) * 0.035))
        d.rounded_rectangle([x0, y0, x1, y1], radius=t, fill="#1c1c1c")
        d.ellipse([(x0 + x1) // 2 - 3, y0 + t // 2 - 3, (x0 + x1) // 2 + 3, y0 + t // 2 + 3], fill="#777")
        iw, ih = w - 2 * t, h - 2 * t
        page.paste(cover(src, iw, ih, focus), (x0 + t, y0 + t), rounded_mask(iw, ih, t // 2))
        if cell.get("pip") and cell["pip"] in ch["panels"]:
            pw = round(iw * 0.22)
            ph = round(pw * 0.75)
            pip = cover(Image.open(OUT / "panels" / ch["panels"][cell["pip"]]).convert("L").convert("RGB"), pw, ph)
            px, py = x0 + t + iw - pw - 10, y0 + t + ih - ph - 10
            d.rectangle([px - 3, py - 3, px + pw + 2, py + ph + 2], fill="white")
            page.paste(pip, (px, py))
        d.rounded_rectangle([x0, y0, x1, y1], radius=t, outline="black", width=4)
    elif cell.get("flashback"):  # borderless, faded edges
        im = cover(src, w, h, focus)
        fade = Image.new("L", (w, h), 0)
        f = round(min(w, h) * 0.08)
        ImageDraw.Draw(fade).rectangle([f, f, w - f, h - f], fill=255)
        page.paste(im, (x0, y0), fade.filter(ImageFilter.GaussianBlur(f * 0.6)))
    else:
        page.paste(cover(src, w, h, focus), (x0, y0))
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline="black", width=4)


def render_page(b: dict, page: dict, pi: int, ch: dict, wireframe: bool = False, issues: list[str] | None = None) -> Image.Image:
    """One page. Lettering boxes of one panel that cover each other go into `issues`: p6's count was hidden under its
    narration box and nobody saw it until the pages were out."""
    W, H = b["page"]
    im = Image.new("RGB", (W, H), "white")
    base = round(W / 40)
    for k, (cell, box) in enumerate(page_cells(b, page), 1):
        if "box" in cell:  # insets: white halo so they sit on top of the big panel
            ImageDraw.Draw(im).rectangle([box[0] - 8, box[1] - 8, box[2] + 8, box[3] + 8], fill="white")
        if wireframe and not cell.get("fill"):
            placeholder(im, cell, box, f"{k}. {cell.get('label', cell['id'])}")
        else:
            place_panel(im, cell, box, ch)
        for s in cell.get("sfx", []):
            draw_sfx(im, s, box)
        drawn = []
        for e in cell.get("text", []):
            bx = draw_entry(im, e, box, base)
            for pe, pb in drawn:
                if issues is not None and overlap(pb, bx) > 0.05:
                    issues.append(f"page {pi} {cell['id']}: 「{e['text'].replace(chr(10), '')[:8]}」 ({e.get('pos', 'tr')}) covers "
                                  f"「{pe['text'].replace(chr(10), '')[:8]}」 ({pe.get('pos', 'tr')}); move one or shorten it")
            drawn.append((e, bx))
    ImageDraw.Draw(im).text((W // 2 - 8, H - 40), str(pi), fill="#888", font=ImageFont.truetype(font_path("plain"), 20))
    return im


def spread(pages: list[Image.Image], per_row: int, height: int, rtl: bool = True) -> Image.Image:
    W, H = pages[0].size
    tw = round(W * height / H)
    thumbs = [p.resize((tw, height)) for p in pages]
    rows = [thumbs[i:i + per_row] for i in range(0, len(thumbs), per_row)]
    sheet = Image.new("RGB", (per_row * (tw + 14), len(rows) * (height + 20)), "#666")
    for ri, row in enumerate(rows):
        for k, t in enumerate(row):
            x = (per_row - 1 - k) * (tw + 14) if rtl else k * (tw + 14)
            sheet.paste(t, (x + 7, ri * (height + 20)))
    return sheet


def print_lettering(issues: list[str]) -> None:
    for m in issues:
        print(f"WARN   lettering: {m}")


def cmd_plan(a) -> None:
    """Gate 3: every page as a wireframe, each panel labelled in reading order, with the real lettering."""
    b = load_board()
    OUT.mkdir(parents=True, exist_ok=True)
    issues: list[str] = []
    pages = [render_page(b, page, pi, {"panels": {}}, wireframe=True, issues=issues) for pi, page in enumerate(b["pages"], 1)]
    spread(pages, 4, 1000, b.get("direction", "rtl") == "rtl").save(OUT / "plan.png")
    print(OUT / "plan.png")
    print_lettering(issues)


def cmd_pages(a) -> None:
    b = load_board()
    ch = load_choices()
    dest = OUT / "pages"
    dest.mkdir(parents=True, exist_ok=True)
    pages, issues = [], []
    for pi, page in enumerate(b["pages"], 1):
        if a.pages and pi not in a.pages:
            continue
        im = render_page(b, page, pi, ch, issues=issues)
        p = dest / f"page_{pi:02d}.png"
        im.save(p)
        pages.append(im)
        print(p)
    print_lettering(issues)
    if a.pages:
        return
    pages[0].save(OUT / "comic.pdf", save_all=True, append_images=pages[1:], resolution=150)
    spread(pages, len(pages), 850, b.get("direction", "rtl") == "rtl").save(OUT / "overview.jpg", quality=85)
    print(OUT / "comic.pdf", OUT / "overview.jpg")


IG_SIZES = {"3:4": (1080, 1440), "4:5": (1080, 1350)}
IG_MAX = 20  # slides in one Instagram post
DISCLOSURE = "AI 輔助創作｜故事純屬虛構"


def board_title(b: dict) -> str:
    """The title as lettered on the pages (its line breaks kept), else the board's `title`."""
    for _, cell, _ in all_panels(b):
        for e in cell.get("text", []):
            if e["kind"] == "title":
                return e["text"]
    return b.get("title", "")


def fit_on(im: Image.Image, w: int, h: int, colour="white") -> Image.Image:
    """The whole image scaled to fit inside w x h, centred on a plain background: nothing of the page is cropped."""
    s = min(w / im.width, h / im.height)
    small = im.convert("RGB").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), colour)
    canvas.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return canvas


def ig_cover(b: dict, ch: dict, w: int, h: int, panel: str | None) -> Image.Image:
    """Slide 1, which the profile grid and the feed show: one picked panel filling the slide (`--cover`, or page 1
    as it is), the vertical title on black, and the disclosure along the bottom."""
    if panel:
        cell = find_panel(b, panel)
        if panel not in ch["panels"]:
            raise SystemExit(f"--cover {panel}: that panel has no picked candidate")
        im = cover(panel_source(cell, ch), w, h, tuple(cell.get("focus", (0.5, 0.5))))
        draw_entry(im, {"kind": "title", "text": board_title(b), "pos": "tr", "scale": 1.3}, (0, 0, w, h), round(w / 40))
    else:
        im = fit_on(Image.open(OUT / "pages" / "page_01.png"), w, h)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(font_path("plain"), round(w / 38))
    tw = d.textlength(DISCLOSURE, font=font)
    y = h - round(w / 38) - 22
    d.rectangle([0, y - 10, w, h], fill="white")
    d.text(((w - tw) / 2, y), DISCLOSURE, fill="#333", font=font)
    return im


def ig_end(b: dict, w: int, h: int, handle: str | None) -> Image.Image:
    """The last slide: the title, the disclosure and where to find more, on white."""
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    title = ImageFont.truetype(font_path("serif"), round(w / 16))
    plain = ImageFont.truetype(font_path("plain"), round(w / 30))
    lines = [(board_title(b).replace("\n", ""), title)]
    lines += [("（完）", plain), ("", plain), ("故事和人物純屬虛構", plain), ("文字和圖由 AI 輔助創作", plain)]
    if handle:
        lines += [("", plain), (f"更多故事：{handle}", plain)]
    heights = [round(f.size * 1.6) for _, f in lines]
    y = (h - sum(heights)) // 2
    for (text, f), lh in zip(lines, heights):
        d.text(((w - d.textlength(text, font=f)) / 2, y), text, fill="black", font=f)
        y += lh
    return im


# A brand file (`--brand-file brand.json`) holds an account's look and words: colours, seal, the disclosure, how a
# story number is written, the end card's lines and the caption template. The code draws; the file decides what.
# Without one, export and reel keep their plain defaults. See assets/example_brand.json.
BRAND_COLOURS = {"paper": "#FFFFFF", "ink": "#141414", "accent": "#B8322A", "muted": "#696969"}


def load_brand(path: str | None) -> dict | None:
    """Read a brand file; paths in it (seal, logo, ledger) are relative to the file itself."""
    if not path:
        return None
    p = Path(path).resolve()
    br = json.loads(p.read_text(encoding="utf-8"))
    for k in ("seal", "logo", "ledger"):
        if br.get(k):
            br[k] = str((p.parent / br[k]).resolve())
    br["rgb"] = {k: hex_rgb(v) for k, v in {**BRAND_COLOURS, **br.get("colors", {})}.items()}
    br.setdefault("name", "")
    br.setdefault("disclosure", DISCLOSURE)
    br.setdefault("number", "第 {n} 首")
    return br


def brand_text(template: str, br: dict, number: int | None = None, title: str = "") -> str:
    """Fill {name} {number} {title} {disclosure} {handle}. With no number yet, {number} becomes the brand's name, so
    「{number}｜{title}」 reads 「鬼唱詩｜title」 until the story has its slot."""
    num = br["number"].format(n=number) if number else br.get("name", "")
    return template.format(name=br.get("name", ""), number=num, title=title, disclosure=br["disclosure"],
                           handle=br.get("handle") or "")


def seal_images(path: str | None, red) -> tuple[Image.Image | None, Image.Image | None]:
    """(solid, outline) from a square seal picture with light characters on a red ground (an avatar): solid is the
    picture as it is, for the cover; outline turns it round to red characters in a red frame on transparent, the way
    the seal is stamped on the end card."""
    if not path:
        return None, None
    solid = Image.open(path).convert("RGB")
    g = solid.convert("L")
    chars = g.point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.MaxFilter(3))
    s = solid.width
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ink = Image.new("RGBA", (s, s), tuple(red) + (255,))
    out.paste(ink, (0, 0), chars)
    frame = Image.new("L", (s, s), 0)
    k = round(s * 0.045)
    ImageDraw.Draw(frame).rectangle([k, k, s - 1 - k, s - 1 - k], outline=255, width=round(s * 0.05))
    out.paste(ink, (0, 0), frame)
    return solid, out


def _serif(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(font_path("serif"), size)
    try:
        f.set_variation_by_name("SemiBold")
    except (OSError, ValueError, AttributeError):
        pass
    return f


def brand_cover(b: dict, ch: dict, w: int, h: int, panel: str | None, br: dict, number: int | None,
                seal: Image.Image | None) -> Image.Image:
    """Slide 1: the picked panel framed on the paper colour, the vertical title at its top right, and a strip under
    it with the brand's `cover_strip` line (「鬼唱詩｜第 N 首」), the disclosure and the seal. The same frame for every
    comic, so the profile grid reads as one shelf."""
    c = br["rgb"]
    im = Image.new("RGB", (w, h), c["paper"])
    m = round(w * 0.05)
    strip = round(h * 0.11)
    box = (m, m, w - m, h - m - strip)
    pw, ph = box[2] - box[0], box[3] - box[1]
    if panel:
        cell = find_panel(b, panel)
        if panel not in ch["panels"]:
            raise SystemExit(f"--cover {panel}: that panel has no picked candidate")
        pic = cover(panel_source(cell, ch), pw, ph, tuple(cell.get("focus", (0.5, 0.5))))
    else:
        pic = cover(Image.open(OUT / "pages" / "page_01.png").convert("RGB"), pw, ph, (0.5, 0.0))
    im.paste(pic, box[:2])
    d = ImageDraw.Draw(im)
    d.rectangle([box[0] - 1, box[1] - 1, box[2], box[3]], outline=c["ink"], width=5)
    draw_entry(im, {"kind": "title", "text": board_title(b), "pos": "tr", "scale": 1.3}, box, round(w / 40))
    top = box[3] + round(strip * 0.22)
    line = brand_text(br.get("cover_strip", "{name}｜{number}"), br, number) if number else br.get("name", "")
    big = _serif(round(w / 23))
    small = ImageFont.truetype(font_path("plain"), round(w / 42))
    d.text((m, top), line, font=big, fill=c["ink"])
    d.text((m, top + round(big.size * 1.35)), br["disclosure"], font=small, fill=c["muted"])
    if seal is not None:
        sz = round(strip * 0.8)
        im.paste(seal.resize((sz, sz), Image.LANCZOS), (w - m - sz, box[3] + (strip - sz) // 2 + 4))
    return im


def brand_end(w: int, h: int, br: dict, handle: str | None, seal: Image.Image | None) -> Image.Image:
    """The last slide on the paper colour: the brand's `end_card` lines (the first one large), the handle, and the
    seal stamped at the bottom right."""
    c = br["rgb"]
    im = Image.new("RGB", (w, h), c["paper"])
    d = ImageDraw.Draw(im)
    texts = br.get("end_card") or ["（完）", br["disclosure"]]
    lines = [(texts[0], _serif(round(w / 13)), c["ink"], 2.2)]
    lines += [(t, _serif(round(w / 25)), c["ink"], 1.7) for t in texts[1:]]
    if len(lines) > 1:
        lines[-1] = (*lines[-1][:3], 2.2)
    if handle:
        lines.append((handle, ImageFont.truetype(font_path("plain"), round(w / 28)), c["muted"], 1.0))
    heights = [round(f.size * gap) for _, f, _, gap in lines]
    y = round(h * 0.42 - sum(heights) / 2)
    for (text, f, colour, _), lh in zip(lines, heights):
        d.text(((w - d.textlength(text, font=f)) / 2, y), text, font=f, fill=colour)
        y += lh
    if seal is not None:
        sz = round(w * 0.17)
        m = round(w * 0.07)
        s = seal.resize((sz, sz), Image.LANCZOS)
        im.paste(s, (w - m - sz, h - m - sz), s)
    return im


def cmd_export(a) -> None:
    """Instagram carousel from the laid-out pages: a cover, every page whole on a 3:4 (or 4:5) slide, an end card,
    and a caption with the disclosure. A page of 1200 x 1700 leaves about 32 px of white at each side on 3:4. More
    pages than fit in one post (20 slides) are split into parts. With --brand-file the cover, end card, page ground
    and caption follow the brand file."""
    b, ch = load_board(), load_choices()
    pages = sorted((OUT / "pages").glob("page_*.png"))
    if not pages:
        raise SystemExit("no pages yet: run `pages` first")
    w, h = IG_SIZES[a.ratio]
    dest = OUT / "export" / "ig"
    dest.mkdir(parents=True, exist_ok=True)
    for f in dest.glob("*"):
        f.unlink()
    per = IG_MAX - 2
    parts = [pages[i:i + per] for i in range(0, len(pages), per)]
    title = board_title(b).replace("\n", "")
    br = a.brand
    handle = a.handle or (br or {}).get("handle")
    solid, outline = seal_images(br.get("seal"), br["rgb"]["accent"]) if br else (None, None)
    ground = br["rgb"]["paper"] if br else "white"
    for k, part in enumerate(parts, 1):
        tag = f"part{k}_" if len(parts) > 1 else ""
        first = brand_cover(b, ch, w, h, a.cover, br, a.number, solid) if br else ig_cover(b, ch, w, h, a.cover)
        slides = [first] + [fit_on(Image.open(p), w, h, ground) for p in part]
        if k == len(parts):
            slides.append(brand_end(w, h, br, handle, outline) if br else ig_end(b, w, h, handle))
        for i, s in enumerate(slides, 1):
            s.save(dest / f"{tag}{i:02d}.jpg", quality=92)
        print(f"{dest / (tag + '01.jpg')} .. {tag}{len(slides):02d}.jpg ({len(slides)} slides)")
    split = f"（{len(parts)} 之 1）" if len(parts) > 1 else ""
    if br:
        cfg = br.get("caption", {})
        head = brand_text(cfg.get("title", "{number}｜{title}"), br, a.number, title) + split
        lines = [brand_text(x, br, a.number, title) for x in cfg.get("lines", ["{disclosure}"])]
        tags = a.tags.split(",") if a.tags_given else cfg.get("tags", [])
        cap = [head, "", *lines, "", " ".join(tags)]
    else:
        cap = [f"[創作] {title}" + split, "", DISCLOSURE, "漫畫由右往左、由上往下讀。", "", " ".join(a.tags.split(","))]
    (dest / "caption.txt").write_text("\n".join(cap) + "\n", encoding="utf-8")
    print(dest / "caption.txt")


# ---------------------------------------------------------------------------
# Reels: 9:16 video for Instagram Reels, YouTube Shorts and TikTok
# ---------------------------------------------------------------------------

REEL_W, REEL_H, REEL_FPS = 1080, 1920, 30
# The apps draw a header over the top, and the account name, caption and buttons over the bottom fifth and the right
# edge. Every word of a Reel stays inside this box so nothing is covered; pictures may run past it.
REEL_SAFE = (90, 260, 960, 1480)
REEL_PIC = (280, 1250)  # the picture band of a teaser (y0, y1); the caption sits under it
REEL_CAP_Y = 1290
CAPTION_KINDS = ("narration", "speech", "voice", "phone", "screen")
NO_START_H = set("，。、：；！？」』）…—～")
PAUSE_SHORT, PAUSE_LONG = set("，、：；"), set("。！？…")


def ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def ffmpeg_exe() -> str:
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError:
        raise SystemExit("reel needs ffmpeg: put it on PATH, or `py -m pip install imageio-ffmpeg`") from None
    return imageio_ffmpeg.get_ffmpeg_exe()


def write_video(frames, path: Path, fps: int = REEL_FPS) -> int:
    """Pipe RGB frames into ffmpeg: H.264, yuv420p, faststart, no sound. Music is added in the app, where the
    trending sounds are. Returns the number of frames written."""
    import subprocess
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{REEL_W}x{REEL_H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    try:
        for f in frames:
            proc.stdin.write(f.convert("RGB").tobytes())
            n += 1
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed writing {path}")
    return n


def reel_font(size: int, kind: str = "serif", weight: str | None = "SemiBold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(font_path(kind), size)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except (OSError, ValueError, AttributeError):
            pass  # not a variable font: its one weight it is
    return f


def _w(chars, font) -> float:
    return sum(font.getlength(c) for c, _ in chars)


def wrap_h(chars: list[tuple[str, int]], font, max_w: float) -> list[list[tuple[str, int]]]:
    """Horizontal lines for a caption: greedy, then balanced, since two lines of similar length read better than a long
    one and a stub. Closing punctuation never starts a line; "\n" forces a break. `chars` are (character, flag)."""
    def greedy(limit: float) -> list[list[tuple[str, int]]]:
        lines, cur = [], []
        for c in chars:
            if c[0] == "\n":
                lines.append(cur)
                cur = []
            elif cur and _w(cur + [c], font) > limit and c[0] not in NO_START_H:
                lines.append(cur)
                cur = [c]
            else:
                cur.append(c)
        if cur:
            lines.append(cur)
        return lines

    lines = greedy(max_w)
    if len(lines) > 1 and not any(c[0] == "\n" for c in chars):
        balanced = greedy(min(max_w, _w(chars, font) / len(lines) * 1.06 + font.size))
        if len(balanced) == len(lines):
            lines = balanced
    return lines


BREAK_AFTER_H = set("，。、：；！？…」』")


def wrap_phrases(chars: list[tuple[str, int]], font, max_w: float, max_lines: int) -> list[list[tuple[str, int]]] | None:
    """Lines that break only after punctuation, packed and then balanced; None when a phrase is wider than the line or
    it takes more than max_lines (the caller then tries a smaller size, and breaks between characters only last).
    「妹妹，妳後面那三個是妳同／事喔？」 was the first teaser's caption before this."""
    if any(c[0] == "\n" for c in chars):
        return None
    ps, cur = [], []
    for i, c in enumerate(chars):
        cur.append(c)
        nxt = chars[i + 1][0] if i + 1 < len(chars) else ""
        if c[0] in BREAK_AFTER_H and nxt not in BREAK_AFTER_H:
            ps.append(cur)
            cur = []
    if cur:
        ps.append(cur)
    if any(_w(p, font) > max_w for p in ps):
        return None

    def pack(limit: float) -> list[list[tuple[str, int]]]:
        lines, line = [], []
        for p in ps:
            if line and _w(line + p, font) > limit:
                lines.append(line)
                line = list(p)
            else:
                line += p
        if line:
            lines.append(line)
        return lines

    lines = pack(max_w)
    if len(lines) > 1:
        balanced = pack(max(max(_w(p, font) for p in ps), _w(chars, font) / len(lines) * 1.06))
        if len(balanced) == len(lines):
            lines = balanced
    return lines if len(lines) <= max_lines else None


def fit_lines(chars, sizes, max_w: float, max_lines: int, kind: str = "serif", weight: str | None = "SemiBold"):
    """(size, font, lines) at the largest size whose punctuation-only breaks fit; failing that, the largest size whose
    character breaks fit; failing that, the smallest size as it comes out."""
    for size in sizes:
        font = reel_font(size, kind, weight)
        lines = wrap_phrases(chars, font, max_w, max_lines)
        if lines:
            return size, font, lines
    for size in sizes:
        font = reel_font(size, kind, weight)
        lines = wrap_h(chars, font, max_w)
        if len(lines) <= max_lines:
            return size, font, lines
    return size, font, lines


def text_layer(lines, font, colours: dict, line_h: float, alphas: list[float] | None = None) -> Image.Image:
    """Centred lines on a transparent layer, each character in its flag's colour with a black outline; `alphas` (one
    per character, reading order) fades characters in one by one."""
    w = int(max(_w(l, font) for l in lines)) + 20
    h = int(line_h * len(lines)) + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = 0
    for i, line in enumerate(lines):
        x = (w - _w(line, font)) / 2
        y = 10 + i * line_h
        for c, flag in line:
            a = 1.0 if alphas is None else alphas[k]
            k += 1
            if a > 0:
                r, g, b = colours[flag]
                d.text((x, y), c, font=font, fill=(r, g, b, round(255 * a)), stroke_width=3,
                       stroke_fill=(0, 0, 0, round(255 * a)))
            x += font.getlength(c)
    return im


def paste_layer(base: Image.Image, layer: Image.Image, xy, opacity: float = 1.0) -> None:
    if opacity <= 0:
        return
    if opacity < 1:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda v: round(v * opacity)))
    base.paste(layer, xy, layer)


def centred_text(im: Image.Image, y: float, text: str, font, fill) -> float:
    """One centred line; returns the y below it."""
    d = ImageDraw.Draw(im)
    d.text(((REEL_W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)
    return y + font.size * 1.5


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def panel_caption(cell: dict) -> str:
    """A panel's lettering as one horizontal caption: narration as it is, speech in 「」, line breaks dropped."""
    parts = []
    for e in cell.get("text", []):
        if e["kind"] in CAPTION_KINDS:
            t = e["text"].replace("\n", "")
            if e["kind"] in ("speech", "voice", "phone") and not t.startswith("「"):
                t = f"「{t}」"
            parts.append(t)
    return "".join(parts)


def caption_layer(text: str) -> Image.Image | None:
    if not text:
        return None
    size, font, lines = fit_lines([(c, 0) for c in text], (60, 52, 46), REEL_SAFE[2] - REEL_SAFE[0], 3)
    if len(lines) > 3:
        print(f"WARN reel: caption runs to {len(lines)} lines; shorten it with --captions: {text}")
    return text_layer(lines, font, {0: (242, 242, 242)}, size * 1.45)


def panel_motion(src: Image.Image, n: int, focus=(0.5, 0.5)):
    """(picture, top-left) for each of n frames. A panel wider than the band pushes in slowly toward its `focus`; a
    taller one fills the band's width and pans from top to bottom, so all of it is seen."""
    W, H = src.size
    y0, y1 = REEL_PIC
    band_h = y1 - y0
    wide = W / H >= REEL_W / band_h
    vw, vh = (REEL_W, round(REEL_W * H / W)) if wide else (REEL_W, band_h)
    top = y0 + (band_h - vh) // 2 if wide else y0
    for i in range(n):
        t = ease(i / max(1, n - 1))
        if wide:
            s = 1 + 0.08 * t
            bw, bh = W / s, H / s
            cx = min(max(W * focus[0], bw / 2), W - bw / 2)
            cy = min(max(H * focus[1], bh / 2), H - bh / 2)
        else:
            s = 1 + 0.04 * t
            bw = W / s
            bh = bw * vh / vw
            cx, cy = W / 2, bh / 2 + (H - bh) * t
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
        yield src.transform((vw, vh), Image.Transform.EXTENT, box, Image.Resampling.BICUBIC), (0, top)


def reel_end(title: str, end_text: str, handle: str | None, accent, logo: str | None,
             disclosure: str = DISCLOSURE) -> Image.Image:
    im = Image.new("RGB", (REEL_W, REEL_H), "black")
    y = 560
    if logo:
        lg = Image.open(logo).convert("RGBA").resize((240, 240), Image.LANCZOS)
        im.paste(lg, ((REEL_W - 240) // 2, 470), lg)
        y = 780
    if title:
        y = centred_text(im, y, f"〈{title}〉", reel_font(50), (190, 190, 190))
    y = centred_text(im, y + 10, end_text, reel_font(76), (245, 245, 245))
    if handle:
        y = centred_text(im, y + 20, handle, reel_font(46, "plain", None), accent)
    centred_text(im, y + 10, disclosure, reel_font(34, "plain", None), (140, 140, 140))
    return im


def frame_sheet(samples: list[Image.Image], path: Path) -> None:
    """Sampled frames side by side, for looking at a Reel without playing it."""
    tw, th = 270, 480
    sheet = Image.new("RGB", (len(samples) * (tw + 10) + 10, th + 20), "#777")
    for i, f in enumerate(samples):
        sheet.paste(f.resize((tw, th), Image.LANCZOS), (10 + i * (tw + 10), 10))
    sheet.save(path, quality=90)


def reel_caption(path: Path, first: str, lines: list[str], tags: str) -> None:
    path.write_text("\n".join([first, "", *lines, "", " ".join(tags.split(","))]) + "\n", encoding="utf-8")


def reel_caption_parts(a, kind: str, title: str) -> tuple[str, list[str]]:
    """First line and body of a Reel's caption: from the brand file's `reel` block when there is one ("teaser_lines"
    or "line_lines"), else the plain disclosure."""
    br = a.brand
    if not br:
        first = f"[創作] {title}" if kind == "teaser" else title
        return first, [DISCLOSURE] + (["全篇漫畫在主頁。"] if kind == "teaser" else [])
    cfg = br.get("reel", {})
    if kind == "teaser":
        first = brand_text(cfg.get("title", br.get("caption", {}).get("title", "{number}｜{title}")), br, a.number, title)
    else:
        first = title
    lines = cfg.get(f"{kind}_lines", ["{disclosure}"])
    return first, [brand_text(x, br, a.number, title) for x in lines]


def reel_teaser(a) -> None:
    b, ch = load_board(), load_choices()
    if not a.ids:
        raise SystemExit("reel teaser needs panel ids, e.g. `reel teaser p8 p9 p10`")
    caps = a.captions.split("|") if a.captions else []
    items = []
    for k, pid in enumerate(a.ids):
        cell = find_panel(b, pid)
        if pid not in ch["panels"]:
            raise SystemExit(f"{pid} has no picked candidate")
        text = caps[k] if k < len(caps) and caps[k] != "" else panel_caption(cell)
        if text == "-":
            text = ""
        items.append((cell, panel_source(cell, ch), caption_layer(text)))
    title = board_title(b).replace("\n", "") if a.title is None else a.title
    accent = hex_rgb(a.accent)
    end = reel_end(title, a.end, a.handle, accent, a.logo, a.disclosure)
    per = [round(a.seconds * REEL_FPS) for _ in items]
    per[-1] += REEL_FPS  # the last panel is the one to sit with
    n_end = round(2.5 * REEL_FPS)
    total = sum(per) + n_end
    marks = {round(total * i / 7) for i in range(7)} | {total - 1}
    samples: list[Image.Image] = []
    black = Image.new("RGB", (REEL_W, REEL_H), "black")

    def frames():
        idx = 0
        for k, ((cell, src, cap), n) in enumerate(zip(items, per)):
            for i, (pic, xy) in enumerate(panel_motion(src, n, tuple(cell.get("focus", (0.5, 0.5))))):
                f = black.copy()
                f.paste(pic, xy)
                if cap is not None:  # the first caption is there from frame 0: it is the hook
                    op = 1.0 if k == 0 else min(1.0, max(0.0, (i - 6) / 8))
                    paste_layer(f, cap, ((REEL_W - cap.width) // 2, REEL_CAP_Y), op)
                fade = 1.0
                if k > 0 and i < 4:
                    fade = (i + 1) / 5
                if i >= n - 5:
                    fade = min(fade, (n - i) / 6)
                if fade < 1:
                    f = Image.blend(black, f, fade)
                if idx in marks:
                    samples.append(f.copy())
                idx += 1
                yield f
        for i in range(n_end):
            f = Image.blend(black, end, min(1.0, (i + 1) / 8))
            if idx in marks:
                samples.append(f.copy())
            idx += 1
            yield f

    dest = OUT / "export" / "reels"
    dest.mkdir(parents=True, exist_ok=True)
    name = a.name or "teaser_" + "-".join(a.ids)
    n = write_video(frames(), dest / f"{name}.mp4")
    # the cover: the first panel half way through its move, the title over the top of the picture
    cell, src, cap = items[0]
    pic, xy = list(panel_motion(src, per[0], tuple(cell.get("focus", (0.5, 0.5)))))[per[0] // 2]
    cov = black.copy()
    cov.paste(pic, xy)
    if cap is not None:
        paste_layer(cov, cap, ((REEL_W - cap.width) // 2, REEL_CAP_Y))
    if title:
        size, font, lines = fit_lines([(c, 0) for c in title], (84, 72), REEL_SAFE[2] - REEL_SAFE[0], 3, "serif", "Bold")
        tl = text_layer(lines, font, {0: (255, 255, 255)}, size * 1.3)
        paste_layer(cov, tl, ((REEL_W - tl.width) // 2, 300))
    cov.save(dest / f"{name}_cover.jpg", quality=92)
    cov.crop((0, 240, REEL_W, 1680)).save(dest / f"{name}_grid.jpg", quality=90)  # the 3:4 the profile grid shows
    frame_sheet(samples, dest / f"{name}_frames.jpg")
    first, lines = reel_caption_parts(a, "teaser", title)
    reel_caption(dest / f"{name}_caption.txt", first, lines, a.tags)
    print(f"{dest / name}.mp4: {n} frames, {n / REEL_FPS:.1f} s; cover, grid, frames and caption beside it")


def parse_accent(text: str) -> list[tuple[str, int]]:
    """Characters with a flag: 1 inside {braces}, which are dropped."""
    out, flag = [], 0
    for c in text:
        if c == "{":
            flag = 1
        elif c == "}":
            flag = 0
        else:
            out.append((c, flag))
    return out


def reel_line(a) -> None:
    """A one-line story: black, the words appear one by one at reading pace, a beat before the {accented} part, which
    comes in the accent colour; then a hold, and a fade to black so the loop restarts cleanly."""
    if not a.text:
        raise SystemExit('reel line needs --text, e.g. --text "我回頭，床上那個人還在{睡}。"')
    chars = parse_accent(a.text)
    plain = [c for c in chars if c[0] != "\n"]
    sizes = (84, 72, 60) if len(plain) <= 28 else (72, 60) if len(plain) <= 44 else (60, 52)
    size, font, lines = fit_lines(chars, sizes, 840, 6)
    line_h = size * 1.55
    times, t, prev = [], 0.5, 0
    for c, flag in plain:
        if flag and not prev:
            t += a.beat
        times.append(t)
        t += 1 / a.cps
        t += 0.25 if c in PAUSE_SHORT else 0.45 if c in PAUSE_LONG else 0
        prev = flag
    n = round((times[-1] + a.hold) * REEL_FPS)
    colours = {0: (238, 238, 238), 1: hex_rgb(a.accent)}
    bg = Image.new("RGB", (REEL_W, REEL_H), "black")
    y = 1360
    if a.handle:
        y = centred_text(bg, y, a.handle, reel_font(40, "plain", None), hex_rgb(a.accent))
    centred_text(bg, y, a.disclosure, reel_font(30, "plain", None), (120, 120, 120))
    black = Image.new("RGB", (REEL_W, REEL_H), "black")
    marks = {round(n * i / 7) for i in range(7)} | {n - 1}
    samples: list[Image.Image] = []
    full = None

    def frames():
        nonlocal full
        for i in range(n):
            tt = i / REEL_FPS
            alphas = [min(1.0, max(0.0, (tt - tc) * REEL_FPS / 4)) for tc in times]
            layer = text_layer(lines, font, colours, line_h, alphas)
            f = bg.copy()
            paste_layer(f, layer, ((REEL_W - layer.width) // 2, round(870 - layer.height / 2)))
            if i == n - 8:
                full = f.copy()
            if i >= n - 6:
                f = Image.blend(black, f, (n - i) / 7)
            if i in marks:
                samples.append(f.copy())
            yield f

    dest = OUT / "export" / "reels"
    dest.mkdir(parents=True, exist_ok=True)
    name = a.name or "line_" + hashlib.sha1(a.text.encode()).hexdigest()[:8]
    count = write_video(frames(), dest / f"{name}.mp4")
    full.save(dest / f"{name}_cover.jpg", quality=92)
    full.crop((0, 240, REEL_W, 1680)).save(dest / f"{name}_grid.jpg", quality=90)
    frame_sheet(samples, dest / f"{name}_frames.jpg")
    first, lines = reel_caption_parts(a, "line", "".join(c for c, _ in plain))
    reel_caption(dest / f"{name}_caption.txt", first, lines, a.tags)
    print(f"{dest / name}.mp4: {count} frames, {count / REEL_FPS:.1f} s; cover, grid, frames and caption beside it")


def cmd_reel(a) -> None:
    """9:16 videos for Reels, Shorts and TikTok. `teaser`: a few picked panels, each moving slowly with its caption,
    then an end card that sends viewers to the full comic. `line`: a one-line story typed out on black. Silent mp4,
    1080 x 1920, 30 fps, plus a cover, the 3:4 the profile grid shows, a strip of sampled frames and a caption."""
    (reel_line if a.mode == "line" else reel_teaser)(a)


def cmd_status(a) -> None:
    """Where the run stands: picks per page, the panels still missing (with how many candidates each has), how many
    review briefs exist, and GPU minutes from out/log.jsonl by kind."""
    b, ch = load_board(), load_choices()
    total = picked = 0
    for pi, page in enumerate(b["pages"], 1):
        ids = [c["id"] for c, _ in page_cells(b, page) if not c.get("fill")]
        got = [i for i in ids if i in ch["panels"]]
        total, picked = total + len(ids), picked + len(got)
        missing = [f"{i}({len(candidates(OUT / 'panels', i))})" for i in ids if i not in ch["panels"]]
        print(f"page {pi}: {len(got)}/{len(ids)} picked" + (f"; missing {' '.join(missing)}" if missing else ""))
    print(f"all: {picked}/{total} picked; style {ch.get('style', '-')}; {len(ch['sheets'])} sheets chosen")
    briefs = sorted((OUT / "review").glob("*.md")) if (OUT / "review").exists() else []
    print(f"review briefs: {len(briefs)}" + (f" (latest {max(briefs, key=lambda f: f.stat().st_mtime).name})" if briefs else ""))
    # exec_s is the GPU's own time; wall_s also counts the wait in ComfyUI's queue (〈三個人〉: 284 min wall, 147 exec)
    mins: dict[str, float] = {}
    wall = 0.0
    images = 0
    if (OUT / "log.jsonl").exists():
        for line in (OUT / "log.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            mins[r.get("kind", "?")] = mins.get(r.get("kind", "?"), 0.0) + r.get("exec_s", r.get("wall_s", 0)) / 60
            wall += r.get("wall_s", 0) / 60
            images += len(r.get("files", []))
    print("GPU: " + (", ".join(f"{k} {v:.1f} min" for k, v in mins.items()) + f"; total {sum(mins.values()):.1f} min, "
                     f"{images} images ({wall:.1f} min with queue waits)" if mins else "nothing drawn yet"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=".", help="work folder with board.json (default: current folder)")
    ap.add_argument("--board", default="board.json", help="board file name inside the work folder")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    st = sub.add_parser("styles")
    st.add_argument("--panel", required=True, help="the panel to draw in every style, usually the main character's intro")
    st.add_argument("--seed", type=int, default=3301)
    s = sub.add_parser("sheets")
    s.add_argument("--n", type=int, default=3)
    p = sub.add_parser("panels")
    p.add_argument("--pass", dest="pass_", type=int, default=1)
    p.add_argument("--n", type=int, default=2)
    p.add_argument("--force", action="store_true", help="draw even if lint reports errors")
    li = sub.add_parser("lint")
    li.add_argument("--only", type=lambda v: v.split(","), default=None)
    rv = sub.add_parser("review")
    rv.add_argument("ids", nargs="*")
    rv.add_argument("--page", type=int, default=None)
    rv.add_argument("--unpicked", action="store_true")
    rv.add_argument("--name", default=None)
    rv.add_argument("--new", action="store_true", help="only candidates that no earlier brief in out/review listed")
    rv.add_argument("--read", action="store_true", help="a first-time reader's brief for the laid-out pages")
    rv.add_argument("--scene", type=lambda v: v.split(","), default=None,
                    help="scene ids (or 'all'): every picked panel set there, against its fixed layout")
    rv.add_argument("--cast", type=lambda v: v.split(","), default=None,
                    help="character ids (or 'all'): every picked panel of each, side by side with the sheet")
    rp = sub.add_parser("repaint")
    rp.add_argument("candidate", help="the candidate to start from, e.g. p34_1")
    rp.add_argument("--box", required=True, help="x0,y0,x1,y1 in its pixels, or fractions such as 0.3,0.1,0.6,0.5")
    rp.add_argument("--prompt", required=True, help="what to change inside the box")
    rp.add_argument("--n", type=int, default=3)
    rp.add_argument("--seed", type=int, default=0)
    fl = sub.add_parser("fill")
    fl.add_argument("candidate")
    fl.add_argument("--box", required=True, help="x0,y0,x1,y1 (or fractions); solid black inside it turns white")
    tn = sub.add_parser("tone")
    tn.add_argument("candidate")
    tn.add_argument("--poly", required=True, help="'x,y x,y x,y ...' around the area to texture")
    tn.add_argument("--mode", choices=["dots", "strokes"], default="dots")
    cr = sub.add_parser("crop")
    cr.add_argument("candidate")
    cr.add_argument("--box", required=True, help="x0,y0,x1,y1; the height follows the candidate's shape")
    for x in (s, p):
        x.add_argument("--seed", type=int, default=0)
        x.add_argument("--only", type=lambda v: v.split(","), default=None)
    c = sub.add_parser("choose")
    c.add_argument("picks", nargs="+")
    sub.add_parser("refs")
    sub.add_parser("plan")
    ct = sub.add_parser("contact")
    ct.add_argument("ids", nargs="+")
    ct.add_argument("--name", default="pick")
    ct.add_argument("--cols", type=int, default=3)
    ct.add_argument("--width", type=int, default=520)
    pg = sub.add_parser("pages")
    pg.add_argument("--pages", type=lambda v: [int(x) for x in v.split(",")], default=None)
    sub.add_parser("status")
    ex = sub.add_parser("export")
    ex.add_argument("--ratio", choices=sorted(IG_SIZES), default="3:4")
    ex.add_argument("--cover", default=None, help="panel id for slide 1 (default: page 1 as it is)")
    ex.add_argument("--handle", default=None, help="account name for the end card (default: the brand file's)")
    ex.add_argument("--tags", default=None, help="comma-separated hashtags for the caption (default: the brand file's)")
    rl = sub.add_parser("reel")
    rl.add_argument("mode", choices=["teaser", "line"])
    rl.add_argument("ids", nargs="*", help="teaser: the panels in order, usually three")
    rl.add_argument("--captions", default=None,
                    help="teaser: one caption per panel separated by |; empty takes the panel's lettering, - shows none")
    rl.add_argument("--seconds", type=float, default=3.5, help="teaser: seconds per panel (the last gets one more)")
    rl.add_argument("--title", default=None, help="teaser: title on the cover and end card (default: the board's; '' for none)")
    rl.add_argument("--end", default=None, help="teaser: the end card's line (default: the brand file's, else 全篇漫畫在主頁)")
    rl.add_argument("--logo", default=None, help="teaser: a square image (PNG with transparency) for the end card")
    rl.add_argument("--text", default=None, help="line: the story; {braces} mark the part shown in the accent colour")
    rl.add_argument("--cps", type=float, default=7.0, help="line: characters per second")
    rl.add_argument("--beat", type=float, default=0.6, help="line: pause in seconds before the accented part")
    rl.add_argument("--hold", type=float, default=2.5, help="line: seconds the whole line stays up")
    rl.add_argument("--handle", default=None, help="account name (default: the brand file's)")
    rl.add_argument("--accent", default=None, help="accent colour for the handle and the {accented} words")
    rl.add_argument("--name", default=None, help="output file name without extension")
    rl.add_argument("--tags", default=None, help="comma-separated hashtags for the caption (default: the brand file's)")
    for x in (ex, rl):
        x.add_argument("--brand-file", default=None,
                       help="an account's look and words (colours, seal, disclosure, end card, captions); see "
                            "assets/example_brand.json. Without it the plain cover, end card and captions are used")
        x.add_argument("--number", type=int, default=None,
                       help="the story's number in the account (「第 N 首」); leave out until its posting slot is known")
    a = ap.parse_args()
    if a.cmd in ("export", "reel"):
        a.brand = load_brand(a.brand_file)
        br = a.brand or {}
        a.tags_given = a.tags is not None
        a.handle = a.handle or br.get("handle")
        a.disclosure = br.get("disclosure", DISCLOSURE)
        if a.cmd == "export" and a.tags is None:
            a.tags = "#鬼故事,#靈異,#怪談,#漫畫,#創作"
        if a.cmd == "reel":
            reel_cfg = br.get("reel", {})
            if a.tags is None:
                a.tags = ",".join(reel_cfg.get("tags") or br.get("caption", {}).get("tags") or
                                  ["#鬼故事", "#靈異", "#怪談", "#創作"])
            a.accent = a.accent or br.get("colors", {}).get("accent") or "#B8322A"
            a.logo = a.logo or br.get("logo")
            a.end = a.end or reel_cfg.get("end_line") or "全篇漫畫在主頁"
    set_work(Path(a.work))
    global BOARD
    BOARD = a.board
    {"check": cmd_check, "styles": cmd_styles, "sheets": cmd_sheets, "choose": cmd_choose, "refs": cmd_refs,
     "lint": cmd_lint, "review": cmd_review, "repaint": cmd_repaint, "fill": cmd_fill, "tone": cmd_tone, "crop": cmd_crop,
     "plan": cmd_plan, "panels": cmd_panels, "contact": cmd_contact, "pages": cmd_pages, "status": cmd_status,
     "export": cmd_export, "reel": cmd_reel}[a.cmd](a)


if __name__ == "__main__":
    main()
