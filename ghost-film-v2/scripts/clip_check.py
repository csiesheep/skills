"""Machine checks on H3 clips before anyone looks at a strip: a light jump (a night frame that turns into a lit room), a
cut H3 made inside the clip, and speech in a clip that should have none or around the lines it should have.
py -X utf8 clip_check.py [--asr] clips/a.mp4 ...     prints one line per clip, FLAG lines first; exit code 1 if any flag
  light  mean brightness (0-255) of the first second against each later second: FLAG when it moves by more than 35 % and 8
  cut    frame-to-frame difference at 8 fps: FLAG when one step is over 6 times the clip's median step and over 14
  --asr  every word with its time (faster-whisper, as words2.py); FLAG for a clip listed in clip_check_silent.txt
         (one clip name per line, in the current folder) that has three or more words with real length
Use the times to set offset / max_t in clip_notes.json, or to reject the take. It cannot see a wrong action or a wrong
direction of movement: those still need the strip (strips.py)."""
import subprocess, sys
from pathlib import Path
import numpy as np
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
W, H, FPS = 90, 160, 8


def frames(clip):
    raw = subprocess.run([FF, "-v", "error", "-i", clip, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def check(clip):
    f = frames(clip); flags = []
    if len(f) < FPS * 2:
        return ["too short"], ""
    m = f.mean(axis=(1, 2)); base = m[:FPS].mean()
    for s in range(1, len(f) // FPS):
        v = m[s * FPS:(s + 1) * FPS].mean()
        if abs(v - base) > max(8, 0.35 * base):
            flags.append(f"light {base:.0f}->{v:.0f} from {s}s"); break
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2)); med = float(np.median(d)) + 0.3
    for i in np.where((d[:-3] > 6 * med) & (d[:-3] > 14))[0]:   # the last frames of an H3 clip often jump: not a cut
        flags.append(f"cut at {(i + 1) / FPS:.2f}s")
    return flags, f"light {base:.0f}, step median {med:.1f} max {d.max():.1f}"


a = sys.argv[1:]; asr = "--asr" in a; a = [x for x in a if x != "--asr"]
silent = set(Path("clip_check_silent.txt").read_text(encoding="utf8").split()) if Path("clip_check_silent.txt").exists() else set()
model = None; bad = 0
for c in a:
    flags, info = check(c); words = ""
    if asr:
        if model is None:
            from faster_whisper import WhisperModel
            model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
        segs, _ = model.transcribe(c, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
        ws = [w for s in segs for w in s.words if w.end - w.start > 0.05]
        words = " ".join(f"{w.word}[{w.start:.2f}-{w.end:.2f}]" for w in ws)
        if Path(c).stem in silent and len(ws) >= 3:
            flags.append(f"speech in a silent clip ({len(ws)} words)")
    bad += bool(flags)
    print(("FLAG " if flags else "ok   ") + Path(c).name + "  " + ("; ".join(flags) or info) + ("\n     " + words if words else ""), flush=True)
sys.exit(1 if bad else 0)
