"""Same scene twice for the owner: A lines spoken inside the clips (lip sync), B the chosen C voices laid over a clip.
py -X utf8 make_lip_compare.py  (in film/reel) -> ../lip_test.mp4, both halves at the same loudness."""
import glob
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw, ImageFont

FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
SR = 44100
UP = 2 ** (1 / 12)
TMP = Path("_lip")
TMP.mkdir(exist_ok=True)
A = [("lh_b1_s92", 1.72, 5.2), ("lh_b2_s92", 3.3, 7.3), ("lh_m1_s92", 2.82, 5.2)]
VE = {j["name"]: j["text"] for f in ("../vo/bright_jobs.json", "../vo/bright_retake.json") for j in json.load(open(f, encoding="utf8"))}
B = ["VE_B1_s1", "VE_B2_s2", "VE_M1_s1"]
norm = lambda s: re.sub(r"[^一-鿿]", "", s).translate(str.maketrans({"他": "牠", "她": "牠"}))
model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")


def pcm(args):
    raw = subprocess.run([FF, "-v", "error", *args, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def level(x):
    x = x * (.09 / (np.sqrt((x ** 2).mean()) + 1e-9))
    return x * min(1, .95 / np.abs(x).max())


def fade(x):
    n = min(int(.012 * SR), len(x) // 2)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def take(name):
    f = glob.glob(f"C:/Users/sheep/code/ComfyUI/output/ghost_film_vo/{name}_*.flac")[0].replace(chr(92), "/")
    seg, _ = model.transcribe(f, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    w = [x for s in seg for x in s.words if norm(x.word)]
    ref, best = norm(VE[name]), (-1, 0, len(w))
    import difflib
    for a in range(len(w)):
        for b in range(a + 1, len(w) + 1):
            r = difflib.SequenceMatcher(None, ref, norm("".join(x.word for x in w[a:b]))).ratio()
            if r > best[0] + 1e-6:
                best = (r, a, b)
    print(name, round(best[0], 2), "".join(x.word for x in w[best[1]:best[2]]), flush=True)
    s, e = w[best[1]].start, w[best[2] - 1].end
    return fade(pcm(["-ss", f"{max(s - .08, 0):.3f}", "-to", f"{e + .22:.3f}", "-i", f, "-af", f"aresample={SR},asetrate={int(SR * UP)},aresample={SR},atempo={1.15 / UP:.5f}"]))


def label(path, big, small):
    im = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1120, 720, 1280), fill=(20, 20, 22, 225))
    d.text((360, 1168), big, font=ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 44), fill=(255, 196, 80), anchor="mm")
    d.text((360, 1232), small, font=ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 30), fill=(235, 232, 225), anchor="mm")
    im.save(path)


label(TMP / "a.png", "A　對嘴", "嘴型對得上，聲音由影片模型產生")
label(TMP / "b.png", "B　分開配音", "你選的 C 版聲音，嘴型沒有對上")
parts = []
audio_a = []
for i, (n, s, e) in enumerate(A):
    p = TMP / f"a{i}.mp4"
    subprocess.run([FF, "-y", "-v", "error", "-ss", str(s), "-to", str(e), "-i", f"clips/{n}.mp4", "-i", str(TMP / "a.png"), "-filter_complex",
                    "[0:v]scale=720:1280,fps=24,setsar=1[v];[v][1:v]overlay,format=yuv420p[o]", "-map", "[o]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(p)], check=True)
    d = float(subprocess.run([FF, "-i", str(p)], capture_output=True, text=True, encoding="utf8").stderr.split("Duration: ")[1].split(",")[0].split(":")[2])
    x = pcm(["-ss", str(s), "-to", str(e), "-i", f"clips/{n}.mp4"])
    audio_a.append(fade(np.resize(x, int(d * SR)) if len(x) >= int(d * SR) else np.pad(x, (0, int(d * SR) - len(x)))))
    parts.append(p)
xa = level(np.concatenate(audio_a))
gap = np.zeros(int(.28 * SR))
voices = [take(n) for n in B]
xb = np.concatenate([np.zeros(int(.25 * SR)), voices[0], gap, voices[1], gap, voices[2], np.zeros(int(.4 * SR))])
xb = level(xb)
db = len(xb) / SR
pb = TMP / "b.mp4"
subprocess.run([FF, "-y", "-v", "error", "-i", "clips/lh_c1_s91.mp4", "-i", str(TMP / "b.png"), "-filter_complex",
                "[0:v]scale=720:1280,fps=24,setsar=1,split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1[l];[l][1:v]overlay,format=yuv420p[o]",
                "-map", "[o]", "-t", f"{db:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(pb)], check=True)
parts.append(pb)
(TMP / "l.txt").write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf8")
a = np.concatenate([xa, xb])
with wave.open(str(TMP / "a.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(a, -1, 1) * 32767).astype("<i2").tobytes())
subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(TMP / "l.txt"), "-i", str(TMP / "a.wav"), "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", "../lip_test.mp4"], check=True)
print("A", round(len(xa) / SR, 1), "s  B", round(db, 1), "s")
