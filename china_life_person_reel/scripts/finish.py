"""Reel 收尾與檢查。

    py -X utf8 finish.py check <reel>/out/preview.mp4 2.0 6.5 11 ...   # 抽這些秒數的格，拼成 out/check.jpg（每格 240 寬）
    py -X utf8 finish.py final <reel>/out/reel.mp4                      # 音量拉到 -14 LUFS（只動音軌）、量 true peak、出 reel_720p.mp4

render.py 混音時的 loudnorm 加 limiter 常讓成品落在 -14.6 到 -15.6 LUFS；final 依量到的值補增益，
補完 true peak 要低於 -1 dBFS（否則印警告，請把 plan 的 music_gain_db 調低重渲染）。
"""
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

FF = imageio_ffmpeg.get_ffmpeg_exe()


def loud(path):
    r = subprocess.run([FF, "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, errors="replace").stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    p = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    return i, p


def check(video, times):
    video = Path(video)
    tiles = []
    for t in times:
        png = video.with_name(f"_f{t}.png")
        subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=240:427", str(png)], check=True)
        tiles.append(Image.open(png).convert("RGB"))
        png.unlink()
    cols = min(6, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 244, rows * 431), "black")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 244, (i // cols) * 431))
    out = video.with_name("check.jpg")
    sheet.save(out, quality=85)
    print(out)


def final(video):
    video = Path(video)
    i, p = loud(video)
    g = round(-14 - i, 1)
    if abs(g) >= 0.1:
        tmp = video.with_name("_v.mp4")
        subprocess.run([FF, "-v", "error", "-y", "-i", str(video), "-c:v", "copy", "-af", f"volume={g}dB", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(tmp)], check=True)
        tmp.replace(video)
    i2, p2 = loud(video)
    print(f"loudness {i:.1f} → {i2:.1f} LUFS（+{g} dB），true peak {p2:.1f} dBFS")
    if p2 > -1.0:
        print("警告：true peak 高於 -1 dBFS，把 plan 的 music_gain_db 調低 1–2 dB 重渲染")
    small = video.with_name("reel_720p.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(video), "-vf", "scale=720:1280", "-c:v", "libx264", "-crf", "25", "-preset", "slow",
                    "-c:a", "copy", "-movflags", "+faststart", str(small)], check=True)
    print(f"{small}  {small.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    if sys.argv[1] == "check":
        check(sys.argv[2], [float(x) for x in sys.argv[3:]])
    elif sys.argv[1] == "final":
        final(sys.argv[2])
    else:
        print(__doc__)
