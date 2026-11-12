"""Aligned spans for every take of every line: ASR word times, then the word range that best matches the script line
(ref2va takes of short lines often start with a few words of the reference voice's own sentence), then the cut is
transcribed again. Writes takes.json: line -> [{file, span, sim, cut_sim, text}], and picks.json/spans.json with the
best take per line (cut_sim first, then shorter).
py -X utf8 spans2.py   (in <story>/film/vo)"""
import difflib, glob, json, re, subprocess
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
S = json.loads(Path("script.json").read_text(encoding="utf8"))
norm = lambda s: re.sub(r"[^一-鿿]", "", s)
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
T = json.loads(Path("takes.json").read_text(encoding="utf8")) if Path("takes.json").exists() else {}
seen = {t["file"] for v in T.values() for t in v}
Path("_cuts").mkdir(exist_ok=True)


def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


for f in sorted(glob.glob("C:/Users/sheep/code/ComfyUI/output/ghost_film_vo/TW*_[NFMWB][0-9]*.flac")):
    f = f.replace("\\", "/")
    stem = Path(f).stem
    if "aud" in stem or f in seen:
        continue
    name = stem.rsplit("_", 1)[0].split("_", 1)[-1]
    ref = norm(S.get(name, ""))
    if not ref:
        continue
    segs, info = m.transcribe(f, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    ws = [w for s in segs for w in s.words if norm(w.word)]
    if not ws:
        T.setdefault(name, []).append({"file": f, "span": None, "sim": 0, "cut_sim": 0, "text": ""}); continue
    best = (-1, 0, len(ws))
    for i in range(len(ws)):
        for j in range(i + 1, len(ws) + 1):
            r = ratio(ref, norm("".join(w.word for w in ws[i:j])))
            if r > best[0] + 1e-6:
                best = (r, i, j)
    r, i, j = best
    a0, a1 = ws[i].start, ws[-1].end   # junk comes before the line, never after: keep every word to the end
    cut = f"_cuts/{stem}.wav"
    subprocess.run([FF, "-y", "-v", "error", "-i", f, "-ss", f"{max(0, a0 - 0.12):.3f}", "-to", f"{a1 + 0.35:.3f}", cut])
    cs, _ = m.transcribe(cut, language="zh", initial_prompt="以下是繁體中文的句子。")
    ct = "".join(s.text for s in cs)
    rec = {"file": f, "span": [round(a0, 3), round(a1, 3)], "sim": round(r, 3), "cut_sim": round(ratio(ref, norm(ct)), 3),
           "text": ct, "dur": round(a1 - a0, 2)}
    T.setdefault(name, []).append(rec)
    print(name, rec["cut_sim"], ct, flush=True)
    Path("takes.json").write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf8")

picks, spans, bad = {}, {}, []
for name, ts in T.items():
    ok = [t for t in ts if t["span"]]
    if not ok:
        bad.append(name); continue
    b = max(ok, key=lambda t: (t["cut_sim"] >= 0.9, t["cut_sim"], -t["dur"]))
    picks[name], spans[name] = b["file"], b["span"]
    if b["cut_sim"] < 0.9:
        bad.append(f"{name} {b['cut_sim']} {b['text']}")
for k, (f, sp_) in json.loads(Path("overrides.json").read_text(encoding="utf8")).items():   # hand picks after listening by ASR
    picks[k], spans[k] = f, sp_
Path("picks.json").write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf8")
Path("spans.json").write_text(json.dumps(spans, indent=1), encoding="utf8")
Path("takes.json").write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf8")
print("BAD", len(bad)); print("\n".join(bad))
