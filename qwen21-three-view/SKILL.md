---
name: qwen21-three-view
description: Turn one image of a person or character into a front / side / back turnaround (three views on a white background, or five with a 3/4 view and the left profile; full body or head only) with Qwen Image 2.1 on the local ComfyUI, e.g. as reference frames for video generation. Works from photos and drawings, standing or seated, and keeps identity, outfit and one-sided accessories consistent across views. Use whenever the user gives an image and wants other angles or directions of the person in it, a character turnaround / reference sheet / 三視圖 / 正面側面背面 / 轉身參考圖 / "generate different directions of this person", "head turnaround", "5 views", 頭部三視圖, even if they do not name Qwen or ComfyUI.
---

# Qwen 2.1 three-view

One image in, three PNGs out by default: front, right-side profile, back. Full body, standing,
plain white background, about 1120×1472. A run takes about 2–3 minutes on an RTX 3090.

Two options change that:
- `--views 5`: front, 3/4 (turned toward the right of the image), right profile, back, left
  profile, in turning order. About 5–5.5 minutes (321 s and 317 s in testing).
- `--framing head`: head and shoulders only, same angles. The output keeps the source's shape
  (a square source gives 1280×1280).

Inputs from the user:
- **image**: a file path (png / jpg / webp) with one person or character in it.
- optional: what to change (smiling, standing instead of sitting, drop the bag), **views** (3 or
  5), **framing** (full or head), **seed**, **output folder** (default: current folder),
  **variant** (see Rules).

Output folder caveat: if the current folder is under `AppData\Roaming\Claude\` (a Claude desktop
app scratch folder), write to `C:\Users\sheep\Pictures\three_view\` instead, as the
h3-image-to-video skill does; Python may not see files the app writes there.

## Steps

1. **Check ComfyUI is up**: `curl -s http://127.0.0.1:8188/system_stats`. If it fails, tell the
   user to start ComfyUI and stop.
2. **Look at the image** (Read it). Note the style (photo or drawing), hair, every clothing item
   with its colour, shoes, accessories, and which side each one-sided accessory is on.
3. **Write the subject description** (template below) and the per-view extras for one-sided
   accessories. The script adds the angle instructions itself; you only describe the subject.
