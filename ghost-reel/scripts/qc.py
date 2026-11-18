"""Automatic checks on a finished Reel: length, size, dead picture, dead sound, loudness, opening frame, and the seams
at the cuts (sound moving over 10 dB, brightness over 20: a list of where to listen and look first).

    py -X utf8 qc.py [--light] <video.mp4> [...]      --light also lists the cuts where the brightness jumps
"""
import subprocess, sys, wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()


def frames(path, fps=4, w=135, h=240):
    cmd = [FF, "-loglevel", "error", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def audio(path):
    tmp = Path(str(path) + ".qc.wav")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000", str(tmp)], check=True)
    with wave.open(str(tmp)) as wv:
        a = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
    tmp.unlink()
    return a


def runs(mask, step):
    out, start = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        if not m and start is not None:
            out.append((start * step, (i - start) * step)); start = None
    return out


SEAM_FPS, SEAM_WIN, SEAM_GUARD = 12, 0.4, 0.03
SOUND_NOTICE, LIGHT_NOTICE = 10.0, 20.0


def cut_times(path):
    """Hard cuts found in the picture: one frame-to-frame step over 6 times the median step and over 14 (12 fps)."""
    f = frames(path, fps=SEAM_FPS, w=90, h=160)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    med = max(float(np.median(d)), 0.5)
    cuts = [(i + 1) / SEAM_FPS for i in range(len(d)) if d[i] > max(14, 6 * med)]
    out = []
    for t in cuts:   # a flash that lasts a few frames is two steps: keep the first
        if not out or t - out[-1] > 0.3:
            out.append(t)
    return out, f


def seam_report(path, a):
    """Sound level and brightness either side of each cut (from drama-skills' edit verify, EDT-23; ghost-film's verify.py).
    The ear and the eye decide: a hit, a flash or a planned silence is listed too."""
    cuts, f = cut_times(path)
    sr = 16000
    mean = f.mean(axis=(1, 2))
    listen, look = [], []
    edges = [0.0] + cuts + [len(f) / SEAM_FPS]
    for k, t in enumerate(cuts):
        a0, a1 = max(edges[k], t - SEAM_WIN), t - SEAM_GUARD
        b0, b1 = t + SEAM_GUARD, min(edges[k + 2], t + SEAM_WIN)

        def lvl(x0, x1):
            seg = a[int(x0 * sr):int(x1 * sr)]
            return None if len(seg) < 0.1 * sr else max(-70.0, 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9))
        lb, la = lvl(a0, a1), lvl(b0, b1)
        if lb is not None and la is not None and abs(la - lb) > SOUND_NOTICE:
            listen.append(f"{t:.1f}s {la - lb:+.0f}dB")
        i = int(round(t * SEAM_FPS))
        if 1 <= i < len(mean) - 1:
            dl = float(mean[i:i + 2].mean() - mean[max(0, i - 2):i].mean())
            if abs(dl) > LIGHT_NOTICE:
                look.append(f"{t:.1f}s {dl:+.0f}")
    return len(cuts), listen, look


def check(path):
    p = Path(path)
    f = frames(p)
    dur = len(f) / 4
    size = p.stat().st_size / 1e6
    mean = f.mean(axis=(1, 2))
    black = runs(mean < 8, 0.25)
    diff = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    still = runs(diff < 0.25, 0.25)
    a = audio(p)
    blk = 8000
    rms = np.array([np.sqrt((a[i:i + blk] ** 2).mean()) for i in range(0, len(a) - blk, blk)])
    silent = runs(rms < 0.003, 0.5)
    loud = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
    opening_motion = float(diff[:4].mean()) if len(diff) > 4 else 0
    issues = []
    if dur > 179:
        issues.append(f"too long for Reels/Shorts ({dur:.0f}s)")
    for s, d in black:
        if d > 2.0 and s < dur - 4:
            issues.append(f"black {d:.1f}s at {s:.1f}s")
    for s, d in still:
        if d > 3.0:
            issues.append(f"no motion {d:.1f}s at {s:.1f}s")
    for s, d in silent:
        if d > 1.5:
            issues.append(f"silence {d:.1f}s at {s:.1f}s")
    if loud < -26:
        issues.append(f"quiet overall ({loud:.1f} dBFS)")
    if mean[0] < 8:
        issues.append("first frame is black")
    print(f"{p.name}: {dur:.1f}s, {size:.1f} MB, mean level {loud:.1f} dBFS (the mix is normalised to -14 LUFS; "
          f"dBFS is not LUFS, don't 'fix' it), opening motion {opening_motion:.2f}")
    for i in issues:
        print("   -", i)
    n, listen, look = seam_report(p, a)
    print(f"   seams: {n} cuts. LISTEN (sound over {SOUND_NOTICE:.0f} dB): " + (", ".join(listen) or "none")
          + ("  (a hit or a planned silence shows as a pair; say which are deliberate)" if listen else ""))
    if "--light" in sys.argv:   # off by default: a Reel's flashes, static and negflash make the list 20 to 50 entries long
        print(f"   LOOK (light over {LIGHT_NOTICE:.0f}): " + (", ".join(look) or "none"))
    if not issues:
        print("   - no issues")


if __name__ == "__main__":
    for x in sys.argv[1:]:
        if not x.startswith("--"):
            check(x)
