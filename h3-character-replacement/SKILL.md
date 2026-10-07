---
name: h3-character-replacement
description: Replace the person or character in a short video with a different character from 1-3 pictures, keeping the source's motion, timing and audio, with SAM3 masking plus MiniMax-H3 reference-to-video on the local ComfyUI. Use when the user gives a video clip and a picture and asks to swap who is in it, "character replacement", "換角色", "把影片裡的人換成這個角色", "replace the actor with this character", or to restyle the performer while keeping the performance. Only for footage and likenesses the user has the right to use, with the consent of every real person involved; refuses minors, sexual content of real people, and deceptive impersonation (see Rules). For a new video from pictures without a source clip, use h3-reference-to-video.
---

# H3 character replacement

Inputs from the user:
- **video**: a short clip (mp4 / mov, 2-15 s used) with one main subject to replace.
- **identity**: 1-3 pictures of the new character (one sharp, well-lit full-body picture is enough;
  a three-view from qwen21-three-view also works).
- optional: **target** (what SAM3 should find: `person` by default; `woman`, `man in red`,
  `cartoon character`...), **start** / **seconds** (part of the clip), **seed**, **output folder**.

Output folder caveat: if the current folder is under `AppData\Roaming\Claude\` (a Claude desktop
app scratch folder), use `C:\Users\sheep\Videos\h3\` instead, as h3-image-to-video does.

## Steps

1. **Check the rules below first**, from the actual pictures and a few frames of the video
   (PyAV is in `C:\Users\sheep\code\ComfyUI\.venv`; or ask the user what the clip shows).
2. **Check ComfyUI is up**: `curl -s http://127.0.0.1:8188/system_stats`. If not, ask the user to
   start it and stop.
3. **Look at the identity pictures and sample frames** (Read them). Note what the subject does,
   where it is in frame, and the new character's look.
4. **Write the prompt** (template below) to a UTF-8 file.
5. **Run** (real path on this PC: `C:\Users\sheep\.claude\skills\h3-character-replacement\scripts\`):
   ```bash
   python "<skill>/scripts/h3_charrep.py" --video clip.mp4 --identity new_look.png \
     --target person --prompt-file "<out>/prompt.txt" --out-dir "<out>"
   ```
   The size follows the clip's shape at ~0.6 MP; the length is the clip (or `--start` /
   `--seconds`). It takes about **3 minutes per second of video** on an RTX 3090 (5 s ≈ 15 min:
   the reference video costs about twice what reference pictures do), so run it in the background
   with a timeout of at least 90 minutes. `--dry-run` prints the filled graph.
6. **Check it** against the source: extract the same frame numbers from both and compare the
   pose, the timing and the identity. If the mask missed the subject or took in background, rerun
   with another `--target` wording or `--threshold`.
7. **Report** the file, size, length, seed, time, and what did not carry over.

## Prompt template

From MiniMax's reference-video prompt guide (`VIDEO_PROMPT_WRITING_GUIDE_ref_en.md` on
huggingface.co/MiniMaxAI/MiniMax-H3): an edit of a source video is tagged
`[video editing + reference generation + audio reuse]` and its summary starts with
"The target video is an edited version of <Video 1>."

```
subject_definitions:
<Subject 1> is the <new character> in <Picture 1>, <style>, with <face/hair>, <outfit items>.
<Video 1> is the source video: <what the subject does>; the subject's area is masked out in gray.
<Audio 1> is the soundtrack of <Video 1>.

summary:
[video editing + reference generation + audio reuse] The target video is an edited version of
<Video 1>. The masked subject is replaced by <Subject 1>, who performs exactly the same motion,
timing, position and camera framing: <the action>. <The background> stays as it is.

retention_analysis:
<Subject 1> (appears in [Shot 1]): attribute_transfer - <identity and outfit> replace the subject in <Video 1>.
<Video 1> (motion, timing and framing): fully_preserved - <motion, position, camera> are kept exactly.
<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the target video's complete final audio track.

detailed_description:
<style>, <setting>.
[Shot 1] <camera and framing>. <Subject 1>, <full appearance again>, <the action, in order>.

overall_soundscape:
<Audio 1> is reused as is.

non_diegetic_music:
<Audio 1> is reused as is.
```

The script puts the source audio on the output itself (pass `--generated-audio` to keep H3's).
The action and timing carried over in both test runs; the subject's size on screen depended on
the seed (a walk toward the camera stayed full-body with one seed and filled the frame like the
source with another). When framing matters, say the change in the summary and the shot line,
and try another `--seed` if it does not follow.

## Rules

This skill can put one person's identity onto another person's body in real footage, and its
default models are uncensored: the video model is
`minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot` (by its name a fused model with the
Mystic XXX H3 LoRA merged at 0.7) and the text encoder is the heretic 32B. So, before running:

- **Consent.** Real people in the source video, and real people in the identity pictures, must be
  the user or adults who agreed to this. If it is unclear, ask; if the user cannot say yes, stop.
- **No minors.** Never run it when the source video or an identity picture shows a child or anyone
  who looks under 18. Say why and stop.
- **No sexual content of real people**: do not write prompts that undress, sexualise or put a real
  person in sexual situations.
- **No deceptive impersonation**: no swaps meant to pass as a real public figure or a specific
  real person doing or saying something they did not, and no use for fraud or harassment.
- For a standard model set, pass `--unet minimax_h3_ref2va_int8_convrot.safetensors` and
  `--clip` with the standard Comfy-Org 32B encoder (`qwen3vl_32b_minimax_h3_int8_convrot`, 27 GB,
  not installed here); not tested.

## Reference

`scripts/h3_charrep_api.json` is the API graph from a successful run on 2026-10-06, rebuilt from
RunComfy's "MiniMax H3 Character Replacement" description (SAM3 masking in front of
`MiniMaxH3ReferenceToVideo`) on top of ComfyUI's `video_minimax_h3_r2v` template:
`LoadVideo` → `Video Slice` → `GetVideoComponents` → `SAM3_Detect` (model
`sam3.1_multiplex_fp16`, loaded by `CheckpointLoaderSimple`, text from its CLIP; threshold 0.5,
2 refine passes) → `GrowMask` 12 px → `ImageCompositeMasked` with a flat gray (#808080) fill →
`ImageScaleToTotalPixels` 0.6 MP → `ref_videos.ref_video_0`, with the source audio on
`ref_video_audios.ref_video_audio_0`. Identity pictures go to `ref_images`. Video VAE
`minimax_h3_video_vae_fp16`, audio VAE `minimax_h3_audio_vae_fp32`, 8 steps, res_multistep /
simple, template's Lightning LoRA switch off. How RunComfy itself composites the mask is not
published; the gray fill is this skill's choice. Saved by hand in ComfyUI as
**MiniMax H3 Character Replacement - uncensored**. Tests: a 5 s cartoon clip, the subject replaced
by a different adult cartoon character, 922 s (seed 31) and 992 s through this script (seed 77)
on an RTX 3090.
