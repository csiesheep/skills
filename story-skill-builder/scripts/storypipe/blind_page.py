"""把 data/ab/blind/ 的盲讀檔包成一頁 HTML：data/ab/blind_read.html。

頁面只放故事和兩篇共用的骨架，不放答案（哪篇是哪套規則）。
py -m storypipe.blind_page
"""
from __future__ import annotations

import json
from pathlib import Path

from .generate import count_chars
from .genre import GENRE
from .options import STYLES

AB = Path("data/ab")
TEMPLATE = Path(__file__).with_name("blind_page.html")
OUT = AB / "blind_read.html"


def skeleton_rows(plan: dict) -> list[list[str]]:
    """骨架的 [標籤, 值] 列，給頁面顯示；欄位跟著 genre.json 走。"""
    rows = []
    for ax in GENRE.axes:
        vals = plan.get("axes", {}).get(ax.key, [])
        rows.append([ax.label, "、".join(ax.short(v) for v in vals)])
    rows.append([GENRE.cap.label, GENRE.cap.level_label(int(plan.get("cap", 0)))])
    rows.append(["字數", f"{plan.get('target_chars')} 字"])
    style = plan.get("style") or GENRE.default_style
    rows.append(["風格", STYLES[style].label if style in STYLES else style])
    return rows


def main() -> None:
    key = json.loads((AB / "blind" / "key.json").read_text(encoding="utf-8"))
    pairs = []
    for pid, k in sorted(key.items()):
        first = sorted(AB.glob(f"{k['seed']}_*.json"))[0]
        plan = json.loads(first.read_text(encoding="utf-8"))["plan"]
        entry = {"id": pid, "skeleton": skeleton_rows(plan)}
        for label in ("A", "B"):
            text = (AB / "blind" / f"{pid}_{label}.md").read_text(encoding="utf-8").strip()
            title, _, body = text.partition("\n")
            entry[label] = {"title": title.strip(), "body": body.strip(), "chars": count_chars(text)}
        pairs.append(entry)
    data = json.dumps({"pairs": pairs}, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", data)
            .replace("{{LABEL}}", GENRE.label).replace("{{BETTER}}", GENRE.better_word))
    OUT.write_text(html, encoding="utf-8")
    print(f"{len(pairs)} 對 → {OUT}（{len(html) // 1024} KB）")


if __name__ == "__main__":
    main()
