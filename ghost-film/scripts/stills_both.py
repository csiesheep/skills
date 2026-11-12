"""Every still in two shapes (owner, 2026-11-07: 「之後產生原圖時，同時產生直式跟橫式的圖。目前用橫式的圖，產生直式影片，人物會被切」).
The comic board lays panels out landscape or portrait as the page needs; a 9:16 reel cropped from a landscape panel cuts people
off and leaves dark bands top and bottom. This writes <film>/reel_stills/: the same cells, prompts and references, one cell per
9:16 page, so `film.py panels` there draws a true portrait version of every panel. Pass --wide to also write <film>/wide_stills/
(16:9 cells, for the landscape long video).

    cd <story>/film && py -X utf8 <skill>/scripts/stills_both.py [--only f1,f3] [--wide]
    cd reel_stills && py -X utf8 <skill>/scripts/film.py panels --only f1,f3
Then crops.py takes the portrait panel at zoom 1 with nothing cut off."""
import json, shutil, sys
from pathlib import Path

film = Path.cwd()
board = json.loads((film / "board.json").read_text(encoding="utf-8"))
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
cells = [c for pg in board["pages"] for r in pg["rows"] for c in r["cells"] if not only or c["id"] in only]
shapes = [("reel_stills", (1080, 1920), "Vertical 9:16 frame: compose for a phone screen, the people and the subject in the middle "
           "of the frame from head to toe where they fit, nothing important at the edges. ")]
if "--wide" in sys.argv:
    shapes.append(("wide_stills", (1920, 1080), "Wide 16:9 cinema frame. "))
for folder, page, lead in shapes:
    d = film / folder
    (d / "out").mkdir(parents=True, exist_ok=True)
    # file: references are relative to out/. Never copy panels/: the comic's stills share the portrait stills' names
    # (f1_1.png ...) and overwrote six of them in 幫阿公守夜. A board that refers to a picked panel gets it copied by name.
    for sub in ("cast", "sets", "refs", "sheets", "fx"):
        if (film / "out" / sub).exists():
            shutil.copytree(film / "out" / sub, d / "out" / sub, dirs_exist_ok=True)
    for c in cells:
        for r in c.get("refs", []):
            if r.startswith("file:panels/"):
                (d / "out" / "panels").mkdir(parents=True, exist_ok=True)
                shutil.copy2(film / "out" / r[5:], d / "out" / r[5:].replace("panels/", "panels/_ref_"))
    b = {k: v for k, v in board.items() if k != "pages"}
    b.update(page=list(page), margin=0, gutter=[0, 0])
    b["pages"] = [{"rows": [{"h": 1.0, "cells": [{**c, "w": 1.0, "text": [], "prompt": lead + c["prompt"],
                                                      "refs": [r.replace("file:panels/", "file:panels/_ref_") for r in c.get("refs", [])]}]}]}
                  for c in cells]
    (d / "board.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    ch = film / "choices.json"
    c0 = json.loads(ch.read_text(encoding="utf-8")) if ch.exists() else {"style": board.get("style", "F")}
    (d / "choices.json").write_text(json.dumps({"style": c0.get("style", "F"), "panels": {}, "sheets": c0.get("sheets", {}),
                                                "refs": c0.get("refs", {})}, ensure_ascii=False), encoding="utf-8")
    print(d, len(cells), "cells", page)
