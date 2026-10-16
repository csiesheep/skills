"""比較幾份標註：欄位一致率、格式遵守、抄原文、成本耗時、對統計結果的影響、分歧清單。

py -m storypipe.cli compare data/annotated.jsonl data/annotated.haiku55.jsonl data/annotated.sonnet55.jsonl
第一份當參考。參考不是標準答案，只是另一個標註者。欄位來自 genre.json。
"""
from __future__ import annotations

import json
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from .genre import GENRE
from .llm import list_cost
from .stats import compute_weights
from .taxonomy import BEATS

RAW_DIR = Path("data/raw")
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
    cap = GENRE.cap
    ids = sorted(set(A) & set(B))
    a = {i: A[i]["annotation"] for i in ids}
    b = {i: B[i]["annotation"] for i in ids}
    story_agree = sum(a[i]["is_story"] == b[i]["is_story"] for i in ids)
    both = [i for i in ids if a[i]["is_story"] and b[i]["is_story"]]
    m: dict = {"n": len(ids), "story_agree": story_agree, "n_both": len(both)}
    if not both:
        return m
    for ax in GENRE.axes:
        if ax.multi:
            m[f"{ax.key}_first"] = sum(ax.primary(a[i]) == ax.primary(b[i]) for i in both)
            m[f"{ax.key}_first_in_other"] = sum(
                (ax.primary(a[i]) in ax.all_values(b[i])) + (ax.primary(b[i]) in ax.all_values(a[i])) for i in both
            ) / 2
            m[f"{ax.key}_jaccard"] = sum(jaccard(ax.all_values(a[i]), ax.all_values(b[i])) for i in both) / len(both)
        else:
            m[f"{ax.key}_same"] = sum(a[i][ax.key] == b[i][ax.key] for i in both)
            m[f"{ax.key}_kappa"] = kappa([a[i][ax.key] for i in both], [b[i][ax.key] for i in both])
    m["cap_exact"] = sum(a[i][cap.key] == b[i][cap.key] for i in both)
    m["cap_pm1"] = sum(abs(a[i][cap.key] - b[i][cap.key]) <= 1 for i in both)
    m["cap_bias"] = sum(b[i][cap.key] - a[i][cap.key] for i in both) / len(both)
    m["beats_l1"] = sum(sum(abs(a[i]["beats"].get(k, 0) - b[i]["beats"].get(k, 0)) for k in BEATS) for i in both) / len(both)
    m["voice_jaccard"] = sum(jaccard(a[i].get("voice_markers", []), b[i].get("voice_markers", [])) for i in both) / len(both)
    single = [ax for ax in GENRE.axes if not ax.multi]
    m["disagreements"] = [
        {
            "id": i,
            "title": A[i]["title"],
            "is_story": (a[i]["is_story"], b[i]["is_story"]),
            **{ax.key: (ax.primary(a[i]), ax.primary(b[i])) for ax in GENRE.axes},
            "cap": (a[i][cap.key], b[i][cap.key]),
        }
        for i in ids
        if a[i]["is_story"] != b[i]["is_story"]
        or (i in both and any(a[i][ax.key] != b[i][ax.key] for ax in single))
    ]
    return m


def _longest_copy(text: str, body: str) -> int:
    if not text or not body:
        return 0
    sm = SequenceMatcher(None, text, body, autojunk=False)
    return sm.find_longest_match(0, len(text), 0, len(body)).size


def _texts(a: dict) -> list[str]:
    out: list[str] = []
    for tf in GENRE.text_fields:
        v = a.get(tf.key)
        out += list(v) if isinstance(v, list) else [v or ""]
    return out