4. **Run** (use the real path; on this PC the skill lives in `C:\Users\sheep\.claude\skills\`):
   ```bash
   python "C:\Users\sheep\.claude\skills\qwen21-three-view\scripts\three_view.py" \
     --image "<image>" --subject-file "<out>/subject.txt" --noun person \
     --front-extra "..." --back-extra "..." --out-dir "<out>"
   ```
   Add `--views 5` and / or `--framing head` when asked. Per-view sentences: `--front-extra`,
   `--side-extra` (right profile), `--back-extra`, and `--extra VIEW=TEXT` for any view
   (`threequarter`, `side_left`).
   Use `--noun character` for drawings. Put the subject in a UTF-8 file when it has non-ASCII
   text. `--dry-run` prints the three full prompts without running. Run it in the background
   if the tool allows, with a timeout of at least 10 minutes.
5. **Check the result, zoomed in.** The script writes `<stem>_<seed>_<view>.png` per view
   and a `_sheet.png` next to the source. Look at the sheet, then crop the heads: earrings and
   bags are where it goes wrong, and they are too small to judge at sheet size. Check:
   front squarely facing, side is a true profile facing right (side_left facing left), back
   shows no face, every
   one-sided item on the correct side (rule below), face recognisably the same person.
6. **Report** the three paths, the seed, the time, and anything that came out wrong. If one
   view failed, rerun with another `--seed`; the views share a seed but are sampled
   independently, so a new seed redraws all three.

## Subject template

One paragraph, in English (the prompts are English; Chinese works but was not tested):

```
<Photorealistic photo, soft even studio light. | Flat hand-painted 2D cartoon illustration.>
A <young woman / girl / man ...> with <hair: length, colour, cut, bangs>,
<top>, <outer layer>, <bottoms>, <socks / shoes>, <accessories>.
<Expression if wanted, e.g. smiling.> Standing upright, arms relaxed at her sides.
No text, no logo.
```

- Name the source's style in the first sentence; "keep the style the same" alone drifted.
- Say "standing upright" even for a seated source; it converts cleanly.
- Leave out background, pose details and props you want gone (phone in hand, chair, logo).
- The back view reuses the same paragraph; add what the back looks like with `--back-extra`
  ("Long straight black hair down her back.").
- For `--framing head`, describe only what is in a head-and-shoulders shot (hair, face,
  earrings, collar and top) and drop the shoes and "standing upright".

## One-sided items: the left/right rule

The model flips one-sided accessories (one earring, a bag on one shoulder) unless you say
which side of the **image** they are on. Work it out from the character's own side:

| Character's own side | front | threequarter | side (right profile) | back | side_left |
|---|---|---|---|---|---|
| right (e.g. hoop in right ear) | image **left** | visible, turned toward the camera | visible (we see her right side) | image **right** | hidden (far side) |
| left | image **right** | partly hidden | hidden | image **left** | visible |

So for a bag on her right shoulder:
- `--front-extra "The tote bag hangs on her right shoulder, which appears on the left side of the image."`
- `--back-extra "The tote bag hangs on her right shoulder, which appears on the right side of the image."`

For one earring, also say the other ear has none: "a single gold hoop on the character's right
ear only; the ear on the left side of the image has no earring". With this wording an earring
test went from both ears in every back view to 12/12 correct. The 5-view runs (one head-only
cartoon with one earring, one full-body photo with a bag on one shoulder) got the item right in
all 10 views with extras written from this table, e.g.
`--extra "side_left=The visible ear has no earring"` or
`--extra "side_left=The tote bag hangs on her right shoulder, the far shoulder, mostly hidden behind her body"`.

Known weak spot: the 3/4 view can come out shallower than 45 degrees (about 25-30 degrees on the
photo test); this graph is an instruction edit without a camera-angle LoRA, so angles between
the cardinal views are approximate.

## Settings and why

Defaults in the script came from a sweep on a real photo (2026-10-05):

| Setting | Default | What the sweep showed |
|---|---|---|
| steps | 15 | Same look as 25 and 35, about 40% faster than 25. |
| cfg | 1.0 | 2.5–4 squares up the pose but "beautifies" the face away from the person, at 1.6× the time. At cfg 1 the negative prompt is ignored, so do not rely on it. |
| resolution | 1280 | Closest face likeness and cleanest front/back; output ~1120×1472. 768 is fast but soft. |

Change them only when the user asks; `--steps`, `--cfg`, `--resolution` are there for that.

## Rules

- **Variant**: use `standard` unless the user asks for `uncensored`. Both gave nearly the
  same images on ordinary subjects (the uncensored one runs ~25% faster here). Never use
  `uncensored` on a photo of a child.
- If the image shows a real, identifiable person, keep them clothed as in the source; do not
  write prompts that undress them or put them in sexual situations.
- One job at a time; if ComfyUI is busy the job queues behind the current one.

## Setup and reference

Models (the script refuses with a list if any is missing):

| Variant | Image model | Text encoder | VAE |
|---|---|---|---|
| standard | `qwen_image_2.1_int8_convrot.safetensors` (UNETLoader) | `qwen3vl_8b_int8_convrot.safetensors` | `qwen_image_2.1_vae_bf16.safetensors` |
| uncensored | `qwen-image-2.1-UC-Q8_0.gguf` (UnetLoaderGGUF, needs ComfyUI-GGUF) | `qwen3-vl-8b-heretic-1.3.0_fp8_e4m3fn.safetensors` | same |

Standard files: <https://huggingface.co/Comfy-Org/Qwen-Image-2.1> (`diffusion_models/`,
`text_encoders/`, `vae/`). Heretic encoder: <https://huggingface.co/DreamFast/Qwen3-VL-8B-Heretic-1.3.0>
(`comfyui/` folder; its GGUFs have no vision tower and will not work, because the encoder
must see the image). The text encoder must be a Qwen3-VL **8B**: a 32B one fails with
`expected input with shape [*4096], but got ... 5120`.

`scripts/workflow_<variant>_api.json` are API-format graphs taken from successful runs. They
derive from the ComfyTV "Character 3-View (Qwen 2.1)" multiview workflow
(<https://github.com/jtydhr88/ComfyTV/tree/main/workflows/multiview>): three
`TextEncodeQwenImage21` instruction edits of the same source, no LoRA, all in one submission.
The script uses the first branch (nodes 10 / 20 / 30 / 40: encoder, sampler, decode, save) as a
template and lays down one branch per requested view (10+i, 20+i, ...), so the model loads once
for any number of views.
The same graphs with a usage note are saved in ComfyUI as **Qwen21 3-view - standard** and
**Qwen21 3-view - uncensored** for running by hand.
