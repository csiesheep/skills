"""把 data/ab/blind/ 的盲讀檔包成一頁 HTML：data/ab/blind_read.html。

頁面只放故事和兩篇共用的骨架，不放答案（哪篇是 v1、哪篇是 v2）。
py -m storypipe.blind_page
"""
from __future__ import annotations

import json
from pathlib import Path

from .generate import count_chars
from .options import STYLES
from .taxonomy import ENDINGS, MECHANISMS, SETTINGS

AB = Path("data/ab")
TEMPLATE = Path(__file__).with_name("blind_page.html")
OUT = AB / "blind_read.html"
GHOST = {0: "0（不露面）", 1: "1（只有跡象）", 2: "2（一瞬間看見）", 3: "3（可以清楚看見）"}


def main() -> None:
    key = json.loads((AB / "blind" / "key.json").read_text(encoding="utf-8"))
    pairs = []
    for pid, k in sorted(key.items()):
        plan = json.loads((AB / f"{k['seed']}_v1.json").read_text(encoding="utf-8"))["plan"]
        entry = {
            "id": pid,
            "skeleton": {
                "setting": SETTINGS[plan["setting"]].split("／")[0],
                "mechanisms": "、".join(MECHANISMS[m].split("：")[0] for m in plan["mechanisms"]),
                "ending": ENDINGS[plan["ending"]].split("：")[0],
                "ghost": GHOST[plan["ghost_explicitness"]],
                "chars": f"{plan['target_chars']} 字",
                "style": STYLES[plan.get("style", "ptt")].label,
            },
        }
        for label in ("A", "B"):
            text = (AB / "blind" / f"{pid}_{label}.md").read_text(encoding="utf-8").strip()
            title, _, body = text.partition("\n")
            entry[label] = {"title": title.strip(), "body": body.strip(), "chars": count_chars(text)}
        pairs.append(entry)
    data = json.dumps({"pairs": pairs}, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", data)
    OUT.write_text(html, encoding="utf-8")
    print(f"{len(pairs)} 對 → {OUT}（{len(html) // 1024} KB）")


if __name__ == "__main__":
    main()
