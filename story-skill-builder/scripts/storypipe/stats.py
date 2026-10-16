"""從標註結果算出加權抽樣表 weights.json，以及給人看的 report.md。

分數：推文數在「同標籤、同年份的全部看板文章」裡的百分位（母體取自索引，不是只看抓下來的那些，
抓下來的已經過推文篩選）。同年份文章少於 50 篇時，往前後年份擴大到夠為止。
早期文章（genre.json 的 score_from_year 之前，推文很少）和精華區沒有可比的推文訊號，pct 是 None：
不參與高低分比較和權重，但精華區收錄過的可以當範例。

高分組：pct ≥ 0.75。低分組：pct ≤ 0.40（主要是隨機抽的對照組）。
權重：weight = (這個類別在高分組出現的次數 + 1) ^ 0.7，只用有分數的單位算。
（舊版是 平均分數 × ln(1+n)，資料多了以後會把整張表壓平，抽出來的骨架近乎平均分配。）

哪些軸、哪個露出上限、哪些節拍，都來自 genre.json；weights.json 的 axes 區跟著軸走。
"""
from __future__ import annotations

import bisect
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .genre import GENRE
from .taxonomy import BEATS, VOICE_MARKERS

INDEX_FILES: dict[str, str] = dict(GENRE.source.tags)
TAGS: list[str] = list(GENRE.source.tags) or [GENRE.source.default_tag]
HI_Q, LO_Q = 0.75, 0.40
MIN_POP = 50


# ---------------------------------------------------------------------------
# 載入與打分
# ---------------------------------------------------------------------------


def load_annotated(path: Path, stories_only: bool = True, exclude_markers: tuple[str, ...] = ()) -> list[dict]:
    """預設只排除非故事。翻譯／轉述外國故事預設納入；要分開看時傳 exclude_markers=("translated",)。"""
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            ann = rec["annotation"]
            if stories_only and not ann.get("is_story", True):
                continue
            if exclude_markers and any(m in ann.get("voice_markers", []) for m in exclude_markers):
                continue
            rows.append(rec)
    return rows


def _year(ts) -> int | None:
    return datetime.fromtimestamp(ts, tz=timezone.utc).year if ts else None


class Percentiles:
    """每個 (標籤, 年份) 一條排好序的推文數，算百分位用。"""

    def __init__(self, index_files: dict[str, str] = INDEX_FILES):
        self.pop: dict[tuple[str, int], list[int]] = defaultdict(list)
        for tag, f in index_files.items():
            p = Path(f)
            if not p.exists():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                if f"[{tag}]" not in r["title"] or not r.get("ts"):
                    continue
                self.pop[(tag, _year(r["ts"]))].append(int(r["nrec"]))
        for v in self.pop.values():
            v.sort()

    def pct(self, tag: str, year: int, nrec: int) -> float | None:
        vals: list[int] = []
        for w in range(0, 6):
            vals = sorted(x for y in range(year - w, year + w + 1) for x in self.pop.get((tag, y), []))
            if len(vals) >= MIN_POP:
                break
        if not vals:
            return None
        below = bisect.bisect_left(vals, nrec)
        equal = bisect.bisect_right(vals, nrec) - below
        return (below + 0.5 * equal) / len(vals)


def source_of(u: dict) -> str:
    """一個語料單位的來源標籤：標籤（＋對照）、早期、精華區。"""
    sample = u.get("sample") or "top"
    if sample == "digest":
        return "精華區"
    if sample == "unfiltered":
        return "早期"
    tag = u.get("source_tag") if u.get("source_tag") in TAGS else GENRE.source.default_tag
    return tag + ("對照" if sample == "control" else "")


