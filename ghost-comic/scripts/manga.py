"""Manga pages from a story board, on the local ComfyUI (Qwen Image 2.1). Run from the work folder.

    py -X utf8 manga.py check                         # ComfyUI up and the three model files present
    py -X utf8 manga.py styles --panel p2             # gate 1: the same panel in every style option
    py -X utf8 manga.py choose style=A
    py -X utf8 manga.py sheets                        # gate 2: 3 versions of every character and scene
    py -X utf8 manga.py choose me=1 fang=3 room=2 hall=3
    py -X utf8 manga.py refs                          # single-view, grayscale references from the picks
    py -X utf8 manga.py plan                          # gate 3: every page as a wireframe with the real lettering
    py -X utf8 manga.py panels                        # pass 1 (2 candidates each, "n" overrides)
    py -X utf8 manga.py contact p5 p10                # candidates side by side, for picking
    py -X utf8 manga.py choose p5=2 p10=1 ...
    py -X utf8 manga.py panels --pass 2               # panels that use other panels as references
    py -X utf8 manga.py pages                         # lettering, layout, PDF, overview

Files in the work folder: board.json (the storyboard, see references/board_format.md), choices.json
(written by `choose`), out/ (everything generated). Lettering is drawn here, vertical, never by the model.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy  # noqa: E402

WORK = Path.cwd()
OUT = WORK / "out"

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
PER_COL = {"speech": 8, "screen": 8, "phone": 8, "narration": 11, "title": 12, "tag": 8}

# ---------------------------------------------------------------------------
# board and choices
# ---------------------------------------------------------------------------


def set_work(path: Path) -> None:
    global WORK, OUT
    WORK = path.resolve()
    OUT = WORK / "out"


def load_board() -> dict:
    return json.loads((WORK / "board.json").read_text(encoding="utf-8"))


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


def job(kind: str, jid: str, prompt: str, refs: list[Path], w: int, h: int, n: int, seed: int, dest_dir: Path) -> list[str]:
    names = [comfy.upload(p) for p in refs]
    graph = comfy.build_graph(prompt, names, w, h, seed, n, f"ghost_comic/{kind}/{jid}")
    pid, images, wall, exec_s = comfy.run(graph)
    files = []
    for k, img in enumerate(images, 1):
        dest = dest_dir / f"{jid}_{k}.png"
        comfy.fetch(img, dest)
        files.append(dest.name)
    rec = {"kind": kind, "id": jid, "prompt_id": pid, "w": w, "h": h, "n": n, "seed": seed,
           "refs": [p.name for p in refs], "wall_s": wall, "exec_s": exec_s, "files": files}
    log(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return files


def consistency(board: dict, cell: dict) -> str:
    """Fixed scene-layout and character-scale sentences for whatever this panel shows (board["consistency"])."""
    c = board.get("consistency")
    if not c:
        return ""
    refs = cell.get("refs", [])
    out = [text for sid, text in c.get("scene", {}).items() if any(r in refs for r in c.get("scene_refs", {}).get(sid, [f"scene:{sid}"]))]
    out += [text for cid, text in c.get("scale", {}).items() if cid in refs]
    return " ".join(out)


def text_only(board: dict, cell: dict) -> str:
    """A panel prompt without reference images: '<imageN>' mentions dropped, the descriptions appended."""
    p = re.sub(r"\s*(?:from|as in|of|in) <image\d+>", "", cell["prompt"])
    p = re.sub(r"<image\d+>", "the reference", p)
    descs = []
    for r in cell.get("refs", []):
        if r.startswith("scene:"):
            descs.append(board["scenes"][r.split(":", 1)[1]])
        elif r in board.get("characters", {}):
            descs.append(board["characters"][r]["desc"])
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
        files = sorted((OUT / "sheets").glob(f"{sid}_[0-9].png"))
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
        crop = b.get("characters", {}).get(sid, {}).get("ref_crop", "left") if sid in b.get("characters", {}) else "none"
        if crop == "left":
            im = im.crop((0, 0, im.width // 2, im.height))
        elif crop == "right":
            im = im.crop((im.width // 2, 0, im.width, im.height))
        out = dest / f"{sid}.png"
        im.convert("RGB").save(out)
        ch["refs"][sid] = f"refs/{sid}.png"
    save_choices(ch)
    print(json.dumps(ch["refs"], ensure_ascii=False))


def ref_path(ref: str, ch: dict) -> Path:
    if ref.startswith("panel:"):
        return OUT / "panels" / ch["panels"][ref.split(":", 1)[1]]
    if ref.startswith("file:"):
        return OUT / ref.split(":", 1)[1]
    sid = "scene_" + ref.split(":", 1)[1] if ref.startswith("scene:") else ref
    if sid in ch["refs"]:
        return OUT / ch["refs"][sid]
    return OUT / ch["sheets"][sid]


def cmd_panels(a) -> None:
    b = load_board()
    ch = load_choices()
    style = style_text(b, ch, "panel")
    for _, cell, box in all_panels(b):
        if a.only and cell["id"] not in a.only:
            continue
        if not a.only and cell.get("pass", 1) != a.pass_:
            continue
        w, h = gen_size(box)
        refs = [ref_path(r, ch) for r in cell["refs"]]
        prompt = f"{style} {cell['prompt']} {consistency(b, cell)}".strip()
        job("panels", cell["id"], prompt, refs, w, h, cell.get("n", a.n), a.seed or random.randrange(2**31), OUT / "panels")


def cmd_contact(a) -> None:
    font = ImageFont.truetype(font_path("plain"), 22)
    files = []
    for jid in a.ids:
        for d in ("panels", "sheets", "styles"):
            files += sorted((OUT / d).glob(f"{jid}_[0-9].png"))
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


def draw_entry(page: Image.Image, entry: dict, cell_box, base: int) -> None:
    """One text item. The bubble shape says where the voice comes from: speech (round) is said in the room,
    screen / phone (square, double outline) comes through a device, narration is a plain box, title and tag
    are white on black."""
    kind = entry["kind"]
    size = round(base * entry.get("scale", 1.0) * {"title": 1.5, "tag": 1.25}.get(kind, 1.0))
    room = (cell_box[3] - cell_box[1]) - 28 - (size * 1.1 if kind != "speech" else size * 0.8)
    tile = text_block(entry, size, max_h=room / (1.22 if kind == "speech" else 1.0))
    if kind == "speech":  # the text rectangle must fit inside the ellipse: scale by about sqrt(2)
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
    elif kind in ("screen", "phone"):
        d.rounded_rectangle(box, radius=round(size * 0.35), fill="white", outline="black", width=3)
        g = 5
        d.rounded_rectangle([box[0] + g, box[1] + g, box[2] - g, box[3] - g], radius=round(size * 0.25), outline="black", width=1)
    elif kind in ("title", "tag"):
        d.rectangle(box, fill="black")
        white = Image.new("RGBA", tile.size, (255, 255, 255, 255))
        white.putalpha(tile.split()[3])
        page.paste(white, (bx + pad_x, by + pad_y), white)
        return
    else:
        d.rectangle(box, fill="white", outline="black", width=2)
    page.paste(tile, (bx + pad_x, by + pad_y), tile)


def draw_sfx(page: Image.Image, sfx: dict, cell_box) -> None:
    x0, y0, x1, y1 = cell_box
    size = round(min(x1 - x0, y1 - y0) * sfx.get("size", 0.25))
    font = ImageFont.truetype(font_path("bold"), size)
    tile = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((size // 2, size // 3), sfx["text"], font=font, fill="black", stroke_width=max(4, size // 12), stroke_fill="white")
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


def place_panel(page: Image.Image, cell: dict, box, ch: dict) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(page)
    if cell["id"] not in ch["panels"]:
        placeholder(page, cell, box)
        return
    src = Image.open(OUT / "panels" / ch["panels"][cell["id"]]).convert("L").convert("RGB")  # pages stay black and white
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


def render_page(b: dict, page: dict, pi: int, ch: dict, wireframe: bool = False) -> Image.Image:
    W, H = b["page"]
    im = Image.new("RGB", (W, H), "white")
    base = round(W / 40)
    for k, (cell, box) in enumerate(page_cells(b, page), 1):
        if "box" in cell:  # insets: white halo so they sit on top of the big panel
            ImageDraw.Draw(im).rectangle([box[0] - 8, box[1] - 8, box[2] + 8, box[3] + 8], fill="white")
        if wireframe:
            placeholder(im, cell, box, f"{k}. {cell.get('label', cell['id'])}")
        else:
            place_panel(im, cell, box, ch)
        for s in cell.get("sfx", []):
            draw_sfx(im, s, box)
        for e in cell.get("text", []):
            draw_entry(im, e, box, base)
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


def cmd_plan(a) -> None:
    """Gate 3: every page as a wireframe, each panel labelled in reading order, with the real lettering."""
    b = load_board()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = [render_page(b, page, pi, {"panels": {}}, wireframe=True) for pi, page in enumerate(b["pages"], 1)]
    spread(pages, 4, 1000, b.get("direction", "rtl") == "rtl").save(OUT / "plan.png")
    print(OUT / "plan.png")


def cmd_pages(a) -> None:
    b = load_board()
    ch = load_choices()
    dest = OUT / "pages"
    dest.mkdir(parents=True, exist_ok=True)
    pages = []
    for pi, page in enumerate(b["pages"], 1):
        if a.pages and pi not in a.pages:
            continue
        im = render_page(b, page, pi, ch)
        p = dest / f"page_{pi:02d}.png"
        im.save(p)
        pages.append(im)
        print(p)
    if a.pages:
        return
    pages[0].save(OUT / "comic.pdf", save_all=True, append_images=pages[1:], resolution=150)
    spread(pages, len(pages), 850, b.get("direction", "rtl") == "rtl").save(OUT / "overview.jpg", quality=85)
    print(OUT / "comic.pdf", OUT / "overview.jpg")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=".", help="work folder with board.json (default: current folder)")
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
    a = ap.parse_args()
    set_work(Path(a.work))
    {"check": cmd_check, "styles": cmd_styles, "sheets": cmd_sheets, "choose": cmd_choose, "refs": cmd_refs,
     "plan": cmd_plan, "panels": cmd_panels, "contact": cmd_contact, "pages": cmd_pages}[a.cmd](a)


if __name__ == "__main__":
    main()
