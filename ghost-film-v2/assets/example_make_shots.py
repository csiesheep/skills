"""shots_vN.json for 墾丁民宿的敲門聲 from the screenplay order. Clip picks, offsets and in-clip speech spans live in
clip_notes.json ({shot id: {"clip", "offset", "max_t", "speech": [a, b], ...}}), so a new seed is one edit there.
py -X utf8 make_shots.py <N>   -> shots_v<N>.json"""
import json, sys
from pathlib import Path

N = sys.argv[1]
NOTES = json.loads(Path("clip_notes.json").read_text(encoding="utf8"))
SX = "file:C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/sfx/cuts/"
END_THEME = "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/end_theme_12s.wav"

# text of the lines spoken inside clips (lip sync); the subtitle is exactly this
SAY = {"k6m": "「妳們兩個女生，晚上出去要小心喔，房卡一定要帶，我十點就去睡了。」",
       "k8m": "「這網路也太爛了吧，我LINE傳出去，妳過五分鐘才收到。」",
       "k10m": "「我去大街超商買宵夜，妳要什麼？」",
       "k12m": "「妳不要先睡喔，睡了我就自己吃光！」",
       "k23m": "「妳剛剛幹嘛不開門？我手機沒電，敲半天，只好下樓，找老闆娘拿備用卡。」",
       "k26m": "「我沒傳啊，手機在超商就沒電了。」",
       "k27m": "「好啦。宵夜也賣完了，什麼都沒買到。」"}

# (shot id, source in clip_notes, narrator / speak.py lines, extra keys)
SPANS = json.loads(Path("../vo/spans.json").read_text(encoding="utf8"))
SP = 1.15
def vdur(n):   # a voice take's length in the mix (render.py vo_take: sped, -0.12 / +0.35 s around the span)
    s, e = SPANS[n]; return (e - s) / SP + 0.47
SAY.update({"e0m": SAY["k23m"], "e2m": SAY["k23m"], "d1m": "「我沒傳啊，手機在超商就沒電了。」", "d2m": "「好啦。宵夜也賣完了，什麼都沒買到。」",
            "a2m": SAY["k10m"]})
LAUGH = "file:C:/Users/sheep/Pictures/gui_chang_shi/backlog/kenting_knock/film/reel/sfx/V2_laugh.wav"

# v11 (owner on v10): long takes; 我 speaks on screen (her narrator-voice take laid on her own lip movement)
PLAN = [
    ("s00", "c0", ["Q5", "N01", "N02"], {"lead": 1.5, "gap": 0.5, "tail": 0.3, "sfx": [["knock", 2.55, 0.5]]}),
    ("s04", "c0t", [], {"dur": 2.0, "title_fx": 1, "title_fx_dur": 2.0}),
    ("s05", "k3", ["N03"], {}),
    ("s08", "k6m", "say", {"tag": "民宿老闆娘"}),
    ("s09", "k7", ["N05"], {}),
    ("s10", "k8m", "say", {"tag": "小晴"}),
    ("s12", "a2m", ("say", "M1"), {"tag": "晚上十點十分"}),
    ("s15", "k12m", "say", {}),
    ("s16", "k13n", ["N08", "N09"], {"tag": "晚上十一點十五分"}),
    ("s17", "k14", ["Q4"], {"lead": 2.4, "sfx": [["knock", 0.4, 0.55]]}),
    ("s18", "k15", ["N10", "N11"], {}),
    ("s19", "k16", ["N12"], {"sfx": [[SX + "H4.wav", 0.2, 0.45]]}),
    ("s20", "k17q", ["N13"], {}),
    ("s21", "pkfl", ["N14", "Q5"], {"amb": 0, "dur": 11.0, "lead": 0.6, "gap": 3.4, "sfx": [[SX + "D3.wav", 0.0, 0.2], [SX + "H3.wav", 8.6, 0.45]]}),
    ("s24", "k19q", ["N15"], {"lead": 1.2, "lift": 0.8, "sfx": [["knock", 0.3, 0.6], ["knock", 1.9, 0.6], [SX + "D4.wav", 0.0, 0.25]]}),
    ("s26", "e1", [], {"dur": 4.3,  "tag": "十一點三十五分", "amb": 0.8}),
    ("s28", "e2m", "say", {"tail": 0.2}),
    ("s30", "d1m", ("M2", "say"), {}),
    ("s32", "d2m", ("M3", "say"), {}),
    ("s34", "k28m", ["N21", "N22", "N23"], {}),
    ("s36", "k30", ["N24a", "N24"], {"tag": "凌晨三點十分", "lift": 0.8}),
    ("s37", "k31m", ["P1"], {"amb": 0}),
    ("s38", "k32", ["P2"], {}),
    ("s39", "k33", ["P3", "P4"], {"dur": 4.6}),
    ("s39b", "k11f", [], {"dur": 1.0}),
    ("s40a", "k21f", ["P5"], {"dur": 1.0, "lead": 1.3, "amb": 0}),
    ("s40", "k34", ["N25"], {"lead": 3.0, "tail": 0.4, "music_cut": [-1.0, 0]}),
    # the ending, one continuous shot (owner 2026-11-12): her head rises behind 我's shoulder (face C0, no body) -> a fast push
    # into the face filling the screen (the jump) -> black, 「妳發現啦，嘻嘻」
    ("s41", "shf", [], {"dur": 4.2, "offset": 1.6, "zoom": 0.15, "music_cut": [0, 0], "amb": 0.2}),
    ("s42", "shp", [], {"dur": 0.7, "motion": "push", "amt": 2.4, "lift": 0.8, "grain": 0.5, "music_cut": [0, 0],
                        "sfx": [[SX + "H1.wav", 0.0, 0.95], [SX + "H3.wav", -2.4, 0.55]]}),
    ("s43", "black", ["Q10"], {"lead": 0.6, "tail": 0.9, "music_cut": [0, 0]}),
    ("end", None, [], {"end": True, "dur": 5.0, "theme": END_THEME, "theme_at": 0.15, "theme_gain": 1.2}),
]

