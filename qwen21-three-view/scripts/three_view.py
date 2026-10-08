"""Front / side / back views of one character from one image, with Qwen Image 2.1 on the local ComfyUI.

Uploads the image, fills workflow_<variant>_api.json with one prompt per view (3 or 5 views, full
body or head only), seed and settings, submits it, waits, and copies the PNGs to --out-dir.
Standard library only (Pillow is used for the contact sheet when it is installed).

Example:
  python three_view.py --image photo.jpg --subject "Photorealistic photo. A young woman with ..." \
      --front-extra "The tote bag hangs on her right shoulder, which appears on the left side of the image." \
      --back-extra "Long straight black hair down her back. The tote bag appears on the right side of the image."
  python three_view.py --image photo.jpg --subject-file subject.txt --views 5 --framing head
"""
import argparse
import json
import mimetypes
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
# View sets, in turning order. "side" is the right profile (the character faces the right of the
# image, so its own right side is toward the camera); "side_left" the opposite; "threequarter" is a
# 45-degree turn on the way from the front to the right profile.
VIEW_SETS = {"3": ("front", "side", "back"),
             "5": ("front", "threequarter", "side", "back", "side_left")}
# One branch per view in the graph: encoder 10+i, sampler 20+i, decode 30+i, save 40+i.
BRANCH = ("10", "20", "30", "40")

# Angle instructions. The full-body front / side / back wording held up in testing (cartoon bust,
# standing photo, seated top-down photo): "squarely facing" fixes the 3/4 drift a turned source pose
# causes, and naming the image side the character faces stops the model flipping profiles.
ORIENT = {
    "full": {
        "front": "from the front view: standing, body and face squarely facing the camera, shoulders level",
        "threequarter": "from a three-quarter view: standing, body and face turned 45 degrees toward the right "
                        "side of the image, both eyes still visible",
        "side": "from the right side view: standing, exact 90-degree profile, facing to the right of the image",
        "side_left": "from the left side view: standing, exact 90-degree profile, facing to the left of the image",
        "back": "from the back view: standing, body squarely facing away from the camera, face not visible, "
                "shoulders level",
    },
    "head": {
        "front": "from the front view: face and shoulders squarely facing the camera, head level",
        "threequarter": "from a three-quarter view: head and shoulders turned 45 degrees toward the right side "
                        "of the image, both eyes still visible",
        "side": "from the right side view: exact 90-degree profile of the head, facing to the right of the image",
        "side_left": "from the left side view: exact 90-degree profile of the head, facing to the left of the image",
        "back": "from the back view: the back of the head and shoulders, squarely facing away from the camera, "
                "face not visible",
    },
}
SHOT = {"full": "eye-level shot, full body, character reference sheet on a plain white background. ",
        "head": "eye-level shot, head-and-shoulders close-up portrait, character reference sheet on a plain "
                "white background. "}
FRAME = {"full": "Framed tightly: the full body fills the frame from head to shoes. ",
         "head": "Framed tightly: the head and the top of the shoulders fill the frame, nothing below the chest. "}
KEEP = "Keep the identity, face, hairstyle, outfit, materials and style exactly the same. "
KEEP_BACK = "Keep the identity, hairstyle, outfit, materials and style exactly the same. "

# Loader node and the input that names its file, used for the missing-model check.
LOADERS = {"UNETLoader": "unet_name", "UnetLoaderGGUF": "unet_name",
           "CLIPLoader": "clip_name", "VAELoader": "vae_name"}


def build_prompts(noun, subject, views, framing, extra):
    subject = subject.strip().rstrip(".") + ". "
    out = {}
    for v in views:
        keep = KEEP_BACK if v == "back" else KEEP
        e = (extra[v].strip().rstrip(".") + ". ") if extra.get(v) else ""
        angle = f"Show the same {noun} from <image1> {ORIENT[framing][v]}, {SHOT[framing]}"
        out[v] = (angle + FRAME[framing] + keep + e + subject).strip()
    return out


def build_branches(graph, views, prompts, resolution, seed, steps, cfg, stem):
    """Replace the template's view branches with one branch per view (in place); {view: save node id}."""
    template = {k: json.dumps(graph[k]) for k in BRANCH}
    for k in [k for k in graph if 10 <= int(k) < 50]:
        del graph[k]
    save = {}
    for i, v in enumerate(views):
        enc, smp, dec, out = (str(int(b) + i) for b in BRANCH)
        graph[enc] = json.loads(template["10"])
        graph[enc]["inputs"].update(prompt=prompts[v], resolution=resolution)
        graph[smp] = json.loads(template["20"])
        graph[smp]["inputs"].update(seed=seed, steps=steps, cfg=cfg, positive=[enc, 0], negative=[enc, 1],
                                    latent_image=[enc, 2])
        graph[dec] = json.loads(template["30"])
        graph[dec]["inputs"]["samples"] = [smp, 0]
        graph[out] = json.loads(template["40"])
        graph[out]["inputs"].update(images=[dec, 0], filename_prefix=f"three_view/{stem}_{seed}_{v}")
        save[v] = out
    return save


