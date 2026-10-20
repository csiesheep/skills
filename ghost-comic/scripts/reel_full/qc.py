"""Automatic checks on a finished Reel: length, size, dead picture, dead sound, loudness, opening frame.

    py -X utf8 qc.py <video.mp4> [...]
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
    print(f"{p.name}: {dur:.1f}s, {size:.1f} MB, loudness {loud:.1f} dBFS, opening motion {opening_motion:.2f}")
    for i in issues:
        print("   -", i)
    if not issues:
        print("   - no issues")


if __name__ == "__main__":
    for x in sys.argv[1:]:
        check(x)