shots = []
for sid, src, lines, extra in PLAN:
    sh = {"id": sid}
    if src == "black":
        sh["still"] = "src/black.png"; sh["amb"] = 0
    elif src:
        n = NOTES[src]
        sh["clip"] = n["clip"]
        for k in ("offset", "max_t", "lift", "zoom", "focus", "motion", "amt", "amb", "min_speed", "speed", "tint"):
            if k in n:
                sh[k] = n[k]
    if isinstance(lines, tuple):   # a dialogue clip: 小晴's own lip-synced line plus 我's narrator-voice take on her lip movement
        n = NOTES[src]; q0, q1 = n["speech"]; m0 = n["me_at"]
        if lines[0] == "say":
            m = lines[1]; sh["offset"] = q0 - n.get("lead", 0.3)
            sh["lines"] = [{"clip_speech": [q0, q1], "text": SAY[src]}, m]; sh["gap"] = max(0.05, m0 - q1)
            sh["lead"] = n.get("lead", 0.3)
        else:
            m = lines[0]; L = n.get("lead", 0.3); sh["offset"] = m0 - L
            sh["lines"] = [m, {"clip_speech": [q0, q1], "text": SAY[src]}]; sh["gap"] = max(0.05, q0 - m0 - vdur(m)); sh["lead"] = L
        sh["tail"] = n.get("tail", 0.4); sh["amb"] = n.get("amb", 0.06)
    elif lines == "say":
        a, b = NOTES[src]["speech"]
        sh["lines"] = [{"clip_speech": [a, b], "text": SAY[src.rstrip("b")]}]
        sh.setdefault("lead", max(0.2, a - sh.get("offset", 0.0)))
        sh.setdefault("tail", 0.3)
        sh["amb"] = NOTES[src].get("amb", 0.6)
    else:
        sh["lines"] = lines
    sh.update(extra)
    shots.append(sh)

spec = {"out": f"reel_v{N}", "title": "墾丁民宿的敲門聲", "music": f"music/bed_v{N}.wav" if Path(f"music/bed_v{N}.wav").exists() else "music/bed.wav",
        "music_gain": 0.3, "duck": 0.5, "music_level": False, "amb_gain": 0.3, "vo_gain": 1.5, "vo_speed": 1.15,
        "lead": 0.15, "gap": 0.18, "tail": 0.3, "min_speed": 0.35, "sub_y": 0.76, "sub_size": 68, "vo_picks": "picks.json",
        "end_question": "今晚敲你房門的，是誰？", "music_cuts": [], "shots": shots}
Path(f"shots_v{N}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf8")
print("shots", len(shots))
