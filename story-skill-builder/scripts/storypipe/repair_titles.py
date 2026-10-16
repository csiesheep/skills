"""修補已抓下來的舊格式文章：標題空白的，從本文開頭的表頭讀出作者、標題、時間並移掉表頭；
讀不到就用索引上的標題和作者。原檔先備份到 data/raw_backup_<日期>/。

py -m storypipe.repair_titles
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from . import ptt_index
from .collect_ptt import split_old_header

RAW = Path("data/raw")
INDEXES = [
    "data/index/marvel_經驗.jsonl",
    "data/index/marvel_翻譯.jsonl",
    "data/index/marvel_真實.jsonl",
    "data/index/marvel_board_early.jsonl",
    "data/index/digest_entries.jsonl",
]


def main() -> None:
    idx: dict[str, dict] = {}
    for f in INDEXES:
        p = Path(f)
        if p.exists():
            for r in ptt_index.load(p):
                idx.setdefault(r["id"], r)

    backup = Path(f"data/raw_backup_{time.strftime('%Y%m%d-%H%M%S')}")
    backup.mkdir(parents=True)
    total = {"header": 0, "index": 0, "still_empty": 0, "changed_ids": []}
    for f in sorted(RAW.glob("*.jsonl")):
        shutil.copy2(f, backup / f.name)
        out = []
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not (r.get("title") or "").strip():
                hdr, body = split_old_header(r.get("body") or "")
                if hdr.get("標題"):
                    r["title"] = hdr["標題"]
                    r["author"] = r.get("author") or hdr.get("作者", "")
                    r["date"] = r.get("date") or hdr.get("時間", "")
                    r["body"] = body
                    total["header"] += 1
                elif (idx.get(r["id"]) or idx.get("D." + r["id"]) or {}).get("title"):  # 精華區目錄的 id 有 D. 前綴
                    e = idx.get(r["id"]) or idx["D." + r["id"]]
                    r["title"] = e["title"]
                    r["author"] = r.get("author") or e.get("author", "")
                    total["index"] += 1
                else:
                    total["still_empty"] += 1
                if r.get("title"):
                    total["changed_ids"].append(r["id"])
            out.append(json.dumps(r, ensure_ascii=False))
        f.write_text("\n".join(out) + "\n", encoding="utf-8")
    Path("data/repair_titles.ids").write_text("".join(i + "\n" for i in total["changed_ids"]), encoding="utf-8")
    print(f"備份 → {backup}")
    print(f"從表頭補回 {total['header']}，從索引補回 {total['index']}，仍是空白 {total['still_empty']}；改動的 id → data/repair_titles.ids")


if __name__ == "__main__":
    main()
