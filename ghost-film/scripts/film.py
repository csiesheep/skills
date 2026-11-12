"""Run ghost-comic's manga.py commands for a film-still board: py -X utf8 film.py panels [--only f1,f2] (any manga.py command),
from the work folder (board.json, choices.json, out/). Two differences from ghost-comic: the uncensored Qwen Image 2.1 GGUF
draws the stills (uc.py), and pages keep their colour. FILM_FONT overrides the lettering font (default msjhl.ttc, the owner's
pick for film stills)."""
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uc  # noqa: F401,E402  (swaps qwen-image-2.1-UC-Q8_0.gguf into manga's graph)
import manga  # noqa: E402


def panel_source_colour(cell: dict, ch: dict) -> Image.Image:
    """manga.panel_source without the final greyscale: the same mirror and zoom, the film colour kept."""
    src = Image.open(manga.OUT / "panels" / ch["panels"][cell["id"]]).convert("RGB")
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
    return src


manga.panel_source = panel_source_colour


def compose_with_look(board: dict, ch: dict, cell: dict) -> str:
    """A cell's own `look` replaces the style prefix: daytime and flashback panels in a night story."""
    if not cell.get("look"):
        return _compose(board, ch, cell)
    parts = [cell["look"], cell["prompt"], manga.light_text(board, cell), manga.consistency(board, cell)]
    return " ".join(x.strip() for x in parts if x and x.strip())


_compose = manga.compose_prompt
manga.compose_prompt = compose_with_look
manga._FONT_NAMES["serif"] = [os.environ.get("FILM_FONT", "msjhl.ttc")] + manga._FONT_NAMES["serif"]
manga.main()
