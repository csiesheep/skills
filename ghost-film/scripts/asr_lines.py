"""Check every subtitle line of a rendered reel against the mix, one window per line. Whisper over the whole file skips
stretches (2 to 30 s on 墾丁 v11), so a line can look missing when it is there, or the reverse.

py -X utf8 asr_lines.py out/reel_vN/reel_vN.mp4 [--below 0.6]     -> out/reel_vN/_asr_lines.txt, low lines printed

Lines come from the lower half of _timeline.txt (subtitle chunks that touch are one line). 妳/你 and 她/他 count as the
same. A laugh, a giggle or a scream cannot be checked this way: the owner listens."""
import difflib, re, sys
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
f = Path(sys.argv[1])
below = float(sys.argv[sys.argv.index("--below") + 1]) if "--below" in sys.argv else 0.6
lines = []
for row in (f.parent / "_timeline.txt").read_text(encoding="utf8").splitlines():
    m = re.match(r"\s*([\d.]+)-\s*([\d.]+)\s+(.+)", row)
    if not m:
        continue
    a, b, t = float(m[1]), float(m[2]), m[3]
    if lines and a - lines[-1][1] < 0.05:
        lines[-1][1] = b; lines[-1][2] += t
    else:
        lines.append([a, b, t])
norm = lambda s: re.sub(r"[^一-鿿A-Za-z]", "", s).replace("妳", "你").replace("她", "他").upper()
audio = decode_audio(str(f), sampling_rate=16000)
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
out, low = [], 0
for a, b, t in lines:
    w = audio[int(max(0, a - 0.6) * 16000):int((b + 0.8) * 16000)]
    segs, _ = m.transcribe(w, language="zh", initial_prompt="以下是繁體中文的句子。", vad_filter=False)
    heard = "".join(s.text for s in segs)
    sim = difflib.SequenceMatcher(None, norm(t), norm(heard)).ratio()
    row = f"{a:7.2f}  {sim:.2f}  {t}  |  {heard}"
    out.append(row)
    if sim < below:
        low += 1; print("LOW", row, flush=True)
(f.parent / "_asr_lines.txt").write_text("\n".join(out), encoding="utf8")
print(f"{len(lines)} lines, {low} below {below}: {f.parent / '_asr_lines.txt'}")
