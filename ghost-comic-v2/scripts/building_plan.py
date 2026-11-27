"""ghost-comic-v2: the floor plan of a whole location, to scale, drawn before any scene picture (no GPU).

  py -X utf8 building_plan.py plan.json [plan.png]                    draw it and check every camera
  py -X utf8 building_plan.py jobs plan.json jobs.json [--only A,D]   the empty-room master pictures, for ghost-film's fresh_draw.py
  py -X utf8 building_plan.py panels                                   from the comic's work folder: every board cell with a `camera`
                                                                       becomes a crop of its master and a same-framing edit job
  py -X utf8 building_plan.py pick plan.json D candidate.png master.png   keep a candidate as that camera's master (mirrored if the camera says so)

One drawing shows how the rooms connect, and every scene picture and panel is checked against it. Draw the entrance at
the TOP of the page: someone inside facing it then has the page's right on their right.

spec (metres; x to the right, y DOWN the page):
{"title": "...", "subtitle": "...", "px_per_m": 92, "origin": [x, y], "size": [1500, 2900], "legend_y": 1760,
 "rooms":   [{"rect": [x0,y0,x1,y1], "label": "候診區", "fill": [236,232,222]}],               floors, walls drawn around them
 "things":  [{"rect": [x0,y0,x1,y1], "label": "櫃台", "fill": [190,180,165], "font": 20}],     furniture
 "openings":[{"rect": [x0,y0,x1,y1], "kind": "glass|door|window|gap", "label": "玻璃門", "label_at": [x,y]}],
 "lamps":   [{"at": [x,y], "color": [255,230,120]}],
 "cameras": [{"id": "A", "at": [x,y], "look": [x,y], "fov": 90, "len": 3.0, "wedge": false, "color": [30,110,60],
              "sees": {"left": ["左長椅"], "right": ["櫃台"]},      checked on every run: side AND inside the field of view
              "location": "lobby", "view": "Camera ... what is on the left, ahead and on the right of the FRAME.",
              "mirror": true}],   a reverse angle: `view` describes the picture BEFORE it is mirrored (see SKILL.md)
 "locations": {"lobby": {"bible": "the room's fixed parts, one text block, the same in every picture"}},
 "style": "optional text said last in every master (default: ink_tint's style sentence)",
 "master_size": [720, 1280],
 "legend":  {"fixed": ["..."], "cameras": ["A = ..."]}}
A label in `sees` is matched on the first line of a thing's or opening's label. The check covers side and angle only: it
does NOT know about walls or distance, and a camera without `sees` is not checked (a run lists them).
Standard library plus Pillow; `panels` also uses ghost-comic's manga.py."""
import json
import math
import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT, FONT_B = "C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjhbd.ttc"
KIND = {"glass": (70, 120, 200), "door": (150, 110, 70), "window": (120, 170, 220), "gap": (246, 243, 236)}


