"""把原始文章整理成標註用的語料：合併系列文、近似去重。

輸入：data/raw/*.jsonl（看板 + 精華區）
輸出：data/corpus.jsonl，一行一個「單位」，可能是單篇也可能是合併的系列：
{id, url, title, author, nrec, ts, sample, curated, digest_path, body, parts:[{id,title,ts}], series_key}

規則
- 系列：同作者、標題去掉序號後相同、時間跨度 365 天內，兩篇以上就合併，依時間排序接起來。
  作者自己的 Re: 當續章；別人的 Re: 不併。
- 去重：5 字 shingle 抽樣八分之一建倒排索引，包含率（共有 ÷ 較小那篇）≥ 0.8 視為重複。
  保留順序：看板勝過精華區、推文高的勝過低的、長的勝過短的；被去掉的單位如果是精華區收錄，把 curated 旗標轉給保留的那篇。
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT = Path("data/corpus.jsonl")

# ---------------------------------------------------------------------------
# 系列
# ---------------------------------------------------------------------------

_CN_NUM = "一二三四五六七八九十百零〇兩"
_SERIES_PATTERNS = [
    rf"[（(【\[]\s*(?:第\s*)?[{_CN_NUM}0-9０-９]+\s*(?:篇|集|章|回|話|部)?\s*(?:完|終|end)?\s*[）)】\]]",  # （一）(2)【三】
    r"[（(【\[]\s*(?:上|中|下|前|後|續|完|終|上篇|中篇|下篇|前篇|後篇|續篇|完結篇?|最終回)\s*[）)】\]]",
    rf"(?:之|第)\s*[{_CN_NUM}0-9０-９]+\s*(?:篇|集|章|回|話)?",  # 之一、第二篇
    r"(?:上|中|下|前|後|續|完結|最終)\s*篇",
    r"(?:part|ep|pt|vol)\.?\s*\d+",
    r"[#＃]\s*\d+",
    r"[-－—~～:：]\s*[{0}0-9０-９]+\s*$".format(_CN_NUM),  # 結尾的「- 2」「：三」
    r"\s+[0-9０-９]+\s*$",  # 結尾空白加數字
    r"[（(]\s*續\s*[）)]",
    r"續集|續篇|後續|完結|待續",
]
_SERIES_RE = re.compile("|".join(_SERIES_PATTERNS), re.I)
_TAG_RE = re.compile(r"^\s*(?:re\s*:\s*)*(?:\[[^\]]{1,6}\]\s*)?", re.I)


def base_author(author: str) -> str:
    return author.split(" ", 1)[0].split("(", 1)[0].strip().lower()


def is_reply(title: str) -> bool:
    return title.strip().lower().startswith("re:")


def series_key(title: str) -> str:
    t = _TAG_RE.sub("", title)
    t = _SERIES_RE.sub("", t)
    t = re.sub(r"[\s　,，。.!！?？…~～\-－—_:：「」『』\"']+", "", t)
    return t.lower()


def has_series_marker(title: str) -> bool:
    return bool(_SERIES_RE.search(_TAG_RE.sub("", title)))


def merge_series(arts: list[dict], max_span_days: int = 365) -> list[dict]:
    """回傳單位清單。系列被合併，其他原樣（加 parts）。"""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for a in arts:
        k = series_key(a["title"])
        if not k:
            k = a["id"]  # 標題去完是空的，不合併
        groups[(base_author(a.get("author", "")), k)].append(a)

    units: list[dict] = []
    for (author, key), members in groups.items():
        members.sort(key=lambda a: a.get("ts") or 0)
        # 別人的 Re: 不會進同一組（作者不同）；作者自己的 Re: 會。
        # 只有一篇、或全部都沒有序號且不是 Re: 的同名文（可能是巧合同名），不合併。
        marked = [m for m in members if has_series_marker(m["title"]) or is_reply(m["title"])]
        span = ((members[-1].get("ts") or 0) - (members[0].get("ts") or 0)) / 86400
        if len(members) < 2 or not marked or span > max_span_days or not author:
            for m in members:
                units.append(_single(m))
            continue
        units.append(_merged(members, key))
    return units


def _single(a: dict) -> dict:
    u = {k: a.get(k) for k in ("id", "url", "title", "author", "nrec", "ts", "sample", "source_tag", "curated", "digest_path", "body")}
    u["parts"] = [{"id": a["id"], "title": a["title"], "ts": a.get("ts")}]
    u["series_key"] = None
    return u


def _merged(members: list[dict], key: str) -> dict:
    first = members[0]
    body = "\n\n".join(f"【{m['title']}】\n{m['body']}" for m in members)
    samples = {m.get("sample") for m in members}
    return {
        "id": "S." + first["id"],
        "url": first.get("url"),
        "title": first["title"],
        "author": first.get("author"),
        "nrec": max(int(m.get("nrec") or 0) for m in members),  # 系列以最高的那章代表
        "ts": first.get("ts"),
        "sample": "top" if "top" in samples else (first.get("sample") or "top"),
        "curated": any(m.get("curated") for m in members) or None,
        "digest_path": next((m.get("digest_path") for m in members if m.get("digest_path")), None),
        "source_tag": next((m.get("source_tag") for m in members if m.get("source_tag")), None),
        "body": body,
        "parts": [{"id": m["id"], "title": m["title"], "ts": m.get("ts")} for m in members],
        "series_key": key,
    }


# ---------------------------------------------------------------------------
# 近似去重
# ---------------------------------------------------------------------------

_SAMPLE_MOD = 8  # 只留雜湊值 % 8 == 0 的 shingle，約八分之一，兩篇共有的 shingle 會被一致地抽到
_COMMON_DF = 60  # 出現在超過這麼多篇的 shingle 是套話，不拿來比


def _norm(text: str) -> str:
    return re.sub(r"[\s　]+", "", text)


def sampled_shingles(text: str, k: int = 5) -> set[int]:
    t = _norm(text)
    out: set[int] = set()
    for i in range(max(1, len(t) - k + 1)):
        h = int.from_bytes(hashlib.blake2b(t[i : i + k].encode("utf-8"), digest_size=8).digest(), "little")
        if h % _SAMPLE_MOD == 0:
            out.add(h)
    return out


def _rank(u: dict) -> tuple:
    return (u.get("sample") != "digest", int(u.get("nrec") or 0), len(u.get("body") or ""))


def dedupe(units: list[dict], threshold: float = 0.8, min_shingles: int = 20, log=print) -> tuple[list[dict], list[dict]]:
    """回傳 (保留的, 被去掉的)。被去掉的每筆帶 dup_of。

    相似度用包含率：共有 shingle ÷ 較小那篇的 shingle 數。一篇是另一篇的一部分（例如精華區只收系列的一章、
    看板那邊已合併成整串）也算重複。抽樣 shingle 少於 min_shingles 的短文不參與。
    """
    shs = [sampled_shingles(u.get("body") or "") for u in units]
    df: dict[int, int] = defaultdict(int)
    for s in shs:
        for h in s:
            df[h] += 1
    post: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(shs):
        for h in s:
            if df[h] <= _COMMON_DF:
                post[h].append(i)
    size = [sum(1 for h in s if df[h] <= _COMMON_DF) for s in shs]

    parent = list(range(len(units)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    pairs = 0
    for i, s in enumerate(shs):
        if size[i] < min_shingles:
            continue
        co: dict[int, int] = defaultdict(int)
        for h in s:
            if df[h] > _COMMON_DF:
                continue
            for j in post[h]:
                if j > i:
                    co[j] += 1
        for j, c in co.items():
            if size[j] < min_shingles:
                continue
            if c / min(size[i], size[j]) >= threshold:
                pairs += 1
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(len(units)):
        clusters[find(i)].append(i)
    keep, dropped = [], []
    for members in clusters.values():
        members.sort(key=lambda i: _rank(units[i]), reverse=True)
        winner = dict(units[members[0]])
        for i in members[1:]:
            loser = units[i]
            if loser.get("curated"):
                winner["curated"] = True
                winner["digest_path"] = winner.get("digest_path") or loser.get("digest_path")
            dropped.append({**{k: loser.get(k) for k in ("id", "title", "sample", "nrec")}, "dup_of": winner["id"], "dup_title": winner["title"]})
        keep.append(winner)
    log(f"去重：{len(units)} 個單位 → 保留 {len(keep)}，去掉 {len(dropped)}（重複配對 {pairs}）")
    return keep, dropped


# ---------------------------------------------------------------------------


def load_raw(paths: list[Path]) -> list[dict]:
    seen: dict[str, dict] = {}
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                a = json.loads(line)
                a.setdefault("sample", "digest" if a["id"].startswith("D.") else "top")
                if not a.get("ts"):
                    try:
                        a["ts"] = int(a["id"].split(".")[1])
                    except (IndexError, ValueError):
                        a["ts"] = 0
                old = seen.get(a["id"])
                if old is not None and old.get("sample") != "digest" and a.get("sample") == "digest":
                    continue  # 同一個 id 出現兩次時保留看板版本，精華區不蓋掉看板
                seen[a["id"]] = a
    return list(seen.values())


def build(paths: list[Path] | None = None, out: Path = OUT, log=print) -> dict:
    paths = paths or sorted(RAW_DIR.glob("*.jsonl"))
    arts = load_raw(paths)
    board = [a for a in arts if a.get("sample") != "digest"]
    digest = [a for a in arts if a.get("sample") == "digest"]
    # 系列只在看板文章裡合併（精華區常把系列放同一目錄，但 ID 時間是收錄時間，不可靠）
    units = merge_series(board) + [_single(a) for a in digest]
    n_series = sum(1 for u in units if u["series_key"])
    n_parts = sum(len(u["parts"]) for u in units if u["series_key"])
    log(f"原始 {len(arts)} 篇（看板 {len(board)}、精華區 {len(digest)}）；系列 {n_series} 組，併掉 {n_parts} 章")
    keep, dropped = dedupe(units, log=log)
    keep.sort(key=lambda u: -(u.get("ts") or 0))
    out.write_text("".join(json.dumps(u, ensure_ascii=False) + "\n" for u in keep), encoding="utf-8")
    out.with_suffix(".dropped.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in dropped), encoding="utf-8"
    )
    by_sample: dict[str, int] = defaultdict(int)
    for u in keep:
        by_sample[u.get("sample") or "?"] += 1
    stats = {
        "raw": len(arts), "board": len(board), "digest": len(digest), "series": n_series,
        "series_parts": n_parts, "units": len(units), "kept": len(keep), "dropped": len(dropped),
        "by_sample": dict(by_sample), "curated": sum(1 for u in keep if u.get("curated")),
    }
    log(f"→ {out}：{stats}")
    return stats
