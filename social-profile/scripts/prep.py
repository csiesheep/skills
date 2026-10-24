"""Get a profile update ready before opening a browser: the avatar files every site accepts, a check that
nothing important sits in the corners the sites crop away, and every bio counted against its site's limit.

    py -X utf8 prep.py profile.json            # writes avatar_1024.png, avatar_800.png beside profile.json
    py -X utf8 prep.py profile.json --only instagram,tiktok

Wide pictures are optional per site: "facebook": {"cover": "C:/path/cover.png"} writes cover_1640x624.png,
"youtube": {"banner": "C:/path/banner.png", "links": [["全部遊戲", "https://..."]]} writes
banner_2560x1440.png. Both are cropped from the centre to the site's shape; look at the result.

profile.json (see assets/example_profile.json):
    {"image": "C:/path/logo.png",
     "sites": {"instagram": {"handle": "gui.chang.shi", "bio": "line one\\nline two"},
               "tiktok": {"handle": "guichangshi", "name": "鬼唱詩"}, ...}}

Exit status 1 when a bio is over its limit or the image is missing, so a caller can stop there.
Standard library plus Pillow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat

# Lowest figure where sources disagree, so a bio that passes here fits on the site. "seen" = read off the
# site's own counter or dialog on 2026-10-18; "reported" = third-party guides only.
SITES = {
    "instagram": {"bio": 150, "seen": "bio", "edit": "https://www.instagram.com/accounts/edit/",
                  "name": "the display name is changed in Accounts Center, not on the web edit page; "
                          "two changes per 14 days (reported)"},
    "threads": {"bio": 150, "seen": "", "edit": "https://www.threads.com/@{handle}",
                "name": "a Name row is in Edit profile (untested); it keeps its own photo and bio"},
    "facebook": {"bio": 255, "seen": "bio", "edit": "https://www.facebook.com/{handle}",
                 "name": "Page name changes go to Facebook's review"},
    "youtube": {"bio": 1000, "seen": "bio, name", "edit": "https://www.youtube.com/@{handle} -> Customize channel",
                "name": "the name can change twice in 14 days (Studio says so); nothing is live until Publish"},
    "tiktok": {"bio": 80, "seen": "bio, name", "edit": "https://www.tiktok.com/@{handle}",
               "name": "the nickname can change once every 7 days; the save asks to confirm"},
    "pinterest": {"bio": 160, "seen": "", "edit": "https://www.pinterest.com/settings/",
                  "name": "the photo saves on upload; Name and About need Save at the bottom"},
}
SIZES = {"avatar_1024.png": 1024, "avatar_800.png": 800}  # 800 for YouTube (min 98, max 4 MB), 1024 for the rest
YOUTUBE_MAX_BYTES = 4 * 1024 * 1024

# Wide pictures: (site, profile key) -> output size, smallest the site takes, byte limit, what to keep clear.
# Seen 2026-10-21/22: Facebook's cover editor and YouTube Studio's "Customize banner art" dialog.
WIDE = {
    ("facebook", "cover"): {"file": "cover_1640x624.png", "size": (1640, 624), "min": (820, 312),
                            "max_bytes": None,
                            "safe": "phones crop the left and right sides: keep text off the outer edges"},
    ("youtube", "banner"): {"file": "banner_2560x1440.png", "size": (2560, 1440), "min": (2048, 1152),
                            "max_bytes": 6 * 1024 * 1024,
                            "safe": "every device shows only the centre 1546 x 423: name, URL and face go there"},
}


def border_colour(im: Image.Image) -> tuple[int, int, int]:
    """Median colour of the outermost 2% ring: the background a logo sits on."""
    w, h = im.size
    k = max(2, round(min(w, h) * 0.02))
    ring = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(ring)
    d.rectangle([0, 0, w - 1, h - 1], fill=255)
    d.rectangle([k, k, w - 1 - k, h - 1 - k], fill=0)
    return tuple(int(v) for v in ImageStat.Stat(im, ring).median[:3])


def square(im: Image.Image) -> tuple[Image.Image, str | None]:
    """Pad a non-square picture onto its own background colour, so nothing of it is cut off."""
    w, h = im.size
    if w == h:
        return im, None
    s = max(w, h)
    canvas = Image.new("RGB", (s, s), border_colour(im))
    canvas.paste(im, ((s - w) // 2, (s - h) // 2))
    return canvas, f"not square ({w}x{h}): padded to {s}x{s} with its border colour; a square original looks better"


def corner_content(im: Image.Image) -> float:
    """Share of the picture's content (pixels unlike the background) lying outside the inscribed circle,
    which is all the sites show."""
    small = im.resize((256, 256))
    bg = border_colour(small)
    px = small.load()
    inside = outside = 0
    # the inscribed circle itself plus a pixel: a round logo filling it exactly (the transparent circle avatar)
    # must not be flagged, a margin inside it did flag it at 5%
    c, r = 127.5, 129.0
    for y in range(256):
        for x in range(256):
            p = px[x, y]
            if sum(abs(p[i] - bg[i]) for i in range(3)) <= 60:
                continue
            if (x - c) ** 2 + (y - c) ** 2 > r * r:
                outside += 1
            else:
                inside += 1
    total = inside + outside
    return outside / total if total else 0.0


def prepare_image(path: Path, out_dir: Path) -> tuple[list[str], list[str]]:
    notes, problems = [], []
    if not path.exists():
        return notes, [f"image not found: {path}"]
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (255, 255, 255))
        flat.paste(rgba, (0, 0), rgba)
        im = flat
        notes.append("transparency flattened onto white (the sites would do it anyway, some onto black)")
    im = im.convert("RGB")
    im, msg = square(im)
    if msg:
        notes.append(msg)
    if im.width < 800:
        notes.append(f"only {im.width} px wide: it will be enlarged; 1024 px or more looks sharper")
    share = corner_content(im)
    if share > 0.01:
        notes.append(f"{share:.0%} of the picture's content lies outside the circle every site crops to; "
                     "move it toward the centre")
    for name, size in SIZES.items():
        dest = out_dir / name
        im.resize((size, size), Image.LANCZOS).save(dest, optimize=True)
        notes.append(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")
        if size == 800 and dest.stat().st_size > YOUTUBE_MAX_BYTES:
            problems.append(f"{dest} is over YouTube's 4 MB")
    return notes, problems


def prepare_wide(src: Path, spec: dict, out_dir: Path) -> tuple[list[str], list[str]]:
    """Crop a wide picture from the centre to the site's shape and size; report how much was cut."""
    notes, problems = [], []
    if not src.exists():
        return notes, [f"picture not found: {src}"]
    im = Image.open(src).convert("RGB")
    tw, th = spec["size"]
    w, h = im.size
    if w * th > h * tw:  # wider than the site's shape: cut the sides
        cw, ch = round(h * tw / th), h
    else:                # taller: cut top and bottom
        cw, ch = w, round(w * th / tw)
    left, top = (w - cw) // 2, (h - ch) // 2
    im = im.crop((left, top, left + cw, top + ch))
    if cw < spec["min"][0]:
        problems.append(f"{src.name} gives only {cw}x{ch} after cropping; the site wants at least "
                        f"{spec['min'][0]}x{spec['min'][1]}")
    dest = out_dir / spec["file"]
    im.resize((tw, th), Image.LANCZOS).save(dest, optimize=True)
    notes.append(f"wrote {dest} ({dest.stat().st_size // 1024} KB); "
                 f"{1 - cw * ch / (w * h):.0%} of the {w}x{h} original cropped away from the edges")
    notes.append(spec["safe"])
    if spec["max_bytes"] and dest.stat().st_size > spec["max_bytes"]:
        problems.append(f"{dest} is over {spec['max_bytes'] // (1024 * 1024)} MB")
    return notes, problems


