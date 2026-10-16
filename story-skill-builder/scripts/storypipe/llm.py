"""LLM 後端。

三種：
- sdk  : 官方 anthropic SDK（有 ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / `ant auth login` profile 時自動選）
- cli  : Claude Code 的 `claude -p`（有登入 Claude Code 但沒 API key 時自動選）
- fake : 不打網路，給測試管線用

用 STORYPIPE_LLM_BACKEND=sdk|cli|fake 強制指定。

每次呼叫後，`backend.last` 會有這次的實際模型、token、成本、耗時（每個執行緒各自一份，可平行呼叫）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODELS = {
    "annotate": "claude-opus-5-5",  # 2026-10-13 比較 Haiku 5.5／Sonnet 5.5／Opus 5.5 後選定，見 data/compare_v2.md
    "write": "claude-opus-5-5",
    "judge": "claude-opus-5-5",
}

# 伺服器端 refusal fallback：只有這幾個系列支援 "default" 形式。
_FALLBACK_PREFIXES = ("claude-opus", "claude-fable", "claude-sonnet")
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

_USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

# 官方定價（美元／百萬 token，2026-10）。CLI 的價目表不一定認得新模型（costBasis=unknown 時它的數字不可信），
# 所以成本一律用 token 數自己算。Haiku 5.5 是 100K token 以下 prompt 的價格。
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-fable-5-1": (10.00, 50.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def list_cost(model: str, usage: dict) -> float | None:
    """照定價算一次呼叫的成本。快取寫入：1 小時 2 倍、5 分鐘 1.25 倍；快取讀取 0.1 倍。"""
    price = next((p for k, p in PRICES.items() if model.startswith(k)), None)
    if price is None:
        return None
    pin, pout = price
    total_cw = int(usage.get("cache_creation_input_tokens", 0) or 0)
    cw_1h = int(usage.get("cache_1h", total_cw) or 0)  # CLI 用 1 小時快取；沒有細項時當作全是 1 小時
    cw_5m = max(0, total_cw - cw_1h)
    return (
        int(usage.get("input_tokens", 0) or 0) * pin
        + cw_1h * pin * 2.0
        + cw_5m * pin * 1.25
        + int(usage.get("cache_read_input_tokens", 0) or 0) * pin * 0.1
        + int(usage.get("output_tokens", 0) or 0) * pout
    ) / 1e6


class RefusedError(RuntimeError):
    pass


class ModelMismatchError(RuntimeError):
    """要求完整模型名稱，實際跑的卻是別的模型。"""


def detect_backend() -> str:
    forced = os.environ.get("STORYPIPE_LLM_BACKEND")
    if forced:
        return forced
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "sdk"
    if (Path.home() / ".config" / "anthropic").exists():
        return "sdk"
    if shutil.which("claude"):
        return "cli"
    raise RuntimeError(
        "找不到可用的 LLM 後端。三選一：\n"
        "  1. export ANTHROPIC_API_KEY=...\n"
        "  2. ant auth login\n"
        "  3. 裝 Claude Code 並 `claude auth login`，程式會改走 `claude -p`\n"
        "測試管線不想花錢：STORYPIPE_LLM_BACKEND=fake"
    )


def check_served_model(requested: str, served: str) -> None:
    """完整名稱（claude-xxx）必須原樣被服務；別名（haiku、sonnet）不檢查，但 served 會被記下來。"""
    if requested.startswith("claude-") and served and not served.startswith(requested):
        raise ModelMismatchError(f"要求 {requested}，實際跑的是 {served}")


class Backend:
    name = "base"

    def __init__(self) -> None:
        self._tl = threading.local()

    @property
    def last(self) -> dict:
        """這個執行緒上一次呼叫的 {model, model_requested, usage, cost_usd, elapsed_s}。"""
        return getattr(self._tl, "meta", {})

    def _set_last(self, **meta) -> None:
        self._tl.meta = meta

    def text(self, system: str, user: str, model: str, max_tokens: int = 16000, effort: str = "high") -> str:
        raise NotImplementedError

    def structured(
        self, system: str, user: str, schema: Type[T], model: str, max_tokens: int = 8000, effort: str = "medium"
    ) -> T:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# SDK
# ---------------------------------------------------------------------------


class SdkBackend(Backend):
    name = "sdk"

    def __init__(self) -> None:
        super().__init__()
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()

    def _fallback_kwargs(self, model: str) -> dict:
        if os.environ.get("STORYPIPE_NO_FALLBACK") or not model.startswith(_FALLBACK_PREFIXES):
            return {}
        return {"betas": [_FALLBACK_BETA], "fallbacks": "default"}

    def _record(self, msg, model: str, t0: float) -> None:
        usage = {k: int(getattr(msg.usage, k, 0) or 0) for k in _USAGE_KEYS}
        cc = getattr(msg.usage, "cache_creation", None)
        usage["cache_1h"] = int(getattr(cc, "ephemeral_1h_input_tokens", 0) or 0) if cc else 0
        usage["cache_5m"] = int(getattr(cc, "ephemeral_5m_input_tokens", 0) or 0) if cc else 0
        # msg.model 是實際服務的模型；被 refusal fallback 接手時會是 fallback 模型，不做 mismatch 檢查。
        self._set_last(
            model=msg.model, model_requested=model, usage=usage,
            cost_usd=list_cost(msg.model, usage), elapsed_s=time.time() - t0,
        )

    def text(self, system: str, user: str, model: str, max_tokens: int = 16000, effort: str = "high") -> str:
        t0 = time.time()
        with self.client.beta.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": effort},
            **self._fallback_kwargs(model),
        ) as stream:
            msg = stream.get_final_message()
        self._record(msg, model, t0)
        if msg.stop_reason == "refusal":
            raise RefusedError(getattr(getattr(msg, "stop_details", None), "explanation", "refused"))
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("輸出被 max_tokens 截斷，調高 max_tokens 或縮短 target_chars")
        return "".join(b.text for b in msg.content if b.type == "text")

    def structured(
        self, system: str, user: str, schema: Type[T], model: str, max_tokens: int = 8000, effort: str = "medium"
    ) -> T:
        t0 = time.time()
        msg = self.client.beta.messages.parse(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
            output_config={"effort": effort},
            **self._fallback_kwargs(model),
        )
        self._record(msg, model, t0)
        if msg.stop_reason == "refusal":
            raise RefusedError(getattr(getattr(msg, "stop_details", None), "explanation", "refused"))
        if msg.parsed_output is None:
            raise RuntimeError("structured output 解析失敗")
        return msg.parsed_output


# ---------------------------------------------------------------------------
# Claude Code CLI
# ---------------------------------------------------------------------------


def parse_cli_output(stdout: str) -> tuple[dict, list[str]]:
    """`claude -p --output-format json` 的輸出：前面可能有警告行（例如 [claude-code:unrecognized_model] {...}），
    結果是最後一行 JSON。回傳 (結果, 警告行)。"""
    lines = [l for l in stdout.splitlines() if l.strip()]
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].lstrip().startswith("{"):
            try:
                return json.loads(lines[i]), lines[:i]
            except json.JSONDecodeError:
                continue
    raise ValueError(f"claude -p 輸出裡沒有結果 JSON：{stdout[:300]}")


def served_model(data: dict) -> str:
    """modelUsage 裡輸出 token 最多的那個模型。"""
    mu = data.get("modelUsage") or {}
    if not mu:
        return ""
    return max(mu.items(), key=lambda kv: (kv[1] or {}).get("outputTokens", 0))[0]


class CliBackend(Backend):
    name = "cli"

    def __init__(self) -> None:
        super().__init__()
        exe = shutil.which("claude")
        if not exe:
            raise RuntimeError("找不到 claude 指令")
        self.exe = exe

    def _run(self, system: str, user: str, model: str, extra: list[str], effort: str = "medium") -> dict:
        # 模型名稱原樣傳給 CLI，不換別名。
        # --tools "" 和 --strict-mcp-config 讓每次呼叫不載入工具定義和 MCP server，省啟動時間也省 token。
        cmd = [
            self.exe, "-p", "--output-format", "json", "--model", model, "--system-prompt", system,
            "--tools", "", "--strict-mcp-config", "--effort", effort, *extra,
        ]
        t0 = time.time()
        proc = subprocess.run(cmd, input=user, capture_output=True, text=True, encoding="utf-8", timeout=1800)
        try:
            data, _warnings = parse_cli_output(proc.stdout or "")
        except ValueError:
            raise RuntimeError(f"claude -p 失敗 ({proc.returncode}): {(proc.stderr or proc.stdout)[:1500]}")
        served = served_model(data)
        u = data.get("usage") or {}
        usage = {k: int(u.get(k, 0) or 0) for k in _USAGE_KEYS}
        cc = u.get("cache_creation") or {}
        usage["cache_1h"] = int(cc.get("ephemeral_1h_input_tokens", 0) or 0)
        usage["cache_5m"] = int(cc.get("ephemeral_5m_input_tokens", 0) or 0)
        usage["thinking_tokens"] = int((u.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0)
        mu = (data.get("modelUsage") or {}).get(served) or {}
        self._set_last(
            model=served, model_requested=model, usage=usage,
            cost_usd=list_cost(served, usage),
            cli_cost_usd=data.get("total_cost_usd"), cli_cost_basis=mu.get("costBasis"),
            elapsed_s=time.time() - t0,
        )
        if data.get("is_error"):
            raise RuntimeError(f"claude -p 回報錯誤：{data.get('result')}")
        check_served_model(model, served)
        return data

    def text(self, system: str, user: str, model: str, max_tokens: int = 16000, effort: str = "high") -> str:
        return self._run(system, user, model, [], effort=effort)["result"]

    def structured(
        self, system: str, user: str, schema: Type[T], model: str, max_tokens: int = 8000, effort: str = "medium"
    ) -> T:
        json_schema = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        data = self._run(system, user, model, ["--json-schema", json_schema], effort=effort)
        raw = data.get("structured_output")
        if raw is None:
            raw = _extract_json(data.get("result", ""))
        return schema.model_validate(raw)


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"回覆裡沒有 JSON：{text[:200]}")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------------------
# Fake（測試用，不打網路）
# ---------------------------------------------------------------------------


class FakeBackend(Backend):
    name = "fake"

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str]] = []  # (kind, model)
        self._lock = threading.Lock()

    def _note(self, kind: str, model: str) -> None:
        with self._lock:
            self.calls.append((kind, model))
        self._set_last(model=f"fake/{model}", model_requested=model, usage={k: 1 for k in _USAGE_KEYS}, cost_usd=0.0, elapsed_s=0.0)

    def text(self, system: str, user: str, model: str, max_tokens: int = 16000, effort: str = "high") -> str:
        self._note("text", model)
        return (
            "[經驗] 測試用的故事\n\n"
            "飄點微弱，第一次發文。\n\n"
            "這是 fake backend 產生的本文，用來驗證管線會不會跑。\n\n"
            + ("（修訂版）\n" if "fix_notes" in user or "評審意見" in user else "")
            + user[:200].replace("\n", " ")
        )

    def structured(
        self, system: str, user: str, schema: Type[T], model: str, max_tokens: int = 8000, effort: str = "medium"
    ) -> T:
        self._note("structured", model)
        from .taxonomy import Annotation, BeatShare, Verdict

        h = sum(ord(c) for c in user[:400])
        if schema is Annotation:
            settings = ["dorm", "military", "rental", "night_shift", "old_house", "road"]
            mechs = ["presence", "retro_reveal", "identity_swap", "witness_mismatch", "escalation", "sound_only"]
            endings = ["open", "explained", "twist", "fade"]
            return Annotation(  # type: ignore[return-value]
                is_story=(h % 7 != 0),
                setting=settings[h % len(settings)],
                setting_detail="fake 場景",
                mechanisms=[mechs[h % len(mechs)], mechs[(h // 3) % len(mechs)]],
                ending=endings[h % len(endings)],
                beats=BeatShare(normal=0.25, anomaly=0.15, denial=0.1, escalation=0.25, reveal=0.15, aftermath=0.1),
                ghost_explicitness=h % 3,
                realism_anchors=["門禁時間", "值班交接簿"],
                voice_markers=["first_person", "disclaimer"],
                scariest_moment="fake 最可怕的一刻",
                one_line_premise="fake 一句話前提",
            )
        if schema is Verdict:
            revised = "修訂" in user or "第 2 輪" in user or "round 2" in user
            overall = 8 if revised else 5
            return Verdict(  # type: ignore[return-value]
                realism=4, slow_burn=4, ghost_restraint=4 if revised else 2, ending=4, voice=4,
                overall=overall, passes=overall >= 7,
                fix_notes=[] if revised else ["第三段鬼寫太清楚，改成只寫感應燈亮了"],
            )
        raise NotImplementedError(schema)


def make_backend(name: str | None = None) -> Backend:
    name = name or detect_backend()
    if name == "sdk":
        return SdkBackend()
    if name == "cli":
        return CliBackend()
    if name == "fake":
        return FakeBackend()
    raise ValueError(f"unknown backend {name}")