def single_metrics(recs: dict[str, dict], raw: dict[str, dict]) -> dict:
    rs = list(recs.values())
    n = len(rs)
    ann = [r["annotation"] for r in rs]
    anchors = [x for a in ann for x in a.get(GENRE.anchors.key, [])]
    copied = 0
    worst = 0
    for r in rs:
        body = (raw.get(r["id"]) or {}).get("body", "")
        run = max((_longest_copy(t, body) for t in _texts(r["annotation"])), default=0)
        worst = max(worst, run)
        copied += run >= COPY_RUN
    elapsed = [r.get("elapsed_s") for r in rs if r.get("elapsed_s")]
    # 成本一律用 token 數照定價重算，不信紀錄裡的數字（舊紀錄可能是 CLI 用錯價目算的）。
    costs = [c for c in (list_cost(r.get("model") or "", r["usage"]) for r in rs if r.get("usage")) if c is not None]
    usage = Counter()
    for r in rs:
        usage.update({k: int(v or 0) for k, v in (r.get("usage") or {}).items()})

    def field_ok(tf) -> int:
        def ok(a):
            v = a.get(tf.key)
            return all(len(x) <= tf.max_chars for x in v) if isinstance(v, list) else len(v or "") <= tf.max_chars
        return sum(ok(a) for a in ann)

    stories = [a for a in ann if a["is_story"]]
    return {
        "n": n,
        "models": dict(Counter(r.get("model") or "?" for r in rs)),
        "stories": len(stories),
        "field_ok": {tf.key: field_ok(tf) for tf in GENRE.text_fields},
        "anchor_len": sum(map(len, anchors)) / len(anchors) if anchors else 0,
        "anchor_n": len(anchors) / n if n else 0,
        "copied": copied,
        "copy_worst": worst,
        "cap_dist": dict(sorted(Counter(a[GENRE.cap.key] for a in stories).items())),
        "axis_dist": {ax.key: dict(Counter(ax.primary(a) for a in stories).most_common()) for ax in GENRE.axes if not ax.multi},
        "elapsed_mean": sum(elapsed) / len(elapsed) if elapsed else None,
        "cost_total": sum(costs) if costs else None,
        "usage": dict(usage),
    }


def top_k(table: dict, k: int = 5) -> str:
    return "、".join(f"{key}({v['n']})" for key, v in list(table.items())[:k])


def load_raw(raw_dir: Path = RAW_DIR) -> dict[str, dict]:
    raw: dict[str, dict] = {}
    if raw_dir.is_file():
        files = [raw_dir]
    else:
        files = sorted(raw_dir.glob("*.jsonl")) if raw_dir.exists() else []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                raw[x["id"]] = x
    return raw


