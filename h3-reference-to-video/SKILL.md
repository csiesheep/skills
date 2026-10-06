---
name: h3-reference-to-video
description: Make a video of a character from several reference pictures (1-9: e.g. a front / side / back turnaround) with MiniMax-H3 reference-to-video on the local ComfyUI, with generated sound. The references lock the character's look while the prompt says what happens, so the character can turn, walk or move to angles no single photo shows. Use when the user has more than one picture of the same character and wants a video, says "reference to video", "R2V", "用這幾張圖做影片", "用三視圖做影片", or wants a character to stay consistent while turning around. For one picture used as the first frame, use h3-image-to-video; to pin pictures to exact moments, use h3-multiframe-video.
---

# H3 reference-to-video

Inputs from the user:
- **references**: 1-9 image paths of the same character (a three-view from qwen21-three-view is ideal).
- **description**: what should happen ("turns around once and waves", "walks toward the camera").
- optional **seconds** (default 6, allowed 5-15), **seed**, **aspect** (`3:4` for a standing full
  body; default is the first picture's shape), **output folder** (default: current folder).

Output folder caveat: if the current folder is under `AppData\Roaming\Claude\` (a Claude desktop
app scratch folder), use `C:\Users\sheep\Videos\h3\` instead, as h3-image-to-video does.

## Steps

1. **Check ComfyUI is up**: `curl -s http://127.0.0.1:8188/system_stats`. If it fails, tell the
   user to start ComfyUI and stop.
2. **Look at every reference** (Read them). Note the style, the character's features and outfit,
   and which view each picture shows. Check the rules below before going on.
3. **Write the prompt** (template below) to a UTF-8 file in the output folder.
4. **Run** (real path on this PC: `C:\Users\sheep\.claude\skills\h3-reference-to-video\scripts\`):
   ```bash
   python "<skill>/scripts/h3_ref_video.py" --ref front.png --ref side.png --ref back.png \
     --prompt-file "<out>/prompt.txt" --seconds 6 --aspect 3:4 --out-dir "<out>"
   ```
   It takes about **75 seconds per second of video** on an RTX 3090 (6 s ≈ 7.5 min), so run it in
   the background with a timeout of at least 45 minutes. `--dry-run` prints the filled graph.
5. **Check it**: pull 6-8 frames (PyAV is in the ComfyUI venv: `C:\Users\sheep\code\ComfyUI\.venv`)
   and look at them. The background, identity, and one-sided items (earring, bag) are what drift.
6. **Report** the file, length, size, seed, time, and what came out wrong if anything. Offer a
   rerun with another seed or a tweaked prompt.

## Prompt template

References are `<Picture 1>`, `<Picture 2>`, ... in the order of the `--ref` flags.

```
<style>, on <setting>. <Picture 1>, <Picture 2> and <Picture 3> show the same <character> from the
front, the right side and the back; keep the <face, hair, outfit items, one-sided accessories>
exactly as in the pictures.
<Camera: static / slow dolly in / pan>, <framing>. <What happens, in order, one main action at a time.>
Sound: <ambient and action sounds>. <Music or "No music">. No dialogue.
```

- **Pin the background in words.** A plain background drifts into an invented room unless the
  prompt says so, e.g. "on a plain pure white background that stays white the whole time, no room,
  no scenery, no objects". Saying it once in the first line was not enough in a test, and an
  "indoor" sound description appeared to pull in a living room. Keep scene words out of the sound line.
- Name what each reference shows (front / side / back); the model uses that to know what the
  character looks like from each angle.
- 5-7 seconds holds one or two actions well. Longer clips need more beats.

## Rules

- **Models are uncensored.** The video model is
  `minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot` (by its name a fused model with
  the Mystic XXX H3 LoRA merged at 0.7) and the text encoder is the heretic 32B. Because of that:
  - Never run it on a picture of a child or anyone who looks under 18. Say why and stop.
  - If a reference shows a real, identifiable person, keep them clothed as in the picture; do not
    write prompts that undress them or put them in sexual situations.
  - For a standard model, pass `--unet` / `--clip` with standard files (e.g. Comfy-Org's
    `minimax_h3_ref2va_pruned_int8_convrot` and `qwen3vl_32b_minimax_h3_nvfp4_awq`); not tested here.
- Seconds outside 5-15 are outside H3's trained range: the script refuses them unless
  `--allow-long` is passed, and then warn the user it is untested.
- One job at a time; if ComfyUI is busy the job queues behind the current one.

## Reference

`scripts/h3_ref_api.json` is the API graph from a successful run of ComfyUI's
`video_minimax_h3_r2v` template (2026-10-05) with these swaps: video model → the fused mystic07
model, VAE → `minimax_h3_video_vae_fp16`, text encoder → `qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot`,
template's Lightning LoRA switch left off (the fused model has an 8-step turbo merged in), 8 steps,
res_multistep / simple, 24 fps, ~0.6 MP. The script removes the template's image and size nodes and
wires in your references at run time. Same graph, saved by hand in ComfyUI:
**MiniMax H3 R2V - uncensored**. The script is shared with h3-multiframe-video (`--keyframe` adds
pinned frames).