def draw(spec: dict) -> Image.Image:
    W, H = spec.get("size", [1500, 1700])
    s = spec.get("px_per_m", 100)
    ox, oy = spec.get("origin", [200, 200])
    P = lambda x, y: (ox + x * s, oy + y * s)
    im = Image.new("RGB", (W, H), (246, 243, 236))
    d = ImageDraw.Draw(im, "RGBA")
    F = lambda n, b=False: ImageFont.truetype(FONT_B if b else FONT, n)
    ink = (30, 30, 30)
    d.text((60, 36), spec.get("title", ""), font=F(40, True), fill=ink)
    d.text((60, 92), spec.get("subtitle", ""), font=F(24), fill=(90, 90, 90))
    # metre grid
    x_end = int(ox + 14 * s)
    for m in range(-6, 16):
        x, _ = P(m, 0)
        d.line([x, oy - 6 * s, x, oy + 14 * s], fill=(0, 0, 0, 18), width=1)
        _, y = P(0, m)
        d.line([ox - 6 * s, y, x_end, y], fill=(0, 0, 0, 18), width=1)
    for r in spec.get("rooms", []):
        x0, y0, x1, y1 = r["rect"]
        a, b = P(x0, y0), P(x1, y1)
        d.rectangle([*a, *b], fill=tuple(r.get("fill", (236, 232, 222))), outline=ink, width=10)
        if r.get("label"):
            d.text(((a[0] + b[0]) / 2, a[1] + 26), r["label"], font=F(26, True), fill=(80, 80, 80), anchor="mm")
    for t in spec.get("things", []):
        x0, y0, x1, y1 = t["rect"]
        a, b = P(x0, y0), P(x1, y1)
        d.rectangle([*a, *b], fill=tuple(t.get("fill", (190, 180, 165))), outline=ink, width=3)
        if t.get("label"):
            d.multiline_text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), t["label"], font=F(t.get("font", 20)), fill=ink,
                             anchor="mm", align="center")
    for o in spec.get("openings", []):
        x0, y0, x1, y1 = o["rect"]
        a, b = P(x0, y0), P(x1, y1)
        pad = 7
        d.rectangle([a[0] - pad, a[1] - pad, b[0] + pad, b[1] + pad], fill=KIND.get(o.get("kind", "door"), KIND["door"]))
        if o.get("label"):
            lx, ly = P(*o["label_at"]) if o.get("label_at") else (b[0] + 14, (a[1] + b[1]) / 2)
            d.multiline_text((lx, ly), o["label"], font=F(20), fill=ink, anchor="lm" if not o.get("label_at") else "mm", align="center")
    for l in spec.get("lamps", []):
        x, y = P(*l["at"])
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=tuple(l.get("color", (255, 230, 120))), outline=ink, width=3)
    for c in spec.get("cameras", []):
        x, y = P(*c["at"])
        lx, ly = P(*c["look"])
        a = math.atan2(ly - y, lx - x)
        L = c.get("len", 3.0) * s
        half = math.radians(c.get("fov", 90) / 2)
        col = tuple(c.get("color", (30, 110, 60)))
        pts = [(x, y), (x + L * math.cos(a - half), y + L * math.sin(a - half)), (x + L * math.cos(a + half), y + L * math.sin(a + half))]
        if c.get("wedge", True):
            d.polygon(pts, fill=col + (45,), outline=col + (200,))
        else:   # a plain arrow: readable when many cameras share one room
            ex, ey = x + 0.6 * L * math.cos(a), y + 0.6 * L * math.sin(a)
            d.line([x, y, ex, ey], fill=col, width=6)
            for sgn in (2.6, -2.6):
                d.line([ex, ey, ex + 24 * math.cos(a + sgn), ey + 24 * math.sin(a + sgn)], fill=col, width=6)
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=col)
        d.text((x, y), c["id"], font=F(18, True), fill=(255, 255, 255), anchor="mm")
    # scale bar
    bx, by = P(-2.6, 0.0)
    d.line([bx, by, bx + s, by], fill=ink, width=5)
    d.text((bx + s / 2, by + 22), "1 公尺", font=F(20), fill=ink, anchor="mm")
    y = spec.get("legend_y", 1300)
    lg = spec.get("legend", {})
    for title, lines in (("固定不變的東西（每張圖、每個動畫都要一樣）", ["• " + t for t in lg.get("fixed", [])]), ("鏡頭看到什麼", lg.get("cameras", []))):
        if not lines:
            continue
        d.text((60, y), title, font=F(30, True), fill=ink)
        y += 46
        for t in lines:
            for i, line in enumerate(textwrap.wrap(t, 52) or [""]):
                d.text((60 if i == 0 else 90, y), line, font=F(25), fill=ink)
                y += 36
            y += 6
        y += 14
    return im


def check_sides(spec: dict) -> list[str]:
    """Each camera's `sees` against the geometry: the right side of the frame, and inside the field of view. The page has
    y going down, so a positive cross product is the viewer's right. Plan v4 of 〈動物醫院〉 was a mirror image of every
    picture, and two cameras were asked to film a bench they could not see; neither shows by eye."""
    first = lambda label: label.split("\n")[0]
    centre = {}
    for t in spec.get("things", []) + spec.get("openings", []):
        if t.get("label"):
            x0, y0, x1, y1 = t["rect"]
            centre[first(t["label"])] = ((x0 + x1) / 2, (y0 + y1) / 2)
    bad = []
    for c in spec.get("cameras", []):
        fx, fy = c["look"][0] - c["at"][0], c["look"][1] - c["at"][1]
        for side, labels in c.get("sees", {}).items():
            for lab in labels:
                if first(lab) not in centre:
                    bad.append(f"camera {c['id']}: no thing or opening is labelled {first(lab)!r}")
                    continue
                vx, vy = centre[first(lab)][0] - c["at"][0], centre[first(lab)][1] - c["at"][1]
                angle = math.degrees(math.atan2(fx * vy - fy * vx, fx * vx + fy * vy))
                got = "right" if angle > 0 else "left"
                if got != side:
                    bad.append(f"camera {c['id']}: {first(lab)} should be on the {side}, the plan puts it on the {got}")
                if abs(angle) > c.get("fov", 90) / 2:
                    bad.append(f"camera {c['id']}: {first(lab)} is {abs(angle):.0f} degrees off its axis, outside a "
                               f"{c.get('fov', 90)} degree view")
    return bad


