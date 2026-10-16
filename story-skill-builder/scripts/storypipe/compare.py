"""比較幾份標註：欄位一致率、格式遵守、抄原文、成本耗時、對統計結果的影響、分歧清單。

py -m storypipe.cli compare data/annotated.jsonl data/annotated.haiku55.jsonl data/annotated.sonnet55.jsonl
第一份當參考。參考不是標準答案，只是另一個標註者。
"""
from __future__ import annotations

import json
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from .llm import list_cost
from .stats import compute_weights
from .taxonomy import BEATS

RAW = Path("data/raw/ptt_marvel.jsonl")
COPY_RUN = 10  # 連續相同 10 字以上算抄原文（跟 prompt 的規則一致）


def load(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["id"]] = r
    return out


def label_of(path: Path, recs: dict[str, dict]) -> str:
    models = Counter(r.get("model") or "" for r in recs.values())
    top = models.most_common(1)[0][0] if models else ""
    return f"{path.stem} ({top})" if top else path.stem


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 1.0


def kappa(xs: list, ys: list) -> float:
    n = len(xs)
    if not n:
        return float("nan")
    po = sum(x == y for x, y in zip(xs, ys)) / n
    cx, cy = Counter(xs), Counter(ys)
    pe = sum(cx[k] * cy.get(k, 0) for k in cx) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def pair_metrics(A: dict[str, dict], B: dict[str, dict]) -> dict:
    ids = sorted(set(A) & set(B))
    a = {i: A[i]["annotation"] for i in ids}
    b = {i: B[i]["annotation"] for i in ids}
    story_agree = sum(a[i]["is_story"] == b[i]["is_story"] for i in ids)
    both = [i for i in ids if a[i]["is_story"] and b[i]["is_story"]]
    m: dict = {"n": len(ids), "story_agree": story_agree, "n_both": len(both)}
    if not both:
        return m
    m["setting"] = sum(a[i]["setting"] == b[i]["setting"] for i in both)
    m["setting_kappa"] = kappa([a[i]["setting"] for i in both], [b[i]["setting"] for i in both])
    m["mech1"] = sum(a[i]["mechanisms"][0] == b[i]["mechanisms"][0] for i in both)
    m["mech1_in_other"] = sum(
        (a[i]["mechanisms"][0] in b[i]["mechanisms"]) + (b[i]["mechanisms"][0] in a[i]["mechanisms"]) for i in both
    ) / 2
    m["mech_jaccard"] = sum(jaccard(a[i]["mechanisms"], b[i]["mechanisms"]) for i in both) / len(both)
    m["ending"] = sum(a[i]["ending"] == b[i]["ending"] for i in both)
    m["ending_kappa"] = kappa([a[i]["ending"] for i in both], [b[i]["ending"] for i in both])
    m["ghost_exact"] = sum(a[i]["ghost_explicitness"] == b[i]["ghost_explicitness"] for i in both)
    m["ghost_pm1"] = sum(abs(a[i]["ghost_explicitness"] - b[i]["ghost_explicitness"]) <= 1 for i in both)
    m["ghost_bias"] = sum(b[i]["ghost_explicitness"] - a[i]["ghost_explicitness"] for i in both) / len(both)
    m["beats_l1"] = sum(sum(abs(a[i]["beats"][k] - b[i]["beats"][k]) for k in BEATS) for i in both) / len(both)
    m["voice_jaccard"] = sum(jaccard(a[i]["voice_markers"], b[i]["voice_markers"]) for i in both) / len(both)
    m["translated_agree"] = sum(
        ("translated" in a[i]["voice_markers"]) == ("translated" in b[i]["voice_markers"]) for i in both
    )
    m["disagreements"] = [
        {
            "id": i,
            "title": A[i]["title"],
            "is_story": (a[i]["is_story"], b[i]["is_story"]),
            "setting": (a[i]["setting"], b[i]["setting"]),
            "mech1": (a[i]["mechanisms"][0], b[i]["mechanisms"][0]),
            "ending": (a[i]["ending"], b[i]["ending"]),
            "ghost": (a[i]["ghost_explicitness"], b[i]["ghost_explicitness"]),
        }
        for i in ids
        if a[i]["is_story"] != b[i]["is_story"]
        or (i in both and (a[i]["setting"] != b[i]["setting"] or a[i]["ending"] != b[i]["ending"]))
    ]
    return m


