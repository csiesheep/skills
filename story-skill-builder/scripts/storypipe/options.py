"""產生時的使用者選項：用類型設定裡的中文說法指定每個軸、露出上限、長度、風格、口味。

resolve("setting", "校園") → "school"；可以給 key、中文標籤的一部分、或 genre.json 裡的別名。
多個值用逗號分開，規劃器會只在這些裡面依權重抽。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .genre import GENRE, Axis, GenreError
from .paths import PROMPTS_DIR

_SUFFIX = re.compile(r"(結局|結尾|收尾|型|類|式)$")


class OptionError(ValueError):
    pass


def _axis(kind: str) -> Axis:
    try:
        return GENRE.axis(kind)
    except GenreError as e:
        raise OptionError(str(e)) from e


def resolve(kind: str, text: str) -> str:
    """把一個說法對應到 key。對不到或對到多個就報錯，錯誤訊息列出可用的選項。kind 是軸的 key 或 flag。"""
    ax = _axis(kind)
    t = text.strip()
    if t in ax.values:
        return t
    for cand in (t, _SUFFIX.sub("", t)):
        if cand in ax.aliases:
            return ax.aliases[cand]
    hits = [k for k, label in ax.values.items() if t in label or _SUFFIX.sub("", t) in label.split("：")[0]]
    if len(hits) == 1:
        return hits[0]
    choices = "、".join(f"{k}（{ax.short(k)}）" for k in ax.values)
    if not hits:
        raise OptionError(f"「{text}」對不到任何{ax.label}。可用：{choices}")
    raise OptionError(f"「{text}」同時符合 {hits}，請說得更具體。可用：{choices}")


def resolve_list(kind: str, text: str | None) -> list[str] | None:
    if not text:
        return None
    return list(dict.fromkeys(resolve(kind, x) for x in re.split(r"[,，、/／\s]+", text) if x.strip()))


# ---------------------------------------------------------------------------
# 露出上限
# ---------------------------------------------------------------------------


def resolve_cap(text: str | int | None) -> int | None:
    cap = GENRE.cap
    if text is None or text == "":
        return None
    if isinstance(text, int) or str(text).strip().isdigit():
        v = int(text)
        if cap.min <= v <= cap.max:
            return v
        raise OptionError(f"{cap.label}是 {cap.min} 到 {cap.max}")
    t = str(text).strip()
    if t in cap.words:
        return cap.words[t]
    raise OptionError(f"{cap.label}「{t}」看不懂。用 {cap.min} 到 {cap.max}，或：" + "、".join(cap.words))


# ---------------------------------------------------------------------------
# 長度
# ---------------------------------------------------------------------------


def resolve_length(text: str | int | None) -> tuple[int, int] | None:
    """回傳 (下限, 上限)。給單一數字就是 (n, n)；給「1500-2500」就是範圍；給預設名稱就查表。"""
    ln = GENRE.length
    if text is None or text == "":
        return None
    t = str(text).strip().replace("字", "").replace("，", ",")
    t = ln.aliases.get(t, t)
    if t in ln.presets:
        return ln.presets[t]
    m = re.fullmatch(r"(\d+)\s*(?:[-~～到]\s*(\d+))?", t)
    if not m:
        raise OptionError(f"長度「{text}」看不懂。用字數（1500）、範圍（1500-2500）、或：" + "、".join(ln.presets))
    lo = int(m.group(1))
    hi = int(m.group(2) or lo)
    lo, hi = min(lo, hi), max(lo, hi)
    if lo < ln.min or hi > ln.max:
        raise OptionError(f"長度要在 {ln.min} 到 {ln.max} 字之間")
    return lo, hi


# ---------------------------------------------------------------------------
# 風格、口味
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Style:
    key: str
    label: str
    aliases: tuple[str, ...]
    summary: str  # 一句話，給評審看

    def prompt(self, rules: str | None = None) -> str:
        rs = GENRE.rule_sets[rules or GENRE.default_rules]
        return (PROMPTS_DIR / rs.styles / f"{self.key}.md").read_text(encoding="utf-8")


STYLES: dict[str, Style] = {k: Style(s.key, s.label, s.aliases, s.summary) for k, s in GENRE.styles.items()}


def resolve_style(text: str | None) -> Style:
    if not text:
        return STYLES[GENRE.default_style]
    t = text.strip()
    if t in STYLES:
        return STYLES[t]
    for s in STYLES.values():
        if t == s.label or t in s.aliases or t in s.label:
            return s
    raise OptionError(f"風格「{text}」看不懂。可用：" + "、".join(f"{s.key}（{s.label}）" for s in STYLES.values()))


def resolve_taste(text: str | None) -> tuple[str, str]:
    """回傳 (口味名稱, 規則版本)。沒給就是類型的預設口味。"""
    if not text:
        return GENRE.default_taste, GENRE.default_rules
    t = text.strip()
    for name, taste in GENRE.tastes.items():
        if t == name or t.lower() in taste.aliases:
            return name, taste.rules
    raise OptionError(f"口味「{text}」看不懂。可用：" + "、".join(GENRE.tastes))


def describe_options() -> str:
    """給 `options` 指令印出來的說明。"""
    L: list[str] = []
    for ax in GENRE.axes:
        L += [f"{ax.label}（--{ax.flag}，可多個，用逗號分開）："] + [f"  {k:<15} {v}" for k, v in ax.values.items()] + [""]
    cap = GENRE.cap
    L += [f"{cap.label}（--{cap.flag}）：{cap.min} 到 {cap.max}，或 " + "、".join(f"{w}={n}" for w, n in cap.words.items())]
    L += ["", "長度（--length）：字數（1500）、範圍（1500-2500），或"]
    L += [f"  {k:<4} {lo} 到 {hi} 字" for k, (lo, hi) in GENRE.length.presets.items()]
    L += ["", "風格（--style）："]
    L += [f"  {s.key:<10} {s.label:<6} {s.summary}" for s in STYLES.values()]
    L += ["", "口味（--taste）："]
    L += [f"  {name:<4} {t.summary}" for name, t in GENRE.tastes.items()]
    L += ["", "額外要求（--note，可重複）：自由描述，例如「主角是護理師」「發生在颱風夜」"]
    ex = " ".join(f"--{ax.flag} {next(iter(ax.aliases), next(iter(ax.values)))}" for ax in GENRE.axes[:2])
    L += ["", f"中文說法也可以，例如 {ex} --length {next(iter(GENRE.length.presets))} --style {next(iter(STYLES.values())).label}"]
    return "\n".join(L)
