"""從推文內容算「毛率」和「虛率」，檢查跟推文數有關的特徵是不是也跟「讀者覺得毛」有關。

推文數量的是受歡迎；毛率量的是讀者有沒有說出「好毛」「雞皮疙瘩」。兩者方向一致，才比較能說某個特徵讓故事更可怕。

py -m storypipe.scare
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

from .stats import load_units

SCARY = re.compile(
    r"毛毛|好毛|很毛|超毛|有夠毛|真毛|太毛|毛到|毛起來|發毛|毛骨|雞皮|疙瘩|起雞|頭皮發麻|頭皮麻|寒毛|背脊|背涼|發涼|冷汗"
    r"|毛喔|毛啊|毛欸|毛耶|毛ㄟ|毛的|好恐|太恐|可怕|恐怖|嚇死|嚇到|嚇人|不敢|睡不著|怕怕|好怕|驚悚"
)
DOUBT = re.compile(r"虛|唬爛|豪洨|假的|編的|編故事|騙人|騙鬼|太扯|很扯|小說|創作文|業配|釣魚|不信|腦補|幻覺|吃藥|看醫生")
MIN_PUSHES = 10  # 推文少於 10 則的不算比例，雜訊太大


def push_index(raw_dir: Path = Path("data/raw")) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for f in raw_dir.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r.get("pushes") or []
    return out


def rates(pushes: list[dict]) -> tuple[float, float, int]:
    texts = [p.get("text", "") for p in pushes]
    n = len(texts)
    if not n:
        return 0.0, 0.0, 0
    s = sum(1 for t in texts if SCARY.search(t) and not DOUBT.search(t))
    d = sum(1 for t in texts if DOUBT.search(t))
    return s / n, d / n, n


def _welch(a: list[float], b: list[float]) -> float | None:
    """兩組平均數差的 Welch t 檢定，雙尾 p 值（常態近似，樣本大時夠用）。"""
    if len(a) < 5 or len(b) < 5:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    if se == 0:
        return None
    return math.erfc(abs(ma - mb) / se / math.sqrt(2))


def _spearman(xs: list[float], ys: list[float]) -> float:
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return cov / (vx * vy) if vx and vy else 0.0


FEATURES = [
    ("有對話", lambda a: "dialogue" in a["voice_markers"]),
    ("鬼清楚露面（3）", lambda a: a["ghost_explicitness"] == 3),
    ("鬼只有跡象（1）", lambda a: a["ghost_explicitness"] == 1),
    ("鬼完全不露面（0）", lambda a: a["ghost_explicitness"] == 0),
    ("結尾有解釋", lambda a: a["ending"] == "explained"),
    ("結尾開放", lambda a: a["ending"] == "open"),
    ("結尾反轉", lambda a: a["ending"] == "twist"),
    ("日常程序細節", lambda a: "procedure_detail" in a["voice_markers"]),
    ("具體地點", lambda a: "location_specific" in a["voice_markers"]),
    ("轉述家人朋友", lambda a: "friend_of_friend" in a["voice_markers"]),
    ("作者自我懷疑", lambda a: "self_doubt" in a["voice_markers"]),
    ("開頭免責", lambda a: "disclaimer" in a["voice_markers"]),
    ("主要機制：只有聲音", lambda a: a["mechanisms"][0] == "sound_only"),
    ("主要機制：在場感", lambda a: a["mechanisms"][0] == "presence"),
]


def analyze(annotated: Path, corpus: Path) -> str:
    rows, _ = load_units(annotated, corpus)
    corp = {}
    for line in corpus.read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            corp[u["id"]] = u
    P = push_index()
    data = []
    for r in rows:
        if r.get("pct") is None:
            continue
        u = corp[r["id"]]
        pushes = [p for part in u["parts"] for p in P.get(part["id"], [])]
        s, d, n = rates(pushes)
        if n < MIN_PUSHES:
            continue
        data.append({"tag": "翻譯" if r["source"].startswith("翻譯") else "經驗", "pct": r["pct"], "scary": s, "doubt": d, "n": n, "a": r["annotation"]})

    L = ["# 毛率分析", "",
         "毛率：推文裡出現「好毛、雞皮疙瘩、可怕、恐怖、頭皮發麻、不敢……」而且沒有「虛、唬爛、假的、小說……」的比例。",
         "虛率：推文裡出現「虛、唬爛、假的、編的、小說、太扯……」的比例。",
         f"只算有推文分數、推文至少 {MIN_PUSHES} 則的故事。", ""]
    for tag in ("經驗", "翻譯"):
        D = [x for x in data if x["tag"] == tag]
        if len(D) < 30:
            continue
        ms = sum(x["scary"] for x in D) / len(D)
        md = sum(x["doubt"] for x in D) / len(D)
        rho_s = _spearman([x["pct"] for x in D], [x["scary"] for x in D])
        rho_d = _spearman([x["pct"] for x in D], [x["doubt"] for x in D])
        L += [f"## {tag}文（{len(D)} 篇，推文中位數 {sorted(x['n'] for x in D)[len(D) // 2]} 則）", "",
              f"平均毛率 {100 * ms:.1f}%，平均虛率 {100 * md:.1f}%。推文百分位跟毛率的等級相關 {rho_s:+.2f}，跟虛率 {rho_d:+.2f}。", "",
              "| 特徵 | 篇數 | 有：毛率 | 沒有：毛率 | 差 | p | 有：虛率 | 沒有：虛率 | 差 | p |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for name, f in FEATURES:
            yes = [x for x in D if f(x["a"])]
            no = [x for x in D if not f(x["a"])]
            if len(yes) < 10 or len(no) < 10:
                continue
            def m(g, k):
                return sum(x[k] for x in g) / len(g)
            ps, pd = _welch([x["scary"] for x in yes], [x["scary"] for x in no]), _welch([x["doubt"] for x in yes], [x["doubt"] for x in no])
            fmt = lambda p: "—" if p is None else (f"**{p:.3f}**" if p < 0.01 else f"{p:.2f}")  # noqa: E731
            L.append(
                f"| {name} | {len(yes)} | {100 * m(yes, 'scary'):.1f}% | {100 * m(no, 'scary'):.1f}% | {100 * (m(yes, 'scary') - m(no, 'scary')):+.1f} | {fmt(ps)} "
                f"| {100 * m(yes, 'doubt'):.1f}% | {100 * m(no, 'doubt'):.1f}% | {100 * (m(yes, 'doubt') - m(no, 'doubt')):+.1f} | {fmt(pd)} |"
            )
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    md = analyze(Path("data/annotated.opus55.v2.jsonl"), Path("data/corpus.jsonl"))
    Path("data/scare_report.md").write_text(md, encoding="utf-8")
    print(md)
