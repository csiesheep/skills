"""產生故事時的使用者選項：用中文說法指定場景、機制、結尾、鬼露出、長度、風格。

resolve("setting", "校園") → "school"；可以給 key、中文標籤的一部分、或常用別名。
多個值用逗號分開，規劃器會只在這些裡面依權重抽。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .taxonomy import ENDINGS, MECHANISMS, SETTINGS

from .paths import PROMPTS_DIR  # noqa: E402

_ALIASES: dict[str, dict[str, str]] = {
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
        "不是人": "identity_swap", "不是本人": "identity_swap", "身份": "identity_swap",
        "時間": "time_slip", "失控": "escalation", "升級": "escalation",
        "禁忌": "taboo", "報應": "taboo", "事後": "retro_reveal",
        "對不上": "witness_mismatch", "見證": "witness_mismatch",
        "循環": "repetition", "重複": "repetition", "在場": "presence", "感覺": "presence",
        "善意": "benign", "守護": "benign", "報恩": "benign",
        "附身": "possession", "卡到": "possession", "煞到": "possession",
        "物件": "object", "娃娃": "object", "照片": "object",
        "夢": "dream", "託夢": "dead_contact", "聲音": "sound_only",
        "亡者": "dead_contact", "來電": "dead_contact", "通靈": "proxy_sighting", "陰陽眼": "proxy_sighting",
    },
    "ending": {
        "開放": "open", "開放結局": "open", "開放式": "open", "沒解釋": "open", "沒有解釋": "open",
        "解釋": "explained", "有解釋": "explained", "解答": "explained",
        "反轉": "twist", "翻轉": "twist", "逆轉": "twist",
        "淡出": "fade", "搬走": "fade", "沒事": "fade",
    },
}

_TABLES = {"setting": SETTINGS, "mechanism": MECHANISMS, "ending": ENDINGS}
_SUFFIX = re.compile(r"(結局|結尾|收尾|型|類|式)$")


class OptionError(ValueError):
    pass


def resolve(kind: str, text: str) -> str:
    """把一個說法對應到 key。對不到或對到多個就報錯，錯誤訊息列出可用的選項。"""
    table = _TABLES[kind]
    t = text.strip()
    if t in table:
        return t
    for cand in (t, _SUFFIX.sub("", t)):
        if cand in _ALIASES[kind]:
            return _ALIASES[kind][cand]
    hits = [k for k, label in table.items() if t in label or _SUFFIX.sub("", t) in label.split("：")[0]]
    if len(hits) == 1:
        return hits[0]
    choices = "、".join(f"{k}（{v.split('：')[0]}）" for k, v in table.items())
    if not hits:
        raise OptionError(f"「{text}」對不到任何{kind}。可用：{choices}")
    raise OptionError(f"「{text}」同時符合 {hits}，請說得更具體。可用：{choices}")


def resolve_list(kind: str, text: str | None) -> list[str] | None:
    if not text:
        return None
    return list(dict.fromkeys(resolve(kind, x) for x in re.split(r"[,，、/／\s]+", text) if x.strip()))


# ---------------------------------------------------------------------------
# 鬼露出
# ---------------------------------------------------------------------------

_GHOST_WORDS = {
    "不露面": 0, "完全不出現": 0, "看不到": 0, "沒有鬼": 0,
    "間接": 1, "只有跡象": 1, "聲音": 1, "暗示": 1,
    "一瞬間": 2, "一閃": 2, "瞥見": 2, "黑影": 2,
    "清楚": 3, "正面": 3, "直接": 3, "看得很清楚": 3,
}


def resolve_ghost(text: str | int | None) -> int | None:
    if text is None or text == "":
        return None
    if isinstance(text, int) or str(text).strip().isdigit():
        v = int(text)
        if 0 <= v <= 3:
            return v
        raise OptionError("鬼露出是 0 到 3")
    t = str(text).strip()
    if t in _GHOST_WORDS:
        return _GHOST_WORDS[t]
    raise OptionError(f"鬼露出「{t}」看不懂。用 0 到 3，或：" + "、".join(_GHOST_WORDS))


# ---------------------------------------------------------------------------
# 長度
# ---------------------------------------------------------------------------

LENGTH_PRESETS: dict[str, tuple[int, int]] = {
    "極短": (400, 700),
    "短": (800, 1200),
    "中": (1500, 2500),
    "長": (3000, 4500),
    "超長": (5000, 8000),
}
_LEN_ALIASES = {"極短篇": "極短", "短篇": "短", "中篇": "中", "中等": "中", "長篇": "長", "很長": "超長"}
MIN_CHARS, MAX_CHARS = 300, 12000


def resolve_length(text: str | int | None) -> tuple[int, int] | None:
    """回傳 (下限, 上限)。給單一數字就是 (n, n)；給「1500-2500」就是範圍；給預設名稱就查表。"""
    if text is None or text == "":
        return None
    t = str(text).strip().replace("字", "").replace("，", ",")
    t = _LEN_ALIASES.get(t, t)
    if t in LENGTH_PRESETS:
        return LENGTH_PRESETS[t]
    m = re.fullmatch(r"(\d+)\s*(?:[-~～到]\s*(\d+))?", t)
    if not m:
        raise OptionError(f"長度「{text}」看不懂。用字數（1500）、範圍（1500-2500）、或：" + "、".join(LENGTH_PRESETS))
    lo = int(m.group(1))
    hi = int(m.group(2) or lo)
    lo, hi = min(lo, hi), max(lo, hi)
    if lo < MIN_CHARS or hi > MAX_CHARS:
        raise OptionError(f"長度要在 {MIN_CHARS} 到 {MAX_CHARS} 字之間")
    return lo, hi


# ---------------------------------------------------------------------------
# 風格
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Style:
    key: str
    label: str
    aliases: tuple[str, ...]
    summary: str  # 一句話，給評審看

    def prompt(self, rules: str = "v2") -> str:
        # 留白和舊規則用舊版的風格說明（例如「簡約」的最可怕那一幕要省著寫）
        base = PROMPTS_DIR / "v1" if rules in ("v1", "restrained") else PROMPTS_DIR
        return (base / "styles" / f"{self.key}.md").read_text(encoding="utf-8")


STYLES: dict[str, Style] = {
    s.key: s
    for s in [
        Style("ptt", "PTT 鄉民", ("鄉民", "預設", "批踢踢", "口語", "經驗文"), "PTT marvel 板 [經驗] 文的鄉民口吻，口語、粗糙、有免責開頭"),
        Style("minimal", "簡約", ("簡潔", "極簡", "白描", "冷"), "短句白描，形容詞極少，留白多，不解釋情緒"),
        Style("humor", "幽默", ("搞笑", "好笑", "吐槽", "自嘲"), "自嘲吐槽的輕鬆口吻，前段好笑，越接近揭露越收，最後一定是毛的"),
        Style("oral", "口述", ("講故事", "說書", "節目", "podcast", "微疼", "聽眾"), "像在節目或宵夜攤上講給一群人聽，有跟聽眾的互動和停頓"),
        Style("literary", "文學", ("文青", "細膩", "文藝", "散文"), "散文式的細膩描寫，有意象和節制的抒情，但事件本身仍是真實經驗的規模"),
        Style("report", "紀錄", ("日誌", "報告", "冷靜", "紀錄體", "值班日誌"), "像值班日誌或事件紀錄，有時間戳記，語氣冷靜，情緒只從細節漏出來"),
        Style("elder", "長輩講古", ("講古", "阿嬤", "阿公", "長輩", "台語"), "轉述長輩講的往事，夾台語和舊時代細節，長輩的語氣篤定，敘事者半信半疑"),
    ]
}


def resolve_style(text: str | None) -> Style:
    if not text:
        return STYLES["ptt"]
    t = text.strip()
    if t in STYLES:
        return STYLES[t]
    for s in STYLES.values():
        if t == s.label or t in s.aliases or t in s.label:
            return s
    raise OptionError(f"風格「{text}」看不懂。可用：" + "、".join(f"{s.key}（{s.label}）" for s in STYLES.values()))


# 口味：兩套寫作和評審規則。直接 = 照 PTT 讀者資料（看得到的鬼、篤定）；留白 = 克制（上限內留白、可以不確定）。
TASTES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "直接": ("v2", "照 PTT 讀者的資料：最可怕那一幕寫出看到什麼，語氣篤定（預設）", ("具體", "爆文", "ptt", "資料", "v2", "預設")),
    "留白": ("restrained", "克制：鬼的露出上限內也留白，靠旁人反應撐，可以留一點不確定", ("克制", "含蓄", "細膩", "隱晦", "restrained")),
}


def resolve_taste(text: str | None) -> tuple[str, str]:
    """回傳 (口味名稱, 規則版本)。沒給就是「直接」。"""
    if not text:
        return "直接", TASTES["直接"][0]
    t = text.strip()
    for name, (rules, _, aliases) in TASTES.items():
        if t == name or t.lower() in aliases:
            return name, rules
    raise OptionError(f"口味「{text}」看不懂。可用：" + "、".join(TASTES))


def describe_options() -> str:
    """給 `ghost options` 印出來的說明。"""
    L = ["場景（--setting，可多個，用逗號分開）："]
    L += [f"  {k:<15} {v}" for k, v in SETTINGS.items()]
    L += ["", "主要機制（--mechanism）："]
    L += [f"  {k:<15} {v}" for k, v in MECHANISMS.items()]
    L += ["", "結尾（--ending）："]
    L += [f"  {k:<15} {v}" for k, v in ENDINGS.items()]
    L += ["", "鬼露出上限（--ghost）：0 到 3，或 " + "、".join(f"{w}={n}" for w, n in _GHOST_WORDS.items())]
    L += ["", "長度（--length）：字數（1500）、範圍（1500-2500），或"]
    L += [f"  {k:<4} {lo} 到 {hi} 字" for k, (lo, hi) in LENGTH_PRESETS.items()]
    L += ["", "風格（--style）："]
    L += [f"  {s.key:<10} {s.label:<6} {s.summary}" for s in STYLES.values()]
    L += ["", "口味（--taste）："]
    L += [f"  {name:<4} {desc}" for name, (_, desc, _) in TASTES.items()]
    L += ["", "額外要求（--note，可重複）：自由描述，例如「主角是護理師」「發生在颱風夜」"]
    L += ["", "中文說法也可以，例如 --setting 校園,宿舍 --ending 開放結局 --length 短 --style 幽默"]
    return "\n".join(L)