def _longest_copy(text: str, body: str) -> int:
    if not text or not body:
        return 0
    sm = SequenceMatcher(None, text, body, autojunk=False)
    return sm.find_longest_match(0, len(text), 0, len(body)).size


def single_metrics(recs: dict[str, dict], raw: dict[str, dict]) -> dict:
    rs = list(recs.values())
    n = len(rs)
    ann = [r["annotation"] for r in rs]
    anchors = [x for a in ann for x in a["realism_anchors"]]
    copied = 0
    worst = 0
    for r in rs:
        body = (raw.get(r["id"]) or {}).get("body", "")
        a = r["annotation"]
        texts = [a["setting_detail"], a["scariest_moment"], a["one_line_premise"], *a["realism_anchors"]]
        run = max((_longest_copy(t, body) for t in texts), default=0)
        worst = max(worst, run)
        copied += run >= COPY_RUN
    elapsed = [r.get("elapsed_s") for r in rs if r.get("elapsed_s")]
    # 成本一律用 token 數照定價重算，不信紀錄裡的數字（舊紀錄可能是 CLI 用錯價目算的）。
    costs = [c for c in (list_cost(r.get("model") or "", r["usage"]) for r in rs if r.get("usage")) if c is not None]
    usage = Counter()
    for r in rs:
        usage.update({k: int(v or 0) for k, v in (r.get("usage") or {}).items()})
    return {
        "n": n,
        "models": dict(Counter(r.get("model") or "?" for r in rs)),
        "stories": sum(a["is_story"] for a in ann),
        "detail_ok": sum(len(a["setting_detail"]) <= 30 for a in ann),
        "anchors_ok": sum(all(len(x) <= 15 for x in a["realism_anchors"]) for a in ann),
        "scary_ok": sum(len(a["scariest_moment"]) <= 40 for a in ann),
        "premise_ok": sum(len(a["one_line_premise"]) <= 45 for a in ann),
        "anchor_len": sum(map(len, anchors)) / len(anchors) if anchors else 0,
        "anchor_n": len(anchors) / n if n else 0,
        "copied": copied,
        "copy_worst": worst,
        "ghost_dist": dict(sorted(Counter(a["ghost_explicitness"] for a in ann if a["is_story"]).items())),
        "endings": dict(Counter(a["ending"] for a in ann if a["is_story"]).most_common()),
        "elapsed_mean": sum(elapsed) / len(elapsed) if elapsed else None,
        "cost_total": sum(costs) if costs else None,
        "usage": dict(usage),
    }


def top_k(table: dict, k: int = 5) -> str:
    return "、".join(f"{key}({v['n']})" for key, v in list(table.items())[:k])


