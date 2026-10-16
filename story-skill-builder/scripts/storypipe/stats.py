"""從標註結果算出加權抽樣表 weights.json，以及給人看的 report.md。

分數：推文數在「同標籤、同年份的全部看板文章」裡的百分位（母體取自索引，不是只看抓下來的那些，
抓下來的已經過推文篩選）。同年份文章少於 50 篇時，往前後年份擴大到夠為止。
早期文章（2007 年前，推文很少）和精華區沒有可比的推文訊號，pct 是 None：不參與高低分比較和權重，
但精華區收錄過的可以當範例。

高分組：pct ≥ 0.75。低分組：pct ≤ 0.40（主要是隨機抽的對照組）。
權重：weight = (這個類別在高分組出現的次數 + 1) ^ 0.7，只用有分數的故事算。
（舊版是 平均分數 × ln(1+n)，資料多了以後會把整張表壓平，抽出來的骨架近乎平均分配。）
"""
from __future__ import annotations

import bisect
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .taxonomy import BEATS, ENDINGS, MECHANISMS, SETTINGS, VOICE_MARKERS

INDEX_FILES = {"經驗": "data/index/marvel_經驗.jsonl", "翻譯": "data/index/marvel_翻譯.jsonl"}
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


def load_units(annotated_path: Path, corpus_path: Path, index_files: dict[str, str] = INDEX_FILES) -> tuple[list[dict], dict]:
    """標註 × 語料。回傳 (故事列，覆蓋率統計)。每列多了 pct、year、source、curated。只保留仍在語料裡的單位。"""
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
        tag = "翻譯" if u.get("source_tag") == "翻譯" else "經驗"
        year = _year(u.get("ts"))
        if sample == "digest":
            source = "精華區"
        elif sample == "unfiltered":
            source = "早期"
        else:
            source = tag + ("對照" if sample == "control" else "")
        pct = None
        if sample in ("top", "control") and year and year >= 2007:
            pct = P.pct(tag, year, int(u.get("nrec") or 0))
        rows.append({**rec, "pct": pct, "year": year, "source": source, "curated": bool(u.get("curated")),
                     "length_chars": len(u.get("body") or "")})
    cov = {"orphan_annotations": orphan, "non_stories": nonstory, "stories": len(rows),
           "scored": sum(r["pct"] is not None for r in rows)}
    return rows, cov


# ---------------------------------------------------------------------------
# 權重
# ---------------------------------------------------------------------------


WEIGHT_POWER = 0.7  # 權重 = (高分組次數 + 1) ^ 0.7：抽出來的骨架長得像高分故事，又保留一點多樣性


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