def http_json(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def upload(server, path):
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        payload = f.read()
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
        if not key:
            continue
        info = http_json(f"{server}/object_info/{node['class_type']}")
        if not info:
            missing.append(f"node {node['class_type']} (custom node pack not installed)")
            continue
        options = info[node["class_type"]]["input"]["required"][key][0]
        if node["inputs"][key] not in options:
            missing.append(node["inputs"][key])
    return missing


def contact_sheet(src, files, dest):
    try:
        from PIL import Image
    except ImportError:
        return None
    h = 640
    ims = [Image.open(p).convert("RGB") for p in [src] + files]
    ims = [im.resize((max(1, int(im.width * h / im.height)), h)) for im in ims]
    sheet = Image.new("RGB", (sum(im.width for im in ims) + 8 * (len(ims) - 1), h), "white")
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width + 8
    sheet.save(dest)
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True)
    ap.add_argument("--subject", help="who/what to draw: style, hair, outfit, accessories, expression")
    ap.add_argument("--subject-file", help="UTF-8 file holding --subject (use for non-ASCII text)")
    ap.add_argument("--views", choices=sorted(VIEW_SETS), default="3",
                    help="3: front, right profile, back; 5: adds a 3/4 view and the left profile")
    ap.add_argument("--framing", choices=("full", "head"), default="full", help="full body, or head and shoulders")
    ap.add_argument("--extra", action="append", default=[], metavar="VIEW=TEXT",
                    help="a sentence for one view only, e.g. 'side_left=No earring on this ear'; repeat")
    ap.add_argument("--front-extra", default="", help="front-only sentence, e.g. which side a one-sided accessory is on")
    ap.add_argument("--side-extra", default="", help="right-profile-only sentence")
    ap.add_argument("--back-extra", default="", help="back-only sentence: hair from behind, one-sided accessories")
    ap.add_argument("--noun", default="person", help="'person' for photos, 'character' for drawings")
    ap.add_argument("--variant", choices=("standard", "uncensored"), default="standard")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--steps", type=int, default=15)
    ap.add_argument("--cfg", type=float, default=1.0)
    ap.add_argument("--resolution", type=int, default=1280)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds to wait for the job")
    ap.add_argument("--dry-run", action="store_true", help="print the prompts and filled workflow, do not run")
    a = ap.parse_args()

    subject = a.subject
    if a.subject_file:
        with open(a.subject_file, encoding="utf-8") as f:
            subject = f.read()
    if not subject:
        sys.exit("--subject or --subject-file is required")
    if not os.path.isfile(a.image):
        sys.exit(f"image not found: {a.image}")

    views = VIEW_SETS[a.views]
    extra = {"front": a.front_extra, "side": a.side_extra, "back": a.back_extra}
    for item in a.extra:
        view, sep, text = item.partition("=")
        if not sep or view not in views:
            sys.exit(f"--extra must be VIEW=TEXT with VIEW one of {', '.join(views)}; got {item!r}")
        extra[view] = text
    seed = a.seed if a.seed is not None else random.randint(1, 2**31 - 1)
    prompts = build_prompts(a.noun, subject, views, a.framing, extra)
    with open(os.path.join(HERE, f"workflow_{a.variant}_api.json"), encoding="utf-8") as f:
        graph = json.load(f)
    stem = os.path.splitext(os.path.basename(a.image))[0]
    save_node = build_branches(graph, views, prompts, a.resolution, seed, a.steps, a.cfg, stem)

    if a.dry_run:
        print(json.dumps({"seed": seed, "views": list(views), "framing": a.framing, "prompts": prompts,
                          "graph": graph}, ensure_ascii=False, indent=1))
        return

    try:
        http_json(f"{a.server}/system_stats", timeout=10)
    except (urllib.error.URLError, OSError):
        sys.exit(f"ComfyUI is not reachable at {a.server}; start it first")
    missing = missing_models(a.server, graph)
    if missing:
        sys.exit("missing on this ComfyUI: " + ", ".join(missing))

    graph["5"]["inputs"]["image"] = upload(a.server, a.image)
    res = http_json(f"{a.server}/prompt", json.dumps({"prompt": graph, "client_id": uuid.uuid4().hex}).encode())
    pid = res["prompt_id"]
    print(f"queued {pid} (seed {seed}, variant {a.variant})", flush=True)

    start = time.time()
    while True:
        hist = http_json(f"{a.server}/history/{pid}").get(pid)
        if hist and hist.get("status", {}).get("completed"):
            break
        if hist and hist.get("status", {}).get("status_str") == "error":
            msgs = [m for m in hist["status"].get("messages", []) if m[0] == "execution_error"]
            sys.exit("ComfyUI error: " + (msgs[0][1].get("exception_message", "").strip() if msgs else "unknown"))
        if time.time() - start > a.timeout:
            sys.exit(f"timed out after {a.timeout}s; job {pid} may still finish in ComfyUI")
        time.sleep(5)

    os.makedirs(a.out_dir, exist_ok=True)
    saved = []
    for v in views:
        img = hist["outputs"][save_node[v]]["images"][0]
        q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
        dest = os.path.join(a.out_dir, f"{stem}_{seed}_{v}.png")
        with urllib.request.urlopen(f"{a.server}/view?{q}", timeout=120) as r, open(dest, "wb") as f:
            f.write(r.read())
        saved.append(dest)
    sheet = contact_sheet(a.image, saved, os.path.join(a.out_dir, f"{stem}_{seed}_sheet.png"))
    print(json.dumps({"seed": seed, "variant": a.variant, "seconds": round(time.time() - start),
                      "files": saved, "sheet": sheet, "prompts": prompts}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
