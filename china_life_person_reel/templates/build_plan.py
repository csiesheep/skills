"""<這支 Reel 的名字>：<姓名>（seed <seed>，<時期>、<出生地>、<身分>）。時間都是錄影秒數，從 timeline.py 抄。
複製到 <reel>/tools/build_plan.py，填 segments，跑 `py -X utf8 tools/build_plan.py` 寫出 <reel>/plan.json。

剪輯規矩（owner 2026-10-23 看過 Reel 3／Reel 4 後定的）：
- 遊戲畫面不推近（推近會切到字）。要放大只放大另外疊上的大地圖。
- 讀得完字：抉擇卡照原速播（dur = to - from），點下去後定格 1.4–1.8 秒；重點那一列出現後定格 1.2–1.8 秒。
- 每到一個年紀先放一張全螢幕肖像卡（1.8–2.0 秒），回到遊戲時右下角留那個年紀的小肖像；小肖像全片同一大小（render.py 的 INSET_SIZE）。
- 段與段之間溶接 0.5 秒（plan 頂層 dissolve），不硬切。
- 遊戲音效小聲：sfx_gain_db -14。配樂 -5 dB 左右，成品再用 finish.py 拉到 -14 LUFS。
- 字幕寫畫面上的事，平實，不渲染；地名用遊戲畫面上的（引擎的 city 可能不同）。沉重題材不拿苦難當梗。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = lambda a: f"portraits/age{a}_c.png"
BASE = "portraits/base2_c.png"          # 選定的基準臉（clean 後）
# 大地圖鏡頭（--mapshots 的截圖像素，通常 2127x1260）：[放大, 中心 x, 中心 y]。不用大地圖就刪掉。
START = [2.4, 1440, 760]
ROUTE = [1.8, 1380, 640]
WIDE = [1.35, 1320, 620]


def seg(frm, to, dur, caption="", freeze_at=(), sfx_at=(), cam=None, **kw):
    """錄影段：錄影 frm–to 秒壓成 dur 秒；freeze_at=[(錄影秒數, 定格秒數)]；sfx_at=[(音效名, 錄影秒數)]；cam=大地圖鏡頭 [(錄影秒數或 0/1, 鏡頭)]。"""
    p = lambda t: max(0.0, min(1.0, (t - frm) / (to - frm)))
    s = {"src": "life", "from": frm, "to": to, "dur": dur, "cap_y": 170}
    if caption:
        s["caption"] = caption
    if freeze_at:
        s["freeze"] = [[p(t), d] for t, d in freeze_at]
    if sfx_at:
        s["sfx_src"] = [[n, t] for n, t in sfx_at]
    if cam:
        s["bigmap"] = {"cam_t": [[(frm if t == 0 else to if t == 1 else t), *v] for t, v in cam]}
    s.update(kw)
    return s


def card(path, label, sub, dur=1.8):
    """全螢幕肖像卡：米紙底、肖像慢推、下方大字年紀與一行小字。"""
    return {"portrait": path, "label": label, "sub": sub, "dur": dur}


def decision(frm, to, caption, t_card, t_tap, inset, hold=1.5):
    """抉擇卡：原速（讀得到題目），點下去後定格讓人看清楚選了哪一項。t_card、t_tap 抄 timeline.py 的 DECISION 與 tap。"""
    return seg(frm, to, to - frm, caption, inset=inset, freeze_at=[(t_tap + 0.3, hold)], sfx_at=[("decision", t_card), ("choose", t_tap)])


segments = [
    # 冷開場（Reel 3 v3 的教訓：v2 從黑畫面淡入，2 秒就走了 6 成的人）：第一格就是最強的轉折——肖像加一行大字，
    # 再閃兩三個轉折，每張 0.8–1.0 秒、推近 12%、直接切（dissolve 0，溶接會讓兩行字疊在一起）
    {**card(P("03"), "", "", dur=1.0), "caption": "<3 歲，最強的那件事>", "cap_y": 1450, "push": 0.12, "dissolve": 0},
    {**card(P("06"), "", "", dur=0.8), "caption": "<下一個轉折>", "cap_y": 1450, "push": 0.12, "dissolve": 0},
    {**card(P("15"), "", "", dur=0.8), "caption": "<再下一個>", "cap_y": 1450, "push": 0.12, "dissolve": 0},
    # 她是誰：基準臉 + 名字，再接戶帖（card_ready ~2 秒、begin 的 tap ~7 秒）
    {**card(BASE, "<姓名>", "<西元年>年，生在<地方>的<身分>家", dur=1.2), "dissolve": 0},
    seg(4.4, 8.4, 2.2, "<一句話把人帶進她的一生>", sfx_at=[("start", 7.5)]),
    # 每個年紀：card(...) 接 decision(...) 或 seg(..., inset=P("NN"), freeze_at=[...])
    # card(P("06"), "6 歲", "<那一年的事>"),
    # decision(28.4, 32.6, "<字幕>", 28.8, 31.3, P("06"), hold=1.8),
    # seg(64.8, 67.2, 2.4, "<字幕>", inset=P("06"), freeze_at=[(66.2, 1.8)]),
    # 一段很長的歲月快轉：ramp=[[0, 1], [0.15, 3], [0.85, 3], [1, 1]]
    # 大地圖（搬家）：seg(46.4, 51.5, 4.0, "逃荒到<地方>", inset=P("16"), cam=[(0, START), (47.6, START), (49.5, ROUTE), (1, ROUTE)], freeze_at=[(49.6, 1.6)])
    # 結局：她的分享卡
    {"image": "rec/life/end_card.png", "dur": 3.4, "caption": "<姓名>，享年 <N> 歲", "cap_at": [0.05, 0.6],
     "zoom": [[0, 1.6, 540, 760], [0.45, 1.6, 540, 800], [0.9, 1.0, 540, 960], [1, 1.0, 540, 960]], "sfx": [["stamp", 0.05]]},
    # （可選）遊戲模擬的數字卡：cards.py stats
    # {"image": "cards/stats.png", "dur": 4.6},
    # 首頁 + 網址
    {"src": "home", "from": 0.5, "to": 7.5, "dur": 3.0, "caption": "你投胎到古代，會是誰？\ngames.csiesheep.com/china_life",
     "cap_y": 760, "cap_at": [0.08, 1.0]},
]

plan = {"fps": 30, "music": "music/bed.flac", "music_offset": 0.0, "music_gain_db": -5,
        "sfx_gain_db": -14, "music_fade_out": 2.5, "dissolve": 0.5, "segments": segments}
(ROOT / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print("plan.json written", round(sum(s["dur"] + sum(f[1] for f in s.get("freeze", [])) for s in segments), 1), "s")
