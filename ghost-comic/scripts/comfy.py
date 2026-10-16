"""Minimal client for the local ComfyUI and the Qwen Image 2.1 graph every comic image goes through.

Text to image when no reference is given; with references (character sheets, scene sheets, earlier
panels) the same graph edits from them: TextEncodeQwenImage21 takes them as images.image_1..n and the
prompt names them <image1>, <image2>... Standard library only.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SERVER = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
MODELS = {
    "unet": "qwen_image_2.1_int8_convrot.safetensors",
    "clip": "qwen3vl_8b_int8_convrot.safetensors",  # an 8B Qwen3-VL encoder; a 32B one fails on a shape mismatch
    "vae": "qwen_image_2.1_vae_bf16.safetensors",
}
STEPS = 15  # 15 steps, CFG 1, euler/simple: the settings that held up in testing (CFG > 1 drifts faces)
CLIENT = "ghost-comic-" + uuid.uuid4().hex[:8]


def http(path: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(SERVER + path, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def alive() -> bool:
    try:
        http("/system_stats", timeout=5)
        return True
    except Exception:  # noqa: BLE001
        return False


def missing_models(models: dict = MODELS) -> list[str]:
    """Model files the graph needs that this ComfyUI does not list."""
    info = json.loads(http("/object_info/UNETLoader")), json.loads(http("/object_info/CLIPLoader")), json.loads(http("/object_info/VAELoader"))
    have = set()
    for block, node in zip(info, ("UNETLoader", "CLIPLoader", "VAELoader")):
        req = block[node]["input"]["required"]
        for v in req.values():
            if isinstance(v, list) and v and isinstance(v[0], list):
                have.update(v[0])
    return [m for m in models.values() if m not in have]


def upload(path: Path) -> str:
    name = "gcomic_" + path.name
    boundary = uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
        "Content-Type: image/png\r\n\r\n".encode(),
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    res = json.loads(http("/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))
    return res["name"]


def build_graph(prompt: str, ref_names: list[str], w: int, h: int, seed: int, n: int, prefix: str, models: dict = MODELS) -> dict:
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": models["unet"], "weight_dtype": "default"}},
        "2": {"class_type": "QwenImage21Cache", "inputs": {"model": ["1", 0], "device": "auto", "dtype": "default"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": models["clip"], "type": "qwen_image", "device": "default"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": models["vae"]}},
        "10": {"class_type": "TextEncodeQwenImage21", "inputs": {
            "clip": ["3", 0], "prompt": prompt, "negative_prompt": "", "resolution": 1024, "vae": ["4", 0]}},
        # explicit size: the encoder's own latent follows image_1's aspect, a panel needs its cell's
        "11": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": n}},
        "20": {"class_type": "KSampler", "inputs": {
            "model": ["2", 0], "seed": seed, "steps": STEPS, "cfg": 1.0, "sampler_name": "euler",
            "scheduler": "simple", "positive": ["10", 0], "negative": ["10", 1],
            "latent_image": ["11", 0], "denoise": 1.0}},
        "30": {"class_type": "VAEDecode", "inputs": {"samples": ["20", 0], "vae": ["4", 0]}},
        "40": {"class_type": "SaveImage", "inputs": {"images": ["30", 0], "filename_prefix": prefix}},
    }
    for i, name in enumerate(ref_names, 1):
        nid = str(50 + i)
        g[nid] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g["10"]["inputs"][f"images.image_{i}"] = [nid, 0]
    return g


def run(graph: dict) -> tuple[str, list[dict], float, float | None]:
    """Submit, wait, return (prompt_id, images, wall seconds, execution seconds)."""
    t0 = time.time()
    res = json.loads(http("/prompt", json.dumps({"prompt": graph, "client_id": CLIENT}).encode(),
                          {"Content-Type": "application/json"}))
    pid = res["prompt_id"]
    while True:
        time.sleep(2)
        hist = json.loads(http(f"/history/{pid}"))
        if pid in hist:
            break
    entry = hist[pid]
    status = entry.get("status", {})
    msgs = {m[0]: m[1] for m in status.get("messages", [])}
    if status.get("status_str") != "success":
        raise RuntimeError(json.dumps(msgs.get("execution_error", status), ensure_ascii=False)[:2000])
    exec_s = None
    if "execution_start" in msgs and "execution_success" in msgs:
        exec_s = (msgs["execution_success"]["timestamp"] - msgs["execution_start"]["timestamp"]) / 1000
    return pid, entry["outputs"]["40"]["images"], round(time.time() - t0, 1), exec_s


def fetch(img: dict, dest: Path) -> None:
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(http("/view?" + q))
