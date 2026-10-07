"""Replace the person in a video with another character, with MiniMax-H3 reference-to-video on the local ComfyUI.

SAM3 finds the subject (--target, e.g. "person") in every frame of the source clip; that area is
filled gray and the masked clip goes to H3 as <Video 1>, with the source audio. The identity
pictures (--identity, 1-3) are <Picture 1..N>. H3 redraws the subject as the new identity with the
source motion and timing; the source audio is kept on the output. Fills h3_charrep_api.json next to
this file, submits it, waits, and copies the MP4 to --out-dir. Standard library only.

Example:
  python h3_charrep.py --video clip.mp4 --identity new_look.png --target person \
      --prompt-file prompt.txt --out-dir out
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
TEMPLATE = os.path.join(HERE, "h3_charrep_api.json")
TRAINED_MIN_S, TRAINED_MAX_S = 2.0, 15.0  # the reference-video input takes 2-15 s
MAX_IDENTITY = 3
# Node ids in h3_charrep_api.json (from a successful run on 2026-10-06; see SKILL.md).
LOAD_VIDEO, SLICE, TARGET_TEXT, SAM, GROW, SCALE = "500", "501", "504", "505", "506", "509"
R2V, PROMPT, SECONDS, SEED, STEPS, SAVE, IDENTITY0 = "136", "138", "132", "129", "143", "92", "510"
CREATE_VIDEO, GEN_AUDIO, SRC = "130", "121", "502"
UNET, CLIP = "127", "128"
LOADERS = {"UNETLoader": "unet_name", "CLIPLoader": "clip_name", "VAELoader": "vae_name",
           "CheckpointLoaderSimple": "ckpt_name"}


def mp4_info(path):
    """(width, height, seconds) of the first video track of an MP4 / MOV, or None. Reads box headers only."""
    with open(path, "rb") as f:
        data = f.read(64 * 1024 * 1024)
    seconds, size = None, None
    i = data.find(b"mvhd")
    if i > 0:
        v = data[i + 4]
        if v == 1:
            scale, dur = struct.unpack(">IQ", data[i + 24:i + 36])
        else:
            scale, dur = struct.unpack(">II", data[i + 16:i + 24])
        seconds = dur / scale if scale else None
    start = 0
    while True:
        i = data.find(b"tkhd", start)
        if i < 0:
            break
        box = struct.unpack(">I", data[i - 4:i])[0]
        end = i - 4 + box
        w, h = struct.unpack(">II", data[end - 8:end])
        if w and h:
            size = (w >> 16, h >> 16)
            break
        start = i + 4
    return (size[0], size[1], seconds) if size else None


def video_size(src_w, src_h, megapixels):
    """Keep the source's aspect ratio at about `megapixels`, both sides multiples of 32."""
    scale = math.sqrt(megapixels * 1_000_000 / (src_w * src_h))
    return max(32, round(src_w * scale / 32) * 32), max(32, round(src_h * scale / 32) * 32)


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
    with urllib.request.urlopen(req, timeout=300) as r:
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
    for cls in ("MiniMaxH3ReferenceToVideo", "SAM3_Detect", "LoadVideo"):
        if not http_json(f"{server}/object_info/{cls}"):
            missing.append(f"node {cls} (update ComfyUI)")
    return missing