def compute_weights(rows: list[dict], hi_q: float = HI_Q, lo_q: float = LO_Q, per_setting_examples: int = 25) -> dict:
    if not rows:
        raise ValueError("沒有可用的標註資料")
    rows = [dict(r) for r in rows]
    if not any("pct" in r for r in rows):
        _rank_pct(rows)
    scored = [r for r in rows if r.get("pct") is not None]
    if not scored:
        raise ValueError("沒有帶分數的故事")
    high = [r for r in scored if r["pct"] >= hi_q]
    low = [r for r in scored if r["pct"] <= lo_q]
    A = lambda r: r["annotation"]  # noqa: E731
    S = lambda r: 100 * r["pct"]  # noqa: E731

    high_ids = {id(r) for r in high}
    settings = _table([(A(r)["setting"], S(r), id(r) in high_ids) for r in scored])
    primary_mech = _table([(A(r)["mechanisms"][0], S(r), id(r) in high_ids) for r in scored if A(r)["mechanisms"]])
    any_mech = _table([(m, S(r), id(r) in high_ids) for r in scored for m in A(r)["mechanisms"]])
    endings = _table([(A(r)["ending"], S(r), id(r) in high_ids) for r in scored])
    pairs = _table([(f"{A(r)['setting']}|{A(r)['mechanisms'][0]}", S(r), id(r) in high_ids) for r in scored if A(r)["mechanisms"]],
                   min_n=3 if len(scored) >= 300 else 2)

    def mean_beats(group: list[dict]) -> dict[str, float]:
        if not group:
            return {b: 0.0 for b in BEATS}
        return {b: round(sum(A(r)["beats"][b] for r in group) / len(group), 3) for b in BEATS}

    def ghost_dist(group: list[dict]) -> dict[str, int]:
        d = {str(i): 0 for i in range(4)}
        for r in group:
            d[str(A(r)["ghost_explicitness"])] += 1
        return d

    def ghost_mean(group: list[dict]) -> float:
        return round(sum(A(r)["ghost_explicitness"] for r in group) / len(group), 2) if group else 0.0

    def share(group: list[dict], key) -> dict[str, float]:
        c = Counter(k for r in group for k in key(r))
        return {k: v / len(group) for k, v in c.items()} if group else {}

    def contrast(key, hi=None, lo=None, base=None) -> list[dict]:
        hi, lo, base = (high if hi is None else hi), (low if lo is None else lo), (scored if base is None else base)
        sh, sl, sa = share(hi, key), share(lo, key), share(base, key)
        keys = sorted(set(sh) | set(sl), key=lambda k: -sa.get(k, 0))
        return [{"key": k, "high": round(sh.get(k, 0), 3), "low": round(sl.get(k, 0), 3),
                 "lift": round(sh.get(k, 0) / sl[k], 2) if sl.get(k) else None,
                 "p": _two_prop_p(sh.get(k, 0), len(hi), sl.get(k, 0), len(lo))} for k in keys]

    # 範例池：高分組 + 精華區收錄過的（沒分數的當 0.8），每個場景最多 per_setting_examples 篇
    cand = high + [r for r in rows if r.get("pct") is None and r.get("curated")]
    cand.sort(key=lambda r: -(r["pct"] if r.get("pct") is not None else 0.8))
    per: dict[str, int] = defaultdict(int)
    examples = []
    for r in cand:
        s = A(r)["setting"]
        if per[s] >= per_setting_examples:
            continue
        per[s] += 1
        examples.append({
            "id": r["id"], "title": r["title"], "score": round(r["pct"], 3) if r.get("pct") is not None else None,
            "source": r.get("source"), "year": r.get("year"), "curated": r.get("curated", False),
            "setting": s, "setting_detail": A(r)["setting_detail"], "mechanisms": A(r)["mechanisms"],
            "ending": A(r)["ending"], "ghost_explicitness": A(r)["ghost_explicitness"],
            "one_line_premise": A(r)["one_line_premise"], "scariest_moment": A(r)["scariest_moment"],
            "realism_anchors": A(r)["realism_anchors"],
        })

    lengths_top = [r["length_chars"] for r in high if r.get("length_chars")]
    unscored = [r for r in rows if r.get("pct") is None]
    return {
        "n_stories": len(rows),
        "n_scored": len(scored),
        "n_top": len(high),
        "n_low": len(low),
        "hi_q": hi_q,
        "lo_q": lo_q,
        "settings": settings,
        "mechanisms_primary": primary_mech,
        "mechanisms_any": any_mech,
        "endings": endings,
        "pairs": pairs,
        "beats_top": mean_beats(high),
        "beats_low": mean_beats(low),
        "beats_all": mean_beats(scored),
        "ghost_explicitness": {
            "top_mean": ghost_mean(high), "bottom_mean": ghost_mean(low), "all_mean": ghost_mean(scored),
            "dist_top": ghost_dist(high), "dist_low": ghost_dist(low),
        },
        "length_top": {"p25": _percentile(lengths_top, 0.25), "p50": _percentile(lengths_top, 0.5), "p75": _percentile(lengths_top, 0.75)},
        "contrast": {
            "setting": contrast(lambda r: [A(r)["setting"]]),
            "mechanism": contrast(lambda r: [A(r)["mechanisms"][0]]),
            "ending": contrast(lambda r: [A(r)["ending"]]),
            "ghost": contrast(lambda r: [str(A(r)["ghost_explicitness"])]),
            "voice": contrast(lambda r: A(r)["voice_markers"]),
        },
        # 依標籤分開比：高低分組的來源組成不同（低分組約一半是翻譯文），混在一起比會把來源差異當成品質差異
        "contrast_by_tag": {
            tag: {
                "n_high": len(hs), "n_low": len(ls),
                "setting": contrast(lambda r: [A(r)["setting"]], hs, ls, bs),
                "mechanism": contrast(lambda r: [A(r)["mechanisms"][0]], hs, ls, bs),
                "ending": contrast(lambda r: [A(r)["ending"]], hs, ls, bs),
                "ghost": contrast(lambda r: [str(A(r)["ghost_explicitness"])], hs, ls, bs),
                "voice": contrast(lambda r: A(r)["voice_markers"], hs, ls, bs),
            }
            for tag in ("經驗", "翻譯")
            for hs, ls, bs in [(
                [r for r in high if str(r.get("source", "")).startswith(tag)],
                [r for r in low if str(r.get("source", "")).startswith(tag)],
                [r for r in scored if str(r.get("source", "")).startswith(tag)],
            )]
            if hs and ls
        },
        "years_top": dict(sorted(Counter(r.get("year") for r in high if r.get("year")).items())),
        "sources": {
            "all": dict(Counter(r.get("source", "?") for r in rows)),
            "top": dict(Counter(r.get("source", "?") for r in high)),
            "low": dict(Counter(r.get("source", "?") for r in low)),
        },
        "unscored_endings": dict(Counter(A(r)["ending"] for r in unscored)),
        "unscored_ghost_mean": ghost_mean(unscored),
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# 報告
# ---------------------------------------------------------------------------


def render_report(w: dict, coverage: dict | None = None) -> str:
    def lab(table: dict, k: str) -> str:
        return table.get(k, k).split("：")[0]

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

    mech_lab = {k: v for k, v in MECHANISMS.items()}
    pair_labels = {k: f"{lab(SETTINGS, k.split('|')[0])} × {lab(MECHANISMS, k.split('|')[1])}" for k in w["pairs"]}
    L = ["# 故事 DNA 統計", ""]
    if coverage:
        L += [f"標註裡的故事 {coverage['stories']} 個（另有非故事 {coverage['non_stories']} 個、已不在語料裡的舊標註 {coverage['orphan_annotations']} 個）。", ""]
    L += [
        f"有推文分數的 {w['n_scored']} 個；高分組（同年同標籤前 {100 * (1 - w['hi_q']):.0f}%）{w['n_top']} 個，"
        f"低分組（後 {100 * w['lo_q']:.0f}%）{w['n_low']} 個。沒有分數的（早期、精華區）{w['n_stories'] - w['n_scored']} 個，只用在範例池和分布。",
        "",
        "來源：全部 " + str(w["sources"]["all"]) + "；高分組 " + str(w["sources"]["top"]) + "；低分組 " + str(w["sources"]["low"]),
        "",
        "高分組年份：" + "、".join(f"{y}:{n}" for y, n in w["years_top"].items()),
        "",
    ]
    L += tbl("場景", w["settings"], SETTINGS)
    L += tbl("主要恐怖機制", w["mechanisms_primary"], mech_lab)
    L += tbl("結尾型態", w["endings"], ENDINGS)
    L += tbl("場景 × 機制", w["pairs"], pair_labels)
    for tag, c in w.get("contrast_by_tag", {}).items():
        L += [f"# {tag}文內部的高低分對比（高分組 {c['n_high']}、低分組 {c['n_low']}）", "",
              "同標籤內比，才不會把經驗文和翻譯文的差異誤當成品質差異。p 值 < 0.05 加粗；低分組篇數少時，沒加粗的差異多半是雜訊。", ""]
        L += ctr(f"{tag}｜場景", c["setting"], SETTINGS)
        L += ctr(f"{tag}｜主要機制", c["mechanism"], mech_lab)
        L += ctr(f"{tag}｜結尾", c["ending"], ENDINGS)
        L += ctr(f"{tag}｜鬼露出", c["ghost"], {})
        L += ctr(f"{tag}｜敘事聲音", c["voice"], VOICE_MARKERS, 12)
    L += ["# 全部混在一起的對比（受來源組成影響，只當參考）", ""]
    L += ctr("場景", w["contrast"]["setting"], SETTINGS)
    L += ctr("主要機制", w["contrast"]["mechanism"], mech_lab)
    L += ctr("結尾", w["contrast"]["ending"], ENDINGS)
    L += ctr("鬼露出", w["contrast"]["ghost"], {})
    L += ctr("敘事聲音", w["contrast"]["voice"], VOICE_MARKERS, 12)
    L += [
        "## 節拍比例", "", "| 節拍 | 高分組 | 低分組 | 全部 |", "|---|---|---|---|",
        *[f"| {b} | {w['beats_top'][b]:.2f} | {w['beats_low'][b]:.2f} | {w['beats_all'][b]:.2f} |" for b in BEATS],
        "",
        "## 鬼的露出程度", "",
        f"高分組平均 {w['ghost_explicitness']['top_mean']}，低分組平均 {w['ghost_explicitness']['bottom_mean']}，"
        f"沒分數的 {w['unscored_ghost_mean']}。高分組分布 {w['ghost_explicitness']['dist_top']}，低分組 {w['ghost_explicitness']['dist_low']}。",
        "",
        "## 高分組字數", "",
        f"p25 {w['length_top']['p25']:.0f}、p50 {w['length_top']['p50']:.0f}、p75 {w['length_top']['p75']:.0f}",
        "",
        f"## 範例池（{len(w['examples'])} 個，每個場景最多 25 個）", "",
        "依場景：" + "、".join(f"{lab(SETTINGS, k)} {v}" for k, v in Counter(e["setting"] for e in w["examples"]).most_common()),
        "",
        *[
            f"- {('%.2f' % e['score']) if e['score'] is not None else '收錄'} [{e.get('source')}/{e.get('year')}] {e['title']}："
            f"{e['one_line_premise']}（{lab(SETTINGS, e['setting'])}；{'/'.join(e['mechanisms'])}；{e['ending']}；鬼 {e['ghost_explicitness']}）"
            for e in w["examples"][:20]
        ],
        "",
    ]
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
