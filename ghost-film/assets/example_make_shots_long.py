"""shots_vN.json for 隔壁空床的簾子 from the screenplay order (copied from kenting_knock's make_shots11.py). Clip picks,
offsets and in-clip speech spans live in clip_notes.json, so a new seed is one edit there.
Shot ids s01, s04, s06, s14, s17, s18, s20, s27, s28 anchor music/build_bed.py: keep them.
py -X utf8 make_shots.py <N>   -> shots_v<N>.json"""
import json, sys
from pathlib import Path

N = sys.argv[1]
NOTES = json.loads(Path("clip_notes.json").read_text(encoding="utf8"))
HERE = __import__("os").getcwd().replace("\\", "/")
SX = "file:C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/sfx/cuts/"
END_THEME = "C:/Users/sheep/Pictures/gui_chang_shi/brand/music/licensed/end_theme_12s.wav"

# lines spoken inside clips (lip sync); the subtitle is exactly this
SAY = {"h4": "「妳請一個禮拜假，老闆不會罵喔？」",
       "h6": "「家屬吃的，不要跟別人講。」",
       "h7": "「剛清完，等新病人。」",
       "h12": "「妳晚上睡過去一點，不要靠那邊。」",
       "h13": "「沒有為什麼。」",
       "h14m": "「妳幹嘛？」",
       "h17": "「來，這邊比較好睡。」",
       "h19": "「阿琪！」",
       "h24": "「前兩天晚上，我就有聽到隔壁簾子裡有人在講話。」",
       "h24b": "「一直在問，旁邊那個妹妹，幾歲啊。我都沒回答。我怕一回答，就算是答應了。」"}

SPANS = json.loads(Path("../vo/spans.json").read_text(encoding="utf8"))
SP = 1.15
def vdur(n):   # a voice take's length in the mix (render.py vo_take: sped, -0.12 / +0.35 s around the span)
    s, e = SPANS[n]; return (e - s) / SP + 0.47

PLAN = [
    # 1 cold open, one take: the hand on her ankle under the curtain
    ("s01", "h3L", ["N01"], {"dur": 7.0, "lead": 1.0, "sfx": [[SX + "D3.wav", 0.0, 0.3], [SX + "H4.wav", 4.6, 0.35]]}),
    # 2 title over the closed curtain with a thin gap
    ("s04", "tc", [], {"dur": 3.4, "title_fx": 1, "title_fx_dur": 3.4}),
    # 3 day one, one take: mother's question, her answer, she lies back on the cot
    ("s05p", "d1a", ["N02"], {"tag": "住院第一天", "lead": 0.2, "dur": 5.4}),
    ("s05", "d1", "talk", {}),
    ("s05n", "still:src/eb.png", ["N03", "N04", "N05"], {"lead": 0.3, "motion": "push", "amt": 0.1, "focus": [0.5, 0.6]}),
    # 4 阿琪, 11 pm, one take
    ("s06", "nq", "talk", {"tag": "夜班護理師 阿琪"}),
    # 5 the second night, one take
    ("s09", "n2", ["N11", "N06"], {"tag": "第二晚 凌晨兩點十分", "lead": 1.5}),
    ("s10", "h10", [], {"dur": 2.6, "amb": 1.0}),
    # 6-7 the next morning
    ("s11", "h11", ["N17"], {"tag": "隔天早上"}),
    ("s12", "c12", "talk", {}),
    # 8 the third night, one take: N13 over the dragging, then the two lines in the room
    ("s14", "n3", "talk", {"tag": "第三晚 十一點半", "pre": "N13"}),
    # 9 the reveal
    ("s16", "h16", ["N14"], {"tag": "凌晨兩點四十分", "lift": 1.5, "dur": 2.6}),
    ("s17", "h17", "say", {"music_cut": [0, 0], "amb": 0.9}),
    # her point of view, continuing the last frame of s17: the face turns, the hand takes her ankle and drags
    ("s18", "h18g", [{"sub": "「阿琪！阿琪！」", "dur": 1.9}], {"dur": 5.0, "lead": 3.1, "sfx": [[SX + "H1.wav", 1.4, 0.8],
        ["file:%s/sfx_local/scream.wav" % HERE, 1.6, 1.0], ["file:%s/sfx_local/aqi.wav" % HERE, 3.1, 1.1]]}),
    # 11 lights on
    ("s20", "h20m", ["N15"], {"lead": 0.8, "tail": 0.8}),
    ("s22", "h22", ["N07"], {"tag": "凌晨三點"}),
    # 13 the next day, another room
    ("s23", "h23", ["N16"], {"tag": "隔天"}),
    ("s24", "h24", "say", {}),
    ("s25", "h25", ["M6"], {"lead": 0.3}),
    ("s26", "h24b", "say", {}),
    ("s26d", "h26m", "talk", {"tag": "出院那天"}),
    ("s27", "h27", ["N08", "N09", "N10"], {"tag": "現在", "zoom": 0.22, "focus": [0.5, 0.25]}),
    ("s28", "h28", [], {"dur": 2.2, "music_cut": [0, 0], "amb": 0.4}),
    ("s29", "rise", [], {"dur": 5.6, "offset": 0.4, "music_cut": [0, 0], "amb": 0.5}),
    ("s30", "h30", [], {"dur": 1.1, "motion": "push", "amt": 0.12, "lift": 0.85, "grain": 0.5, "music_cut": [0, 0],
                        "sfx": [[SX + "H1.wav", 0.0, 0.95], [SX + "H3.wav", -2.4, 0.55]]}),
    ("s31", "black", ["A2"], {"lead": 0.6, "tail": 0.9, "music_cut": [0, 0]}),
    ("end", None, [], {"end": True, "dur": 4.0, "theme": END_THEME, "theme_at": 0.15, "theme_gain": 1.2}),
]

