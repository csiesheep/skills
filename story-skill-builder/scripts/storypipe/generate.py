"""規劃器（純抽樣）＋寫手（LLM）＋評審（LLM）迴圈。"""
from __future__ import annotations

import json
import random
from pathlib import Path

from .annotate import load_prompt
from .genre import GENRE
from .llm import DEFAULT_MODELS, Backend
from .taxonomy import BEAT_LABELS, BEATS, VERDICT_DIMS, Plan, Verdict


# ---------------------------------------------------------------------------
# 規劃器
# ---------------------------------------------------------------------------


def _weighted_pick(
    rng: random.Random, table: dict[str, dict], exclude: set[str] | None = None, only: list[str] | None = None
) -> str:
    """依權重抽一個。only 是使用者限定的選項：表裡有權重的照權重抽，資料裡沒出現過的給最小權重，確保還是抽得到。"""
    if only:
        floor = min((v["weight"] for v in table.values()), default=1.0) or 1.0
        items = [(k, table[k]["weight"] if k in table else floor) for k in only if not exclude or k not in exclude]
    else:
        items = [(k, v["weight"]) for k, v in table.items() if not exclude or k not in exclude]
    if not items:
        raise ValueError("抽樣表是空的")
    keys, weights = zip(*items)
    return rng.choices(keys, weights=weights, k=1)[0]


def _as_list(x: str | list[str] | None) -> list[str] | None:
    if x is None:
        return None
    return [x] if isinstance(x, str) else list(x)


def make_plan(
    weights: dict,
    rng: random.Random,
    cap_max: int | None = None,
    target_chars: int | None = None,
    length_range: tuple[int, int] | None = None,
    style: str | None = None,
    style_note: str = "",
    notes: list[str] | None = None,
    rules: str | None = None,
    **choices: str | list[str] | None,
) -> Plan:
    """每個軸可以用它的 key 或 flag 當關鍵字參數限定值（一個或多個）；給多個就只在這些裡面依權重抽。
    長度：target_chars 給定值；length_range 給範圍（在範圍內隨機）；都沒給就用高分組的字數分布。"""
    from .options import STYLES

    ln = GENRE.length
    style = style or GENRE.default_style
    rules = rules or GENRE.default_rules
    only: dict[str, list[str] | None] = {}
    for k, v in choices.items():
        only[GENRE.axis(k).key] = _as_list(v)
    fixed = [ax.fixed_name for ax in GENRE.axes if only.get(ax.key)]

    chosen: dict[str, list[str]] = {}
    for ax in GENRE.axes:
        entry = weights["axes"][ax.key]
        o = only.get(ax.key)
        primary = None
        if not o and GENRE.pair and ax.key == GENRE.pair[1] and GENRE.pair[0] in chosen:
            first = chosen[GENRE.pair[0]][0]
            pair_opts = {k.split("|", 1)[1]: v for k, v in weights.get("pairs", {}).items() if k.split("|", 1)[0] == first}
            if pair_opts and rng.random() < 0.7:
                primary = _weighted_pick(rng, pair_opts)
        if primary is None:
            primary = _weighted_pick(rng, entry["table"], only=o)
        vals = [primary]
        if ax.multi and ax.max_items > 1 and rng.random() < 0.5:
            try:
                vals.append(_weighted_pick(rng, entry.get("any") or entry["table"], exclude={primary}))
            except ValueError:
                pass
        chosen[ax.key] = vals

    base = weights["beats_top"]
    noisy = {b: max(0.0, base.get(b, 0.0) * rng.uniform(0.8, 1.2)) for b in BEATS}
    total = sum(noisy.values()) or 1.0
    beats = {b: v / total for b, v in noisy.items()}

    if cap_max is None:
        dist = weights["cap"]["dist_top"]
        levels = [int(k) for k in dist]
        counts = [dist[str(lv)] + 0.5 for lv in levels]  # +0.5 讓沒出現過的等級還是有一點機率
        cap_max = rng.choices(levels, weights=counts, k=1)[0]
    else:
        fixed.append(GENRE.cap.label)

    if target_chars is not None:
        target_chars = max(ln.min, min(int(target_chars), ln.max))
        fixed.append("長度")
    elif length_range is not None:
        lo, hi = length_range
        target_chars = rng.randint(lo, hi)
        fixed.append("長度")
    else:
        lt = weights["length_top"]
        lo, hi = int(lt["p25"]), int(lt["p75"])
        target_chars = rng.randint(min(lo, hi), max(lo, hi)) if hi > lo else int(lt["p50"] or ln.sample_clamp[0])
        target_chars = max(ln.sample_clamp[0], min(target_chars, ln.sample_clamp[1]))

    examples = weights.get("examples", [])
    ex_ax, match_ax = GENRE.example_axis, GENRE.example_match_axis
    same = [e for e in examples if (e["axes"].get(ex_ax) or [None])[0] == chosen[ex_ax][0]]
    anchor_pool = [a for e in (same or examples) for a in e["anchors"]]
    rng.shuffle(anchor_pool)
    anchor_hints = list(dict.fromkeys(anchor_pool))[:8]

    same_match = [e for e in examples if chosen[match_ax][0] in e["axes"].get(match_ax, [])]
    pool = same_match or examples
    structural = [e["premise"] for e in rng.sample(pool, k=min(3, len(pool)))]

    st = STYLES[style]
    if style != GENRE.default_style or style_note:
        fixed.append("風格")
    if notes:
        fixed.append("額外要求")
    return Plan(
        axes=chosen,
        axis_labels={k: [GENRE.axis(k).label_of(v) for v in vs] for k, vs in chosen.items()},
        cap=cap_max,
        beats=beats,
        target_chars=target_chars,
        anchor_hints=anchor_hints,
        structural_examples=structural,
        seed=rng.randint(0, 10**9),
        style=style,
        style_label=st.label,
        style_note=style_note or "",
        user_notes=list(notes or []),
        fixed=fixed,
        rules=rules,
    )


