"""MiniMax-H3 reference-to-video on the local ComfyUI, with optional pinned keyframes.

Reference images (--ref, 1-9) lock the character's identity; keyframes (--keyframe PATH@SECONDS)
pin a still to a moment of the output (the multiframe workflow). With no keyframes this is plain
reference-to-video. Fills h3_ref_api.json next to this file, submits it, waits, and copies the MP4
to --out-dir. Standard library only.

Examples:
  python h3_ref_video.py --ref front.png --ref side.png --ref back.png --prompt-file p.txt --seconds 6
  python h3_ref_video.py --ref front.png --keyframe side.png@2 --keyframe back.png@4 \
      --keyframe front.png@6.5 --prompt-file p.txt --seconds 7
"""
import argparse
import json
import math
import mimetypes
import os
import random
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "h3_ref_api.json")
FPS = 24
TRAINED_MIN_S, TRAINED_MAX_S = 5.0, 15.0
MAX_REFS = 9
# Node ids in h3_ref_api.json (taken from a successful run of the ComfyUI template
# video_minimax_h3_r2v with the models swapped; see SKILL.md).
R2V, PROMPT, SECONDS, SEED, STEPS, GUIDER, SAVE = "136", "138", "132", "129", "143", "126", "92"
VIDEO_VAE, AUDIO_VAE, UNET, CLIP = "119", "120", "127", "128"
LOADERS = {"UNETLoader": "unet_name", "CLIPLoader": "clip_name", "VAELoader": "vae_name"}


def image_size(path):
    """(width, height) from a PNG, JPEG or WebP header, or None."""
    with open(path, "rb") as f:
        head = f.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            chunk = head[12:16]
            if chunk == b"VP8X":
                return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
            if chunk == b"VP8 ":
                f.seek(26)
                w, h = struct.unpack("<HH", f.read(4))
                return w & 0x3FFF, h & 0x3FFF
            if chunk == b"VP8L":
                f.seek(21)
                b = f.read(4)
                return 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return None
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                marker = f.read(2)
                if len(marker) < 2 or marker[0] != 0xFF:
                    return None
                if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
                    continue
                length = struct.unpack(">H", f.read(2))[0]
                if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(1)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                f.seek(length - 2, 1)
    return None


def video_size(img_w, img_h, megapixels):
    """Keep the image's aspect ratio at about `megapixels`, both sides multiples of 32."""
    scale = math.sqrt(megapixels * 1_000_000 / (img_w * img_h))
    return max(32, round(img_w * scale / 32) * 32), max(32, round(img_h * scale / 32) * 32)


def frame_count(seconds):
    """The template's length rule: about seconds*24 frames, rounded up to 17k+5."""
    n = max(5, round(seconds * FPS))
    return n + (5 - n % 17) % 17


