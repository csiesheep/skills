"""結構 schema：標註（LLM 輸出）、評審（LLM 輸出）、規劃（純 Python）。

欄位從類型設定（genre.json）長出來；標註、統計、規劃、評審四個階段共用這一份定義。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, create_model

from .genre import GENRE

BEATS: list[str] = list(GENRE.beats)
BEAT_LABELS: dict[str, str] = dict(GENRE.beats)
VOICE_MARKERS: dict[str, str] = dict(GENRE.voice_markers)


# ---------------------------------------------------------------------------
# 標註 schema（LLM 輸出）
# ---------------------------------------------------------------------------


class _BeatBase(BaseModel):
    """各節拍佔全文的比例，加總約為 1。"""

    def normalized(self):
        d = self.model_dump()
        total = sum(d.values()) or 1.0
        return self.__class__(**{k: v / total for k, v in d.items()})


BeatShare = create_model("BeatShare", __base__=_BeatBase, **{b: (float, Field(ge=0, le=1)) for b in BEATS})  # type: ignore[call-overload]


def _annotation_model():
    fields: dict = {"is_story": (bool, Field(description=GENRE.is_unit_description))}
    for ax in GENRE.axes:
        lit = Literal[tuple(ax.values)]  # type: ignore[valid-type]
        if ax.multi:
            fields[ax.key] = (list[lit], Field(min_length=1, max_length=ax.max_items, description=ax.description))  # type: ignore[valid-type]
        else:
            fields[ax.key] = (lit, Field(description=ax.description))
        if ax.detail:
            fields[ax.detail.key] = (str, Field(description=ax.detail.description))
    fields["beats"] = (BeatShare, Field(description="各節拍佔全文的比例，加總為 1：" + "、".join(f"{k}={v}" for k, v in GENRE.beats.items())))
    fields[GENRE.cap.key] = (int, Field(ge=GENRE.cap.min, le=GENRE.cap.max, description=GENRE.cap.description))
    fields[GENRE.anchors.key] = (list[str], Field(max_length=GENRE.anchors.max_items or 8, description=GENRE.anchors.description))
    if VOICE_MARKERS:
        fields["voice_markers"] = (list[Literal[tuple(VOICE_MARKERS)]], Field(description="只勾實際出現的"))  # type: ignore[valid-type]
    else:
        fields["voice_markers"] = (list[str], Field(default_factory=list))
    fields[GENRE.moment.key] = (str, Field(description=GENRE.moment.description))
    fields[GENRE.premise.key] = (str, Field(description=GENRE.premise.description))
    return create_model("Annotation", **fields)


Annotation = _annotation_model()
"""一個單位的結構 DNA。不含原文。"""


# ---------------------------------------------------------------------------
# 評審 schema（LLM 輸出）
# ---------------------------------------------------------------------------


def _verdict_model():
    fields: dict = {k: (int, Field(ge=1, le=5, description=desc)) for k, desc in GENRE.verdict_dims.items()}
    fields["overall"] = (int, Field(ge=1, le=10))
    fields["passes"] = (bool, Field())
    fields["fix_notes"] = (list[str], Field(max_length=5, description="具體到段落的改法"))
    return create_model("Verdict", **fields)


Verdict = _verdict_model()
VERDICT_DIMS: list[str] = list(GENRE.verdict_dims)


# ---------------------------------------------------------------------------
# 規劃器輸出（純 Python，不經 LLM）
# ---------------------------------------------------------------------------


class Plan(BaseModel):
    axes: dict[str, list[str]] = Field(description="每個軸抽到的值；單值軸是一個元素，多值軸第一個是主要的")
    axis_labels: dict[str, list[str]]
    cap: int
    beats: dict[str, float]
    target_chars: int
    anchor_hints: list[str] = Field(description="同類高分單位用過的錨點類型，當提示不當抄本")
    structural_examples: list[str] = Field(description="同類高分單位的一句話前提，看結構不看文字")
    seed: int
    style: str = ""
    style_label: str = ""
    style_note: str = Field(default="", description="使用者自由描述的風格補充")
    user_notes: list[str] = Field(default_factory=list, description="使用者的額外要求")
    fixed: list[str] = Field(default_factory=list, description="哪些欄位是使用者指定的，評審要特別檢查")
    rules: str = Field(default="", description="寫作和評審規則的版本，對應 genre.json 的 rule_sets")

    def primary(self, axis_key: str) -> str:
        return self.axes[axis_key][0]
