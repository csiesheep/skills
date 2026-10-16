"""從推文內容算第二個品質訊號（鬼故事是「毛率」和「虛率」），檢查跟推文數有關的特徵是不是也跟它有關。

推文數量的是受歡迎；第二訊號量的是讀者有沒有說出類型想要的反應（好毛、笑死、哭了）。
兩者方向一致，才比較能說某個特徵讓單位更好。關鍵字在 genre.json 的 signal。

py -m storypipe.scare [--annotated data/annotated.jsonl] [--corpus data/corpus.jsonl] [--out data/scare_report.md]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from .genre import GENRE
from .stats import TAGS, load_units

SIG = GENRE.signal
POS = re.compile(SIG.positive) if SIG else None
NEG = re.compile(SIG.negative) if SIG else None
MIN_PUSHES = SIG.min_comments if SIG else 10  # 推文少於這個數的不算比例，雜訊太大


def push_index(raw_dir: Path = Path("data/raw")) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for f in raw_dir.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r.get("pushes") or []
    return out


def rates(pushes: list[dict]) -> tuple[float, float, int]:
    """回傳 (正向率, 負向率, 推文數)。"""
    if POS is None or NEG is None:
        raise ValueError("genre.json 沒有 signal，算不了第二訊號")
    texts = [p.get("text", "") for p in pushes]
    n = len(texts)
    if not n:
        return 0.0, 0.0, 0
    s = sum(1 for t in texts if POS.search(t) and not NEG.search(t))
    d = sum(1 for t in texts if NEG.search(t))
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


def features() -> list[tuple[str, object]]:
    """要檢查的特徵：每個敘事聲音標記、露出上限的每一級、每個軸的每個主要值。"""
    cap = GENRE.cap
    out: list[tuple[str, object]] = []
    for k, label in GENRE.voice_markers.items():
        out.append((label.split("：")[0], lambda a, k=k: k in a.get("voice_markers", [])))
    for lv in range(cap.min, cap.max + 1):
        out.append((f"{cap.short_name} {cap.level_label(lv)}", lambda a, lv=lv: a[cap.key] == lv))
    for ax in GENRE.axes:
        for k in ax.values:
            out.append((f"{ax.label}：{ax.short(k)}", lambda a, ax=ax, k=k: ax.primary(a) == k))
    return out


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
        pushes = [p for part in u.get("parts", [{"id": r["id"]}]) for p in P.get(part["id"], [])]
        s, d, n = rates(pushes)
        if n < MIN_PUSHES:
            continue
        tag = next((t for t in TAGS if str(r["source"]).startswith(t)), TAGS[0])
        data.append({"tag": tag, "pct": r["pct"], "pos": s, "neg": d, "n": n, "a": r["annotation"]})

    pn, nn = SIG.positive_name, SIG.negative_name
    L = [f"# {pn}分析", "",
         f"{pn}：推文裡出現正向關鍵字（{SIG.positive[:60]}…）而且沒有負向關鍵字的比例。",
         f"{nn}：推文裡出現負向關鍵字（{SIG.negative[:60]}…）的比例。",
         f"只算有推文分數、推文至少 {MIN_PUSHES} 則的{GENRE.unit}。", ""]
    for tag in TAGS:
        D = [x for x in data if x["tag"] == tag]
        if len(D) < 30:
            continue
        ms = sum(x["pos"] for x in D) / len(D)
        md = sum(x["neg"] for x in D) / len(D)
        rho_s = _spearman([x["pct"] for x in D], [x["pos"] for x in D])
        rho_d = _spearman([x["pct"] for x in D], [x["neg"] for x in D])
        L += [f"## {tag}文（{len(D)} 篇，推文中位數 {sorted(x['n'] for x in D)[len(D) // 2]} 則）", "",
              f"平均{pn} {100 * ms:.1f}%，平均{nn} {100 * md:.1f}%。推文百分位跟{pn}的等級相關 {rho_s:+.2f}，跟{nn} {rho_d:+.2f}。", "",
              f"| 特徵 | 篇數 | 有：{pn} | 沒有：{pn} | 差 | p | 有：{nn} | 沒有：{nn} | 差 | p |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for name, f in features():
            yes = [x for x in D if f(x["a"])]
            no = [x for x in D if not f(x["a"])]
            if len(yes) < 10 or len(no) < 10:
                continue

            def m(g, k):
                return sum(x[k] for x in g) / len(g)

            ps, pd = _welch([x["pos"] for x in yes], [x["pos"] for x in no]), _welch([x["neg"] for x in yes], [x["neg"] for x in no])
            fmt = lambda p: "—" if p is None else (f"**{p:.3f}**" if p < 0.01 else f"{p:.2f}")  # noqa: E731
            L.append(
                f"| {name} | {len(yes)} | {100 * m(yes, 'pos'):.1f}% | {100 * m(no, 'pos'):.1f}% | {100 * (m(yes, 'pos') - m(no, 'pos')):+.1f} | {fmt(ps)} "
                f"| {100 * m(yes, 'neg'):.1f}% | {100 * m(no, 'neg'):.1f}% | {100 * (m(yes, 'neg') - m(no, 'neg')):+.1f} | {fmt(pd)} |"
            )
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotated", default="data/annotated.jsonl")
    ap.add_argument("--corpus", default="data/corpus.jsonl")
    ap.add_argument("--out", default="data/scare_report.md")
    a = ap.parse_args()
    md = analyze(Path(a.annotated), Path(a.corpus))
    Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
