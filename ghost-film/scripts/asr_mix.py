"""ASR of a rendered reel's mix with times: py -X utf8 asr_mix.py out/reel_vN/reel_vN.mp4 -> out/reel_vN/_asr.txt"""
import sys
from pathlib import Path
from faster_whisper import WhisperModel
f = sys.argv[1]
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
segs, _ = m.transcribe(f, language="zh", initial_prompt="以下是繁體中文的句子。", vad_filter=False)
out = Path(f).parent / "_asr.txt"
with open(out, "w", encoding="utf8") as o:
    for s in segs:
        o.write(f"{s.start:7.2f}-{s.end:7.2f}  {s.text}\n")
print(out)