def run(paths: list[Path], out_path: Path, raw_path: Path = RAW_DIR) -> str:
    cap = GENRE.cap
    files = [(p, load(p)) for p in paths]
    common = set.intersection(*(set(r) for _, r in files))
    files = [(p, {i: r[i] for i in common}) for p, r in files]
    raw = load_raw(raw_path)
    labels = [label_of(p, r) for p, r in files]
    singles = [single_metrics(r, raw) for _, r in files]

    L: list[str] = ["# 標註模型比較", "", f"共同篇數 {len(common)}。第一份是參考：{labels[0]}。參考不是標準答案。", ""]

    L += ["## 各份標註本身", "", "| 指標 | " + " | ".join(labels) + " |", "|---" * (len(labels) + 1) + "|"]

    def row(name: str, vals: list[str]) -> None:
        L.append(f"| {name} | " + " | ".join(vals) + " |")

    row("實際模型", [", ".join(f"{k}×{v}" for k, v in s["models"].items()) for s in singles])
    row(f"判為{GENRE.unit}", [f"{s['stories']}/{s['n']}" for s in singles])
    for tf in GENRE.text_fields:
        row(f"{tf.label or tf.key} ≤ {tf.max_chars} 字", [pct(s["field_ok"][tf.key], s["n"]) for s in singles])
    row("錨點平均字數", [f"{s['anchor_len']:.1f}" for s in singles])
    row(f"抄原文（連續 ≥ {COPY_RUN} 字）", [f"{s['copied']} 篇，最長 {s['copy_worst']} 字" for s in singles])
    row(f"{cap.short_name}分布（{GENRE.unit}）", [str(s["cap_dist"]) for s in singles])
    for ax in GENRE.axes:
        if not ax.multi:
            row(f"{ax.label}分布（{GENRE.unit}）", [str(s["axis_dist"][ax.key]) for s in singles])
    row("每篇耗時", [f"{s['elapsed_mean']:.1f}s" if s["elapsed_mean"] else "n/a" for s in singles])
    row("定價成本（全部，照 token 重算）", [f"${s['cost_total']:.4f}" if s["cost_total"] else "n/a" for s in singles])
    row("每篇定價成本", [f"${s['cost_total'] / s['n']:.5f}" if s["cost_total"] and s["n"] else "n/a" for s in singles])
    row("每篇輸出 token", [f"{s['usage'].get('output_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    row("其中思考 token", [f"{s['usage'].get('thinking_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    row("每篇快取寫入 token", [f"{s['usage'].get('cache_creation_input_tokens', 0) / s['n']:.0f}" if s["usage"] else "n/a" for s in singles])
    L.append("")

    L += ["## 兩兩一致率", "", f"{GENRE.unit}判斷以全部共同篇數算；其餘欄位只算雙方都判為{GENRE.unit}的篇。", ""]
    pairs = list(combinations(range(len(files)), 2))
    L += ["| 指標 | " + " | ".join(f"{labels[i].split(' ')[0]} vs {labels[j].split(' ')[0]}" for i, j in pairs) + " |",
          "|---" * (len(pairs) + 1) + "|"]
    pm = {(i, j): pair_metrics(files[i][1], files[j][1]) for i, j in pairs}

    def prow(name: str, f) -> None:
        L.append(f"| {name} | " + " | ".join(f(pm[p]) for p in pairs) + " |")

    prow(f"{GENRE.unit}判斷一致", lambda m: pct(m["story_agree"], m["n"]))
    prow(f"雙方都是{GENRE.unit}", lambda m: str(m["n_both"]))
    for ax in GENRE.axes:
        if ax.multi:
            prow(f"主要{ax.label}相同", lambda m, k=ax.key: pct(m.get(f"{k}_first", 0), m["n_both"]))
            prow(f"主要{ax.label}落在對方清單", lambda m, k=ax.key: pct(m.get(f"{k}_first_in_other", 0), m["n_both"]))
            prow(f"{ax.label}集合 Jaccard", lambda m, k=ax.key: f"{m.get(f'{k}_jaccard', 0):.2f}")
        else:
            prow(f"{ax.label}相同", lambda m, k=ax.key: f"{pct(m.get(f'{k}_same', 0), m['n_both'])}（κ {m.get(f'{k}_kappa', 0):.2f}）")
    prow(f"{cap.short_name}完全相同", lambda m: pct(m.get("cap_exact", 0), m["n_both"]))
    prow(f"{cap.short_name}差 ≤ 1", lambda m: pct(m.get("cap_pm1", 0), m["n_both"]))
    prow(f"{cap.short_name}偏差（後者減前者）", lambda m: f"{m.get('cap_bias', 0):+.2f}")
    prow("節拍比例 L1 距離（0 到 2）", lambda m: f"{m.get('beats_l1', 0):.2f}")
    prow("聲音標記 Jaccard", lambda m: f"{m.get('voice_jaccard', 0):.2f}")
    L.append("")

    L += ["## 對統計結果的影響（同一批篇目算出的前五名）", ""]
    for (p, recs), lab in zip(files, labels):
        try:
            w = compute_weights([r for r in recs.values() if r["annotation"]["is_story"]])
        except ValueError:
            continue
        L.append(f"- **{lab}**")
        for ax in GENRE.axes:
            L.append(f"  - {ax.label}：{top_k(w['axes'][ax.key]['table'])}")
        beats = "、".join(f"{b} {w['beats_top'][b]:.2f}" for b in BEATS)
        L.append(f"  - 高分組{cap.short_name}平均 {w['cap']['top_mean']}，節拍 {beats}")
    L.append("")

    single_keys = ["is_story"] + [ax.key for ax in GENRE.axes] + ["cap"]
    L += [f"## 跟參考的分歧（{GENRE.unit}判斷、單值軸）", ""]
    for j in range(1, len(files)):
        dis = pm[(0, j)].get("disagreements", [])
        L.append(f"### {labels[0].split(' ')[0]} vs {labels[j]}：{len(dis)} 篇")
        L.append("")
        for d in dis:
            parts = []
            for k in single_keys:
                x, y = d[k]
                parts.append(f"{k} {x}→{y}" if x != y else f"{k} {x}")
            L.append(f"- {d['title']}：" + "；".join(parts))
        L.append("")

    md = "\n".join(L)
    out_path.write_text(md, encoding="utf-8")
    return md
