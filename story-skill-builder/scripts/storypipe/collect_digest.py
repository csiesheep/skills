"""PTT 精華區：先遞迴列出所有目錄和文章（list_tree），再挑文章抓本文（fetch_list）。

精華區文章的 ID 是收錄時產生的，跟看板上原文的 ID 不同，所以去重要靠內容（corpus.py）。
"""
from __future__ import annotations

import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .collect_ptt import BASE, DELAY_SEC, _get

INDEX_DIR = Path("data/index")
ROOTS = {
    "新版經驗區": "/man/marvel/DFB6/index.html",
    "舊版經驗區": "/man/marvel/D2C/index.html",
}

# 標題標籤：這些明顯不是經驗文
_SKIP_TAGS = re.compile(r"\[(問卦|問題|討論|新聞|公告|心得|閒聊|請益|情報|活動|徵求|求救|協尋|轉錄|分享|影片|圖片|廣告|創作)\]")  # 創作是虛構小說，不是經驗文


def parse_dir(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for ent in soup.select("div.m-ent div.title a"):
        href = ent.get("href", "")
        text = ent.get_text(strip=True)
        kind = "dir" if href.endswith("/index.html") else "article"
        title = re.sub(r"^[◆◇]\s*", "", text).strip()
        out.append({"kind": kind, "href": urljoin(BASE, href), "title": title})
    return out


def list_tree(max_dirs: int = 5000, log=print) -> Path:
    """BFS 列出兩個經驗區的所有文章，存 data/index/digest_entries.jsonl。可續跑：已列過的目錄跳過。"""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    dirs_path = INDEX_DIR / "digest_dirs.jsonl"
    seen_dirs: dict[str, dict] = {}
    if dirs_path.exists():
        for line in dirs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                seen_dirs[d["href"]] = d
    queue: deque[tuple[str, list[str]]] = deque((urljoin(BASE, h), [name]) for name, h in ROOTS.items())
    n = 0
    with dirs_path.open("a", encoding="utf-8") as out:
        while queue and n < max_dirs:
            href, path = queue.popleft()
            if href in seen_dirs:
                children = seen_dirs[href]["children"]
            else:
                try:
                    children = parse_dir(_get(href))
                except FileNotFoundError:
                    children = []
                rec = {"href": href, "path": path, "children": children}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                seen_dirs[href] = rec
                n += 1
                if n % 50 == 0:
                    log(f"已列 {n} 個目錄，佇列剩 {len(queue)}")
                time.sleep(DELAY_SEC)
            for c in children:
                if c["kind"] == "dir" and "舊版精華區" not in c["title"] and c["href"] not in seen_dirs:
                    queue.append((c["href"], path + [c["title"]]))

    # 攤平成文章清單
    arts: dict[str, dict] = {}
    for d in seen_dirs.values():
        for c in d["children"]:
            if c["kind"] != "article":
                continue
            art_id = c["href"].rsplit("/", 1)[-1].replace(".html", "")
            arts[art_id] = {
                "id": "D." + art_id,  # 目錄用的 id；抓下來的文章 id 是網址檔名（沒有 D.），精華區檔名跟看板不重複
                "url": c["href"],
                "title": c["title"],
                "digest_path": "/".join(d["path"]),
                "curated": True,
                "sample": "digest",
            }
    flat = INDEX_DIR / "digest_entries.jsonl"
    flat.write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in arts.values()), encoding="utf-8")
    log(f"精華區：{len(seen_dirs)} 個目錄、{len(arts)} 篇文章 → {flat}")
    return flat


def select(entries: list[dict]) -> list[dict]:
    """去掉明顯不是經驗文的（問卦、新聞、轉錄……）。Re: 保留，精華區收的回文常是故事。"""
    return [e for e in entries if not _SKIP_TAGS.search(e["title"])]
