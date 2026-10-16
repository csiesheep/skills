"""用 LLM 把每篇原文拆成結構欄位（Annotation），存成 JSONL。可中斷續跑、可平行。

每筆紀錄會帶 model（實際服務的模型）、model_requested、usage、cost_usd、elapsed_s。
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .llm import DEFAULT_MODELS, Backend
from .taxonomy import Annotation

from .paths import PROMPTS_DIR  # noqa: E402
PROMPT_VERSION = "v2.1"  # v1：給推文分數和推文、定義較鬆；v2：只給標題本文、補結尾和機制判定規則；v2.1：is_story 補「小說形式的創作、新聞、知識介紹算 false」


_LIMIT_WORDS = ("limit", "rate", "overloaded", "529", "429", "quota", "too many requests", "capacity")


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def score_of(art: dict) -> int:
    """推文分數：優先用索引頁的 nrec（爆 = 100），沒有就用 推 - 噓。"""
    nrec = art.get("nrec")
    if nrec is not None:
        return int(nrec)
    return int(art.get("push", 0)) - int(art.get("boo", 0))


def build_user_prompt(art: dict, max_body_chars: int = 24000) -> str:  # 合併後的系列可能很長
    """只給標題和本文。不給推文分數和推文：統計要算欄位跟分數的關係，標註者不能先看到分數。"""
    body = art["body"]
    if len(body) > max_body_chars:
        body = body[:max_body_chars] + "\n（以下略）"
    return f"標題：{art['title']}\n\n本文：\n{body}"


def _done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    out.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return out


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_ids(path: Path) -> list[str]:
    """從 JSONL（每行有 id）或純文字（每行一個 id）讀篇目。"""
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ids.append(json.loads(line)["id"] if line.startswith("{") else line)
    return ids


def _round_beats(d: dict) -> dict:
    d["beats"] = {k: round(v, 3) for k, v in d["beats"].items()}
    return d


def annotate_file(
    raw_path: Path,
    out_path: Path,
    backend: Backend,
    model: str | None = None,
    limit: int | None = None,
    only_ids: set[str] | None = None,
    workers: int = 1,
    effort: str = "medium",
    log=print,
    limit_wait_s: int = 300,
    max_limit_waits: int = 96,
) -> int:
    """回傳這次新標註的篇數。遇到額度或流量限制，等 limit_wait_s 秒再試，最多 max_limit_waits 次（預設 8 小時）。"""
    model = model or DEFAULT_MODELS["annotate"]
    system = load_prompt("annotate.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_ids(out_path)

    todo: list[dict] = []
    for art in iter_jsonl(raw_path):
        if art["id"] in done or (only_ids is not None and art["id"] not in only_ids):
            continue
        todo.append(art)
        if limit is not None and len(todo) >= limit:
            break

    lock = threading.Lock()
    tot = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    cost = {"usd": 0.0}
    served: dict[str, int] = {}
    added = {"n": 0, "fail": 0}
    t0 = time.time()

    def work(art: dict):
        other_tries = 0
        limit_waits = 0
        while True:
            try:
                ann = backend.structured(system, build_user_prompt(art), Annotation, model, max_tokens=2500, effort=effort)
                return art, ann, dict(backend.last)
            except Exception as e:  # noqa: BLE001
                msg = str(e).lower()
                if any(w in msg for w in _LIMIT_WORDS) and limit_waits < max_limit_waits:
                    limit_waits += 1
                    log(f"limit {art['id']}：{str(e)[:120]}；等 {limit_wait_s // 60} 分鐘再試（第 {limit_waits} 次）")
                    time.sleep(limit_wait_s)
                    continue
                if other_tries < 2 and not isinstance(e, ValueError):
                    other_tries += 1
                    time.sleep(10 * other_tries)
                    continue
                raise

    with out_path.open("a", encoding="utf-8") as out:
        def handle(art: dict, ann: Annotation, meta: dict) -> None:
            ann.beats = ann.beats.normalized()
            rec = {
                "id": art["id"],
                "url": art.get("url", ""),
                "title": art["title"],
                "score": score_of(art),
                "length_chars": len(art["body"]),
                "annotation": _round_beats(ann.model_dump()),
                "model": meta.get("model", ""),
                "model_requested": meta.get("model_requested", model),
                "effort": effort,
                "prompt_version": PROMPT_VERSION,
                "usage": meta.get("usage", {}),
                "cost_usd": meta.get("cost_usd"),  # 照定價自己算的
                "cli_cost_usd": meta.get("cli_cost_usd"),  # CLI 自己報的，看 cli_cost_basis 決定信不信
                "cli_cost_basis": meta.get("cli_cost_basis"),
                "elapsed_s": round(meta.get("elapsed_s", 0.0), 1),
            }
            with lock:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                added["n"] += 1
                for k in tot:
                    tot[k] += int(rec["usage"].get(k, 0) or 0)
                cost["usd"] += float(rec["cost_usd"] or 0.0)
                served[rec["model"]] = served.get(rec["model"], 0) + 1
                a = ann
                log(
                    f"[{added['n']}/{len(todo)}] {rec['elapsed_s']:>5.1f}s {rec['model']:<26} score={rec['score']:>3} "
                    f"{a.setting:<13} {'/'.join(a.mechanisms):<30} {a.ending:<9} ghost={a.ghost_explicitness} "
                    f"story={a.is_story} | {art['title']}"
                )

        def fail(art: dict, e: Exception) -> None:
            with lock:
                added["fail"] += 1
            log(f"fail {art['id']} {art['title']}: {e}")

        if workers <= 1:
            for art in todo:
                try:
                    handle(*work(art))
                except Exception as e:  # noqa: BLE001
                    fail(art, e)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(work, art): art for art in todo}
                for fut in as_completed(futs):
                    try:
                        handle(*fut.result())
                    except Exception as e:  # noqa: BLE001
                        fail(futs[fut], e)

    elapsed = time.time() - t0
    if added["n"] or added["fail"]:
        log(
            f"done: {added['n']} ok, {added['fail']} fail | served={served} | tokens in={tot['input_tokens']} "
            f"out={tot['output_tokens']} cache_create={tot['cache_creation_input_tokens']} cache_read={tot['cache_read_input_tokens']} "
            f"| 定價成本=${cost['usd']:.4f} | 牆鐘 {elapsed:.0f}s，workers={workers}"
        )
    return added["n"]
