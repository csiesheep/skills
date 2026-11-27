"""Word-level speech start/end of every picked take (faster-whisper), saved to spans.json for render.py.
py -X utf8 spans.py [names...]"""
import json, sys
from pathlib import Path
from faster_whisper import WhisperModel
H = Path.cwd()   # <story>/film/vo
picks = json.loads((H / "picks.json").read_text(encoding="utf8"))
sp = json.loads((H / "spans.json").read_text(encoding="utf8")) if (H / "spans.json").exists() else {}
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
for n in (sys.argv[1:] or picks):
    segs, _ = m.transcribe(picks[n], language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    ws = [w for s in segs for w in s.words]
    sp[n] = [round(ws[0].start, 3), round(ws[-1].end, 3)] if ws else None
    print(n, sp[n], "".join(w.word for w in ws), flush=True)
(H / "spans.json").write_text(json.dumps(sp, indent=1), encoding="utf8")