def count(text: str) -> int:
    """Characters as the sites count them: line breaks count, as on Instagram's counter (65/150 for 62
    characters on four lines)."""
    return len(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile", help="profile.json")
    ap.add_argument("--only", type=lambda v: v.split(","), default=None, help="comma-separated site keys")
    a = ap.parse_args()
    pf = Path(a.profile).resolve()
    prof = json.loads(pf.read_text(encoding="utf-8"))
    sites = prof.get("sites", {})
    unknown = [s for s in sites if s not in SITES]
    if unknown:
        raise SystemExit(f"unknown site keys {unknown}; use {sorted(SITES)}")
    chosen = [s for s in sites if a.only is None or s in a.only]

    problems: list[str] = []
    if prof.get("image"):
        notes, probs = prepare_image(Path(prof["image"]), pf.parent)
        print("IMAGE")
        for n in notes:
            print("  " + n)
        problems += probs
    else:
        print("IMAGE  none given: photos stay as they are")

    print("\nSITES")
    for s in chosen:
        cfg, lim = sites[s], SITES[s]
        handle = cfg.get("handle", "")
        changes = (["photo"] if prof.get("image") and cfg.get("photo", True) else []) + \
                  [f for f in ("name", "bio", "cover", "banner", "links") if cfg.get(f)]
        print(f"- {s}: account {handle or '(no handle: cannot check the account, add one)'}; "
              f"change {', '.join(changes) or 'nothing'}")
        print(f"    open {lim['edit'].format(handle=handle)}")
        if cfg.get("name"):
            print(f"    name \"{cfg['name']}\": {lim['name']}")
        if cfg.get("bio"):
            n = count(cfg["bio"])
            seen = "seen on the site" if "bio" in lim["seen"] else "reported"
            flag = "OVER" if n > lim["bio"] else "ok"
            print(f"    bio {n}/{lim['bio']} ({seen}) {flag}; {cfg['bio'].count(chr(10)) + 1} line(s)")
            if n > lim["bio"]:
                problems.append(f"{s} bio is {n} characters, limit {lim['bio']}")
            if cfg["bio"] != cfg["bio"].strip():
                print("    bio starts or ends with spaces or a line break; strip it")
        for (site, key), spec in WIDE.items():
            if site == s and cfg.get(key):
                notes, probs = prepare_wide(Path(cfg[key]), spec, pf.parent)
                for n in notes:
                    print(f"    {key}: {n}")
                problems += probs
        for title, url in cfg.get("links", []):
            print(f"    link \"{title}\" -> {url}")
            if not url.startswith(("http://", "https://")):
                problems.append(f"{s} link {url!r} needs http:// or https://")
        if not handle:
            problems.append(f"{s} has no handle to check the signed-in account against")

    if problems:
        print("\nFIX FIRST")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\nready")


if __name__ == "__main__":
    main()
