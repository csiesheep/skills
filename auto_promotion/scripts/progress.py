"""Append one line to the auto-promotion progress log in the Obsidian vault.

    py -X utf8 progress.py <task id> <status> "<what happened>" [--link URL ...]

Writes to C:/Users/sheep/code/obsidian/Projects/auto promotion/<Taiwan date>.md (created with a header if
missing), one table row per call: Taiwan time, task, status, text, links. Status is one word from
開始 / 進度 / 完成 / 發文 / 跳過 / 失敗 / 警告. Several scheduled runs write at once, so the append takes a
lock file next to the log (waits up to 20 s, takes over a lock older than 2 minutes). Pipes in the text are
replaced so the table stays intact. Standard library only.
"""
import argparse
import datetime as dt
import os
import time
from pathlib import Path

LOG_DIR = Path(r"C:/Users/sheep/code/obsidian/Projects/auto promotion")
TW = dt.timezone(dt.timedelta(hours=8))
STATUSES = ["開始", "進度", "完成", "發文", "跳過", "失敗", "警告"]
HEADER = """# 自動推廣進度 {date}

每個排程任務（生在中國、蓋牌投票箱、鬼唱詩）在這裡記一行：開始、重要進度、發文連結、跳過或失敗的原因。時間是台灣時間。
排程與流程：~/.claude/skills/auto_promotion/SKILL.md

| 時間 | 排程 | 狀態 | 內容 | 連結 |
|---|---|---|---|---|
"""


def clean(s: str) -> str:
    return " ".join(str(s).replace("|", "／").split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("status", choices=STATUSES)
    ap.add_argument("text")
    ap.add_argument("--link", action="append", default=[])
    a = ap.parse_args()
    now = dt.datetime.now(TW)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{now.date().isoformat()}.md"
    lock = path.with_suffix(".lock")
    for _ in range(100):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 120:
                    lock.unlink()
                    continue
            except FileNotFoundError:
                continue
            time.sleep(0.2)
    try:
        new = not path.exists()
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            if new:
                f.write(HEADER.format(date=now.date().isoformat()))
            links = " ".join(clean(u) for u in a.link)
            f.write(f"| {now:%H:%M} | {clean(a.task)} | {a.status} | {clean(a.text)} | {links} |\n")
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass
    print(path)


if __name__ == "__main__":
    main()
