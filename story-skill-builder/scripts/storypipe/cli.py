"""指令入口：py -m storypipe.cli <collect|annotate|stats|generate> ..."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .llm import DEFAULT_MODELS, make_backend
from .taxonomy import ENDINGS, MECHANISMS, SETTINGS

RAW = Path("data/raw/ptt_marvel.jsonl")
ANNOTATED = Path("data/annotated.opus55.v2.jsonl")  # 預設：Opus 5.5 + prompt v2；種子在 data/annotated.seed.jsonl
WEIGHTS = Path("data/weights.json")
REPORT = Path("data/report.md")
OUT_DIR = Path("data/out")


def cmd_collect(a: argparse.Namespace) -> int:
    from .collect_ptt import collect

    n = collect(a.board, a.query, Path(a.out), max_articles=a.max, max_pages=a.max_pages)
    print(f"新增 {n} 篇 → {a.out}")
    return 0


def cmd_index(a: argparse.Namespace) -> int:
    from . import ptt_index

    for q in a.query:
        p = ptt_index.build(a.board, q, max_pages=a.max_pages)
        print(f"{q}：{sum(1 for _ in p.open(encoding='utf-8'))} 篇 → {p}")
    return 0


def cmd_fetch(a: argparse.Namespace) -> int:
    from . import ptt_index
    from .collect_ptt import fetch_list

    rows = ptt_index.load(Path(a.index))
    control = a.control
    if a.control_ratio is not None:  # 對照組篇數 = 高推文篇數 × 比例
        n_top0 = len(ptt_index.select_for_fetch(rows, min_nrec=a.min_nrec, control_n=0, tag=a.tag))
        control = round(n_top0 * a.control_ratio)
    pick = ptt_index.select_for_fetch(rows, min_nrec=a.min_nrec, control_n=control, tag=a.tag, seed=a.seed)
    n_top = sum(r["sample"] == "top" for r in pick)
    print(f"索引 {len(rows)} 篇，標籤 {a.tag}，挑出 top {n_top} + control {len(pick) - n_top}", flush=True)
    extra = {"source_tag": a.source_tag} if a.source_tag else None
    n = fetch_list(pick, Path(a.out), extra=extra, log=lambda m: print(m, flush=True))
    print(f"新增 {n} 篇 → {a.out}")
    return 0


def cmd_fetch_early(a: argparse.Namespace) -> int:
    """早期文章：[真實] 標籤全收，加上看板 2003 到 2006 年的列表頁（排除創作、轉貼等），都不看推文數。"""
    from . import ptt_index
    from .collect_ptt import fetch_list, load_done_ids

    have: set[str] = set()
    for f in Path("data/raw").glob("*.jsonl"):
        have |= load_done_ids(f)
    zs = ptt_index.select_unfiltered(ptt_index.load(Path(a.zhenshi_index)), require_tag="[真實]", source_tag="真實", exclude_ids=have)
    zs_ids = {r["id"] for r in zs}
    early_rows = [r for r in ptt_index.load(Path(a.early_index)) if r["ts"] and r["ts"] < a.until_ts]
    early = ptt_index.select_unfiltered(ptt_index.early_title_ok(early_rows), source_tag="早期", exclude_ids=have | zs_ids)
    print(f"[真實] {len(zs)} 篇，早期列表 {len(early)} 篇（已抓過的跳過）", flush=True)
    n = fetch_list(zs + early, Path(a.out), log=lambda m: print(m, flush=True))
    print(f"新增 {n} 篇 → {a.out}")
    return 0


def cmd_digest(a: argparse.Namespace) -> int:
    from . import collect_digest, ptt_index
    from .collect_ptt import fetch_list

    flat = collect_digest.list_tree()
    pick = collect_digest.select(ptt_index.load(flat))
    print(f"精華區挑出 {len(pick)} 篇")
    n = fetch_list(pick, Path(a.out))
    print(f"新增 {n} 篇 → {a.out}")
    return 0


def cmd_corpus(a: argparse.Namespace) -> int:
    from .corpus import build

    build([Path(p) for p in a.raw] if a.raw else None, Path(a.out))
    return 0


def cmd_annotate(a: argparse.Namespace) -> int:
    from .annotate import annotate_file, load_ids

    backend = make_backend(a.backend)
    only = set(load_ids(Path(a.ids_from))) if a.ids_from else None
    print(f"backend={backend.name} model={a.model} effort={a.effort} workers={a.workers}"
          + (f" ids={len(only)} from {a.ids_from}" if only is not None else ""))
    n = annotate_file(
        Path(a.raw), Path(a.out), backend, model=a.model, limit=a.limit,
        only_ids=only, workers=a.workers, effort=a.effort,
    )
    print(f"新增 {n} 篇標註 → {a.out}")
    return 0


def cmd_stats(a: argparse.Namespace) -> int:
    from .stats import run

    excl = ("translated",) if a.exclude_translated else ()
    w = run(Path(a.annotated), Path(a.out), Path(a.report), exclude_markers=excl, corpus_path=Path(a.corpus))
    print(f"故事 {w['n_stories']} 個，有分數 {w.get('n_scored')}，高分組 {w['n_top']}、低分組 {w.get('n_low')} → {a.out}，報告 {a.report}")
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    from .compare import run as compare_run

    md = compare_run([Path(f) for f in a.files], Path(a.out))
    print(md)
    return 0


def cmd_batch_report(a: argparse.Namespace) -> int:
    from .batch_report import report

    pending = None
    if a.corpus and Path(a.annotated).exists():
        done = {json.loads(l)["id"] for l in Path(a.annotated).read_text(encoding="utf-8").splitlines() if l.strip()}
        units = [json.loads(l)["id"] for l in Path(a.corpus).read_text(encoding="utf-8").splitlines() if l.strip()]
        pending = sum(1 for i in units if i not in done)
    md = report(Path(a.annotated), Path(a.ids), Path(a.corpus), Path(a.log) if a.log else None, pending_after=pending)
    out = Path(a.out or (Path(a.ids).with_suffix(".report.md")))
    out.write_text(md, encoding="utf-8")
    print(md)
    return 0


def cmd_options(a: argparse.Namespace) -> int:
    from .options import describe_options

    print(describe_options())
    return 0


def cmd_generate(a: argparse.Namespace) -> int:
    from .generate import generate, save_result
    from .options import OptionError, resolve_ghost, resolve_length, resolve_list, resolve_style

    try:
        settings = resolve_list("setting", a.setting)
        mechanisms = resolve_list("mechanism", a.mechanism)
        endings = resolve_list("ending", a.ending)
        ghost = resolve_ghost(a.ghost)
        length = resolve_length(a.length if a.length is not None else a.chars)
        style = resolve_style(a.style)
        from .options import resolve_taste

        taste_name, rules = resolve_taste(a.taste) if a.taste else (None, a.rules)
    except OptionError as e:
        print(f"選項錯誤：{e}\n用 `py -m storypipe.cli options` 看所有選項。")
        return 2
    target = length[0] if length and length[0] == length[1] else None
    length_range = length if length and length[0] != length[1] else None

    backend = make_backend(a.backend)
    weights = json.loads(Path(a.weights).read_text(encoding="utf-8"))
    models = dict(DEFAULT_MODELS)
    if a.write_model:
        models["write"] = a.write_model
    if a.judge_model:
        models["judge"] = a.judge_model
    print(f"backend={backend.name} write={models['write']} judge={models['judge']}")
    for i in range(a.n):
        seed = a.seed + i if a.seed is not None else None
        res = generate(
            backend,
            weights,
            seed=seed,
            max_rounds=a.rounds,
            models=models,
            setting=settings,
            mechanism=mechanisms,
            ending=endings,
            ghost_max=ghost,
            target_chars=target,
            length_range=length_range,
            style=style.key,
            style_note=a.style_note or "",
            notes=a.note or [],
            rules=rules,
        )
        stem = f"{time.strftime('%Y%m%d-%H%M%S')}_{res['seed']}"
        md, js = save_result(res, Path(a.out_dir), stem)
        print(
            f"\n=== {md} (round {res['final_round']}, overall {res['final_verdict']['overall']}, "
            f"{res['final_chars']} 字 / 目標 {res['plan']['target_chars']}) ===\n"
        )
        print(res["final"])
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ghost", description="鬼故事產生器")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="抓 PTT 文章")
    c.add_argument("--board", default="marvel")
    c.add_argument("--query", default="經驗 recommend:30", help="PTT 站內搜尋字串，recommend:N 篩推文數")
    c.add_argument("--max", type=int, default=200)
    c.add_argument("--max-pages", type=int, default=50)
    c.add_argument("--out", default=str(RAW))
    c.set_defaults(fn=cmd_collect)

    ix = sub.add_parser("index", help="建 PTT 搜尋索引（只翻列表頁）")
    ix.add_argument("--board", default="marvel")
    ix.add_argument("--query", nargs="+", default=["經驗"])
    ix.add_argument("--max-pages", type=int, default=2000)
    ix.set_defaults(fn=cmd_index)

    fe = sub.add_parser("fetch", help="從索引挑文章抓本文（推文 ≥ N 全部 + 隨機低推文對照組）")
    fe.add_argument("--index", default="data/index/marvel_經驗.jsonl")
    fe.add_argument("--min-nrec", type=int, default=30)
    fe.add_argument("--control", type=int, default=500, help="對照組篇數（推文 ≤ 9）")
    fe.add_argument("--control-ratio", type=float, default=None, help="對照組篇數改成高推文篇數 × 這個比例")
    fe.add_argument("--tag", default="[經驗]", help="標題要含的標籤")
    fe.add_argument("--source-tag", default=None, help="每筆加 source_tag 欄位，例如 翻譯")
    fe.add_argument("--seed", type=int, default=0)
    fe.add_argument("--out", default=str(RAW))
    fe.set_defaults(fn=cmd_fetch)

    fl = sub.add_parser("fetch-early", help="抓早期文章：[真實] 全收 + 看板 2003 到 2006 年列表（不看推文數）")
    fl.add_argument("--zhenshi-index", default="data/index/marvel_真實.jsonl")
    fl.add_argument("--early-index", default="data/index/marvel_board_early.jsonl")
    fl.add_argument("--until-ts", type=int, default=1167609600, help="早期列表只收這個時間以前的（預設 2007-01-01）")
    fl.add_argument("--out", default="data/raw/ptt_marvel_early.jsonl")
    fl.set_defaults(fn=cmd_fetch_early)

    dg = sub.add_parser("digest", help="抓精華區經驗區")
    dg.add_argument("--out", default="data/raw/ptt_marvel_digest.jsonl")
    dg.set_defaults(fn=cmd_digest)

    co = sub.add_parser("corpus", help="合併系列、去重 → data/corpus.jsonl（標註的輸入）")
    co.add_argument("--raw", nargs="*", default=None, help="預設 data/raw/*.jsonl")
    co.add_argument("--out", default="data/corpus.jsonl")
    co.set_defaults(fn=cmd_corpus)

    an = sub.add_parser("annotate", help="LLM 標註結構")
    an.add_argument("--raw", default="data/corpus.jsonl", help="標註輸入；預設是 corpus 建好的語料")
    an.add_argument("--out", default=str(ANNOTATED))
    an.add_argument("--limit", type=int, default=None, help="這次最多標幾篇")
    an.add_argument("--model", default=DEFAULT_MODELS["annotate"], help="完整名稱會被檢查；實際服務的模型記在每筆的 model 欄")
    an.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    an.add_argument("--workers", type=int, default=1, help="平行幾路")
    an.add_argument("--ids-from", default=None, help="只標這些篇：JSONL（每行有 id）或每行一個 id 的文字檔")
    an.add_argument("--backend", default=None, choices=["sdk", "cli", "fake"])
    an.set_defaults(fn=cmd_annotate)

    br = sub.add_parser("batch-report", help="一批標註的時間、花費、分布報告")
    br.add_argument("--ids", required=True)
    br.add_argument("--log", default=None)
    br.add_argument("--annotated", default=str(ANNOTATED))
    br.add_argument("--corpus", default="data/corpus.jsonl")
    br.add_argument("--out", default=None)
    br.set_defaults(fn=cmd_batch_report)

    cp = sub.add_parser("compare", help="比較幾份標註的一致性")
    cp.add_argument("files", nargs="+", help="第一份當參考，其他跟它比，也兩兩互比")
    cp.add_argument("--out", default="data/compare.md")
    cp.set_defaults(fn=cmd_compare)

    st = sub.add_parser("stats", help="算加權表和報告")
    st.add_argument("--annotated", default=str(ANNOTATED))
    st.add_argument("--out", default=str(WEIGHTS))
    st.add_argument("--report", default=str(REPORT))
    st.add_argument("--exclude-translated", action="store_true", help="排除翻譯／轉述外國故事（預設納入）")
    st.add_argument("--corpus", default="data/corpus.jsonl", help="用來查來源、年份、推文數；不存在就退回舊算法")
    st.set_defaults(fn=cmd_stats)

    g = sub.add_parser("generate", help="產生故事（規劃 → 寫 → 評審 → 改）")
    g.add_argument("--weights", default=str(WEIGHTS))
    g.add_argument("--n", type=int, default=1, help="產幾篇")
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--rounds", type=int, default=3, help="最多評審幾輪")
    g.add_argument("--setting", default=None, help="場景，可多個用逗號分開，中文也行：校園,宿舍")
    g.add_argument("--mechanism", default=None, help="主要機制，可多個：附身,事後")
    g.add_argument("--ending", default=None, help="結尾：開放結局、有解釋、反轉、淡出，可多個")
    g.add_argument("--ghost", default=None, help="鬼的露出上限：0 到 3，或 不露面、間接、一瞬間、清楚")
    g.add_argument("--length", default=None, help="長度：字數 1500、範圍 1500-2500，或 極短、短、中、長、超長")
    g.add_argument("--chars", default=None, help="同 --length（舊名稱）")
    g.add_argument("--style", default=None, help="風格：PTT 鄉民（預設）、簡約、幽默、口述、文學、紀錄、長輩講古")
    g.add_argument("--style-note", default=None, help="風格的自由補充，例如「像寫給朋友的信」")
    g.add_argument("--note", action="append", default=None, help="額外要求，可重複：--note 主角是護理師 --note 發生在颱風夜")
    g.add_argument("--taste", default=None, help="口味：直接（預設，照 PTT 讀者資料）或 留白（克制）")
    g.add_argument("--rules", default="v2", choices=["v1", "v2", "restrained"],
                   help="直接指定規則版本（--taste 優先）：v2 = 直接、restrained = 留白、v1 = 2026-10-14 前的舊規則，只供對照")
    g.add_argument("--write-model", default=None)
    g.add_argument("--judge-model", default=None)
    g.add_argument("--backend", default=None, choices=["sdk", "cli", "fake"])
    g.add_argument("--out-dir", default=str(OUT_DIR))
    g.set_defaults(fn=cmd_generate)

    op = sub.add_parser("options", help="列出 generate 能用的所有選項")
    op.set_defaults(fn=cmd_options)
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
