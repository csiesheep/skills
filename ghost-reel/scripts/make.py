"""Make a comic's Reel full from its shot list, in one command.

    py -X utf8 make.py <story folder> [--version v3|v1|v2] [--brand-file brand.json] [--music track] [--out dir]
                       [--reuse] [--check]

Reads `reels/shots.json` (draft.py writes a first one), renders the version, mixes music and sound effects, brings
the sound to -14 LUFS and writes, in the folder contract's place:

    reels/full_v3_cinema/full_v3_cinema.mp4          (v1: reels/full_v1_manga/full_v1_manga.mp4)
                        full_v3_cinema_cover.jpg     the frame at 1 s, for the Reel cover
                        full_v3_cinema_frames.jpg    a contact sheet, one frame every 1.5 s
                        full_v3_cinema_preview720.mp4  720p, under 10 MB: what Claude in Chrome can upload
                        full_v3_cinema_qc.txt        qc.py's report

The silent picture is kept in drafts/reels/_work/, so --reuse redoes only the sound after a sound-only edit.
--check only validates the shot list (panels exist, clips exist, nothing at or after the reveal opens the film).
A render takes about 8 to 11 minutes; run it in the background.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

NAMES = {"v1": "full_v1_manga", "v2": "full_v2_storytime", "v3": "full_v3_cinema"}


def check(S, R, version) -> list[str]:
    """Problems that would make the render fail or give the ending away."""
    ids = {c["id"] for _, c, _ in R.mg.all_panels(R.BOARD)}
    problems = []
    shots = {"v3": [(p, o) for p, _, _, o in S.V3], "v2": [(p, o) for p, _, o in S.V2],
             "v1": [(p, {}) for p, *_ in S.HOOK] + list(S.V1.items())}[version]
    for pid, o in shots:
        if pid != "TITLE" and pid not in ids:
            problems.append(f"{pid}: not on the board")
        if o.get("clip") and not Path(o["clip"]).exists():
            problems.append(f"{pid}: clip missing {o['clip']}")
    reveal_page, after = R.mg.reveal_point(R.BOARD)
    opening = [p for p, _ in shots[:2]] if version != "v1" else [p for p, *_ in S.HOOK]
    for pid in opening:
        if pid in after:
            problems.append(f"{pid} opens the film but is the reveal or after it (page {reveal_page})")
    return problems


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", help="the story folder, e.g. .../gui_chang_shi/stories/name_call")
    ap.add_argument("--version", choices=sorted(NAMES), default="v3")
    ap.add_argument("--brand-file", default=None, help="default: <stories>/../brand/brand.json")
    ap.add_argument("--music", default=None, help="default: the shot list's track for this version, in the brand's music folder")
    ap.add_argument("--out", default=None, help="default: reels/<full_v3_cinema> in the story folder")
    ap.add_argument("--reuse", action="store_true", help="keep the silent picture from the last render; redo sound only")
    ap.add_argument("--check", action="store_true", help="validate the shot list and stop")
    ap.add_argument("--cut", default=None, help="a V3 cut from shots.json's \"cuts\" (long, part1…): written to "
                                                "reels/full_v3_cinema_<cut>/")
    a = ap.parse_args()

    import reel as R
    import sfx as SFX
    import story
    import qc

    d = Path(a.story).resolve()
    bf = Path(a.brand_file) if a.brand_file else d.parent.parent / "brand" / "brand.json"
    brand = R.mg.load_brand(str(bf))
    if a.cut and a.version != "v3":
        print("--cut is for V3", file=sys.stderr)
        return 2
    S = story.load(d, brand, a.cut)
    R.setup(S, brand.get("name", "鬼唱詩"))
    problems = check(S, R, a.version)
    for p in problems:
        print("✗", p)
    if problems:
        return 1
    if a.check:
        print(f"{a.version}: shot list OK")
        return 0
    SFX.use_samples(bf.parent / "sfx")
    music = a.music or (str(bf.parent / "music" / S.MUSIC[a.version]) if S.MUSIC.get(a.version) else None)
    name = NAMES[a.version] + (f"_{a.cut}" if a.cut else "")
    out = Path(a.out) if a.out else d / "reels" / name
    out.mkdir(parents=True, exist_ok=True)
    mp4 = out / f"{name}.mp4"
    n, total = R.produce(a.version, d / "drafts" / "reels" / "_work" / (a.cut or "main"), mp4, out / f"{name}_frames.jpg",
                         music=music, reuse=a.reuse)
    ff = R.mg.ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", "1.0", "-i", str(mp4), "-frames:v", "1", "-q:v", "2",
                    str(out / f"{name}_cover.jpg")], check=True)
    # 720p at about 0.85 Mbps: an 82 s film comes to about 9 MB, under the 10 MB a Claude in Chrome upload takes
    audio_k = 96 if total < 120 else 64
    kbps = max(250, int(9.3 * 8 * 1024 / max(total, 1)) - audio_k)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(mp4), "-vf", "scale=720:1280:flags=lanczos",
                    "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-maxrate", f"{kbps * 2}k",
                    "-bufsize", f"{kbps * 2}k", "-c:a", "aac", "-b:a", f"{audio_k}k", "-movflags", "+faststart",
                    str(out / f"{name}_preview720.mp4")], check=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        qc.check(mp4)
    (out / f"{name}_qc.txt").write_bytes(buf.getvalue().encode("utf-8"))
    print(buf.getvalue().rstrip())
    prev = out / f"{name}_preview720.mp4"
    print(f"{a.version}: {n} frames, {total:.1f} s -> {mp4} ({mp4.stat().st_size / 1e6:.0f} MB); "
          f"preview {prev.stat().st_size / 1e6:.1f} MB; cover, frames and qc beside it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
