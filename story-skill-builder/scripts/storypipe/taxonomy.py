"""故事 DNA 的詞彙表與結構 schema。

標註、統計、規劃、評審四個階段共用這一份定義；改這裡就等於改整條管線的語言。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 詞彙表
# ---------------------------------------------------------------------------

SETTINGS: dict[str, str] = {
    "dorm": "學校宿舍",
    "military": "當兵／軍營／營區",
    "night_shift": "夜班／值班／警衛",
    "mountain": "山路／山區／登山",
    "rental": "租屋處／老公寓／套房",
    "hospital": "醫院／診所／照護",
    "store": "超商／店面／打工",
    "old_house": "老家／鄉下老宅／三合院",
    "school": "校園／教室／社團",
    "hotel": "飯店／旅館／民宿",
    "road": "深夜開車／騎車／夜路",
    "funeral": "喪事／靈堂／塔位／告別式",
    "temple": "廟宇／宮壇／儀式／收驚",
    "office": "辦公室／公司／廠房",
    "transport": "公車／捷運／火車／計程車",
    "childhood_home": "童年家中／親戚家",
    "home": "自家／現在住的家（非租屋、非童年）",
    "ruins": "廢墟／廢棄建築／探險",
    "stairwell": "電梯／樓梯間／頂樓",
    "abroad": "國外旅行／出差",
    "water": "海邊／溪邊／水域",
    "other": "其他",
}

MECHANISMS: dict[str, str] = {
    "identity_swap": "身份錯置：那個人不是人，或不是本人",
    "time_slip": "時間錯亂：時序對不上、多出或少掉一段時間",
    "escalation": "逐步失控：小異常一路升級",
    "taboo": "犯禁忌後的報應",
    "retro_reveal": "事後才知道：事後才拼出真相才發毛",
    "witness_mismatch": "見證不一致：別人看到的和我不一樣",
    "repetition": "重複／循環：同一件事一再發生",
    "presence": "在場感：有東西在，但看不到",
    "benign": "善意／報恩／守護型",
    "possession": "附身／精神異常／卡到",
    "object": "物件作祟：照片、娃娃、衣物、手機",
    "dream": "夢境滲入現實",
    "sound_only": "只有聲音，沒有影像",
    "dead_contact": "亡者來電／訊息／託夢：已故者主動聯絡",
    "proxy_sighting": "透過第三者看見：自己沒感覺，通靈的親友描述得很具體",
}

ENDINGS: dict[str, str] = {
    "open": "開放：沒有解釋，就這樣結束",
    "explained": "有解釋：事後被人點破或查到前因",
    "twist": "反轉：最後一兩句把前面翻掉",
    "fade": "淡出：搬走、不再去、慢慢沒事",
}

BEATS: list[str] = ["normal", "anomaly", "denial", "escalation", "reveal", "aftermath"]
BEAT_LABELS: dict[str, str] = {
    "normal": "正常生活鋪陳",
    "anomaly": "第一個小異常",
    "denial": "合理化／否認",
    "escalation": "升級",
    "reveal": "揭露／最可怕的一刻",
    "aftermath": "餘波",
}

VOICE_MARKERS: dict[str, str] = {
    "first_person": "第一人稱親身經歷",
    "friend_of_friend": "朋友的朋友／家人的事",
    "disclaimer": "開頭免責：飄點微弱、文筆不好",
    "ptt_jargon": "鄉民用語、注音文、XD",
    "ai_polished": "自承用 AI 潤飾",
    "location_specific": "有具體地點（縣市、路名、幾樓）",
    "time_specific": "有具體時間（幾點、季節、年份）",
    "procedure_detail": "有日常程序細節（值班流程、宿舍規定）",
    "dialogue": "有對話",
    "self_doubt": "作者自己也懷疑是不是想太多",
    "translated": "翻譯或轉述外國（日本、韓國等）的故事，不是台灣在地經驗",
}

SettingKey = Literal[tuple(SETTINGS)]  # type: ignore[valid-type]
MechanismKey = Literal[tuple(MECHANISMS)]  # type: ignore[valid-type]
EndingKey = Literal[tuple(ENDINGS)]  # type: ignore[valid-type]
VoiceKey = Literal[tuple(VOICE_MARKERS)]  # type: ignore[valid-type]


# ---------------------------------------------------------------------------
# 標註 schema（LLM 輸出）
# ---------------------------------------------------------------------------


class BeatShare(BaseModel):
    """六個節拍各佔全文的比例，加總約為 1。"""

    normal: float = Field(ge=0, le=1)
    anomaly: float = Field(ge=0, le=1)
    denial: float = Field(ge=0, le=1)
    escalation: float = Field(ge=0, le=1)
    reveal: float = Field(ge=0, le=1)
    aftermath: float = Field(ge=0, le=1)

    def normalized(self) -> "BeatShare":
        total = sum(self.model_dump().values()) or 1.0
        return BeatShare(**{k: v / total for k, v in self.model_dump().items()})


class Annotation(BaseModel):
    """一篇故事的結構 DNA。不含原文。"""

    is_story: bool = Field(description="是不是一篇可以獨立閱讀的鬼故事；問卦、討論、轉貼、系列中段都是 false")
    setting: SettingKey
    setting_detail: str = Field(description="最可怕那一幕發生的具體場景，30 字內，例如「中部某大學女宿三樓廁所」")
    mechanisms: list[MechanismKey] = Field(min_length=1, max_length=3, description="依重要性排序；第一個是最可怕那一幕為什麼可怕")
    ending: EndingKey
    beats: BeatShare
    ghost_explicitness: int = Field(ge=0, le=3, description="0 完全沒正面寫鬼；1 只有間接跡象；2 有一瞬間看見；3 清楚描述外觀或互動")
    realism_anchors: list[str] = Field(max_length=6, description="讓它像真的細節，每個 15 字內")
    voice_markers: list[VoiceKey]
    scariest_moment: str = Field(description="最可怕的一刻，用自己的話一句講完，40 字內")
    one_line_premise: str = Field(description="一句話前提，45 字內，不抄原文")


# ---------------------------------------------------------------------------
# 評審 schema（LLM 輸出）
# ---------------------------------------------------------------------------


class Verdict(BaseModel):
    realism: int = Field(ge=1, le=5, description="真實感：錨點夠不夠具體、日常")
    slow_burn: int = Field(ge=1, le=5, description="鋪陳：有沒有正常段和否認段，還是一開始就在鬧")
    ghost_restraint: int = Field(ge=1, le=5, description="鬼的處理，照評分規則打分")
    ending: int = Field(ge=1, le=5, description="結尾餘味：收太乾淨或加道德教訓扣分")
    voice: int = Field(ge=1, le=5, description="像不像 PTT 真人發文；AI 腔扣分")
    overall: int = Field(ge=1, le=10)
    passes: bool
    fix_notes: list[str] = Field(max_length=5, description="具體到段落的改法")


# ---------------------------------------------------------------------------
# 規劃器輸出（純 Python，不經 LLM）
# ---------------------------------------------------------------------------


class Plan(BaseModel):
    setting: SettingKey
    setting_label: str
    mechanisms: list[MechanismKey]
    mechanism_labels: list[str]
    ending: EndingKey
    ending_label: str
    beats: BeatShare
    ghost_explicitness: int
    target_chars: int
    anchor_hints: list[str] = Field(description="同場景高分故事用過的錨點類型，當提示不當抄本")
    structural_examples: list[str] = Field(description="同機制高分故事的一句話前提，看結構不看文字")
    seed: int
    style: str = "ptt"
    style_label: str = "PTT 鄉民"
    style_note: str = Field(default="", description="使用者自由描述的風格補充")
    user_notes: list[str] = Field(default_factory=list, description="使用者的額外要求")
    fixed: list[str] = Field(default_factory=list, description="哪些欄位是使用者指定的，評審要特別檢查")
    rules: str = Field(default="v2", description="寫作和評審規則的版本：v1 是 2026-10-14 前的舊規則（留白、自我懷疑），v2 照全量資料修過")
