"""規劃器（純抽樣）＋寫手（LLM）＋評審（LLM）迴圈。"""
from __future__ import annotations

import json
import random
from pathlib import Path

from .annotate import load_prompt
from .llm import DEFAULT_MODELS, Backend
from .taxonomy import BEATS, BEAT_LABELS, ENDINGS, MECHANISMS, SETTINGS, BeatShare, Plan, Verdict


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
    setting: str | list[str] | None = None,
    mechanism: str | list[str] | None = None,
    ending: str | list[str] | None = None,
    ghost_max: int | None = None,
    target_chars: int | None = None,
    length_range: tuple[int, int] | None = None,
    style: str = "ptt",
    style_note: str = "",
    notes: list[str] | None = None,
    rules: str = "v2",
) -> Plan:
    """setting、mechanism、ending 可以給一個或多個 key；給多個就只在這些裡面依權重抽。
    長度：target_chars 給定值；length_range 給範圍（在範圍內隨機）；都沒給就用高分組的字數分布。"""
    from .options import MAX_CHARS, MIN_CHARS, STYLES

    settings_only, mech_only, ending_only = _as_list(setting), _as_list(mechanism), _as_list(ending)
    fixed = [name for name, v in (("場景", settings_only), ("主要機制", mech_only), ("結尾", ending_only)) if v]

    setting = _weighted_pick(rng, weights["settings"], only=settings_only)

    pair_opts = {k.split("|")[1]: v for k, v in weights.get("pairs", {}).items() if k.split("|")[0] == setting}
    if mech_only:
        primary = _weighted_pick(rng, weights["mechanisms_primary"], only=mech_only)
    elif pair_opts and rng.random() < 0.7:
        primary = _weighted_pick(rng, pair_opts)
    else:
        primary = _weighted_pick(rng, weights["mechanisms_primary"])
    mechanisms = [primary]
    if rng.random() < 0.5:
        try:
            mechanisms.append(_weighted_pick(rng, weights["mechanisms_any"], exclude={primary}))
        except ValueError:
            pass

    ending = _weighted_pick(rng, weights["endings"], only=ending_only)

    base = weights["beats_top"]
    noisy = {b: max(0.0, base[b] * rng.uniform(0.8, 1.2)) for b in BEATS}
    beats = BeatShare(**noisy).normalized()

    if ghost_max is None:
        dist = weights["ghost_explicitness"]["dist_top"]
        levels = [int(k) for k in dist]
        counts = [dist[str(l)] + 0.5 for l in levels]  # +0.5 讓沒出現過的等級還是有一點機率
        ghost_max = rng.choices(levels, weights=counts, k=1)[0]
    else:
        fixed.append("鬼露出上限")

    if target_chars is not None:
        target_chars = max(MIN_CHARS, min(int(target_chars), MAX_CHARS))
        fixed.append("長度")
    elif length_range is not None:
        lo, hi = length_range
        target_chars = rng.randint(lo, hi)
        fixed.append("長度")
    else:
        lt = weights["length_top"]
        lo, hi = int(lt["p25"]), int(lt["p75"])
        target_chars = rng.randint(min(lo, hi), max(lo, hi)) if hi > lo else int(lt["p50"] or 1500)
        target_chars = max(800, min(target_chars, 4000))

    examples = weights.get("examples", [])
    same_setting = [e for e in examples if e["setting"] == setting]
    anchor_pool = [a for e in (same_setting or examples) for a in e["realism_anchors"]]
    rng.shuffle(anchor_pool)
    anchor_hints = list(dict.fromkeys(anchor_pool))[:8]

    same_mech = [e for e in examples if primary in e["mechanisms"]]
    pool = same_mech or examples
    structural = [e["one_line_premise"] for e in rng.sample(pool, k=min(3, len(pool)))]

    st = STYLES[style]
    if style != "ptt" or style_note:
        fixed.append("風格")
    if notes:
        fixed.append("額外要求")
    return Plan(
        setting=setting,
        setting_label=SETTINGS[setting],
        mechanisms=mechanisms,
        mechanism_labels=[MECHANISMS[m] for m in mechanisms],
        ending=ending,
        ending_label=ENDINGS[ending],
        beats=beats,
        ghost_explicitness=ghost_max,
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
    beats_txt = "、".join(f"{BEAT_LABELS[b]} {int(getattr(plan.beats, b) * tc)} 字" for b in BEATS)
    lines = [
        f"場景：{plan.setting_label}",
        f"恐怖機制：{'；'.join(plan.mechanism_labels)}",
        f"結尾型態：{plan.ending_label}",
        f"鬼的露出上限 ghost_explicitness：{plan.ghost_explicitness}",
        f"target_chars：{tc}（誤差兩成內）",
        f"節拍字數分配（大約）：{beats_txt}",
        f"風格：{plan.style_label}（{STYLES[plan.style].summary}）" + (f"；補充：{plan.style_note}" if plan.style_note else ""),
        "錨點提示（同場景高分故事用過的細節類型，當提示，不當抄本）：" + "、".join(plan.anchor_hints),
        "結構範例（只看結構，不看文字，不要重講同一件事）：",
        *[f"  - {s}" for s in plan.structural_examples],
    ]
    if plan.user_notes:
        lines.append("使用者的額外要求（一定要做到；跟上面衝突時以這裡為準，但鬼的克制和不抄襲的規則不變）：")
        lines += [f"  - {n}" for n in plan.user_notes]
    if plan.fixed:
        lines.append("使用者指定的欄位：" + "、".join(plan.fixed))
    if plan.ending == "twist":
        lines.append("注意：結尾是反轉時，揭露段只寫敘事者當下看到的表面事件，真相留給最後一兩句翻；兩段不要搶同一個高潮。")
    if plan.ending == "explained":
        lines.append("注意：結尾是有解釋時，解釋要從別人嘴裡說出來（長輩、廟公、鄰居），不是敘事者自己推理。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 寫手 / 評審
# ---------------------------------------------------------------------------


RULE_DIRS = {"v2": "", "v1": "v1/", "restrained": "restrained/"}


def rules_prompt(name: str, rules: str = "v2") -> str:
    """v2（直接）讀 prompts/，restrained（留白）讀 prompts/restrained/，v1（2026-10-14 前的舊規則）讀 prompts/v1/。"""
    return load_prompt(RULE_DIRS.get(rules, "") + name)


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
        log(
            f"round {r}: {count_chars(story)} 字 overall={verdict.overall} realism={verdict.realism} slow_burn={verdict.slow_burn} "
            f"ghost={verdict.ghost_restraint} ending={verdict.ending} voice={verdict.voice} passes={verdict.passes}"
        )
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
    header = (
        f"<!-- seed {result['seed']} | {p.get('setting')} / {p.get('ending')} / {p.get('style', 'ptt')} | "
        f"target {p.get('target_chars')} 字, actual {result.get('final_chars')} 字 | round {result['final_round']} | "
        f"overall {v['overall']} | realism {v['realism']} slow_burn {v['slow_burn']} ghost {v['ghost_restraint']} "
        f"ending {v['ending']} voice {v['voice']} -->\n\n"
    )
    md_path.write_text(header + result["final"] + "\n", encoding="utf-8")
    return md_path, json_path
