"""抓 PTT 看板文章：用站內搜尋的 recommend: 篩推文數，再逐篇抓本文和推噓。

輸出 JSONL，一行一篇：
{id, url, board, title, author, date, nrec, push, boo, neutral, body, pushes:[{tag,user,text}]}

禮貌原則：單執行緒、每篇間隔 >= 1.5 秒、帶 UA、可中斷續抓。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

BASE = "https://www.ptt.cc"
HEADERS = {"User-Agent": "Mozilla/5.0 ghost-story-research (structure analysis; contact via PTT)"}
COOKIES = {"over18": "1"}
DELAY_SEC = 1.2


def _get(url: str, retries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=20)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                raise FileNotFoundError(url)
            last = RuntimeError(f"HTTP {r.status_code} {url}")
        except (requests.RequestException,) as e:  # noqa: PERF203
            last = e
        time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"give up {url}: {last}")


def parse_nrec(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    if text == "爆":
        return 100
    if text.startswith("X"):
        rest = text[1:]
        return -10 * int(rest) if rest.isdigit() else -10
    return int(text) if text.lstrip("-").isdigit() else 0


def iter_search(board: str, query: str, max_pages: int = 50):
    """逐頁 yield 搜尋結果的 {href,title,author,nrec}。沒有結果就停。"""
    for page in range(1, max_pages + 1):
        url = f"{BASE}/bbs/{board}/search?page={page}&q={quote(query)}"
        html = _get(url)
        soup = BeautifulSoup(html, "html.parser")
        ents = soup.select("div.r-ent")
        if not ents:
            return
        for ent in ents:
            a = ent.select_one("div.title a")
            if a is None:  # 已刪除文章
                continue
            nrec_el = ent.select_one("div.nrec")
            yield {
                "href": urljoin(BASE, a["href"]),
                "title": a.get_text(strip=True),
                "author": ent.select_one("div.author").get_text(strip=True) if ent.select_one("div.author") else "",
                "nrec": parse_nrec(nrec_el.get_text() if nrec_el else ""),
            }
        time.sleep(DELAY_SEC)


_SIGNATURE_RE = re.compile(r"^※ (發信站|文章網址|編輯)")
_OLD_HDR = {
    "作者": re.compile(r"作者\s*[:：]\s*(.+?)\s*(?:(?:看板|站內|信區)\s*[:：].*)?$"),
    "標題": re.compile(r"標題\s*[:：]\s*(.+?)\s*$"),
    "時間": re.compile(r"時間\s*[:：]\s*(.+?)\s*$"),
}
_JUNK = re.compile(r"\x1b\[[0-9;]*m|[\x00-\x08\x0b-\x1f]")


def split_old_header(body: str, max_lines: int = 6) -> tuple[dict, str]:
    """舊格式文章的作者、標題、時間寫在本文前幾行（常夾著控制碼殘渣，例如「e作者: … EeE」）。
    讀出來並從本文移掉。前 max_lines 行沒有「標題」就原樣回傳。"""
    lines = body.split("\n")
    found: dict[str, str] = {}
    last = -1
    for i, line in enumerate(lines[:max_lines]):
        clean = _JUNK.sub("", line).strip()
        for key, rx in _OLD_HDR.items():
            if key in found:
                continue
            m = rx.search(clean)
            if m and clean.find(key) <= 3:  # 標籤要在行首附近，避免把內文的「時間：」當成表頭
                found[key] = m.group(1).strip()
                last = i
    if "標題" not in found or "作者" not in found:  # 兩行都要有；只有「原文標題：」這類的不算表頭
        return {}, body
    rest = "\n".join(lines[last + 1 :]).lstrip("\n")
    rest = re.sub(r"^[\s─-]{0,3}\n", "", rest)
    return found, rest.strip()


def parse_article(html: str, url: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("#main-content")
    if main is None:
        raise ValueError("no main-content")

    meta: dict[str, str] = {}
    for line in main.select("div.article-metaline, div.article-metaline-right"):
        tag = line.select_one(".article-meta-tag")
        val = line.select_one(".article-meta-value")
        if tag and val:
            meta[tag.get_text(strip=True)] = val.get_text(strip=True)

    # 本文：main-content 底下、metaline 之後、第一個 ※ 發信站 之前的所有文字；跳過推文 div。
    body_parts: list[str] = []
    pushes: list[dict] = []
    reached_signature = False
    for node in main.children:
        if isinstance(node, Tag):
            cls = node.get("class") or []
            if "article-metaline" in cls or "article-metaline-right" in cls:
                continue
            if "push" in cls:
                tag_el = node.select_one(".push-tag")
                user_el = node.select_one(".push-userid")
                txt_el = node.select_one(".push-content")
                if tag_el and user_el and txt_el:
                    pushes.append(
                        {
                            "tag": tag_el.get_text(strip=True),
                            "user": user_el.get_text(strip=True),
                            "text": txt_el.get_text(strip=True).lstrip(":").strip(),
                        }
                    )
                continue
            text = node.get_text()
            if _SIGNATURE_RE.match(text.strip()):
                reached_signature = True
            if not reached_signature:
                body_parts.append(text)
        elif isinstance(node, NavigableString):
            if not reached_signature:
                body_parts.append(str(node))

    body = "".join(body_parts)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if body.endswith("\n--"):  # 簽名檔分隔線
        body = body[:-3].rstrip()
    if not meta.get("標題"):  # 2007 年以前的舊格式：表頭混在本文開頭
        hdr, body = split_old_header(body)
        for k, v in hdr.items():
            meta.setdefault(k, v)

    push = sum(1 for p in pushes if p["tag"] == "推")
    boo = sum(1 for p in pushes if p["tag"] == "噓")
    neutral = len(pushes) - push - boo

    art_id = url.rsplit("/", 1)[-1].replace(".html", "") if url else ""
    return {
        "id": art_id,
        "url": url,
        "board": meta.get("看板", ""),
        "title": meta.get("標題", ""),
        "author": meta.get("作者", ""),
        "date": meta.get("時間", ""),
        "push": push,
        "boo": boo,
        "neutral": neutral,
        "body": body,
        "pushes": pushes,
    }


def fetch_article(url: str) -> dict:
    return parse_article(_get(url), url)


def load_done_ids(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    ids: set[str] = set()
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return ids


def collect(
    board: str,
    query: str,
    out_path: Path,
    max_articles: int = 200,
    min_body_chars: int = 600,
    title_must_contain: str | None = "[經驗]",
    max_pages: int = 50,
    log=print,
) -> int:
    """抓到 out_path（JSONL，append）。回傳這次新增的篇數。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done_ids(out_path)
    added = 0
    with out_path.open("a", encoding="utf-8") as out:
        for hit in iter_search(board, query, max_pages=max_pages):
            if added >= max_articles:
                break
            if title_must_contain and title_must_contain not in hit["title"]:
                continue
            if hit["title"].startswith("Re:"):  # 回文多半是討論或衛教，不是故事
                continue
            art_id = hit["href"].rsplit("/", 1)[-1].replace(".html", "")
            if art_id in done:
                continue
            try:
                art = fetch_article(hit["href"])
            except Exception as e:  # noqa: BLE001
                log(f"skip {hit['href']}: {e}")
                time.sleep(DELAY_SEC)
                continue
            art["nrec"] = hit["nrec"]
            if len(art["body"]) < min_body_chars:
                log(f"too short ({len(art['body'])}): {art['title']}")
                time.sleep(DELAY_SEC)
                continue
            out.write(json.dumps(art, ensure_ascii=False) + "\n")
            out.flush()
            done.add(art_id)
            added += 1
            log(f"[{added}/{max_articles}] nrec={art['nrec']:>3} push={art['push']:>3} {art['title']}")
            time.sleep(DELAY_SEC)
    return added


