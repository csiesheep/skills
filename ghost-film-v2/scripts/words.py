"""Speech start and end inside a clip's sound: py -X utf8 words.py clip.mp4 ..."""
import sys
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    segs, _ = m.transcribe(f, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    ws = [w for s in segs for w in s.words]
    if ws:
        print(f"{f.split('/')[-1]}\t{ws[0].start:.2f}-{ws[-1].end:.2f}\t" + "".join(w.word for w in ws))
    else:
        print(f, "no speech")