def build(graph, video, identities, prompt, target, start, seconds, size, seed, steps, threshold, grow,
          generated_audio):
    graph[LOAD_VIDEO]["inputs"]["file"] = video
    graph[SLICE]["inputs"].update(start_time=float(start), duration=float(seconds))
    graph[TARGET_TEXT]["inputs"]["text"] = target
    graph[SAM]["inputs"]["threshold"] = threshold
    graph[GROW]["inputs"]["expand"] = grow
    r2v = graph[R2V]["inputs"]
    r2v["width"], r2v["height"] = size
    graph[IDENTITY0]["inputs"]["image"] = identities[0]
    for i, name in enumerate(identities[1:], start=1):
        nid = str(int(IDENTITY0) + 10 + i)
        graph[nid] = {"class_type": "LoadImage", "inputs": {"image": name}}
        r2v[f"ref_images.ref_image_{i}"] = [nid, 0]
    if generated_audio:  # use H3's own soundtrack instead of the source clip's
        graph[CREATE_VIDEO]["inputs"]["audio"] = [GEN_AUDIO, 0]
    graph[PROMPT]["inputs"]["value"] = prompt
    graph[SECONDS]["inputs"]["value"] = float(seconds)
    graph[SEED]["inputs"]["noise_seed"] = seed
    graph[STEPS]["inputs"]["value"] = steps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True, help="source clip (mp4 / mov), one subject to replace")
    ap.add_argument("--identity", action="append", default=[], help="picture of the new character; repeat, 1-3")
    ap.add_argument("--prompt-file", required=True, help="UTF-8 prompt file")
    ap.add_argument("--target", default="person", help="what SAM3 should find and replace: person, woman, cartoon character...")
    ap.add_argument("--start", type=float, default=0.0, help="start of the part of the clip to use, seconds")
    ap.add_argument("--seconds", type=float, help="length to use (2-15); default: the rest of the clip, up to 15")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--steps", type=int, default=8, help="the fused model has an 8-step turbo merged in")
    ap.add_argument("--megapixels", type=float, default=0.6)
    ap.add_argument("--aspect", help="W:H override; default: the source video's shape")
    ap.add_argument("--threshold", type=float, default=0.5, help="SAM3 detection threshold")
    ap.add_argument("--grow", type=int, default=12, help="pixels to widen the mask by")
    ap.add_argument("--generated-audio", action="store_true", help="keep H3's soundtrack instead of the source audio")
    ap.add_argument("--unet", help="override the video model file")
    ap.add_argument("--clip", help="override the text encoder file")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--prefix", default="h3_charrep")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--dry-run", action="store_true", help="print the filled workflow, do not run")
    a = ap.parse_args()

    if not 1 <= len(a.identity) <= MAX_IDENTITY:
        sys.exit(f"give 1-{MAX_IDENTITY} --identity pictures")
    for p in [a.video] + a.identity:
        if not os.path.isfile(p):
            sys.exit(f"file not found: {p}")
    info = mp4_info(a.video)
    if not info and not (a.aspect and a.seconds):
        sys.exit(f"cannot read the size and length of {a.video}; pass --aspect and --seconds")
    seconds = a.seconds
    if seconds is None:
        if not info[2]:
            sys.exit("cannot read the clip length; pass --seconds")
        seconds = min(TRAINED_MAX_S, info[2] - a.start)
    if not TRAINED_MIN_S <= seconds <= TRAINED_MAX_S:
        sys.exit(f"--seconds {seconds:g} is outside the {TRAINED_MIN_S:g}-{TRAINED_MAX_S:g}s the reference video takes")
    if info and info[2] and a.start + seconds > info[2] + 0.05:
        sys.exit(f"--start {a.start:g} + {seconds:g}s runs past the clip's {info[2]:.2f}s")
    if a.aspect:
        try:
            w, h = (float(x) for x in a.aspect.split(":"))
        except ValueError:
            sys.exit(f"--aspect must look like 16:9, got {a.aspect!r}")
    else:
        w, h = info[0], info[1]
    size = video_size(w, h, a.megapixels)
    with open(a.prompt_file, encoding="utf-8") as f:
        prompt = f.read().strip()
    seed = a.seed if a.seed is not None else random.randint(1, 2**31 - 1)

    with open(TEMPLATE, encoding="utf-8") as f:
        graph = json.load(f)
    if a.unet:
        graph[UNET]["inputs"]["unet_name"] = a.unet
    if a.clip:
        graph[CLIP]["inputs"]["clip_name"] = a.clip
    graph[SAVE]["inputs"]["filename_prefix"] = f"video/{a.prefix}"
    args = (a.target, a.start, seconds, size, seed, a.steps, a.threshold, a.grow, a.generated_audio)

    if a.dry_run:
        build(graph, os.path.basename(a.video), [os.path.basename(p) for p in a.identity], prompt, *args)
        print(json.dumps(graph, ensure_ascii=False, indent=1))
        return

    try:
        http_json(f"{a.server}/system_stats", timeout=10)
    except (urllib.error.URLError, OSError):
        sys.exit(f"ComfyUI is not reachable at {a.server}; start it first")
    missing = missing_models(a.server, graph)
    if missing:
        sys.exit("missing on this ComfyUI: " + ", ".join(missing))
    video = upload(a.server, a.video)
    identities = [upload(a.server, p) for p in a.identity]
    build(graph, video, identities, prompt, *args)

    res = http_json(f"{a.server}/prompt", json.dumps({"prompt": graph, "client_id": uuid.uuid4().hex}).encode())
    pid = res["prompt_id"]
    print(f"queued {pid}: {size[0]}x{size[1]}, {seconds:g}s from {a.start:g}s, target {a.target!r}, "
          f"{len(identities)} identity picture(s), seed {seed}", flush=True)
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
    print(json.dumps({"prompt_id": pid, "file": dest, "seconds": seconds, "size": f"{size[0]}x{size[1]}",
                      "seed": seed, "target": a.target, "identity": a.identity,
                      "elapsed_s": round(time.time() - start)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
