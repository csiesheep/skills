#!/usr/bin/env python3
"""從 PTT marvel 板的抽樣表抽一副鬼故事骨架，印成寫手看的說明。只用標準函式庫。

  python ghost_plan.py plan [--setting 校園,宿舍] [--mechanism 附身] [--ending 開放結局]
                            [--ghost 0-3|不露面|間接|一瞬間|清楚] [--length 短|1500|1500-2500]
                            [--style 幽默] [--style-note ...] [--taste 直接|留白]
                            [--note 主角是護理師 ...] [--seed N] [--json]
  python ghost_plan.py options          列出所有可用的值
  python ghost_plan.py count FILE       數字數（不算第一行標題和空白）
  python ghost_plan.py surface FILE     版面和標點跟熱門文比（斷行、句長、引號、數字），超出範圍的列出來
  python ghost_plan.py post FILE [--mode attach|chain|ig]
                                        轉成可以發的貼文：標題改 [創作]、加 AI 標示、照平台字數上限切
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE = HERE.parent / "assets" / "table.json"

SETTINGS = {
    "dorm": "學校宿舍", "military": "當兵／軍營／營區", "night_shift": "夜班／值班／警衛",
    "mountain": "山路／山區／登山", "rental": "租屋處／老公寓／套房", "hospital": "醫院／診所／照護",
    "store": "超商／店面／打工", "old_house": "老家／鄉下老宅／三合院", "school": "校園／教室／社團",
    "hotel": "飯店／旅館／民宿", "road": "深夜開車／騎車／夜路", "funeral": "喪事／靈堂／塔位／告別式",
    "temple": "廟宇／宮壇／儀式／收驚", "office": "辦公室／公司／廠房", "transport": "公車／捷運／火車／計程車",
    "childhood_home": "童年家中／親戚家", "home": "自家／現在住的家（非租屋、非童年）",
    "ruins": "廢墟／廢棄建築／探險", "stairwell": "電梯／樓梯間／頂樓", "abroad": "國外旅行／出差",
    "water": "海邊／溪邊／水域", "other": "其他",
}
MECHANISMS = {
    "identity_swap": "身份錯置：那個人不是人，或不是本人", "time_slip": "時間錯亂：時序對不上、多出或少掉一段時間",
    "escalation": "逐步失控：小異常一路升級", "taboo": "犯禁忌後的報應", "retro_reveal": "事後才知道：事後才拼出真相才發毛",
    "witness_mismatch": "見證不一致：別人看到的和我不一樣", "repetition": "重複／循環：同一件事一再發生",
    "presence": "在場感：有東西在，但看不到", "benign": "善意／報恩／守護型", "possession": "附身／精神異常／卡到",
    "object": "物件作祟：照片、娃娃、衣物、手機", "dream": "夢境滲入現實", "sound_only": "只有聲音，沒有影像",
    "dead_contact": "亡者來電／訊息／託夢：已故者主動聯絡",
    "proxy_sighting": "透過第三者看見：自己沒感覺，通靈的親友描述得很具體",
}
ENDINGS = {
    "open": "開放：沒有解釋，就這樣結束", "explained": "有解釋：事後被人點破或查到前因",
    "twist": "反轉：最後一兩句把前面翻掉", "fade": "淡出：搬走、不再去、慢慢沒事",
}
BEATS = ["normal", "anomaly", "denial", "escalation", "reveal", "aftermath"]
BEAT_LABELS = {"normal": "正常生活鋪陳", "anomaly": "第一個小異常", "denial": "合理化／否認",
               "escalation": "升級", "reveal": "揭露／最可怕的一刻", "aftermath": "餘波"}

ALIASES = {
    "setting": {
        "學校": "school", "校園": "school", "教室": "school", "社團": "school", "補習班": "school",
        "宿舍": "dorm", "女宿": "dorm", "男宿": "dorm",
        "當兵": "military", "軍中": "military", "軍營": "military", "部隊": "military", "營區": "military",
        "夜班": "night_shift", "值班": "night_shift", "警衛": "night_shift", "保全": "night_shift",
        "山": "mountain", "山上": "mountain", "登山": "mountain", "山路": "mountain",
        "租屋": "rental", "套房": "rental", "雅房": "rental", "公寓": "rental",
        "醫院": "hospital", "急診": "hospital", "病房": "hospital", "診所": "hospital",
        "超商": "store", "便利商店": "store", "打工": "store", "店面": "store",
        "老家": "old_house", "三合院": "old_house", "鄉下": "old_house", "古厝": "old_house",
        "飯店": "hotel", "旅館": "hotel", "民宿": "hotel", "汽車旅館": "hotel",
        "夜路": "road", "開車": "road", "騎車": "road", "公路": "road",
        "喪事": "funeral", "靈堂": "funeral", "殯儀館": "funeral", "告別式": "funeral", "塔位": "funeral",
        "廟": "temple", "宮廟": "temple", "宮壇": "temple", "收驚": "temple",
        "公司": "office", "辦公室": "office", "工廠": "office", "職場": "office",
        "公車": "transport", "捷運": "transport", "火車": "transport", "計程車": "transport",
        "小時候": "childhood_home", "童年": "childhood_home", "親戚家": "childhood_home", "外婆家": "childhood_home",
        "自家": "home", "家裡": "home", "自己家": "home",
        "廢墟": "ruins", "廢屋": "ruins", "探險": "ruins",
        "電梯": "stairwell", "樓梯": "stairwell", "頂樓": "stairwell",
        "國外": "abroad", "出國": "abroad", "出差": "abroad",
        "海邊": "water", "溪邊": "water", "河邊": "water", "水庫": "water",
    },
    "mechanism": {
        "不是人": "identity_swap", "不是本人": "identity_swap", "身份": "identity_swap", "時間": "time_slip",
        "失控": "escalation", "升級": "escalation", "禁忌": "taboo", "報應": "taboo", "事後": "retro_reveal",
        "對不上": "witness_mismatch", "見證": "witness_mismatch", "循環": "repetition", "重複": "repetition",
        "在場": "presence", "感覺": "presence", "善意": "benign", "守護": "benign", "報恩": "benign",
        "附身": "possession", "卡到": "possession", "煞到": "possession", "物件": "object", "娃娃": "object",
        "照片": "object", "夢": "dream", "託夢": "dead_contact", "聲音": "sound_only", "亡者": "dead_contact",
        "來電": "dead_contact", "通靈": "proxy_sighting", "陰陽眼": "proxy_sighting",
    },
    "ending": {
        "開放": "open", "開放結局": "open", "開放式": "open", "沒解釋": "open", "沒有解釋": "open",
        "解釋": "explained", "有解釋": "explained", "解答": "explained",
        "反轉": "twist", "翻轉": "twist", "逆轉": "twist", "淡出": "fade", "搬走": "fade", "沒事": "fade",
    },
}
TABLES = {"setting": SETTINGS, "mechanism": MECHANISMS, "ending": ENDINGS}
SUFFIX = re.compile(r"(結局|結尾|收尾|型|類|式)$")

GHOST_LEVELS = {0: "從頭到尾沒有任何直接證據，只有感覺", 1: "只有間接跡象：聲音、東西被動過、別人的反應",
                2: "可以有一瞬間看見：黑影、人形、照片裡多了東西", 3: "可以清楚看見外觀、表情或有互動"}
GHOST_WORDS = {"不露面": 0, "完全不出現": 0, "看不到": 0, "間接": 1, "只有跡象": 1, "暗示": 1,
               "一瞬間": 2, "一閃": 2, "瞥見": 2, "黑影": 2, "清楚": 3, "正面": 3, "直接": 3}
LENGTH_PRESETS = {"極短": (400, 700), "短": (800, 1200), "中": (1500, 2500), "長": (3000, 4500), "超長": (5000, 8000)}
LENGTH_ALIASES = {"極短篇": "極短", "短篇": "短", "中篇": "中", "中等": "中", "長篇": "長", "很長": "超長"}
MIN_CHARS, MAX_CHARS = 300, 12000

STYLES = {
    "ptt": ("PTT 鄉民", ("鄉民", "預設", "批踢踢", "口語", "經驗文"), "PTT marvel 板 [經驗] 文的鄉民口吻，口語、粗糙、有免責開頭"),
    "minimal": ("簡約", ("簡潔", "極簡", "白描", "冷"), "短句白描，形容詞極少，留白多，不解釋情緒"),
    "humor": ("幽默", ("搞笑", "好笑", "吐槽", "自嘲"), "自嘲吐槽的輕鬆口吻，前段好笑，越接近揭露越收，最後一定是毛的"),
    "oral": ("口述", ("講故事", "說書", "節目", "podcast", "微疼", "聽眾"), "像在節目或宵夜攤上講給一群人聽，有跟聽眾的互動和停頓"),
    "literary": ("文學", ("文青", "細膩", "文藝", "散文"), "散文式的細膩描寫，有意象和節制的抒情，但事件本身仍是真實經驗的規模"),
    "report": ("紀錄", ("日誌", "報告", "冷靜", "紀錄體", "值班日誌"), "像值班日誌或事件紀錄，有時間戳記，語氣冷靜，情緒只從細節漏出來"),
    "elder": ("長輩講古", ("講古", "阿嬤", "阿公", "長輩", "台語"), "轉述長輩講的往事，夾台語和舊時代細節，長輩的語氣篤定，敘事者半信半疑"),
}
TASTES = {
    "直接": ("direct", "照 PTT 讀者的資料：最可怕那一幕寫出看到什麼，語氣篤定（預設）", ("具體", "爆文", "ptt", "資料", "direct", "預設")),
    "留白": ("restrained", "克制：鬼的露出上限內也留白，靠旁人反應撐，可以留一點不確定", ("克制", "含蓄", "隱晦", "restrained")),
}


class OptionError(ValueError):
    pass


def resolve(kind: str, text: str) -> str:
    table = TABLES[kind]
    t = text.strip()
    if t in table:
        return t
    for cand in (t, SUFFIX.sub("", t)):
        if cand in ALIASES[kind]:
            return ALIASES[kind][cand]
    hits = [k for k, label in table.items() if t in label or SUFFIX.sub("", t) in label.split("：")[0]]
    if len(hits) == 1:
        return hits[0]
    choices = "、".join(f"{k}（{v.split('：')[0]}）" for k, v in table.items())
    if not hits:
        raise OptionError(f"「{text}」對不到任何 {kind}。可用：{choices}")
    raise OptionError(f"「{text}」同時符合 {hits}，請說得更具體。可用：{choices}")


def resolve_list(kind: str, text: str | None) -> list[str] | None:
    if not text:
        return None
    return list(dict.fromkeys(resolve(kind, x) for x in re.split(r"[,，、/／\s]+", text) if x.strip()))


def resolve_ghost(text: str | None) -> int | None:
    if text is None or text == "":
        return None
    t = str(text).strip()
    if t.isdigit() and 0 <= int(t) <= 3:
        return int(t)
    if t in GHOST_WORDS:
        return GHOST_WORDS[t]
    raise OptionError("鬼露出用 0 到 3，或：" + "、".join(GHOST_WORDS))


def resolve_length(text: str | None) -> tuple[int, int] | None:
    if text is None or text == "":
        return None
    t = str(text).strip().replace("字", "")
    t = LENGTH_ALIASES.get(t, t)
    if t in LENGTH_PRESETS:
        return LENGTH_PRESETS[t]
    m = re.fullmatch(r"(\d+)\s*(?:[-~～到]\s*(\d+))?", t)
    if not m:
        raise OptionError("長度用字數（1500）、範圍（1500-2500），或：" + "、".join(LENGTH_PRESETS))
    lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
    lo, hi = min(lo, hi), max(lo, hi)
    if lo < MIN_CHARS or hi > MAX_CHARS:
        raise OptionError(f"長度要在 {MIN_CHARS} 到 {MAX_CHARS} 字之間")
    return lo, hi


def resolve_style(text: str | None) -> str:
    if not text:
        return "ptt"
    t = text.strip()
    if t in STYLES:
        return t
    for k, (label, aliases, _) in STYLES.items():
        if t == label or t in aliases or t in label:
            return k
    raise OptionError("風格可用：" + "、".join(f"{k}（{v[0]}）" for k, v in STYLES.items()))


def resolve_taste(text: str | None) -> str:
    if not text:
        return "直接"
    t = text.strip()
    for name, (_, _, aliases) in TASTES.items():
        if t == name or t.lower() in aliases:
            return name
    raise OptionError("口味可用：" + "、".join(TASTES))


def weighted_pick(rng: random.Random, table: dict, exclude: set | None = None, only: list | None = None) -> str:
    if only:
        floor = min((v["weight"] for v in table.values()), default=1.0) or 1.0
        items = [(k, table[k]["weight"] if k in table else floor) for k in only if not exclude or k not in exclude]
    else:
        items = [(k, v["weight"]) for k, v in table.items() if not exclude or k not in exclude]
    keys, weights = zip(*items)
    return rng.choices(keys, weights=weights, k=1)[0]


def make_plan(T: dict, rng: random.Random, settings=None, mechanisms=None, endings=None, ghost=None,
              length=None, style="ptt", style_note="", notes=None, taste="直接") -> dict:
    fixed = [n for n, v in (("場景", settings), ("主要機制", mechanisms), ("結尾", endings)) if v]
    setting = weighted_pick(rng, T["settings"], only=settings)
    pair_opts = {k.split("|")[1]: v for k, v in T["pairs"].items() if k.split("|")[0] == setting}
    if mechanisms:
        primary = weighted_pick(rng, T["mechanisms_primary"], only=mechanisms)
    elif pair_opts and rng.random() < 0.7:
        primary = weighted_pick(rng, pair_opts)
    else:
        primary = weighted_pick(rng, T["mechanisms_primary"])
    mechs = [primary]
    if rng.random() < 0.5:
        mechs.append(weighted_pick(rng, T["mechanisms_any"], exclude={primary}))
    ending = weighted_pick(rng, T["endings"], only=endings)

    noisy = {b: max(0.0, T["beats_top"][b] * rng.uniform(0.8, 1.2)) for b in BEATS}
    total = sum(noisy.values()) or 1.0
    beats = {b: v / total for b, v in noisy.items()}

    if ghost is None:
        levels = [int(k) for k in T["ghost_dist_top"]]
        ghost = rng.choices(levels, weights=[T["ghost_dist_top"][str(l)] + 0.5 for l in levels], k=1)[0]
    else:
        fixed.append("鬼露出上限")
    if length:
        target = rng.randint(*length)
        fixed.append("長度")
    else:
        lt = T["length_top"]
        target = max(800, min(rng.randint(min(lt["p25"], lt["p75"]), max(lt["p25"], lt["p75"])), 4000))

    ex = T["examples"]
    same_setting = [e for e in ex if e["setting"] == setting]
    anchors = [a for e in (same_setting or ex) for a in e["anchors"]]
    rng.shuffle(anchors)
    # 結構範例：先挑同場景又同機制的，不夠再補同機制的，最後同場景的
    both = [e for e in same_setting if primary in e["mechanisms"]]
    mech_only = [e for e in ex if primary in e["mechanisms"] and e not in both]
    rng.shuffle(both)
    rng.shuffle(mech_only)
    same_mech = (both + mech_only + [e for e in same_setting if e not in both]) or ex
    if style != "ptt" or style_note:
        fixed.append("風格")
    if taste != "直接":
        fixed.append("口味")
    if notes:
        fixed.append("額外要求")
    return {
        "seed": rng.randint(0, 10**9), "setting": setting, "mechanisms": mechs, "ending": ending,
        "beats": beats, "ghost": ghost, "target_chars": target, "style": style, "style_note": style_note,
        "taste": taste, "notes": list(notes or []), "fixed": fixed,
        "anchor_hints": list(dict.fromkeys(anchors))[:8],
        "structural_examples": [e["premise"] for e in same_mech[:3]],
    }


def render(p: dict) -> str:
    tc = p["target_chars"]
    label, _, summary = STYLES[p["style"]]
    L = [
        f"場景：{SETTINGS[p['setting']]}",
        f"恐怖機制：{MECHANISMS[p['mechanisms'][0]]}（主要）"
        + (f"；{MECHANISMS[p['mechanisms'][1]]}（輔助，可以只是點綴）" if len(p["mechanisms"]) > 1 else ""),
        f"結尾型態：{ENDINGS[p['ending']]}",
        f"鬼的露出上限 ghost_explicitness：{p['ghost']}（{GHOST_LEVELS[p['ghost']]}）",
        f"target_chars：{tc}（誤差兩成內）",
        "節拍字數分配（大約）：" + "、".join(f"{BEAT_LABELS[b]} {int(p['beats'][b] * tc)} 字" for b in BEATS),
        f"風格：{label}（{summary}）" + (f"；補充：{p['style_note']}" if p["style_note"] else ""),
        f"口味：{p['taste']}（{TASTES[p['taste']][1]}）",
        "錨點提示（同場景高分故事用過的細節類型，當提示，不當抄本）：" + "、".join(p["anchor_hints"]),
        "結構範例（只看結構，不看文字，不要重講同一件事）：",
        *[f"  - {s}" for s in p["structural_examples"]],
    ]
    if p["notes"]:
        L.append("使用者的額外要求（一定要做到；跟上面衝突時以這裡為準，但鬼的處理和不抄襲的規則不變）：")
        L += [f"  - {n}" for n in p["notes"]]
    if p["fixed"]:
        L.append("使用者指定的欄位：" + "、".join(p["fixed"]))
    if p["ending"] == "twist":
        L.append("注意：結尾是反轉時，揭露段只寫敘事者當下看到的表面事件，真相留給最後一兩句翻；兩段不要搶同一個高潮。")
    if p["ending"] == "explained":
        L.append("注意：結尾是有解釋時，解釋要從別人嘴裡說出來（長輩、廟公、鄰居、查到的紀錄），不是敘事者自己推理。")
    return "\n".join(L)


def count_chars(text: str) -> int:
    body = text.split("\n", 1)[1] if "\n" in text else text
    return sum(1 for ch in body if not ch.isspace())


SURFACE = HERE.parent / "assets" / "surface.json"
_LINE_END = re.compile(r"[，。！？」』…、：；.!?)）~～]$")
SURFACE_ADVICE = {  # (too few, too many)
    "line_chars": ("一行太短，像在寫詩；把短行接起來", "手動斷行：一行 15 到 30 字，在停頓的地方就換行，不用等句子講完"),
    "open_lines": ("換行就是停頓：斷在句子中間的行，行尾不用再打逗號", "幾乎每行都斷在句中，讀起來太碎；有些行講完一句再換"),
    "sentence_spread": ("句子長短要亂：有一口氣用逗號接到底的長句，也有兩三個字的短句", "長句太多，拆幾句短的出來"),
    "quotes": ("至少讓旁人的一兩句反應用他們自己的話說出來", "引號對話太多：大部分改成轉述（學姊說她……），只留最關鍵的一兩句用「」"),
    "ellipses": ("講到一半、不想講下去的地方用「...」", "「...」太多，留在真的講不下去的地方"),
    "marks": ("反應和自問自答用問號、驚嘆號（蛤？、真的假的！）", "問號驚嘆號太多，像在喊"),
    "digits": ("時間、年紀、樓層、年份用阿拉伯數字（3點、25歲、7樓、2015年）", "數字太多，像在寫報告"),
}


def surface(text: str) -> dict[str, float]:
    """How the body looks on the page, the numbers a reader notices before reading a word. Real top marvel posts
    break lines by hand (about 23 characters a line, more than half the lines ending mid-sentence), vary sentence
    length wildly, report most speech instead of quoting it, and write times as digits; the first generated stories
    wrote one paragraph per line in even sentences and the owner spotted every one of them."""
    body = text.split("\n", 1)[1] if "\n" in text else text
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    chars = sum(len(l) for l in lines) or 1
    sents = [len(s) for s in re.split(r"[。！？!?]", body) if s.strip()]
    mean = sum(sents) / len(sents) if sents else 0
    spread = (sum((s - mean) ** 2 for s in sents) / len(sents)) ** 0.5 if sents else 0
    lens = sorted(len(l) for l in lines) or [0]
    k = 1000 / chars
    return {
        "line_chars": lens[len(lens) // 2],
        "open_lines": 100 * sum(1 for l in lines if not _LINE_END.search(l)) / max(1, len(lines)),
        "sentence_spread": spread,
        "quotes": body.count("「") * k,
        "ellipses": len(re.findall(r"\.\.\.|…|。。", body)) * k,
        "marks": len(re.findall(r"[？！?!]", body)) * k,
        "digits": len(re.findall(r"\d", body)) * k,
    }


_DISCLAIMER = re.compile(r"排版|飄點|文筆")
TELL_ADVICE = {
    "opening_disclaimer": ("建議", "開頭的免責（手機排版、飄點微弱、文筆差）熱門文只有少數有，大多直接講事情；五篇最多一篇用"),
    "quote_ending": ("必改", "最後一句不要是一句「」對白：停在敘事者自己的一句話、現在的狀況或一個細節；對白翻完，後面再接一兩句自己的話"),
    "title_na": ("建議", "標題用直白的名詞（麵攤的阿伯、重修微積分的學長），不要「XX那YY」（那晚、那張、那個禮拜）"),
}


def tells(text: str) -> dict[str, bool]:
    """Habits of the generated drafts that real top posts rarely have: a disclaimer in the first lines (every draft,
    a sixth of real posts), a quoted line in the last three (nearly every draft, 7% of real posts), 那 in the title
    (four drafts in ten, 3% of real posts). Each is fine once in a while; together they give a draft away."""
    title, _, body = text.strip().partition("\n")
    lines = [l for l in body.splitlines() if l.strip()]
    return {"opening_disclaimer": bool(_DISCLAIMER.search("\n".join(lines[:3]))),
            "quote_ending": "「" in "\n".join(lines[-3:]),
            "title_na": "那" in re.sub(r"^\s*\[[^\]]*\]\s*", "", title)}


def surface_report(text: str, table: dict) -> list[str]:
    """One line per measure off the real top posts (table: assets/surface.json): 必改 outside their middle 80%,
    建議 outside their middle half. Real posts vary a lot, so a single measure at an edge is fine; a draft at the edge
    of all of them at once (no ellipsis, no digits, few marks, every line a paragraph) is what reads as generated."""
    out = []
    for name, v in surface(text).items():
        r = table["features"][name]
        for lo, hi, level in (("p10", "p90", "必改"), ("p25", "p75", "建議")):
            if v < r[lo] or v > r[hi]:
                low = v < r[lo]
                out.append(f"{level} {name} {v:.1f}（熱門文中間 {r[lo]:.1f} 到 {r[hi]:.1f}，{'太少' if low else '太多'}）："
                           f"{SURFACE_ADVICE[name][0 if low else 1]}")
                break
    for name, hit in tells(text).items():
        if hit:
            level, advice = TELL_ADVICE[name]
            rate = table.get("tells", {}).get(name)
            out.append(f"{level} {name}（熱門文 {rate:.0%} 這樣寫）：{advice}" if rate is not None else f"{level} {name}：{advice}")
    return out


DISCLOSURE = "（AI 輔助創作，故事純屬虛構）"
_TAG = re.compile(r"^\s*\[(經驗|真實|翻譯|創作)\]\s*")
_SENT = re.compile(r"(?<=[。！？…])(?![」』）])|(?<=[」』）])")


def post_title(title: str) -> str:
    """A generated story is fiction: a marvel [經驗] tag says it happened, so posts use [創作]."""
    return "[創作] " + _TAG.sub("", title).strip()


def _pieces(body: str, room: int) -> list[str]:
    """Paragraphs, then sentences, then hard cuts: every piece fits in `room` characters."""
    out = []
    for para in body.split("\n"):
        if len(para) <= room:
            out.append(para)
            continue
        for s in (x for x in _SENT.split(para) if x):
            while len(s) > room:
                out.append(s[:room])
                s = s[room:]
            out.append(s)
    return out


def _pack(pieces: list[str], room: int) -> list[str]:
    """Pieces joined by line breaks into chunks of at most `room` characters."""
    chunks, cur = [], ""
    for p in pieces:
        joined = (cur + "\n" + p) if cur else p
        if len(joined) <= room:
            cur = joined
            continue
        if cur.strip():
            chunks.append(cur.strip("\n"))
        cur = p
    if cur.strip():
        chunks.append(cur.strip("\n"))
    return chunks


def make_posts(text: str, mode: str = "attach", limit: int = 500) -> dict:
    """attach: one post (title, disclosure, the opening up to the limit, cut at a paragraph or sentence) plus the
    whole story as a text attachment. chain: the story in numbered posts of at most `limit` characters, cut at
    paragraphs or sentences. ig: one caption within Instagram's 2,200 characters with the opening and the disclosure."""
    title, _, body = text.strip().partition("\n")
    head = f"{post_title(title)}\n{DISCLOSURE}\n\n"
    body = body.strip("\n")
    if mode == "chain":
        room = limit - len(" (99/99)")
        first = _pack(_pieces(body, room - len(head)), room - len(head))
        rest = _pack(_pieces("\n".join(first[1:]), room), room) if len(first) > 1 else []
        chunks = [head + first[0]] + rest
        n = len(chunks)
        return {"posts": [f"{c} ({i}/{n})" if n > 1 else c for i, c in enumerate(chunks, 1)], "attachment": None}
    if mode == "ig":
        tail = "\n\n（全文看輪播）\n\n#鬼故事 #靈異 #怪談 #創作"
        room = 2200 - len(head) - len(tail)
        return {"posts": [head + _pack(_pieces(body, room), room)[0] + tail], "attachment": None}
    more = "……（全文在附件）"
    room = limit - len(head) - len(more)
    return {"posts": [head + _pack(_pieces(body, room), room)[0] + more],
            "attachment": f"{post_title(title)}\n{DISCLOSURE}\n\n{body}"}


