"""把 ACE-Step 生成的配樂剪成連續、夠長的底樂（bed.flac）。

ACE 生成的曲子常常開頭有幾秒靜音、中段斷掉一截、或比要求的長度早結束（Reel 3：95 秒的曲子 88 秒就沒聲音了；
Reel 4：70 秒的曲子 17–25 秒整段靜音）。這支找出有聲音的段落，依序接起來，段與段之間交叉淡入淡出 2–3 秒，
不夠長就從頭再接一輪，直到超過 --min 秒。

    py -X utf8 bed.py <reel>/music/bed.flac --min 100 <a.flac> [<b.flac> ...]   # 一首或多首依序取用
    py -X utf8 bed.py --check <file>                                            # 只列出有聲音的段落
"""
import argparse
import subprocess

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000


def read(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def voiced(x, thresh_db=-45, min_gap=0.5, min_len=4.0):
    """有聲音的段落 [(start, end) 秒]：以 50 ms 的 RMS 判斷，短於 min_gap 的靜音不切。"""
    hop = int(0.05 * SR)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop, 2) ** 2).mean(axis=(1, 2)) + 1e-12)
    on = 20 * np.log10(rms) > thresh_db
    segs, s = [], None
    gap = int(min_gap / 0.05)
    quiet = 0
    for i, v in enumerate(on):
        if v:
            if s is None:
                s = i
            quiet = 0
        elif s is not None:
            quiet += 1
            if quiet > gap:
                segs.append((s, i - quiet + 1))
                s, quiet = None, 0
    if s is not None:
        segs.append((s, n))
    return [(a * 0.05, b * 0.05) for a, b in segs if (b - a) * 0.05 >= min_len]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?")
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--min", type=float, default=90)
    ap.add_argument("--xfade", type=float, default=2.5)
    ap.add_argument("--check")
    a = ap.parse_intermixed_args()
    if a.check:
        x = read(a.check)
        print(f"{len(x) / SR:.1f} 秒；有聲音：", ", ".join(f"{s:.1f}–{e:.1f}" for s, e in voiced(x)))
        return
    pieces = []
    for f in a.inputs:
        x = read(f)
        pieces += [x[int(s * SR):int(e * SR)] for s, e in voiced(x)]
    if not pieces:
        raise SystemExit("沒有有聲音的段落")
    n = int(a.xfade * SR)
    fade = np.linspace(0, 1, n)[:, None]
    out = pieces[0]
    k = 1
    while len(out) < a.min * SR:
        p = pieces[k % len(pieces)]
        k += 1
        out = np.concatenate([out[:-n], out[-n:] * (1 - fade) + p[:n] * fade, p[n:]])
    subprocess.run([FF, "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", a.out],
                   input=out.astype(np.float32).tobytes(), check=True)
    print(f"{a.out}  {len(out) / SR:.1f} 秒（{k} 段）")


if __name__ == "__main__":
    main()