def fetch_list(entries: list[dict], out_path: Path, extra: dict | None = None, min_body_chars: int = 300, log=print) -> int:
    """依清單逐篇抓本文，append 到 out_path（已抓過的 id 跳過）。extra 的欄位會加到每筆（例如 sample）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done_ids(out_path)
    todo = [e for e in entries if e["id"] not in done]
    added = 0
    with out_path.open("a", encoding="utf-8") as out:
        for k, e in enumerate(todo, 1):
            try:
                art = fetch_article(e["url"])
            except FileNotFoundError:
                log(f"404 {e['id']} {e['title']}")
                time.sleep(DELAY_SEC)
                continue
            except Exception as ex:  # noqa: BLE001
                log(f"skip {e['id']}: {ex}")
                time.sleep(DELAY_SEC)
                continue
            if not art.get("title"):  # 舊格式讀不到標題時，用索引上的
                art["title"] = e.get("title", "")
            if not art.get("author"):
                art["author"] = e.get("author", "")
            art["nrec"] = e.get("nrec", art.get("push", 0) - art.get("boo", 0))
            art["ts"] = e.get("ts")
            art.update(extra or {})
            for k2 in ("sample", "digest_path", "curated", "source_tag"):
                if k2 in e:
                    art[k2] = e[k2]
            if len(art["body"]) < min_body_chars:
                time.sleep(DELAY_SEC)
                continue
            out.write(json.dumps(art, ensure_ascii=False) + "\n")
            out.flush()
            added += 1
            if added % 50 == 0 or k == len(todo):
                log(f"[{k}/{len(todo)}] 已寫入 {added} 篇，最近一篇 nrec={art['nrec']} {art['title']}")
            time.sleep(DELAY_SEC)
    return added


if __name__ == "__main__":  # 直接跑：py -m storypipe.collect_ptt [max]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    collect("marvel", "經驗 recommend:30", Path("data/raw/ptt_marvel.jsonl"), max_articles=n)
