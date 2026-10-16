"""一批標註的報告：時間、花費、標記分布，並推估剩下的量。

py -m storypipe.cli batch-report --ids data/batch1.ids --log data/annotate_batch1.log
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from .llm import list_cost
from .taxonomy import ENDINGS, MECHANISMS, SETTINGS


def source_of(u: dict) -> str:
    s = u.get("sample")
    if s == "digest":
        return "精華區"
    if s == "unfiltered":
        return "早期"
    base = "翻譯" if u.get("source_tag") == "翻譯" else "經驗"
    return base + ("對照" if s == "control" else "")


SOURCES = ["經驗", "經驗對照", "翻譯", "翻譯對照", "早期", "精華區"]


def _pct(a: float, b: float) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def _q(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0.0


def _wall(log: Path | None) -> float | None:
    if not log or not log.exists():
        return None
    t = log.read_text(encoding="utf-8", errors="replace")
    m1 = re.search(r"^start (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", t, re.M)
    m2 = re.search(r"^exit \d+ (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", t, re.M)
    if not (m1 and m2):
        return None
    f = "%Y-%m-%d %H:%M:%S"
    return (datetime.strptime(m2.group(1), f) - datetime.strptime(m1.group(1), f)).total_seconds()


def report(ann_path: Path, ids_path: Path, corpus_path: Path, log_path: Path | None = None, pending_after: int | None = None) -> str:
    ids = [l.strip() for l in ids_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    idset = set(ids)
    units = {}
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            if u["id"] in idset:
                units[u["id"]] = u
    recs = {}
    for line in ann_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] in idset:
                recs[r["id"]] = r
    R = list(recs.values())
    n = len(R)
    src = {i: source_of(units[i]) for i in recs if i in units}

    cost = {r["id"]: list_cost(r.get("model") or "", r.get("usage") or {}) or 0.0 for r in R}
    el = [r.get("elapsed_s") or 0 for r in R]
    usage = Counter()
    for r in R:
        usage.update({k: int(v or 0) for k, v in (r.get("usage") or {}).items()})
    chars = {r["id"]: len((units.get(r["id"]) or {}).get("body") or "") for r in R}
    wall = _wall(log_path)

    L = [f"# 標註批次報告：{ids_path.name}", ""]
    L += [
        f"篇目 {len(ids)} 個，完成 {n} 個，失敗或未完成 {len(ids) - n} 個。",
        f"實際模型：{dict(Counter(r.get('model') for r in R))}；prompt：{dict(Counter(r.get('prompt_version') for r in R))}；effort：{dict(Counter(r.get('effort') for r in R))}。",
        "",
        "## 時間",
        "",
        "| 指標 | 數值 |",
        "|---|---|",
    ]
    if wall:
        L.append(f"| 牆鐘時間 | {wall / 60:.1f} 分鐘 |")
        L.append(f"| 吞吐量 | 每分鐘 {n / (wall / 60):.1f} 個 |")
    L += [
        f"| 單次呼叫中位數 | {_q(el, .5):.1f} 秒 |",
        f"| 單次呼叫 p90 | {_q(el, .9):.1f} 秒 |",
        f"| 單次呼叫最長 | {max(el) if el else 0:.1f} 秒 |",
        "",
        "## 花費（照官方定價用 token 數算）",
        "",
        "| 指標 | 數值 |",
        "|---|---|",
        f"| 合計 | ${sum(cost.values()):.2f} |",
        f"| 每個單位平均 | ${sum(cost.values()) / max(1, n):.4f} |",
        f"| 每個單位中位數 | ${_q(list(cost.values()), .5):.4f} |",
        f"| 每個單位 p90 | ${_q(list(cost.values()), .9):.4f} |",
        f"| 每千字成本 | ${1000 * sum(cost.values()) / max(1, sum(chars.values())):.4f} |",
        f"| 每單位輸出 token | {usage['output_tokens'] / max(1, n):.0f}（思考 {usage['thinking_tokens'] / max(1, n):.0f}） |",
        f"| 每單位快取寫入 token | {usage['cache_creation_input_tokens'] / max(1, n):.0f} |",
        f"| 每單位快取讀取 token | {usage['cache_read_input_tokens'] / max(1, n):.0f} |",
        "",
    ]
    if pending_after is not None:
        avg = sum(cost.values()) / max(1, n)
        L += [
            f"**推估剩下 {pending_after} 個**：約 ${avg * pending_after:.0f}"
            + (f"，4 路平行約 {pending_after / (n / (wall / 60)) / 60:.1f} 小時" if wall else "")
            + "。",
            "",
        ]

    # 依來源
    by = defaultdict(list)
    for r in R:
        by[src.get(r["id"], "?")].append(r)
    L += ["## 依來源", "", "| 來源 | 單位 | 判為故事 | 翻譯標記 | 平均花費 | 字數中位數 | 鬼露出平均 | 結尾：開放／解釋／反轉／淡出 |", "|---|---|---|---|---|---|---|---|"]
    for s in SOURCES + ["?"]:
        g = by.get(s)
        if not g:
            continue
        st = [r for r in g if r["annotation"]["is_story"]]
        e = Counter(r["annotation"]["ending"] for r in st)
        gh = [r["annotation"]["ghost_explicitness"] for r in st]
        L.append(
            f"| {s} | {len(g)} | {len(st)}（{_pct(len(st), len(g))}） | {sum('translated' in r['annotation']['voice_markers'] for r in st)} "
            f"| ${sum(cost[r['id']] for r in g) / len(g):.4f} | {int(_q([chars[r['id']] for r in g], .5))} "
            f"| {sum(gh) / len(gh) if gh else 0:.2f} | {e['open']}／{e['explained']}／{e['twist']}／{e['fade']} |"
        )
    L.append("")

    # 分布（只算故事）
    S = [r for r in R if r["annotation"]["is_story"]]
    ns = len(S)

    def dist(title: str, key, labels: dict, k: int = 10) -> None:
        c = Counter(key(r) for r in S)
        L.extend([f"## {title}（故事 {ns} 個）", "", "| 類別 | 個數 | 比例 |", "|---|---|---|"])
        for kk, v in c.most_common(k):
            L.append(f"| {labels.get(kk, kk).split('：')[0]} | {v} | {_pct(v, ns)} |")
        L.append("")

    dist("場景", lambda r: r["annotation"]["setting"], SETTINGS, 12)
    dist("主要機制", lambda r: r["annotation"]["mechanisms"][0], MECHANISMS, 15)
    dist("結尾", lambda r: r["annotation"]["ending"], ENDINGS, 4)
    dist("鬼露出", lambda r: str(r["annotation"]["ghost_explicitness"]), {}, 4)

    non = [r for r in R if not r["annotation"]["is_story"]]
    L += [f"## 判為非故事的標題抽樣（共 {len(non)} 個）", ""]
    for r in sorted(non, key=lambda r: r["id"])[:25]:
        L.append(f"- [{src.get(r['id'], '?')}] {r['title']}")
    L.append("")
    return "\n".join(L)