def describe() -> str:
    L = ["場景（--setting，可多個，用逗號分開）："] + [f"  {k:<15} {v}" for k, v in SETTINGS.items()]
    L += ["", "主要機制（--mechanism）："] + [f"  {k:<15} {v}" for k, v in MECHANISMS.items()]
    L += ["", "結尾（--ending）："] + [f"  {k:<15} {v}" for k, v in ENDINGS.items()]
    L += ["", "鬼露出上限（--ghost）：0 到 3，或 " + "、".join(f"{w}={n}" for w, n in GHOST_WORDS.items())]
    L += ["", "長度（--length）：字數、範圍，或"] + [f"  {k:<4} {lo} 到 {hi} 字" for k, (lo, hi) in LENGTH_PRESETS.items()]
    L += ["", "風格（--style）："] + [f"  {k:<10} {v[0]:<6} {v[2]}" for k, v in STYLES.items()]
    L += ["", "口味（--taste）："] + [f"  {k:<4} {v[1]}" for k, v in TASTES.items()]
    L += ["", "額外要求（--note，可重複）：自由描述，例如「主角是護理師」「發生在颱風夜」"]
    return "\n".join(L)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("plan")
    for opt in ("--setting", "--mechanism", "--ending", "--ghost", "--length", "--style", "--style-note", "--taste"):
        p.add_argument(opt, default=None)
    p.add_argument("--note", action="append", default=None)
    p.add_argument("--seed", type=int, default=None, help="可重現；配合 --count 時從這個 seed 往上連號")
    p.add_argument("--count", type=int, default=1, help="一次抽幾副骨架（要寫幾篇來比，SKILL.md 預設 3）")
    p.add_argument("--json", action="store_true", help="印 JSON 而不是說明文字")
    sub.add_parser("options")
    c = sub.add_parser("count")
    c.add_argument("file")
    su = sub.add_parser("surface")
    su.add_argument("file")
    po = sub.add_parser("post")
    po.add_argument("file")
    po.add_argument("--mode", choices=["attach", "chain", "ig"], default="attach")
    po.add_argument("--limit", type=int, default=500, help="Threads 單篇上限")
    a = ap.parse_args(argv)
    if a.cmd == "options":
        print(describe())
        return 0
    if a.cmd == "count":
        print(count_chars(Path(a.file).read_text(encoding="utf-8")))
        return 0
    if a.cmd == "surface":
        text = Path(a.file).read_text(encoding="utf-8")
        table = json.loads(SURFACE.read_text(encoding="utf-8"))
        for name, v in surface(text).items():
            r = table["features"][name]
            print(f"{name:<16} {v:6.1f}   熱門文 {r['p10']:.1f} / {r['p50']:.1f} / {r['p90']:.1f}")
        issues = surface_report(text, table)
        print("\n" + ("\n".join("- " + m for m in issues) if issues else "都在熱門文的範圍內"))
        return 0
    if a.cmd == "post":
        r = make_posts(Path(a.file).read_text(encoding="utf-8"), a.mode, a.limit)
        for i, p in enumerate(r["posts"], 1):
            print(f"===== 第 {i} 則（{len(p)} 字）=====\n{p}\n")
        if r["attachment"]:
            print(f"===== 文字附件（{len(r['attachment'])} 字）=====\n{r['attachment']}")
        return 0
    if a.cmd != "plan":
        ap.print_help()
        return 1
    try:
        kw = dict(settings=resolve_list("setting", a.setting), mechanisms=resolve_list("mechanism", a.mechanism),
                  endings=resolve_list("ending", a.ending), ghost=resolve_ghost(a.ghost), length=resolve_length(a.length),
                  style=resolve_style(a.style), style_note=a.style_note or "", notes=a.note or [], taste=resolve_taste(a.taste))
    except OptionError as e:
        print(f"選項錯誤：{e}", file=sys.stderr)
        return 2
    T = json.loads(TABLE.read_text(encoding="utf-8"))
    n = max(1, a.count)
    base = a.seed if a.seed is not None else None
    plans = []
    for i in range(n):
        seed = base + i if base is not None else random.randrange(10**9)
        plan = make_plan(T, random.Random(seed), **kw)
        plan["seed"] = seed
        plans.append(plan)
    if a.json:
        print(json.dumps(plans[0] if n == 1 else plans, ensure_ascii=False, indent=1))
    else:
        for i, plan in enumerate(plans, 1):
            head = f"===== 骨架 {i}/{n}\n" if n > 1 else ""
            print(head + f"seed={plan['seed']}\n" + render(plan) + ("\n" if n > 1 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
