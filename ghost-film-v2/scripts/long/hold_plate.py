"""A clip that pushes in (or moves) at the start and then settles: play it once forward, then ping-pong only its settled
end, so a long segment never pulls back out the way a full reverse does (s45b on 〈動物醫院的兩點十分〉).

py -X utf8 hold_plate.py clips/ch_s45b_s113.mp4 3.0 clips/ch_s45b_s113_hold.mp4
    -> forward 0..end, then (settle..end reversed, settle..end forward) twice; point chain_map.json's "file" at it."""
import subprocess
import sys

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
src, settle, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
e = subprocess.run([FF, "-i", src], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
end = int(h) * 3600 + int(m) * 60 + float(s) - .05
fc = (f"[0:v]trim=0:{end:.3f},setpts=PTS-STARTPTS[a];[0:v]trim={settle:.3f}:{end:.3f},setpts=PTS-STARTPTS,split[b][c];"
      f"[b]reverse[r];[r][c]concat=n=2[rc];[rc]split[x][y];[a][x][y]concat=n=3[v]")
subprocess.run([FF, "-y", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], check=True)
print(out)