def render_plan(plan: Plan, target_chars: int | None = None) -> str:
    from .options import STYLES

    tc = target_chars or plan.target_chars
    beats_txt = "、".join(f"{BEAT_LABELS[b]} {int(plan.beats.get(b, 0.0) * tc)} 字" for b in BEATS)
    lines = [f"{ax.label}：{'；'.join(plan.axis_labels[ax.key])}" for ax in GENRE.axes]
    lines += [
        f"{GENRE.cap.label} {GENRE.cap.key}：{plan.cap}",
        f"target_chars：{tc}（誤差兩成內）",
        f"節拍字數分配（大約）：{beats_txt}",
        f"風格：{plan.style_label}（{STYLES[plan.style].summary}）" + (f"；補充：{plan.style_note}" if plan.style_note else ""),
        f"{GENRE.anchors.label}（{GENRE.anchors.plan_hint}）：" + "、".join(plan.anchor_hints),
        f"結構範例（{GENRE.premise.plan_hint}）：",
        *[f"  - {s}" for s in plan.structural_examples],
    ]
    if plan.user_notes:
        lines.append("使用者的額外要求（一定要做到；跟上面衝突時以這裡為準，但露出上限和不抄襲的規則不變）：")
        lines += [f"  - {n}" for n in plan.user_notes]
    if plan.fixed:
        lines.append("使用者指定的欄位：" + "、".join(plan.fixed))
    for ax in GENRE.axes:
        for v in plan.axes[ax.key]:
            if v in ax.plan_notes:
                lines.append(ax.plan_notes[v])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 寫手 / 評審
# ---------------------------------------------------------------------------


def rules_prompt(name: str, rules: str | None = None) -> str:
    """依 genre.json 的 rule_sets 找規則檔：每套規則一個子目錄（根目錄是 ""）。"""
    key = rules or GENRE.default_rules
    rs = GENRE.rule_sets.get(key)
    if rs is None:
        raise ValueError(f"沒有規則版本 {key}；有：" + "、".join(GENRE.rule_sets))
    return load_prompt(rs.dir + name)