shots = []
for sid, src, lines, extra in PLAN:
    sh = {"id": sid}
    if src == "black":
        sh["still"] = "src/black.png"; sh["amb"] = 0
    elif src and src.startswith("still:"):
        sh["still"] = src[6:]; sh["amb"] = 0
    elif src:
        n = NOTES[src]
        sh["clip"] = n["clip"]
        for k in ("offset", "max_t", "lift", "zoom", "focus", "motion", "amt", "amb", "min_speed", "speed", "tint"):
            if k in n:
                sh[k] = n[k]
    if isinstance(lines, tuple):   # a dialogue clip: the other person's own lip-synced line plus 我's narrator-voice take
        n = NOTES[src]; q0, q1 = n["speech"]; m0 = n["me_at"]
        if lines[0] == "say":      # they speak, then 我 answers at me_at
            m = lines[1]; L = n.get("lead", 0.3); sh["offset"] = q0 - L
            sh["lines"] = [{"clip_speech": [q0, q1], "text": SAY[src]}, m]; sh["gap"] = max(0.05, m0 - q1)
            sh["lead"] = L
        else:                      # 我 speaks first at me_at, they answer
            m = lines[0]; L = n.get("lead", 0.3); sh["offset"] = max(n.get("offset", 0.0), m0 - L)
            sh["lines"] = [m, {"clip_speech": [q0, q1], "text": SAY[src]}]
            sh["gap"] = max(0.05, q0 - (sh["offset"] + L) - vdur(m)); sh["lead"] = L
        sh["tail"] = n.get("tail", 0.4); sh["amb"] = n.get("amb", 0.06)
    elif lines == "talk":   # a long take with several lip-synced lines: each line keeps the clip's own pause after it
        n = NOTES[src]; T = n["talk"]; off = n.get("offset", 0.0); pre = extra.pop("pre", None)
        sh["lines"] = [{"clip_speech": [a, b], "text": x, "gap": (T[i + 1][0] - b) if i + 1 < len(T) else 0.0}
                       for i, (a, b, x) in enumerate(T)]
        sh["lead"] = T[0][0] - off
        if pre:              # a narration line first, ending just before the first spoken line
            sh["gap"] = 0.05; sh["lead"] = max(0.0, T[0][0] - off - vdur(pre) - 0.05); sh["lines"].insert(0, pre)
        sh["dur"] = n["end"] - off; sh["amb"] = 0
    elif lines == "say":
        a, b = NOTES[src]["speech"]
        sh["lines"] = [{"clip_speech": [a, b], "text": SAY[src]}]
        sh.setdefault("lead", max(0.2, a - sh.get("offset", 0.0)))
        sh.setdefault("tail", 0.3)
        sh["amb"] = NOTES[src].get("amb", 0.6)
    else:
        sh["lines"] = lines
    sh.update(extra)
    shots.append(sh)

spec = {"out": f"reel_v{N}", "title": "隔壁空床的簾子",
        "music": f"music/bed_v{N}.wav" if Path(f"music/bed_v{N}.wav").exists() else "music/bed.wav",
        "music_gain": 0.3, "duck": 0.5, "music_level": False, "amb_gain": 0.3, "vo_gain": 1.5, "vo_speed": 1.15,
        "lead": 0.15, "gap": 0.18, "tail": 0.3, "min_speed": 0.35, "sub_y": 0.76, "sub_size": 68, "vo_picks": "picks.json",
        "end_question": "你陪病的時候，隔壁床有人嗎？", "music_cuts": [], "shots": shots}
Path(f"shots_v{N}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf8")
print("shots", len(shots))