def load_units(annotated_path: Path, corpus_path: Path, index_files: dict[str, str] = INDEX_FILES) -> tuple[list[dict], dict]:
    """標註 × 語料。回傳 (單位列，覆蓋率統計)。每列多了 pct、year、source、curated。只保留仍在語料裡的單位。"""
    corpus = {}
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            u = json.loads(line)
            corpus[u["id"]] = u
    P = Percentiles(index_files)
    rows, orphan, nonstory = [], 0, 0
    for rec in load_annotated(annotated_path, stories_only=False):
        u = corpus.get(rec["id"])
        if u is None:
            orphan += 1
            continue
        if not rec["annotation"].get("is_story", True):
            nonstory += 1
            continue
        sample = u.get("sample") or "top"
        source = source_of(u)
        tag = u.get("source_tag") if u.get("source_tag") in TAGS else GENRE.source.default_tag
        year = _year(u.get("ts"))
        pct = None
        if sample in ("top", "control") and year and year >= GENRE.source.score_from_year:
            pct = P.pct(tag, year, int(u.get("nrec") or 0))
        rows.append({**rec, "pct": pct, "year": year, "source": source, "curated": bool(u.get("curated")),
                     "length_chars": len(u.get("body") or "")})
    cov = {"orphan_annotations": orphan, "non_stories": nonstory, "stories": len(rows),
           "scored": sum(r["pct"] is not None for r in rows)}
    return rows, cov


# ---------------------------------------------------------------------------
# 權重
# ---------------------------------------------------------------------------


WEIGHT_POWER = 0.7  # 權重 = (高分組次數 + 1) ^ 0.7：抽出來的骨架長得像高分單位，又保留一點多樣性


def _table(rows: list[tuple], min_n: int = 1) -> dict[str, dict]:
    """rows 是 (類別, 分數, 是否在高分組)。舊格式 (類別, 分數) 也接受，那時權重退回 平均分數 × ln(1+n)。"""
    by: dict[str, list[float]] = defaultdict(list)
    hi: dict[str, int] = defaultdict(int)
    has_flag = bool(rows) and len(rows[0]) == 3
    for row in rows:
        k, s = row[0], row[1]
        by[k].append(s)
        if has_flag and row[2]:
            hi[k] += 1
    out = {}
    for k, scores in by.items():
        n = len(scores)
        if n < min_n:
            continue
        mean = sum(scores) / n
        weight = (hi[k] + 1) ** WEIGHT_POWER if has_flag else mean * math.log1p(n)
        out[k] = {"n": n, "n_high": hi[k] if has_flag else None, "mean_score": round(mean, 1), "weight": round(weight, 3)}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["weight"]))


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    idx = (len(vs) - 1) * p
    lo, hi = math.floor(idx), math.ceil(idx)
    if lo == hi:
        return vs[lo]
    return vs[lo] + (vs[hi] - vs[lo]) * (idx - lo)


def _two_prop_p(p1: float, n1: int, p2: float, n2: int) -> float | None:
    """兩比例 z 檢定的雙尾 p 值（常態近似）。樣本太小時不準，只當篩選用。"""
    if not n1 or not n2:
        return None
    pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    z = abs(p1 - p2) / se
    return round(math.erfc(z / math.sqrt(2)), 4)


def _rank_pct(rows: list[dict]) -> None:
    """沒有語料和索引時的退路：在資料本身裡依 score 排名次。"""
    xs = sorted(r["score"] for r in rows)
    for r in rows:
        below = bisect.bisect_left(xs, r["score"])
        equal = bisect.bisect_right(xs, r["score"]) - below
        r["pct"] = (below + 0.5 * equal) / len(xs)


