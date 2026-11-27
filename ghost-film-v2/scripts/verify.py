"""Seam report for a finished cut: where a stranger would hear or see a jump. Measures only; it decides nothing.
py -X utf8 verify.py out/reel_vN/reel_vN.mp4 [out/reel_vN/_timeline.txt]
  cuts    shot starts from _timeline.txt (default: next to the mp4)
  sound   RMS of the 0.4 s before and after each cut (0.03 s guard, louder channel, floor -70 dBFS): LISTEN when the
          change is over 10 dB. A deliberate hit or a deliberate silence will be listed too: the ears sort them
  light   mean brightness of the frame before and after each cut: LOOK when it moves by more than 20 (0-255)
  frames  one frame that differs by more than 20 from both neighbours while they agree within 10: a bad frame
Idea and thresholds from zenstory-ai/drama-skills (edit_tool.py verify, EDT-23). Exit code is always 0."""
import re, subprocess, sys
from pathlib import Path
import numpy as np

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
SR, WIN, GUARD, SHORTEST, FLOOR = 16000, 0.4, 0.03, 0.1, -70.0
SOUND_NOTICE, LIGHT_NOTICE, SPIKE = 10.0, 20.0, 20.0
GW, GH = 36, 64


def run(args):
    return subprocess.run([FF, "-v", "error"] + args, capture_output=True).stdout


def audio(mp4):
    raw = run(["-i", str(mp4), "-vn", "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"])
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    return a.reshape(-1, 2) if len(a) >= 2 else a.reshape(0, 2)


def gray(mp4, fps):
    raw = run(["-i", str(mp4), "-an", "-vf", f"fps={fps},scale={GW}:{GH}", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    return np.frombuffer(raw, np.uint8).reshape(-1, GH, GW).astype(np.float32)


def fps_of(mp4):
    r = subprocess.run([FF, "-i", str(mp4)], capture_output=True, text=True, encoding="utf8", errors="replace").stderr
    m = re.search(r"(\d+(?:\.\d+)?) fps", r)
    return float(m.group(1)) if m else 24.0


def cuts(tl):
    out = []
    for ln in Path(tl).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(\d+\.\d+)\s+(\d+\.\d+)\s+(\S+)$", ln)
        if m:
            out.append((float(m.group(1)), float(m.group(2)), m.group(3)))
    return out


def level(a, t0, t1):
    i0, i1 = max(0, int(t0 * SR)), min(len(a), int(t1 * SR))
    if i1 - i0 < SHORTEST * SR:
        return None
    seg = a[i0:i1]
    rms = np.sqrt((seg ** 2).mean(axis=0)).max()   # the louder channel: opposite phases cannot cancel
    return max(FLOOR, 20 * np.log10(rms + 1e-9))


def main():
    mp4 = Path(sys.argv[1])
    tl = Path(sys.argv[2]) if len(sys.argv) > 2 else mp4.parent / "_timeline.txt"
    sh = cuts(tl)
    fps = fps_of(mp4)
    a, g = audio(mp4), gray(mp4, fps)
    print(f"{mp4.name}: {len(sh)} shots, {len(g) / fps:.1f}s picture, {len(a) / SR:.1f}s sound")
    listen, look = [], []
    print("\ncut      from -> to              sound dB (before -> after)    light (before -> after)")
    for k in range(1, len(sh)):
        t = sh[k][0]
        lb = level(a, max(sh[k - 1][0], t - WIN), t - GUARD)
        la = level(a, t + GUARD, min(sh[k][0] + sh[k][1], t + WIN))
        f = int(round(t * fps))
        mb = g[max(0, f - 2):f].mean() if f >= 1 else None
        ma = g[f:f + 2].mean() if f < len(g) else None
        s_txt, flag_s = "not compared", ""
        if lb is not None and la is not None:
            d = la - lb
            s_txt = f"{lb:6.1f} -> {la:6.1f} ({d:+.1f})"
            if abs(d) > SOUND_NOTICE:
                flag_s = " LISTEN"
                listen.append((t, sh[k - 1][2], sh[k][2], d))
        l_txt, flag_l = "", ""
        if mb is not None and ma is not None:
            dl = ma - mb
            l_txt = f"{mb:5.1f} -> {ma:5.1f} ({dl:+.1f})"
            if abs(dl) > LIGHT_NOTICE:
                flag_l = " LOOK"
                look.append((t, sh[k - 1][2], sh[k][2], dl))
        print(f"{t:6.2f}  {sh[k - 1][2]:>8} -> {sh[k][2]:<8}  {s_txt:<30}{flag_s:7}  {l_txt}{flag_l}")
    m = g.mean(axis=(1, 2))
    bad = [i for i in range(1, len(m) - 1) if abs(m[i] - m[i - 1]) > SPIKE and abs(m[i] - m[i + 1]) > SPIKE and abs(m[i - 1] - m[i + 1]) < 10]
    print(f"\nLISTEN (sound moves over {SOUND_NOTICE:.0f} dB): " + (", ".join(f"{t:.2f}s {x}->{y} {d:+.0f}dB" for t, x, y, d in listen) or "none"))
    print(f"LOOK   (light moves over {LIGHT_NOTICE:.0f}): " + (", ".join(f"{t:.2f}s {x}->{y} {d:+.0f}" for t, x, y, d in look) or "none"))
    print("BAD FRAME: " + (", ".join(f"{i / fps:.2f}s" for i in bad) or "none"))
    print("\nA fear hit or a planned silence belongs on the LISTEN list; say which ones are deliberate when reporting.")


if __name__ == "__main__":
    main()
