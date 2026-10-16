"""類型設定：一個類型的詞彙表、標註欄位、選項說法、長度、風格、口味，全部來自 genre.json。

管線的程式只認這裡的結構，不認任何一個類型的字；換類型就是把 STORYPIPE_GENRE 指到另一個資料夾。
範例：genres/ghost-story/genre.json。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .paths import GENRE_DIR


class GenreError(ValueError):
    pass


@dataclass(frozen=True)
class TextField:
    """標註裡的自由文字欄位（場景細節、錨點、最可怕的一刻、一句話前提）。"""

    key: str
    description: str
    max_chars: int
    label: str = ""
    max_items: int | None = None  # 清單欄位才有
    plan_hint: str = ""


@dataclass(frozen=True)
class Axis:
    """一個類別軸：標註時選一個（或依序選幾個）值，統計時算權重，產生時依權重抽。"""

    key: str
    label: str
    flag: str
    values: dict[str, str]
    aliases: dict[str, str] = field(default_factory=dict)
    multi: bool = False
    max_items: int = 1
    description: str = ""
    fixed_label: str = ""
    detail: TextField | None = None
    plan_notes: dict[str, str] = field(default_factory=dict)

    def label_of(self, key: str) -> str:
        return self.values.get(key, key)

    def short(self, key: str) -> str:
        return self.label_of(key).split("：")[0]

    def primary(self, annotation: dict) -> str | None:
        """標註裡這個軸的主要值：單值軸就是那個值，多值軸是第一個。"""
        v = annotation.get(self.key)
        if isinstance(v, list):
            return v[0] if v else None
        return v

    def all_values(self, annotation: dict) -> list[str]:
        v = annotation.get(self.key)
        if v is None:
            return []
        return list(v) if isinstance(v, list) else [v]

    @property
    def fixed_name(self) -> str:
        return self.fixed_label or self.label


@dataclass(frozen=True)
class Cap:
    """露出上限：一個整數刻度，規劃器給寫手一個上限，評審檢查有沒有超過。"""

    key: str
    label: str
    flag: str
    min: int
    max: int
    description: str
    short: str = ""
    levels: dict[str, str] = field(default_factory=dict)
    words: dict[str, int] = field(default_factory=dict)

    def level_label(self, n: int) -> str:
        name = self.levels.get(str(n))
        return f"{n}（{name}）" if name else str(n)

    @property
    def short_name(self) -> str:
        return self.short or self.label


@dataclass(frozen=True)
class Source:
    kind: str
    board: str
    tags: dict[str, str]  # 標籤 → 索引檔（算百分位的母體）
    default_tag: str
    default_query: str = ""
    score_from_year: int = 0


@dataclass(frozen=True)
class Length:
    presets: dict[str, tuple[int, int]]
    aliases: dict[str, str]
    min: int
    max: int
    sample_clamp: tuple[int, int]


@dataclass(frozen=True)
class StyleSpec:
    key: str
    label: str
    aliases: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class Taste:
    name: str
    rules: str
    summary: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class RuleSet:
    key: str
    dir: str  # prompts/ 底下的子目錄，"" 是根目錄
    styles: str  # 風格檔的目錄


@dataclass(frozen=True)
class Signal:
    positive_name: str
    negative_name: str
    positive: str  # regex
    negative: str  # regex
    min_comments: int = 10


@dataclass(frozen=True)
class Genre:
    name: str
    label: str
    unit: str
    title_prefix: str
    source: Source
    is_unit_description: str
    axes: list[Axis]
    pair: tuple[str, str] | None
    example_axis: str
    example_match_axis: str
    cap: Cap
    beats: dict[str, str]
    anchors: TextField
    moment: TextField
    premise: TextField
    voice_markers: dict[str, str]
    length: Length
    rule_sets: dict[str, RuleSet]
    tastes: dict[str, Taste]
    styles: dict[str, StyleSpec]
    verdict_dims: dict[str, str]
    verdict_cap_dim: str | None
    signal: Signal | None
    path: Path
    better_word: str = "好"  # 盲讀頁的問法：「A 比較毛」「A 比較好笑」

    def axis(self, key_or_flag: str) -> Axis:
        for ax in self.axes:
            if key_or_flag in (ax.key, ax.flag):
                return ax
        raise GenreError(f"類型 {self.name} 沒有「{key_or_flag}」這個軸；有：" + "、".join(a.key for a in self.axes))

    @property
    def default_taste(self) -> str:
        return next(iter(self.tastes))

    @property
    def default_rules(self) -> str:
        return self.tastes[self.default_taste].rules

    @property
    def default_style(self) -> str:
        return next(iter(self.styles))

    @property
    def text_fields(self) -> list[TextField]:
        out = [ax.detail for ax in self.axes if ax.detail]
        return out + [self.anchors, self.moment, self.premise]

    def axis_values(self, annotation: dict) -> dict[str, list[str]]:
        return {ax.key: ax.all_values(annotation) for ax in self.axes}


def _need(d: dict, key: str, where: str):
    if key not in d:
        raise GenreError(f"genre.json 的 {where} 少了「{key}」")
    return d[key]


def _text_field(d: dict, where: str, with_items: bool = False) -> TextField:
    return TextField(
        key=_need(d, "key", where), description=_need(d, "description", where), max_chars=int(_need(d, "max_chars", where)),
        label=d.get("label", ""), max_items=int(d["max_items"]) if with_items and "max_items" in d else None,
        plan_hint=d.get("plan_hint", ""),
    )


def _axis(d: dict) -> Axis:
    key = _need(d, "key", "axes[]")
    values = _need(d, "values", f"axes[{key}]")
    if not values:
        raise GenreError(f"軸 {key} 沒有任何值")
    aliases = d.get("aliases", {})
    bad = [a for a, v in aliases.items() if v not in values]
    if bad:
        raise GenreError(f"軸 {key} 的別名指到不存在的值：{bad}")
    multi = bool(d.get("multi", False))
    return Axis(
        key=key, label=_need(d, "label", f"axes[{key}]"), flag=d.get("flag", key), values=dict(values), aliases=dict(aliases),
        multi=multi, max_items=int(d.get("max_items", 3 if multi else 1)), description=d.get("description", ""),
        fixed_label=d.get("fixed_label", ""), detail=_text_field(d["detail"], f"axes[{key}].detail") if d.get("detail") else None,
        plan_notes=dict(d.get("plan_notes", {})),
    )


def load_genre(path: Path | None = None) -> Genre:
    folder = Path(path) if path else GENRE_DIR
    f = folder / "genre.json"
    if not f.exists():
        raise GenreError(f"找不到類型設定 {f}；用 STORYPIPE_GENRE 指到有 genre.json 和 prompts/ 的資料夾")
    d = json.loads(f.read_text(encoding="utf-8"))
    for k in ("name", "label", "axes", "cap", "beats", "anchors", "moment", "premise", "length", "rule_sets", "tastes", "styles", "verdict"):
        _need(d, k, "最外層")
    axes = [_axis(a) for a in d["axes"]]
    keys = [a.key for a in axes]
    if len(set(keys)) != len(keys):
        raise GenreError(f"軸的 key 重複：{keys}")
    pair = tuple(d["pair"]) if d.get("pair") else None
    if pair:
        if len(pair) != 2 or any(p not in keys for p in pair):
            raise GenreError(f"pair 要是兩個軸的 key：{pair}")
        if keys.index(pair[0]) > keys.index(pair[1]):
            raise GenreError("pair 的第一個軸要排在第二個軸前面（抽樣先抽第一個）")
    example_axis = d.get("example_axis", keys[0])
    example_match_axis = d.get("example_match_axis", keys[-1])
    for k in (example_axis, example_match_axis):
        if k not in keys:
            raise GenreError(f"example_axis / example_match_axis 指到不存在的軸：{k}")
    c = d["cap"]
    cap = Cap(
        key=_need(c, "key", "cap"), label=_need(c, "label", "cap"), flag=c.get("flag", "cap"), min=int(c.get("min", 0)),
        max=int(_need(c, "max", "cap")), description=_need(c, "description", "cap"), short=c.get("short", ""),
        levels={str(k): v for k, v in c.get("levels", {}).items()}, words={k: int(v) for k, v in c.get("words", {}).items()},
    )
    if any(not (cap.min <= v <= cap.max) for v in cap.words.values()):
        raise GenreError("cap.words 有值超出 min 到 max")
    s = d.get("source", {})
    source = Source(
        kind=s.get("kind", "ptt"), board=s.get("board", ""), tags=dict(s.get("tags", {})), default_tag=s.get("default_tag") or next(iter(s.get("tags", {"": ""}))),
        default_query=s.get("default_query", ""), score_from_year=int(s.get("score_from_year", 0)),
    )
    ln = d["length"]
    length = Length(
        presets={k: (int(v[0]), int(v[1])) for k, v in _need(ln, "presets", "length").items()},
        aliases=dict(ln.get("aliases", {})), min=int(ln.get("min", 100)), max=int(ln.get("max", 20000)),
        sample_clamp=tuple(ln.get("sample_clamp", [ln.get("min", 100), ln.get("max", 20000)])),  # type: ignore[arg-type]
    )
    rule_sets = {k: RuleSet(key=k, dir=v.get("dir", ""), styles=v.get("styles", "styles")) for k, v in d["rule_sets"].items()}
    tastes = {}
    for name, t in d["tastes"].items():
        rules = _need(t, "rules", f"tastes[{name}]")
        if rules not in rule_sets:
            raise GenreError(f"口味 {name} 用的規則 {rules} 不在 rule_sets 裡")
        tastes[name] = Taste(name=name, rules=rules, summary=t.get("summary", ""), aliases=tuple(t.get("aliases", [])))
    if not tastes:
        raise GenreError("至少要有一種口味")
    styles = {}
    for st in d["styles"]:
        k = _need(st, "key", "styles[]")
        styles[k] = StyleSpec(key=k, label=_need(st, "label", f"styles[{k}]"), aliases=tuple(st.get("aliases", [])), summary=st.get("summary", ""))
    if not styles:
        raise GenreError("至少要有一種風格")
    v = d["verdict"]
    dims = dict(_need(v, "dims", "verdict"))
    cap_dim = v.get("cap_dim")
    if cap_dim and cap_dim not in dims:
        raise GenreError(f"verdict.cap_dim {cap_dim} 不在 dims 裡")
    sig = d.get("signal")
    signal = Signal(
        positive_name=sig.get("positive_name", "正向率"), negative_name=sig.get("negative_name", "負向率"),
        positive=_need(sig, "positive", "signal"), negative=_need(sig, "negative", "signal"), min_comments=int(sig.get("min_comments", 10)),
    ) if sig else None
    return Genre(
        name=d["name"], label=d["label"], unit=d.get("unit", "篇"), title_prefix=d.get("title_prefix", ""), source=source,
        is_unit_description=d.get("is_unit_description", "是不是一個可以獨立閱讀的單位"), axes=axes, pair=pair,  # type: ignore[arg-type]
        example_axis=example_axis, example_match_axis=example_match_axis, cap=cap, beats=dict(d["beats"]),
        anchors=_text_field(d["anchors"], "anchors", with_items=True), moment=_text_field(d["moment"], "moment"),
        premise=_text_field(d["premise"], "premise"), voice_markers=dict(d.get("voice_markers", {})), length=length,
        rule_sets=rule_sets, tastes=tastes, styles=styles, verdict_dims=dims, verdict_cap_dim=cap_dim, signal=signal, path=folder,
        better_word=d.get("better_word", "好"),
    )


GENRE = load_genre()
