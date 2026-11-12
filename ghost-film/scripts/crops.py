"""9:16 first frames for H3 from picked stills: src/<name>.png (720x1280 at least) and src/_crops.jpg to check them.
cd <story>/film/reel && py -X utf8 <skill>/scripts/crops.py '{"f2": ["../reel_stills/out/panels/f2_1.png", 0.5, 0.5, 1.0]}'
Each entry: [still, centre x, centre y (0..1), zoom (>1 tighter)]. Entries are kept in crops.json, so later calls only add or
change names. Prefer a portrait still (stills_both.py) at zoom 1: a 9:16 cut from a landscape still loses the people."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path.cwd()
cfg = HERE / "crops.json"
CROPS = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
if len(sys.argv) > 1:
    CROPS.update(json.loads(sys.argv[1]))
cfg.write_text(json.dumps(CROPS, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE / "src").mkdir(exist_ok=True)
tiles = []
for name, (path, cx, cy, z) in CROPS.items():
    im = Image.open(HERE / path).convert("RGB")
    W, H = im.size
    bh = H / z; bw = bh * 9 / 16
    if bw > W / z:
        bw = W / z; bh = bw * 16 / 9
    x0 = min(max(W * cx - bw / 2, 0), W - bw); y0 = min(max(H * cy - bh / 2, 0), H - bh)
    c = im.crop((round(x0), round(y0), round(x0 + bw), round(y0 + bh)))
    if c.height < 1280:
        c = c.resize((720, 1280), Image.LANCZOS)
    c.save(HERE / "src" / f"{name}.png")
    t = c.resize((216, 384)); ImageDraw.Draw(t).text((6, 6), f"{name} {c.size}", fill="yellow"); tiles.append(t)
cols = 6; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (221 * cols + 5, 389 * rows + 5), "#333")
for k, t in enumerate(tiles):
    sheet.paste(t, (5 + (k % cols) * 221, 5 + (k // cols) * 389))
sheet.save(HERE / "src" / "_crops.jpg", quality=85)
print(len(CROPS), "crops")
