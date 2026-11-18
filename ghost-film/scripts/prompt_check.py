"""Machine check of H3 prompt files (prompts/<name>.txt) before they go to the GPU. Prints a line per problem; exit 1 if any FLAG.
py -X utf8 prompt_check.py prompts/*.txt                      beats must be contiguous from 0s
py -X utf8 prompt_check.py prompts/a3.txt:8 prompts/b6h.txt:6    file:seconds, as in polite.py clips: the last beat must end at the clip length
  beats   [Xs-Ys] beats (one per line, or inline as in the first/last-frame prompts) start at 0s, touch each other and end at
          the clip length. H3 cuts the end of a line or an action if they run over, and slows the action down to fill a gap
          nobody wrote (drama-skills VID-04)
  camera  WARN: a beat that says both 固定機位 and a move (推近 拉遠 繞 搖 橫移 跟拍) contradicts itself (VID-06; our own 「固定機位，鏡頭極慢地推近」 idiom has shipped, so only a warning); a negated move
          (不推近, 不拉遠) is fine
  music   an image-to-video prompt must have non_diegetic_music: (N/A when there is no score), or H3 adds its own
  sound   WARN: 靜音 / 無聲 in the soundscape also wipes the room sound; write 沒有對話 or 沒有配樂
  length  the whole file over 7000 characters
Idea from zenstory-ai/drama-skills (references/minimax-h3.md, camera-audio-continuity.md); the thresholds are theirs."""
import re, sys
from pathlib import Path

MOVES = ("推近", "拉遠", "繞", "搖", "橫移", "跟拍", "後拉", "前推", "旋轉", "環繞", "推進", "拉近")
BEAT = re.compile(r"\[(\d+(?:\.\d+)?)s\s*-\s*(\d+(?:\.\d+)?)s\]\s*([^\[]*)")


def moves_in(txt):
    txt = re.sub(r"(不要?|沒有|不會|不)\s*(" + "|".join(MOVES) + ")", "", txt)
    return [m for m in MOVES if m in txt]


def check(path, sec=None):
    t = Path(path).read_text(encoding="utf-8")
    i2v = "integrated_multimodal_description" in t
    out = []
    if len(t) > 7000:
        out.append(f"FLAG length {len(t)} characters (limit 7000)")
    beats = BEAT.findall(t)
    if not beats:
        out.append("FLAG no [Xs-Ys] beats" if i2v else "skip: no [Xs-Ys] beats")
    else:
        prev = 0.0
        for a, b, txt in beats:
            a, b = float(a), float(b)
            if abs(a - prev) > 1e-6:
                out.append(f"FLAG beats: gap or overlap, a beat starts at {a:g}s after {prev:g}s")
            if b <= a:
                out.append(f"FLAG beats: [{a:g}s-{b:g}s] ends before it starts")
            if "固定機位" in txt and moves_in(txt):
                out.append(f"WARN camera: [{a:g}s-{b:g}s] says 固定機位 and {moves_in(txt)[0]}")
            prev = b
        if sec is not None and abs(prev - sec) > 1e-6:
            why = "over: the end is cut" if prev > sec else "under: the action is slowed to fill it"
            out.append(f"FLAG beats end at {prev:g}s, the clip is {sec:g}s ({why})")
    if i2v and "non_diegetic_music:" not in t:
        out.append("FLAG music: no non_diegetic_music: block (H3 adds its own score)")
    snd = t.split("overall_soundscape:")[-1].split("non_diegetic_music:")[0] if "overall_soundscape:" in t else ""
    if re.search(r"靜音|無聲", snd):
        out.append("WARN sound: 靜音/無聲 in the soundscape also removes the room sound; say 沒有對話 or 沒有配樂")
    return out


def split_arg(arg):
    m = re.match(r"^(.*):(\d+(?:\.\d+)?)$", arg)
    if m and len(m.group(1)) > 1:   # not a bare drive letter
        return m.group(1), float(m.group(2))
    return arg, None


def main():
    bad = 0
    for arg in sys.argv[1:]:
        path, sec = split_arg(arg)
        probs = check(path, sec)
        print(f"{Path(path).name}: " + ("ok" if not probs else ""))
        for q in probs:
            print("   " + q)
        bad += any(q.startswith("FLAG") for q in probs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
