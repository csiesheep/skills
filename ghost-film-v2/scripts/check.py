"""ASR every take against vo/script.json. py -X utf8 check.py <flac>... -> name, duration, similarity, transcript"""
import difflib, json, re, sys
from pathlib import Path
from faster_whisper import WhisperModel
S = json.loads((Path.cwd() / "script.json").read_text(encoding="utf8"))   # run in <story>/film/vo
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^一-鿿]", "", s)
for f in sys.argv[1:]:
    stem = Path(f).stem.rsplit("_", 1)[0]          # N01_00001 or GW_N01_00001 (a story prefix keeps ComfyUI's output apart)
    name = stem if stem in S else stem.split("_", 1)[-1]
    segs, info = m.transcribe(f, language="zh", initial_prompt="以下是繁體中文的句子。")
    txt = "".join(s.text for s in segs)
    ref = S.get(name, "")
    sim = difflib.SequenceMatcher(None, norm(ref), norm(txt)).ratio() if ref else 0
    print(f"{Path(f).stem}\t{info.duration:.2f}\t{sim:.2f}\t{txt}", flush=True)
