"""The 720p posting copy of a rendered reel, under 9.3 MB. py -X utf8 package.py out/reel_vN/reel_vN.mp4"""
import subprocess, sys
from pathlib import Path
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
src = Path(sys.argv[1]).resolve()
out = src.with_name(src.stem + "_preview720.mp4")
info = subprocess.run([FF, "-i", str(src)], capture_output=True, text=True).stderr.split("Duration: ")[1].split(",")[0]
h, m, s = info.split(":"); dur = int(h) * 3600 + int(m) * 60 + float(s)
vk = int((9.3 * 8 * 1024) / dur - 96)
subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(src), "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
                "-b:v", f"{vk}k", "-maxrate", f"{int(vk*1.3)}k", "-bufsize", f"{vk*2}k", "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart", str(out)], check=True)
print(out, f"{out.stat().st_size/1e6:.1f} MB", f"{dur:.1f}s")
