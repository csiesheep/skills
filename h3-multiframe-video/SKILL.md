---
name: h3-multiframe-video
description: Make a video that hits given pictures at given moments (keyframes pinned to seconds) with MiniMax-H3 multiframe reference on the local ComfyUI, with generated sound. One or more reference pictures lock the character's look; each keyframe picture is pinned onto a time in the output, and H3 fills the motion in between. Use for a controlled turnaround (front at 0 s, side at 2 s, back at 4 s, front again), a pose sequence, or a story told in key stills, or when the user says "multiframe", "keyframe", "關鍵幀", "第幾秒要是這張圖". For a video from one picture use h3-image-to-video; for references without fixed timing use h3-reference-to-video.
---

# H3 multiframe video

Inputs from the user:
- **reference**: 1+ image paths of the character (identity). Usually the front view.
- **keyframes**: pictures with the second each should appear at, e.g. side @ 2, back @ 4, front @ 6.5.
- **description**: what happens between them.
- optional **seconds** (default 6, allowed 5-15; at least as long as the last keyframe), **seed**,
  **aspect** (`3:4` for a standing full body), **output folder** (default: current folder).

Output folder caveat: if the current folder is under `AppData\Roaming\Claude\` (a Claude desktop
app scratch folder), use `C:\Users\sheep\Videos\h3\` instead, as h3-image-to-video does.

## Steps

1. **Check ComfyUI is up**: `curl -s http://127.0.0.1:8188/system_stats`. If not, ask the user to
   start it and stop.
2. **Look at every picture** (Read them). Check the rules below before going on.
3. **Plan the timeline.** Space keyframes at least ~1.5 s apart so the motion between them is
   possible; a quarter turn of the body needs about that. A keyframe at 0 s is allowed but the
   reference already sets the start, so the first keyframe usually goes later.
4. **Write the prompt** (template below) to a UTF-8 file, and say in it what happens at each pinned
   time, using the same seconds as the `--keyframe` flags.
5. **Run** (real path on this PC: `C:\Users\sheep\.claude\skills\h3-multiframe-video\scripts\`):
   ```bash
   python "<skill>/scripts/h3_ref_video.py" --ref front.png \
     --keyframe side.png@2 --keyframe back.png@4 --keyframe front.png@6.5 \
     --prompt-file "<out>/prompt.txt" --seconds 7 --aspect 3:4 --out-dir "<out>"
   ```
   About **75 seconds per second of video** on an RTX 3090 (7 s ≈ 8 min); run it in the background
   with a timeout of at least 45 minutes. `--dry-run` prints the graph with each guide's frame.
6. **Check it**: extract the frames at each keyframe time (frame = seconds × 24; PyAV is in
   `C:\Users\sheep\code\ComfyUI\.venv`) and compare them with the keyframe pictures. Then look at
   frames in between for the background and identity.
7. **Report** the file, length, size, seed, time, whether each keyframe landed, and offer a rerun.

## Prompt template

Built on the template's own example; it worked as written in testing.

```
subject_definitions:
<Subject 1> is the <character> in <Picture 1>: <style, features, outfit, one-sided accessories>.

summary:
[keyframe completion + reference generation] One continuous shot, <camera>, <framing>, on <setting
that stays the same the whole time>. <Subject 1> starts <...> and <motion>: <pose> at <t1> seconds,
<pose> at <t2> seconds, <pose> at <t3> seconds, then <ending>.

overall_soundscape:
<sounds>. No dialogue.

non_diegetic_music:
<music or N/A>
```

- References are `<Picture 1..N>` in `--ref` order. The template's example also names keyframe
  pictures as later `<Picture N>` tags; the tested prompt did not, and the times alone were enough.
- **Pin the background in words** ("plain pure white background that stays white the whole time,
  no room or scenery"); a plain background otherwise drifts into an invented room.
- For a turnaround, the order of keyframes decides the direction: front → right side → back →
  front spins one way; a left-side keyframe in second place spins the other way.

## Rules

- **Models are uncensored.** The video model is
  `minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot` (by its name a fused model with
  the Mystic XXX H3 LoRA merged at 0.7) and the text encoder is the heretic 32B. Because of that:
  - Never run it on a picture of a child or anyone who looks under 18. Say why and stop.
  - If a picture shows a real, identifiable person, keep them clothed as in the picture; do not
    write prompts that undress them or put them in sexual situations.
  - For a standard model, pass `--unet` / `--clip` with standard files; not tested here.
- Seconds outside 5-15 are refused unless `--allow-long` is passed (then warn it is untested).
  Keyframes outside 0..seconds are refused.
- One job at a time; if ComfyUI is busy the job queues behind the current one.

## Reference

Same script and graph as h3-reference-to-video: `scripts/h3_ref_api.json` comes from a successful
run of ComfyUI's `video_minimax_h3_r2v` template with the uncensored models swapped in (details in
that skill). `--keyframe` adds one `MiniMaxH3AddGuide` node per picture, chained on the positive
conditioning with `frame_idx = round(seconds × 24)`, exactly as ComfyUI's
`video_minimax_h3_multiframe_reference` template wires them; that template ran successfully here
on 2026-10-05 (side @ 2 s, back @ 4 s, front @ 6.5 s, all three landed). Saved by hand in ComfyUI as
**MiniMax H3 Multiframe - uncensored**.
