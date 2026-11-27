"""Every word with its time inside clips' sound: py -X utf8 words2.py clip.mp4 ...  (appends to words.txt)"""
import sys
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    segs, _ = m.transcribe(f, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    ws = [w for s in segs for w in s.words]
    line = f"{f.split('/')[-1]}\t" + " ".join(f"{w.word}[{w.start:.2f}-{w.end:.2f}]" for w in ws)
    print(line, flush=True)
    open("words.txt", "a", encoding="utf8").write(line + "\n")