def writer_system(plan: Plan) -> str:
    from .options import STYLES

    system = rules_prompt("style_guide.md", plan.rules) + "\n\n## 這篇的風格\n\n" + STYLES[plan.style].prompt(plan.rules)
    if plan.style_note:
        system += "\n\n使用者對風格的補充：" + plan.style_note
    return system


def write_story(
    backend: Backend,
    plan: Plan,
    model: str | None = None,
    prior: str | None = None,
    verdict: Verdict | None = None,
) -> str:
    user = "規劃：\n" + render_plan(plan)
    if prior is not None and verdict is not None:
        notes = "\n".join(f"- {n}" for n in verdict.fix_notes) or "- 整體再克制一點"
        user += (
            "\n\n上一版：\n" + prior + "\n\n評審意見（逐條修，其他地方不要越改越多）：\n" + notes +
            "\n\n改寫整篇，只輸出新版本，第一行一樣是標題。"
        )
    max_tokens = max(8000, plan.target_chars * 5)  # 中文一字約一到兩個 token，加上思考的餘裕
    return backend.text(writer_system(plan), user, model or DEFAULT_MODELS["write"], max_tokens=max_tokens, effort="high").strip()


def judge_story(backend: Backend, plan: Plan, story: str, model: str | None = None) -> Verdict:
    system = rules_prompt("judge.md", plan.rules)
    user = "規劃：\n" + render_plan(plan) + f"\n\n實際字數：{count_chars(story)}\n\n故事：\n" + story
    return backend.structured(system, user, Verdict, model or DEFAULT_MODELS["judge"], max_tokens=3000, effort="high")


def count_chars(story: str) -> int:
    """不算標題行、空白和換行的字數。"""
    body = story.split("\n", 1)[1] if "\n" in story else story
    return sum(1 for ch in body if not ch.isspace())


def generate(
    backend: Backend,
    weights: dict,
    seed: int | None = None,
    max_rounds: int = 3,
    models: dict | None = None,
    log=print,
    **plan_overrides,
) -> dict:
    models = {**DEFAULT_MODELS, **(models or {})}
    seed = seed if seed is not None else random.randrange(10**9)
    rng = random.Random(seed)
    plan = make_plan(weights, rng, **plan_overrides)
    log(f"seed={seed}\n{render_plan(plan)}\n")

    rounds: list[dict] = []
    story = write_story(backend, plan, models["write"])
    for r in range(1, max_rounds + 1):
        verdict = judge_story(backend, plan, story, models["judge"])
        rounds.append({"round": r, "story": story, "chars": count_chars(story), "verdict": verdict.model_dump()})
        dims = " ".join(f"{k}={getattr(verdict, k)}" for k in VERDICT_DIMS)
        log(f"round {r}: {count_chars(story)} 字 overall={verdict.overall} {dims} passes={verdict.passes}")
        for n in verdict.fix_notes:
            log(f"  - {n}")
        if verdict.passes or r == max_rounds:
            break
        story = write_story(backend, plan, models["write"], prior=story, verdict=verdict)

    best = max(rounds, key=lambda x: x["verdict"]["overall"])
    return {
        "seed": seed,
        "plan": plan.model_dump(),
        "rounds": rounds,
        "final_round": best["round"],
        "final": best["story"],
        "final_chars": best["chars"],
        "final_verdict": best["verdict"],
    }


def save_result(result: dict, out_dir: Path, stem: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    v = result["final_verdict"]
    p = result["plan"]
    axes_txt = " / ".join((p.get("axes", {}).get(ax.key) or ["?"])[0] for ax in GENRE.axes)
    dims = " ".join(f"{k} {v.get(k)}" for k in VERDICT_DIMS)
    header = (
        f"<!-- seed {result['seed']} | {axes_txt} / {p.get('style', '')} | "
        f"target {p.get('target_chars')} 字, actual {result.get('final_chars')} 字 | round {result['final_round']} | "
        f"overall {v['overall']} | {dims} -->\n\n"
    )
    md_path.write_text(header + result["final"] + "\n", encoding="utf-8")
    return md_path, json_path