def http_json(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def upload(server, path):
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    with open(path, "rb") as f:
        payload = f.read()
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + payload + (
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n"
            f"--{boundary}--\r\n").encode()
    req = urllib.request.Request(f"{server}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.load(r)
    return f"{res['subfolder']}/{res['name']}" if res.get("subfolder") else res["name"]


def missing_models(server, graph):
    missing = []
    for node in graph.values():
        key = LOADERS.get(node["class_type"])
        if key:
            info = http_json(f"{server}/object_info/{node['class_type']}")
            if node["inputs"][key] not in info[node["class_type"]]["input"]["required"][key][0]:
                missing.append(node["inputs"][key])
    for cls in ("MiniMaxH3ReferenceToVideo", "MiniMaxH3AddGuide"):
        if not http_json(f"{server}/object_info/{cls}"):
            missing.append(f"node {cls} (update ComfyUI)")
    return missing


def parse_keyframe(s):
    path, sep, sec = s.rpartition("@")
    if not sep or not path:
        sys.exit(f"--keyframe must be PATH@SECONDS, got {s!r}")
    return path, float(sec)


def build(graph, refs, keyframes, prompt, seconds, seed, steps, size):
    """Wire reference images and the keyframe guide chain into the base graph (in place)."""
    r2v = graph[R2V]["inputs"]
    r2v["width"], r2v["height"] = size
    for i, name in enumerate(refs):
        nid = str(900 + i)
        graph[nid] = {"class_type": "LoadImage", "inputs": {"image": name}}
        r2v[f"ref_images.ref_image_{i}"] = [nid, 0]
    positive = [R2V, 0]
    last = frame_count(seconds) - 1
    for i, (name, sec) in enumerate(keyframes):
        img, guide = str(950 + 2 * i), str(951 + 2 * i)
        graph[img] = {"class_type": "LoadImage", "inputs": {"image": name}}
        graph[guide] = {"class_type": "MiniMaxH3AddGuide", "inputs": {
            "positive": positive, "latent": [R2V, 1], "frame_idx": min(last, max(0, round(sec * FPS))),
            "vae": [VIDEO_VAE, 0], "audio_vae": [AUDIO_VAE, 0], "image": [img, 0]}}
        positive = [guide, 0]
    graph[GUIDER]["inputs"]["conditioning"] = positive
    graph[PROMPT]["inputs"]["value"] = prompt
    graph[SECONDS]["inputs"]["value"] = float(seconds)
    graph[SEED]["inputs"]["noise_seed"] = seed
    graph[STEPS]["inputs"]["value"] = steps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", action="append", default=[], help="reference image; repeat, 1-9; <Picture 1..N> in order")
    ap.add_argument("--keyframe", action="append", default=[], help="PATH@SECONDS, pinned onto that moment; repeat")
    ap.add_argument("--prompt-file", required=True, help="UTF-8 prompt file")
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--allow-long", action="store_true", help=f"allow seconds outside {TRAINED_MIN_S:g}-{TRAINED_MAX_S:g}")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--steps", type=int, default=8, help="the fused model has an 8-step turbo merged in")
    ap.add_argument("--megapixels", type=float, default=0.6)
    ap.add_argument("--aspect", help="W:H for the video, e.g. 3:4 for a standing full body; default: the first --ref's shape")
    ap.add_argument("--unet", help="override the video model file")
    ap.add_argument("--clip", help="override the text encoder file")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--prefix", default="h3_ref")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--dry-run", action="store_true", help="print the filled workflow, do not run")
    a = ap.parse_args()

    if not 1 <= len(a.ref) <= MAX_REFS:
        sys.exit(f"give 1-{MAX_REFS} --ref images")
    keyframes = [parse_keyframe(k) for k in a.keyframe]
    for p in a.ref + [k[0] for k in keyframes]:
        if not os.path.isfile(p):
            sys.exit(f"image not found: {p}")
    if not TRAINED_MIN_S <= a.seconds <= TRAINED_MAX_S and not a.allow_long:
        sys.exit(f"--seconds {a.seconds:g} is outside H3's trained {TRAINED_MIN_S:g}-{TRAINED_MAX_S:g}s; pass --allow-long to try anyway")
    for path, sec in keyframes:
        if not 0 <= sec <= a.seconds:
            sys.exit(f"keyframe {path}@{sec:g} is outside 0-{a.seconds:g}s")
    with open(a.prompt_file, encoding="utf-8") as f:
        prompt = f.read().strip()
    if a.aspect:
        try:
            size = tuple(float(x) for x in a.aspect.split(":"))
            assert len(size) == 2 and min(size) > 0
        except (ValueError, AssertionError):
            sys.exit(f"--aspect must look like 3:4, got {a.aspect!r}")
    else:
        size = image_size(a.ref[0])
        if not size:
            sys.exit(f"cannot read the size of {a.ref[0]} (png / jpg / webp); pass --aspect")
    size = video_size(*size, a.megapixels)
    seed = a.seed if a.seed is not None else random.randint(1, 2**31 - 1)

    with open(TEMPLATE, encoding="utf-8") as f:
        graph = json.load(f)
    if a.unet:
        graph[UNET]["inputs"]["unet_name"] = a.unet
    if a.clip:
        graph[CLIP]["inputs"]["clip_name"] = a.clip
    graph[SAVE]["inputs"]["filename_prefix"] = f"video/{a.prefix}"
    names = {p: os.path.basename(p) for p in a.ref + [k[0] for k in keyframes]}

    if a.dry_run:
        build(graph, [names[p] for p in a.ref], [(names[p], s) for p, s in keyframes],
              prompt, a.seconds, seed, a.steps, size)
        print(json.dumps(graph, ensure_ascii=False, indent=1))
        return

    try:
        http_json(f"{a.server}/system_stats", timeout=10)
    except (urllib.error.URLError, OSError):
        sys.exit(f"ComfyUI is not reachable at {a.server}; start it first")
    missing = missing_models(a.server, graph)
    if missing:
        sys.exit("missing on this ComfyUI: " + ", ".join(missing))
    uploaded = {p: upload(a.server, p) for p in names}
    build(graph, [uploaded[p] for p in a.ref], [(uploaded[p], s) for p, s in keyframes],
          prompt, a.seconds, seed, a.steps, size)

    res = http_json(f"{a.server}/prompt", json.dumps({"prompt": graph, "client_id": uuid.uuid4().hex}).encode())
    pid = res["prompt_id"]
    print(f"queued {pid}: {size[0]}x{size[1]}, {a.seconds:g}s, {len(a.ref)} refs, "
          f"{len(keyframes)} keyframes, seed {seed}", flush=True)
    start = time.time()
    while True:
        hist = http_json(f"{a.server}/history/{pid}").get(pid)
        status = (hist or {}).get("status", {})
        if status.get("completed"):
            break
        if status.get("status_str") == "error":
            msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
            sys.exit("ComfyUI error: " + (msgs[0][1].get("exception_message", "").strip() if msgs else "unknown"))
        if time.time() - start > a.timeout:
            sys.exit(f"timed out after {a.timeout}s; job {pid} may still finish in ComfyUI")
        time.sleep(10)

    os.makedirs(a.out_dir, exist_ok=True)
    out = hist["outputs"][SAVE]["images"][0]
    dest = os.path.join(a.out_dir, out["filename"])
    q = urllib.parse.urlencode({"filename": out["filename"], "subfolder": out["subfolder"], "type": out["type"]})
    with urllib.request.urlopen(f"{a.server}/view?{q}", timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(json.dumps({"prompt_id": pid, "file": dest, "seconds": a.seconds, "size": f"{size[0]}x{size[1]}",
                      "seed": seed, "refs": a.ref, "keyframes": a.keyframe,
                      "elapsed_s": round(time.time() - start)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
