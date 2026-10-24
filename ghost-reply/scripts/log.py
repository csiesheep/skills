"""The daily reply file and a summary across days.

    py -X utf8 log.py new <engagement folder> [--date 2026-10-20]
    py -X utf8 log.py summary <engagement folder>

`new` writes <folder>/<date>.md with the sections a day needs (posts, result table, list candidates) unless it
exists; files are named by the Taiwan date. The result table has 平台, 狀態 (待發/排定/已發) and 時間 columns, the
ones game-promote's `plan.py slots` reads, so the same script can time Claude-posted replies. `summary` reads the
result tables of every day's file (the tables whose header has 用哪個) and totals, per
style A/B/C: how many were posted, and the likes, replies and follows filled in after 24 hours. Standard library
only.
"""
import argparse
import datetime as dt
import re
from pathlib import Path

TEMPLATE = """# {date} 回覆別人的貼文

三種風格：A 冷句、B 微型故事（「聽過」的口吻，不說成自己的親身經歷）、C 接話。不貼連結、不說「來看我的」。原文是英文就用英文回。

## 1. <平台>｜<作者> <主題>｜<多久前>，<讚、回覆、瀏覽>

<網址>

原文重點：

- A：
- B：
- C：

## 結果（貼出後填，24 小時後補數字）

| # | 平台 | 帳號 | 用哪個 | 狀態 | 時間 | 24 小時讚 | 回覆 | 帶來追蹤 |
|---|---|---|---|---|---|---|---|---|
| 1 | IG | | | 待發 | | | | |

## 固定名單候選

"""


def cmd_new(a) -> None:
    folder = Path(a.folder)
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{a.date}.md"
    if p.exists():
        print(f"{p} exists; not overwritten")
        return
    p.write_text(TEMPLATE.format(date=a.date), encoding="utf-8")
    print(p)


def number(cell: str) -> int | None:
    m = re.search(r"\d+", cell.replace(",", ""))
    return int(m.group()) if m else None


def result_rows(text: str):
    """Each row of every result table (header has 用哪個) as {style, likes, replies, follows} cells, by header name,
    so old tables (貼出時間, no 狀態) and new ones (狀態, 時間 for game-promote's plan.py slots) both read."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not (line.startswith("|") and "用哪個" in line):
            continue
        head = [c.strip() for c in line.strip().strip("|").split("|")]

        def col(pred):
            return next((k for k, h in enumerate(head) if pred(h)), None)

        cs, cl, cr, cf = col(lambda h: h == "用哪個"), col(lambda h: "讚" in h), col(lambda h: h == "回覆"),             col(lambda h: "追蹤" in h)
        for row in lines[i + 2:]:
            if not row.startswith("|"):
                break
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            get = lambda k: cells[k] if k is not None and k < len(cells) else ""
            yield {"style": get(cs), "likes": get(cl), "replies": get(cr), "follows": get(cf)}


def cmd_summary(a) -> None:
    totals: dict[str, dict[str, int]] = {}
    days = 0
    for p in sorted(Path(a.folder).glob("????-??-??.md")):
        rows = [c for c in result_rows(p.read_text(encoding="utf-8")) if c["style"][:1].upper() in ("A", "B", "C")]
        if rows:
            days += 1
        for cells in rows:
            style = cells["style"][:1].upper()
            t = totals.setdefault(style, {"posted": 0, "measured": 0, "likes": 0, "replies": 0, "follows": 0})
            t["posted"] += 1
            likes, replies, follows = number(cells["likes"]), number(cells["replies"]), number(cells["follows"])
            if likes is not None:
                t["measured"] += 1
                t["likes"] += likes
                t["replies"] += replies or 0
                t["follows"] += follows or 0
    print(f"{days} day(s)")
    names = {"A": "冷句", "B": "微型故事", "C": "接話"}
    for s in "ABC":
        if s not in totals:
            continue
        t = totals[s]
        avg = f"{t['likes'] / t['measured']:.1f}" if t["measured"] else "-"
        print(f"{s} {names[s]}: posted {t['posted']}, measured {t['measured']}, likes {t['likes']} (avg {avg}), "
              f"replies {t['replies']}, follows {t['follows']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("folder")
    # Taiwan date: the audience's day, and the name game-promote's plan.py slots looks for.
    n.add_argument("--date", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat())
    s = sub.add_parser("summary")
    s.add_argument("folder")
    a = ap.parse_args()
    {"new": cmd_new, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