def compute_weights(rows: list[dict], hi_q: float = HI_Q, lo_q: float = LO_Q, per_example_axis: int = 25) -> dict:
    if not rows:
        raise ValueError("沒有可用的標註資料")
    rows = [dict(r) for r in rows]
    if not any("pct" in r for r in rows):
        _rank_pct(rows)
    scored = [r for r in rows if r.get("pct") is not None]
    if not scored:
        raise ValueError("沒有帶分數的單位")
    high = [r for r in scored if r["pct"] >= hi_q]
    low = [r for r in scored if r["pct"] <= lo_q]
    A = lambda r: r["annotation"]  # noqa: E731
    S = lambda r: 100 * r["pct"]  # noqa: E731
    cap = GENRE.cap

    high_ids = {id(r) for r in high}
    axes: dict[str, dict] = {}
    for ax in GENRE.axes:
        entry = {"table": _table([(ax.primary(A(r)), S(r), id(r) in high_ids) for r in scored if ax.primary(A(r)) is not None])}
        if ax.multi:
            entry["any"] = _table([(m, S(r), id(r) in high_ids) for r in scored for m in ax.all_values(A(r))])
        axes[ax.key] = entry
    pairs: dict[str, dict] = {}
    if GENRE.pair:
        a, b = GENRE.axis(GENRE.pair[0]), GENRE.axis(GENRE.pair[1])
        pairs = _table(
            [(f"{a.primary(A(r))}|{b.primary(A(r))}", S(r), id(r) in high_ids) for r in scored if a.primary(A(r)) and b.primary(A(r))],
            min_n=3 if len(scored) >= 300 else 2,
        )

    def mean_beats(group: list[dict]) -> dict[str, float]:
        if not group:
            return {b: 0.0 for b in BEATS}
        return {b: round(sum(A(r)["beats"].get(b, 0.0) for r in group) / len(group), 3) for b in BEATS}

    def cap_dist(group: list[dict]) -> dict[str, int]:
        d = {str(i): 0 for i in range(cap.min, cap.max + 1)}
        for r in group:
            d[str(A(r)[cap.key])] = d.get(str(A(r)[cap.key]), 0) + 1
        return d

    def cap_mean(group: list[dict]) -> float:
        return round(sum(A(r)[cap.key] for r in group) / len(group), 2) if group else 0.0

    def share(group: list[dict], key) -> dict[str, float]:
        c = Counter(k for r in group for k in key(r))
        return {k: v / len(group) for k, v in c.items()} if group else {}

    def contrast(key, hi: list[dict], lo: list[dict], base: list[dict]) -> list[dict]:
        sh, sl, sa = share(hi, key), share(lo, key), share(base, key)
        keys = sorted(set(sh) | set(sl), key=lambda k: -sa.get(k, 0))
        return [{"key": k, "high": round(sh.get(k, 0), 3), "low": round(sl.get(k, 0), 3),
                 "lift": round(sh.get(k, 0) / sl[k], 2) if sl.get(k) else None,
                 "p": _two_prop_p(sh.get(k, 0), len(hi), sl.get(k, 0), len(lo))} for k in keys]

    def contrasts(hs: list[dict], ls: list[dict], bs: list[dict]) -> dict[str, list[dict]]:
        out = {ax.key: contrast(lambda r, ax=ax: [ax.primary(A(r))], hs, ls, bs) for ax in GENRE.axes}
        out["cap"] = contrast(lambda r: [str(A(r)[cap.key])], hs, ls, bs)
        out["voice"] = contrast(lambda r: A(r).get("voice_markers", []), hs, ls, bs)
        return out

    # 範例池：高分組 + 精華區收錄過的（沒分數的當 0.8），example_axis 的每個值最多 per_example_axis 個
    ex_ax = GENRE.axis(GENRE.example_axis)
    cand = high + [r for r in rows if r.get("pct") is None and r.get("curated")]
    cand.sort(key=lambda r: -(r["pct"] if r.get("pct") is not None else 0.8))
    per: dict[str, int] = defaultdict(int)
    examples = []
    for r in cand:
        a = A(r)
        s = ex_ax.primary(a)
        if per[s] >= per_example_axis:
            continue
        per[s] += 1
        examples.append({
            "id": r["id"], "title": r["title"], "score": round(r["pct"], 3) if r.get("pct") is not None else None,
            "source": r.get("source"), "year": r.get("year"), "curated": r.get("curated", False),
            "axes": GENRE.axis_values(a),
            "detail": {ax.detail.key: a.get(ax.detail.key, "") for ax in GENRE.axes if ax.detail},
            "cap": a[cap.key], "premise": a[GENRE.premise.key], "moment": a[GENRE.moment.key],
            "anchors": list(a.get(GENRE.anchors.key, [])),
        })

    lengths_top = [r["length_chars"] for r in high if r.get("length_chars")]
    unscored = [r for r in rows if r.get("pct") is None]
    by_tag = {}
    for tag in TAGS:
        hs = [r for r in high if str(r.get("source", "")).startswith(tag)]
        ls = [r for r in low if str(r.get("source", "")).startswith(tag)]
        bs = [r for r in scored if str(r.get("source", "")).startswith(tag)]
        if hs and ls:
            by_tag[tag] = {"n_high": len(hs), "n_low": len(ls), **contrasts(hs, ls, bs)}
    return {
        "genre": GENRE.name,
        "n_stories": len(rows),
        "n_scored": len(scored),
        "n_top": len(high),
        "n_low": len(low),
        "hi_q": hi_q,
        "lo_q": lo_q,
        "axes": axes,
        "pairs": pairs,
        "beats_top": mean_beats(high),
        "beats_low": mean_beats(low),
        "beats_all": mean_beats(scored),
        "cap": {
            "top_mean": cap_mean(high), "bottom_mean": cap_mean(low), "all_mean": cap_mean(scored),
            "dist_top": cap_dist(high), "dist_low": cap_dist(low),
        },
        "length_top": {"p25": _percentile(lengths_top, 0.25), "p50": _percentile(lengths_top, 0.5), "p75": _percentile(lengths_top, 0.75)},
        "contrast": contrasts(high, low, scored),
        # 依標籤分開比：高低分組的來源組成不同（例如低分組約一半是翻譯文），混在一起比會把來源差異當成品質差異
        "contrast_by_tag": by_tag,
        "years_top": dict(sorted(Counter(r.get("year") for r in high if r.get("year")).items())),
        "sources": {
            "all": dict(Counter(r.get("source", "?") for r in rows)),
            "top": dict(Counter(r.get("source", "?") for r in high)),
            "low": dict(Counter(r.get("source", "?") for r in low)),
        },
        "unscored": {
            "axes": {ax.key: dict(Counter(ax.primary(A(r)) for r in unscored)) for ax in GENRE.axes},
            "cap_mean": cap_mean(unscored),
        },
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# 報告
# ---------------------------------------------------------------------------


def render_report(w: dict, coverage: dict | None = None) -> str:
    cap = GENRE.cap

    def lab(table: dict, k: str) -> str:
        return str(table.get(k, k)).split("：")[0]

    def tbl(title: str, table: dict, labels: dict) -> list[str]:
        lines = [f"## {title}", "", "| 類別 | 篇數 | 高分組篇數 | 平均百分位 | 權重 |", "|---|---|---|---|---|"]
        for k, v in table.items():
            lines.append(f"| {lab(labels, k)} | {v['n']} | {v.get('n_high', '')} | {v['mean_score']} | {v['weight']} |")
        return lines + [""]

    def ctr(title: str, rows: list[dict], labels: dict, k: int = 15) -> list[str]:
        lines = [f"## {title}：高分組 vs 低分組", "", "| 類別 | 高分組 | 低分組 | 倍數 | p 值 |", "|---|---|---|---|---|"]
        for x in rows[:k]:
            lift = f"{x['lift']:.2f}" if x["lift"] is not None else "—"
            pv = x.get("p")
            ptxt = "—" if pv is None else (f"**{pv:.3f}**" if pv < 0.05 else f"{pv:.2f}")
            lines.append(f"| {lab(labels, x['key'])} | {100 * x['high']:.0f}% | {100 * x['low']:.0f}% | {lift} | {ptxt} |")
        return lines + [""]

    def ctr_block(c: dict, prefix: str) -> list[str]:
        out: list[str] = []
        for ax in GENRE.axes:
            out += ctr(f"{prefix}{ax.label}", c[ax.key], ax.values)
        out += ctr(f"{prefix}{cap.short_name}", c["cap"], {})
        out += ctr(f"{prefix}敘事聲音", c["voice"], VOICE_MARKERS, 12)
        return out

    L = [f"# {GENRE.unit} DNA 統計", ""]
    if coverage:
        L += [f"標註裡的{GENRE.unit} {coverage['stories']} 個（另有非{GENRE.unit} {coverage['non_stories']} 個、已不在語料裡的舊標註 {coverage['orphan_annotations']} 個）。", ""]
    L += [
        f"有推文分數的 {w['n_scored']} 個；高分組（同年同標籤前 {100 * (1 - w['hi_q']):.0f}%）{w['n_top']} 個，"
        f"低分組（後 {100 * w['lo_q']:.0f}%）{w['n_low']} 個。沒有分數的（早期、精華區）{w['n_stories'] - w['n_scored']} 個，只用在範例池和分布。",
        "",
        "來源：全部 " + str(w["sources"]["all"]) + "；高分組 " + str(w["sources"]["top"]) + "；低分組 " + str(w["sources"]["low"]),
        "",
        "高分組年份：" + "、".join(f"{y}:{n}" for y, n in w["years_top"].items()),
        "",
    ]
    for ax in GENRE.axes:
        L += tbl(ax.label if not ax.multi else f"主要{ax.label}", w["axes"][ax.key]["table"], ax.values)
    if w.get("pairs") and GENRE.pair:
        a, b = GENRE.axis(GENRE.pair[0]), GENRE.axis(GENRE.pair[1])
        pair_labels = {k: f"{a.short(k.split('|')[0])} × {b.short(k.split('|')[1])}" for k in w["pairs"]}
        L += tbl(f"{a.label} × {b.label}", w["pairs"], pair_labels)
    for tag, c in w.get("contrast_by_tag", {}).items():
        L += [f"# {tag}文內部的高低分對比（高分組 {c['n_high']}、低分組 {c['n_low']}）", "",
              "同標籤內比，才不會把不同來源的差異誤當成品質差異。p 值 < 0.05 加粗；低分組篇數少時，沒加粗的差異多半是雜訊。", ""]
        L += ctr_block(c, f"{tag}｜")
    L += ["# 全部混在一起的對比（受來源組成影響，只當參考）", ""]
    L += ctr_block(w["contrast"], "")
    L += [
        "## 節拍比例", "", "| 節拍 | 高分組 | 低分組 | 全部 |", "|---|---|---|---|",
        *[f"| {b} | {w['beats_top'][b]:.2f} | {w['beats_low'][b]:.2f} | {w['beats_all'][b]:.2f} |" for b in BEATS],
        "",
        f"## {cap.label}", "",
        f"高分組平均 {w['cap']['top_mean']}，低分組平均 {w['cap']['bottom_mean']}，"
        f"沒分數的 {w['unscored']['cap_mean']}。高分組分布 {w['cap']['dist_top']}，低分組 {w['cap']['dist_low']}。",
        "",
        "## 高分組字數", "",
        f"p25 {w['length_top']['p25']:.0f}、p50 {w['length_top']['p50']:.0f}、p75 {w['length_top']['p75']:.0f}",
        "",
    ]
    ex_ax = GENRE.axis(GENRE.example_axis)
    L += [
        f"## 範例池（{len(w['examples'])} 個，{ex_ax.label}的每個值最多 25 個）", "",
        f"依{ex_ax.label}：" + "、".join(f"{ex_ax.short(k)} {v}" for k, v in Counter((e['axes'].get(ex_ax.key) or ['?'])[0] for e in w["examples"]).most_common()),
        "",
    ]
    for e in w["examples"][:20]:
        parts = "；".join("/".join(e["axes"].get(ax.key, [])) for ax in GENRE.axes)
        score = ("%.2f" % e["score"]) if e["score"] is not None else "收錄"
        L.append(f"- {score} [{e.get('source')}/{e.get('year')}] {e['title']}：{e['premise']}（{parts}；{cap.short_name} {e['cap']}）")
    L.append("")
    return "\n".join(L)


def run(
    annotated_path: Path,
    weights_path: Path,
    report_path: Path | None = None,
    exclude_markers: tuple[str, ...] = (),
    corpus_path: Path | None = None,
) -> dict:
    coverage = None
    if corpus_path and corpus_path.exists():
        rows, coverage = load_units(annotated_path, corpus_path)
        if exclude_markers:
            rows = [r for r in rows if not any(m in r["annotation"].get("voice_markers", []) for m in exclude_markers)]
    else:
        rows = load_annotated(annotated_path, exclude_markers=exclude_markers)
    w = compute_weights(rows)
    if coverage:
        w["coverage"] = coverage
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights_path.write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
    if report_path:
        report_path.write_text(render_report(w, coverage), encoding="utf-8")
    return w
