"""PTT 看板搜尋結果的索引：只翻列表頁，不抓本文。

每頁一行寫進 data/index/<board>_<query>.pages.jsonl：{"page": n, "entries": [...]}，可中斷續跑。
flatten() 把所有頁攤平去重成 data/index/<board>_<query>.jsonl，一行一篇：
{id, url, title, author, nrec, ts, date, query}
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .collect_ptt import BASE, DELAY_SEC, _get, parse_nrec

INDEX_DIR = Path("data/index")


def ts_of(art_id: str) -> int:
    """M.1781762527.A.FC4 → 1781762527（發文的 unix 時間）。"""
    try:
        return int(art_id.split(".")[1])
    except (IndexError, ValueError):
        return 0


def parse_search_page(html: str, query: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for ent in soup.select("div.r-ent"):
        a = ent.select_one("div.title a")
        if a is None:  # 已刪除
            continue
        href = urljoin(BASE, a["href"])
        art_id = href.rsplit("/", 1)[-1].replace(".html", "")
        ts = ts_of(art_id)
        nrec_el = ent.select_one("div.nrec")
        author_el = ent.select_one("div.author")
        out.append(
            {
                "id": art_id,
                "url": href,
                "title": a.get_text(strip=True),
                "author": author_el.get_text(strip=True) if author_el else "",
                "nrec": parse_nrec(nrec_el.get_text() if nrec_el else ""),
                "ts": ts,
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "",
                "query": query,
            }
        )
    return out


def _paths(board: str, query: str) -> tuple[Path, Path]:
    slug = f"{board}_{query}".replace(" ", "_").replace(":", "")
    return INDEX_DIR / f"{slug}.pages.jsonl", INDEX_DIR / f"{slug}.jsonl"


def build(board: str, query: str, max_pages: int = 2000, log=print) -> Path:
    pages_path, flat_path = _paths(board, query)
    pages_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[int] = set()
    if pages_path.exists():
        for line in pages_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["page"])
    with pages_path.open("a", encoding="utf-8") as out:
        for page in range(1, max_pages + 1):
            if page in done:
                continue
            url = f"{BASE}/bbs/{board}/search?page={page}&q={quote(query)}"
            try:
                html = _get(url)
            except FileNotFoundError:
                log(f"page {page}: 404，結束")
                break
            entries = parse_search_page(html, query)
            if not entries:
                log(f"page {page}: 空頁，結束")
                break
            out.write(json.dumps({"page": page, "entries": entries}, ensure_ascii=False) + "\n")
            out.flush()
            if page % 25 == 0:
                log(f"page {page}: {len(entries)} 筆，最舊 {entries[-1]['date']}")
            time.sleep(DELAY_SEC)
    return flatten(board, query)


def build_board_pages(board: str, until_ts: int, start_page: int = 1, max_pages: int = 1000, log=print) -> Path:
    """直接翻看板列表頁 index1、index2……（由舊到新），翻到某頁第一篇的時間 ≥ until_ts 就停。
    給沒有標籤、搜尋不到的早期文章用。存 data/index/<board>_board_early.pages.jsonl，可續跑。"""
    slug = f"{board}_board_early"
    pages_path = INDEX_DIR / f"{slug}.pages.jsonl"
    pages_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[int] = set()
    if pages_path.exists():
        for line in pages_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["page"])
    with pages_path.open("a", encoding="utf-8") as out:
        for page in range(start_page, start_page + max_pages):
            if page in done:
                continue
            try:
                html = _get(f"{BASE}/bbs/{board}/index{page}.html")
            except FileNotFoundError:
                log(f"index{page}: 404，跳過")
                time.sleep(DELAY_SEC)
                continue
            except RuntimeError as e:
                log(f"index{page}: {e}，跳過")
                time.sleep(DELAY_SEC)
                continue
            entries = parse_search_page(html, "board_early")
            out.write(json.dumps({"page": page, "entries": entries}, ensure_ascii=False) + "\n")
            out.flush()
            if page % 25 == 0:
                log(f"index{page}: {len(entries)} 筆，{entries[0]['date'] if entries else '空'}")
            time.sleep(DELAY_SEC)
            if entries and min(e["ts"] for e in entries if e["ts"]) >= until_ts:
                log(f"index{page}: 已到 {entries[0]['date']}，結束")
                break
    return flatten(board, "board_early")


def flatten(board: str, query: str) -> Path:
    pages_path, flat_path = _paths(board, query)
    seen: dict[str, dict] = {}
    for line in pages_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            for e in json.loads(line)["entries"]:
                seen[e["id"]] = e  # 後面的頁覆蓋前面的；推文數以最後看到的為準
    rows = sorted(seen.values(), key=lambda e: -e["ts"])
    flat_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return flat_path


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


_EARLY_SKIP = re.compile(
    r"[\[【［]\s*(創作|轉貼|轉錄|轉載|閒聊|問題|問卦|討論|新聞|公告|心得|請益|情報|活動|徵求|影片|圖片|廣告|小說|連載|占卜[^\]】］]*|板務|徵文|投票)\s*[\]】］]"
)


_EARLY_TAG = re.compile(r"^\s*(?:Re:\s*)?([\[【［{][^\]】］}]{1,10}[\]】］}])")
_EARLY_NUM = re.compile(
    r"[0-9０-９]|[（(\[【<〈][一二三四五六七八九十百上中下前後終完續参參肆伍陸柒捌玖拾壹貳]{1,3}[）)\]】>〉]"
    r"|[上中下]\s*篇|[壹貳參肆伍陸柒捌玖拾]|之[一二三四五六七八九十]|[~～]{1,2}[一二三四五六七八九十參]"
)
_EARLY_NOVEL = re.compile(r"《|》|章|卷|回目|番外|楔子|序幕|終局|後記|小說|創作|短篇|長篇|連載|轉載|轉貼|重貼|FW|Fw|推薦|新作|故事看看|十大|排行|判例|奇譚|劇本|詩|歌")


def early_title_ok(rows: list[dict]) -> list[dict]:
    """2003 到 2006 年的看板列表大多是連載小說。標題規則：
    有標籤的只收 [真實]、[經驗]；沒標籤的，標題有章節編號、小說或轉載字眼、或同作者同標題 5 篇以上，就不收。
    剩下的還會混一些小說、新聞、問答，交給標註的 is_story 判斷。"""
    from .corpus import base_author, series_key

    grp: dict[tuple[str, str], int] = {}
    for r in rows:
        k = (base_author(r["author"]), series_key(r["title"]))
        grp[k] = grp.get(k, 0) + 1
    out = []
    for r in rows:
        t = r["title"]
        m = _EARLY_TAG.match(t)
        if m:
            if m.group(1) in ("[真實]", "[經驗]"):
                out.append(r)
            continue
        if _EARLY_NUM.search(t) or _EARLY_NOVEL.search(t):
            continue
        if grp[(base_author(r["author"]), series_key(t))] >= 5:
            continue
        out.append(r)
    return out


def select_unfiltered(rows: list[dict], require_tag: str | None = None, source_tag: str = "", exclude_ids: set[str] | None = None) -> list[dict]:
    """不看推文數的挑法，給早期文章用（那時推文很少，推文門檻會全擋）。

    排除創作、轉貼、閒聊、問題這類標籤；Re: 只收原作者自己的續篇。sample=unfiltered。
    """
    from .corpus import base_author, is_reply, series_key

    exclude_ids = exclude_ids or set()
    rows = [r for r in rows if r["id"] not in exclude_ids and not _EARLY_SKIP.search(r["title"])]
    if require_tag:
        rows = [r for r in rows if require_tag in r["title"]]
    op_author: dict[str, set[str]] = {}
    for r in rows:
        if not is_reply(r["title"]):
            op_author.setdefault(series_key(r["title"]), set()).add(base_author(r["author"]))
    out = []
    for r in rows:
        if is_reply(r["title"]) and base_author(r["author"]) not in op_author.get(series_key(r["title"]), set()):
            continue
        out.append(dict(r, sample="unfiltered", source_tag=source_tag))
    return out


def select_for_fetch(
    rows: list[dict],
    min_nrec: int = 30,
    control_n: int = 500,
    control_max_nrec: int = 9,
    tag: str = "[經驗]",
    seed: int = 0,
) -> list[dict]:
    """挑要抓本文的：推文 ≥ min_nrec 的全部（sample=top），加隨機 control_n 篇低推文當對照組（sample=control）。

    Re: 只收原作者自己的續篇（同標題的原文作者 = 這篇作者），別人的回文不收。
    """
    import random

    from .corpus import base_author, is_reply, series_key

    rows = [r for r in rows if tag in r["title"]]
    op_author: dict[str, set[str]] = {}
    for r in rows:
        if not is_reply(r["title"]):
            op_author.setdefault(series_key(r["title"]), set()).add(base_author(r["author"]))

    def ok_reply(r: dict) -> bool:
        return base_author(r["author"]) in op_author.get(series_key(r["title"]), set())

    usable = [r for r in rows if not is_reply(r["title"]) or ok_reply(r)]
    top = [dict(r, sample="top") for r in usable if r["nrec"] >= min_nrec]
    low = [r for r in usable if r["nrec"] <= control_max_nrec and not is_reply(r["title"])]
    rng = random.Random(seed)
    control = [dict(r, sample="control") for r in rng.sample(low, k=min(control_n, len(low)))]
    return top + control
