"""ghost-comic-v2: the 水墨淡彩 style on top of ghost-comic's manga.py.

Run from the comic's work folder (the one with board.json), like manga.py:

  py -X utf8 ink_tint.py apply          put the style into board.json (and choices.json), colour on, style said last
  py -X utf8 ink_tint.py tint [ids]     redraw each picked ink sheet with faint colour; the picks then point at them
  py -X utf8 ink_tint.py check          what in board.json still fights the style (no GPU)

Why each step exists (the style test of 2026-11-21, 〈卡丁車的白色安全帽〉):
- On a 1,200 to 1,800 character panel prompt, Qwen Image 2.1 dropped a style given only at the start; the same
  sentence again at the end brought the ink back. `apply` appends it to every panel prompt.
- Written as words, "ink wash with light colour" turned into soft watercolour fashion illustration. The colour has
  to be added to a picture that already has the ink: `tint` edits the picked ink sheet, and panels drawn against the
  tinted sheets came out ink and tint in one pass.
- The ghost is not tinted: she stays ink grey, the one colourless figure.
Standard library plus ghost-comic's comfy.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

V1 = Path(__file__).resolve().parents[2] / "ghost-comic" / "scripts"
sys.path.insert(0, str(V1))
import comfy  # noqa: E402

KEY = "ink_tint"
INK = ("Chinese ink wash painting with brush and ink: varied brush strokes, dry brush texture, grey ink gradations on "
       "rice paper.")
TINT = (" Bold black brush lines and grey ink washes exactly as in a monochrome ink painting, with only a few faint "
        "transparent tints of colour laid over the ink on skin, lips and a few small details; not a watercolour "
        "illustration.")
STYLE = {
    "name": "水墨淡彩",
    # sheets are drawn in plain ink and tinted afterwards (`tint`); panels are drawn ink and tint together
    # rough dry brush: smooth sheets made the indoor panels drawn from them read as fine-line watercolour illustration
    # (vet_night_xray, 2026-11-21)
    "sheet": f"Character design reference sheet as a {INK[0].lower()}{INK[1:]} Rough, loose dry-brush strokes and "
             f"broken ink edges, like a sketch with a calligraphy brush, not clean line art. Almost no colour. Plain "
             f"off-white rice paper background.",
    "panel": f"Comic panel as a {INK[0].lower()}{INK[1:]}{TINT} Night scenes are dark ink washes with the faces left light.",
}
END = "Drawn entirely in this style: "
# "flat black" is not here: 〈卡丁車〉's reveal light said it and still came out as dark ink wash
FIGHTS = re.compile(r"\b(line art|line-art|screentone|halftone|manga|cel shading|clean white)\b", re.I)

KEEP = ("Redraw <image1> keeping its exact Chinese ink wash brushwork: the same bold black brush strokes, dry brush "
        "texture, grey ink washes on off-white rice paper, the same composition")
ADD = ("Add only faint transparent tints of colour over the ink on {where}; everything else stays ink grey exactly as in "
       "<image1>. Both views of the character get identical colours. Not a watercolour illustration. No text.")
# "both views identical": the narrator's jeans came out dark grey in front and pale blue in three-quarter view
# (vet_night_xray, 2026-11-21)


def load(name: str) -> dict:
    p = Path(name)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(name: str, data: dict) -> None:
    Path(name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def cells(b: dict):
    for pg in b.get("pages", []):
        for row in pg.get("rows", []):
            yield from row.get("cells", [])


def apply() -> None:
    b = load("board.json")
    if not b:
        raise SystemExit("no board.json here: run from the comic's work folder")
    b.setdefault("style_options", {})[KEY] = STYLE
    b["style"] = KEY
    b["colour"] = True  # manga.py keeps refs, panels and pages in colour
    b["mono"] = False
    n = 0
    for c in cells(b):
        p = c.get("prompt", "")
        if END not in p:
            c["prompt"] = f"{p} {END}{INK}{TINT}".strip()
            n += 1
    save("board.json", b)
    ch = load("choices.json")
    ch["style"] = KEY
    for k in ("sheets", "refs", "panels"):
        ch.setdefault(k, {})
    save("choices.json", ch)
    print(f"board.json: style {KEY}, colour on, the style said last in {n} more panel prompts")
    check()


def check() -> int:
    """Words that pull the picture back to manga line art. Not errors: a ghost-comic board starts full of them."""
    b = load("board.json")
    hits = []
    for name, text in [(f"lights.{k}", v) for k, v in b.get("lights", {}).items()] + \
                      [(f"scenes.{k}", v) for k, v in b.get("scenes", {}).items()] + \
                      [(c["id"], c.get("prompt", "").split(END)[0]) for c in cells(b)]:
        found = sorted({m.group(0).lower() for m in FIGHTS.finditer(text)})
        if found:
            hits.append(f"  {name}: {', '.join(found)}")
    if b.get("style") != KEY:
        hits.insert(0, f"  style is {b.get('style')!r}, not {KEY!r}: run `apply`")
    if not b.get("colour"):
        hits.insert(0, "  colour is off: pages will be greyscaled")
    print("fights the ink style:" if hits else "nothing in board.json fights the ink style")
    for h in hits:
        print(h)
    return len(hits)


def tint(only: list[str]) -> None:
    b = load("board.json")
    ch = load("choices.json")
    chars, scenes = b.get("characters", {}), b.get("scenes", {})
    out = Path("out/sheets")
    for sid, path in list(ch.get("sheets", {}).items()):
        cid = sid.removeprefix("scene_")
        if only and sid not in only and cid not in only:
            continue
        if "_tint" in Path(path).stem:
            print(f"{sid}: already tinted ({path})")
            continue
        c = chars.get(sid)
        if c and c.get("ghost") and not c.get("tint"):
            print(f"{sid}: the ghost stays ink grey (give her a \"tint\" to colour her anyway)")
            continue
        if c:
            middle = (f"the same person in the same poses, the same clothes, hair and face; "
                      f"{c.get('desc', '')}".rstrip())
            where = c.get("tint") or "the skin, lips and the small details of the clothes"
        elif cid in scenes:
            middle = "the same place, nobody in it"
            where = (b.get("scene_tint", {}) or {}).get(cid) or "the light sources and one or two objects"
        else:
            continue
        src = Path("out") / path
        dest = out / f"{Path(path).stem}_tint.png"
        if not dest.exists():
            name = comfy.upload(src)
            prompt = f"{KEEP}, {middle}. {ADD.format(where=where)}"
            g = comfy.build_graph(prompt, [name], 1536, 1024, 20261121, 1, f"ghost_comic/sheets/{dest.stem}")
            _, imgs, wall, ex = comfy.run(g)
            comfy.fetch(imgs[0], dest)
            print(f"{sid}: {dest.name} ({ex or wall:.0f} s)", flush=True)
        ch["sheets"][sid] = f"sheets/{dest.name}"
        ch.get("refs", {}).pop(sid, None)
    save("choices.json", ch)
    print("picks now point at the tinted sheets; run `manga.py refs` next")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("apply", "tint", "check"):
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "apply":
        apply()
    elif cmd == "check":
        check()
    else:
        tint(sys.argv[2:])


if __name__ == "__main__":
    main()
