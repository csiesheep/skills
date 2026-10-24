"""一個人隨年紀長大的肖像（本機 ComfyUI，http://127.0.0.1:8188）。

    py -X utf8 portraits.py <reel>/person.json base            # 4 張基準臉候選（Z-Image-Turbo）→ <reel>/portraits/base0..3.png
    py -X utf8 portraits.py <reel>/person.json ages base2      # 以選定的基準為參考，用 Qwen Image 2.1 畫每個年紀 → age<NN>.png
    py -X utf8 portraits.py <reel>/person.json ages base2 06 30   # 只重畫某幾個年紀
    py -X utf8 portraits.py <reel>/person.json clean           # 裁掉左右各 5%、下緣 8%（模型愛在角落畫小印章）→ *_c.png

person.json（範例見 templates/person.example.json）：
  {"tag": "reel3",                       # ComfyUI 輸出子資料夾 cl_<tag>/
   "base": "Half-body portrait of a 17-year-old ...",   # 基準臉：年紀、朝代、地方、身分、髮型衣著，不寫畫風
   "ages": {"03": "Redraw the same person as a 3-year-old ...", ...},
   "base_seed": 18460, "age_seed": 46000}
畫風固定成遊戲的水墨淡彩（STYLE），讓不同人的 Reel 一致。
"""
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

API = 'http://127.0.0.1:8188'
COMFY_IN = Path('C:/Users/sheep/code/ComfyUI/input')
QWEN_WF = Path('C:/Users/sheep/.claude/skills/qwen21-three-view/scripts/workflow_standard_api.json')
STYLE = ("Traditional Chinese ink wash portrait painting with light watercolor tints on aged rice paper, visible paper grain, soft brush strokes, "
         "muted ochre, pale green and grey-blue, plain pale paper background, gentle and dignified mood.")
TAIL = "No text, no seals, no calligraphy, no signature, no watermark, no gore."


def post(obj):
    req = urllib.request.Request(API + '/prompt', data=json.dumps({"prompt": obj}).encode(), headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))['prompt_id']


def wait(pid):
    while True:
        h = json.load(urllib.request.urlopen(f"{API}/history/{pid}"))
        if pid in h:
            st = h[pid]['status']
            if st['status_str'] != 'success':
                raise RuntimeError(str(st)[:300])
            return [im for o in h[pid]['outputs'].values() for im in o.get('images', [])]
        time.sleep(2)


def fetch(im, dst):
    url = f"{API}/view?filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}"
    Path(dst).write_bytes(urllib.request.urlopen(url).read())


def zimage(text, seed, prefix):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": text}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1280, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
                                                   "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": prefix}},
    }


def qwen(ref_name, jobs, tag):
    src = json.loads(QWEN_WF.read_text(encoding='utf-8'))
    wf = {k: src[k] for k in ["1", "2", "3", "4", "5"]}
    wf["5"]["inputs"]["image"] = ref_name
    for i, (age, text, seed) in enumerate(jobs):
        e, s, d, v = (json.loads(json.dumps(src[k])) for k in ["10", "20", "30", "40"])
        e["inputs"].update(prompt=f"{text} Keep the same ink wash portrait style, same paper, same palette, half-body composition. {TAIL}", resolution=1280)
        s["inputs"].update(seed=seed, positive=[str(100 + i), 0], negative=[str(100 + i), 1], latent_image=[str(100 + i), 2])
        d["inputs"]["samples"] = [str(200 + i), 0]
        v["inputs"].update(filename_prefix=f"cl_{tag}/age{age}", images=[str(300 + i), 0])
        wf[str(100 + i)], wf[str(200 + i)], wf[str(300 + i)], wf[str(400 + i)] = e, s, d, v
    return wf


def main():
    person_path = Path(sys.argv[1]).resolve()
    cmd = sys.argv[2]
    pj = json.loads(person_path.read_text(encoding='utf-8'))
    out = person_path.parent / 'portraits'
    out.mkdir(exist_ok=True)
    tag = pj.get('tag', person_path.parent.name)
    if cmd == 'base':
        pids = [post(zimage(f"{pj['base']} {STYLE} {TAIL}", pj.get('base_seed', 18460) + i, f"cl_{tag}/base{i}")) for i in range(4)]
        for i, pid in enumerate(pids):
            fetch(wait(pid)[0], out / f'base{i}.png')
            print('base', i)
    elif cmd == 'ages':
        base = sys.argv[3]
        name = f'cl_{tag}_base.png'
        shutil.copy(out / f'{base}.png', COMFY_IN / name)
        ages = sys.argv[4:] or list(pj['ages'])
        pid = post(qwen(name, [(a, pj['ages'][a], pj.get('age_seed', 46000) + int(a)) for a in ages], tag))
        for im in wait(pid):
            age = im['filename'].split('age')[1][:2]
            fetch(im, out / f'age{age}.png')
            print('age', age)
    elif cmd == 'clean':
        from PIL import Image
        for f in sorted(out.glob('*.png')):
            if f.stem.endswith('_c'):
                continue
            im = Image.open(f).convert('RGB')
            w, h = im.size
            im.crop((round(w * .05), 0, round(w * .95), round(h * .92))).save(f.with_name(f.stem + '_c.png'))
            print('clean', f.name)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