def run(paths: list[Path], out_path: Path, raw_path: Path = RAW) -> str:
    files = [(p, load(p)) for p in paths]
    common = set.intersection(*(set(r) for _, r in files))
    files = [(p, {i: r[i] for i in common}) for p, r in files]
    raw = {}
    if raw_path.exists():
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                raw[x["id"]] = x
    labels = [label_of(p, r) for p, r in files]
    singles = [single_metrics(r, raw) for _, r in files]

    L: list[str] = ["# 標註模型比較", "", f"共同篇數 {len(common)}。第一份是參考：{labels[0]}。參考不是標準答案。", ""]

    L += ["## 各份標註本身", "", "| 指標 | " + " | ".join(labels) + " |", "|---" * (len(labels) + 1) + "|"]

    def row(name: str, vals: list[str]) -> None:
        L.append(f"| {name} | " + " | ".join(vals) + " |")

    row("實際模型", [", ".join(f"{k}×{v}" for k, v in s["models"].items()) for s in singles])
    row("判為故事", [f"{s['stories']}/{s['n']}" for s in singles])
    row("場景描述 ≤ 30 字", [pct(s["detail_ok"], s["n"]) for s in singles])
    row("錨點全部 ≤ 15 字", [pct(s["anchors_ok"], s["n"]) for s in singles])
    row("錨點平均字數", [f"{s['anchor_len']:.1f}" for s in singles])
    row("最可怕一刻 ≤ 40 字", [pct(s["scary_ok"], s["n"]) for s in singles])
    row("一句話前提 ≤ 45 字", [pct(s["premise_ok"], s["n"]) for s in singles])
    row(f"抄原文（連續 ≥ {COPY_RUN} 字）", [f"{s['copied']} 篇，最長 {s['copy_worst']} 字" for s in singles])
    row("鬼露出分布（故事）", [str(s["ghost_dist"]) for s in singles])
    row("結尾分布（故事）", [str(s["endings"]) for s in singles])
    row("每篇耗時", [f"{s['elapsed_mean']:.1f}s" if s["elapsed_mean"] else "n/a" for s in singles])
    row("定價成本（全部，照 token 重算）", [f"${s['cost_total']:.4f}" if s["cost_total"] else "n/a" for s in singles])
    row("每篇定價成本", [f"${s['cost_total'] / s['n']:.5f}" if s["cost_total"] and s["n"] else "n/a" for s in singles])
    row("每篇輸出 token", [f"{s['usage'].get('output_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    row("其中思考 token", [f"{s['usage'].get('thinking_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    row("每篇快取寫入 token", [f"{s['usage'].get('cache_creation_input_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    L.append("")

    L += ["## 兩兩一致率", "", "故事判斷以全部共同篇數算；其餘欄位只算雙方都判為故事的篇。", ""]
    pairs = list(combinations(range(len(files)), 2))
    L += ["| 指標 | " + " | ".join(f"{labels[i].split(' ')[0]} vs {labels[j].split(' ')[0]}" for i, j in pairs) + " |",
          "|---" * (len(pairs) + 1) + "|"]
    pm = {(i, j): pair_metrics(files[i][1], files[j][1]) for i, j in pairs}

    def prow(name: str, f) -> None:
        L.append(f"| {name} | " + " | ".join(f(pm[p]) for p in pairs) + " |")

    prow("故事判斷一致", lambda m: pct(m["story_agree"], m["n"]))
    prow("雙方都是故事", lambda m: str(m["n_both"]))
    prow("場景相同", lambda m: f"{pct(m.get('setting', 0), m['n_both'])}（κ {m.get('setting_kappa', 0):.2f}）")
    prow("主要機制相同", lambda m: pct(m.get("mech1", 0), m["n_both"]))
    prow("主要機制落在對方清單", lambda m: pct(m.get("mech1_in_other", 0), m["n_both"]))
    prow("機制集合 Jaccard", lambda m: f"{m.get('mech_jaccard', 0):.2f}")
    prow("結尾相同", lambda m: f"{pct(m.get('ending', 0), m['n_both'])}（κ {m.get('ending_kappa', 0):.2f}）")
    prow("鬼露出完全相同", lambda m: pct(m.get("ghost_exact", 0), m["n_both"]))
    prow("鬼露出差 ≤ 1", lambda m: pct(m.get("ghost_pm1", 0), m["n_both"]))
    prow("鬼露出偏差（後者減前者）", lambda m: f"{m.get('ghost_bias', 0):+.2f}")
    prow("節拍比例 L1 距離（0 到 2）", lambda m: f"{m.get('beats_l1', 0):.2f}")
    prow("聲音標記 Jaccard", lambda m: f"{m.get('voice_jaccard', 0):.2f}")
    prow("翻譯標記一致", lambda m: pct(m.get("translated_agree", 0), m["n_both"]))
    L.append("")

    L += ["## 對統計結果的影響（同一批篇目算出的前五名）", ""]
    for (p, recs), lab in zip(files, labels):
        try:
            w = compute_weights([r for r in recs.values() if r["annotation"]["is_story"]])
        except ValueError:
            continue
        L.append(f"- **{lab}**")
        L.append(f"  - 場景：{top_k(w['settings'])}")
        L.append(f"  - 主要機制：{top_k(w['mechanisms_primary'])}")
        L.append(f"  - 結尾：{top_k(w['endings'], 4)}")
        L.append(f"  - 高分組鬼露出平均 {w['ghost_explicitness']['top_mean']}，節拍 escalation {w['beats_top']['escalation']:.2f}")
    L.append("")

    L += ["## 跟參考的分歧（故事判斷、場景、結尾）", ""]
    for j in range(1, len(files)):
        dis = pm[(0, j)].get("disagreements", [])
        L.append(f"### {labels[0].split(' ')[0]} vs {labels[j]}：{len(dis)} 篇")
        L.append("")
        for d in dis:
            parts = []
            for k in ("is_story", "setting", "mech1", "ending", "ghost"):
                x, y = d[k]
                parts.append(f"{k} {x}→{y}" if x != y else f"{k} {x}")
            L.append(f"- {d['title']}：" + "；".join(parts))
        L.append("")

    md = "\n".join(L)
    out_path.write_text(md, encoding="utf-8")
    return md