def master_jobs(spec: dict, only=None) -> dict:
    """One empty-room master per camera that has a `view`: the location's bible, the view, the style said last."""
    style = spec.get("style")
    if style is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import ink_tint
        style = f"{ink_tint.END}{ink_tint.INK}{ink_tint.TINT}"
    jobs = {}
    for c in spec.get("cameras", []):
        if not c.get("view") or (only and c["id"] not in only):
            continue
        bible = spec["locations"][c["location"]]["bible"]
        jobs[c["id"]] = {"prompt": f"{bible} {c['view']} {style}"}
    return {"out": "plan/masters", "n": 4, "size": spec.get("master_size", [720, 1280]), "jobs": jobs}


def panel_jobs(picked="plan/picked") -> list[str]:
    """Every board cell with a `camera`: crop that camera's master to the cell's shape (never stretched) into
    plan/picked/<camera>_<panel>.png, and write one edit_stills.py job file per size, because a job file has one size.
    A cell may set "camera_crop": [centre x, centre y, zoom]. The candidates are <panel>e_1.png, <panel>e_2.png in out/panels."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ghost-comic" / "scripts"))
    import manga
    manga.set_work(Path("."))
    board, ch = manga.load_board(), manga.load_choices()
    by_size = {}
    for _, c, box in manga.all_panels(board):
        cam = c.get("camera")
        if not cam:
            continue
        W, H = manga.gen_size(box)
        master = Path(picked) / f"{cam}_master.png"
        if not master.exists():
            raise SystemExit(f"{c['id']}: no master for camera {cam}: {master}")
        im = Image.open(master).convert("RGB")
        cx, cy, zoom = c.get("camera_crop", [.5, .5, 1.0])
        bw, bh = im.width / zoom, im.width / zoom * H / W
        if bh > im.height / zoom:
            bh, bw = im.height / zoom, im.height / zoom * W / H
        x0 = min(max(im.width * cx - bw / 2, 0), im.width - bw)
        y0 = min(max(im.height * cy - bh / 2, 0), im.height - bh)
        src = Path(picked) / f"{cam}_{c['id']}.png"
        im.crop((round(x0), round(y0), round(x0 + bw), round(y0 + bh))).resize((W, H), Image.LANCZOS).save(src)
        refs, renum = [], {}
        for i, r in enumerate(c.get("refs", []), 1):      # the master is <image1> now, so the panel's own refs move up
            if r.startswith("scene:"):
                continue
            refs.append("out/" + r[5:] if r.startswith("file:") else "out/" + ch["refs"][r])
            renum[i] = len(refs) + 1
        prompt = re.sub(r"<image(\d+)>", lambda m: f"<image{renum[int(m.group(1))]}>", c["prompt"])
        job = {"src": src.as_posix(), "refs": refs,
               "change": "Add to this empty room what follows, and keep the room, its furniture and the camera exactly as they are. " + prompt}
        by_size.setdefault((W, H), {})[f"{c['id']}e"] = job
    out = []
    for (W, H), jobs in by_size.items():
        f = Path("plan") / f"panel_jobs_{W}x{H}.json"
        f.write_text(json.dumps({"out": "out/panels", "n": 2, "size": [W, H], "jobs": jobs}, ensure_ascii=False, indent=1), encoding="utf-8")
        out.append(f.as_posix())
    return out


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "jobs":
        spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        bad = check_sides(spec)
        if bad:
            raise SystemExit("fix the plan before drawing any scene:\n" + "\n".join(bad))
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
        jobs = master_jobs(spec, only)
        Path(sys.argv[3]).write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", sys.argv[3], len(jobs["jobs"]), "masters:", ", ".join(jobs["jobs"]))
        return
    if sys.argv[1] == "panels":
        for f in panel_jobs():
            print("wrote", f)
        return
    if sys.argv[1] == "pick":
        spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        cam = next(c for c in spec["cameras"] if c["id"] == sys.argv[3])
        im = Image.open(sys.argv[4]).convert("RGB")
        if cam.get("mirror"):
            im = ImageOps.mirror(im)
        Path(sys.argv[5]).parent.mkdir(parents=True, exist_ok=True)
        im.save(sys.argv[5])
        print("master", cam["id"], "mirrored" if cam.get("mirror") else "as drawn", "->", sys.argv[5])
        return
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    bad = check_sides(spec)
    for b in bad or ["sides ok: every camera sees its things on its side and inside its view"]:
        print(b)
    unchecked = [c["id"] for c in spec.get("cameras", []) if not c.get("sees")]
    if unchecked:
        print("not checked (no `sees`):", ", ".join(unchecked))
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(sys.argv[1]).with_suffix(".png")
    draw(spec).save(out)
    print("wrote", out)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
