---
name: ghost-reel
description: Make the Reel full of a finished ghost comic — the whole comic as one 9:16 video of about 80 to 95 seconds with camera moves, effects, subtitles, H3 moving panels, music and sound effects mixed to -14 LUFS — from a shot list per comic (reels/shots.json), in the 鬼唱詩 folder contract. Drafts the shot list from the comic's board (cold open, reveal, ending marked), plans and runs the H3 moving panels on the local ComfyUI, renders V3 電影感 (the main version) or V1 漫動畫, and writes the mp4, a cover, a contact sheet, a 720p copy under 10 MB and a QC report. Use whenever the user wants a Reel full, 整篇影片, 完整版 Reel, 影片版, a video of the whole comic, a Reel for YouTube Shorts / TikTok / Facebook from a comic, the V3 or V1 version, moving panels for a Reel, or to change a Reel's subtitles, timing, music or sounds, even if they only say "做 reel" for a comic that is finished. Not for teasers (ghost-comic `reel teaser`), drawing the comic (ghost-comic), numbering or captions (ghost-pack), or posting (ghost-post).
---

# Ghost reel

The third of five skills (plan: Obsidian `Projects/ghost story/ghost story pipeline.md`):

```
ghost-story → ghost-comic → ghost-reel → ghost-pack → ghost-post
                            ↑ this skill: the Reel full, no number in it
```

Built from the prototype that made 第 2 首〈半夜叫我全名的人〉's V3 on 2026-10-20 (the owner's review rounds are in
`Projects/ghost story/ghost story reel full.md`), then generalised: what was a Python file per comic is now
`reels/shots.json`, and the engine reads the brand file for the seal, handle and disclosure.

**No number inside a video** (owner, 2026-10-20): the title card says only 「鬼唱詩」; the number is in captions,
which ghost-pack writes. The video can be posted in any order.

## Inputs and outputs

In the story folder (`C:/Users/sheep/Pictures/gui_chang_shi/stories/<name>/`, folder contract in the README there):

| Reads | Writes |
|---|---|
| `comic/board.json` with the reveal panel marked `"reveal": true`, `comic/choices.json`, `comic/out/panels/` | `reels/shots.json` (draft.py; then edited by hand) |
| `story.md` (to understand the story; nothing parses it) | `reels/clips/<prefix>_<panel>.mp4`, their `_prompt.txt`, `src/`, `plan.json` (clips.py) |
| brand: `brand/brand.json`, `brand/music/*.flac`, `brand/sfx/*.flac` | `reels/full_v3_cinema/full_v3_cinema.mp4`, `_cover.jpg`, `_frames.jpg`, `_preview720.mp4`, `_qc.txt` (make.py) |

The silent render is kept in `drafts/reels/_work/` so a sound-only change re-renders in seconds (`--reuse`).

## Steps

Scripts are in `<skill dir>/scripts/`; run them with `py -X utf8`. ghost-comic must sit next to this skill (the
engine draws panels with its `manga.py`).

1. **Draft the shot list.** `draft.py <story>` writes `reels/shots.json` from the board: cold open on the hook
   panel before the reveal, title card, every lettered panel in reading order trimmed to about 85 s, the reveal
   (black, stinger, shake, music ducked) and the ending (darken, riser, stinger). It refuses to overwrite an existing
   shot list (`--force` to start over) and refuses a board with no reveal mark.
2. **Edit it as a director, with the story open.** The draft knows panels, not the story. On 〈阿嬤說我後面跟了三個人〉
   it kept every speech panel and dropped the narration that carries the plot (the three patients who died on her
   shift). Read `story.md` and the pages, then:
   - choose the beats a stranger needs to follow the story and feel the turn; cut the rest. 80 to 95 s.
   - one short subtitle per shot (at most about 18 characters a line; the engine wraps), in the story's words,
     spoken lines in 「」; no subtitle where the picture says it.
   - the cold open: the strangest line of the first half, said over its panel, before the title. Never the reveal.
   - the reveal gets about 5 s and, if the picture needs it, the one line that makes it land.
   - check every crop: a 9:16 frame cut from a wide or square panel misses the subject unless the panel's focus
     says where it is. On 〈阿嬤〉's first render three shots missed: p8 went black (the grandmother at the edge), p7
     showed her son under 「陳阿嬤」, p17 showed a wall under 「王伯伯」. Before rendering, look at each panel with an
     x grid and set `"focus": [x, y]` on the subject (p7 0.27, p8 0.66, p17 0.36); prefer `push` to `pan_rtl` when
     the subject is small. After rendering, the frames sheet and qc.py's "black" line catch what was missed.
   - `v3_beds` from the setting (a hospital: a drone and a heartbeat near the end; a mountain: wind and insects);
     `music` from `brand/music` (rotate tracks between comics).
   `story.py`'s docstring lists every key and option. `make.py <story> --check` validates it.
3. **Moving panels (H3).** `clips.py plan <story> [--panels p1,p8,...]` crops the chosen panels 9:16 and drafts a
   prompt per panel; the default pick is the cold open, the establishing panel, the panel before the reveal, the
   reveal, the ending and the widest others (6). **Rewrite every prompt**: what moves (wind, light, cloth, breath,
   a slow push), black-and-white manga line art kept, faces kept still. Avoid face close-ups: faces melt. Then,
   with ComfyUI up, `clips.py run <story>` (about 3 minutes per 5-second clip, in the background; it resumes after a
   crash). Look at each clip (a contact sheet of a frame every second or so): on 〈阿嬤〉 five of six were usable; a
   blanket turned into rippling water (p28, left static) and the cold-open room drifted toward grey rendered shading
   with a touch of colour. Redo a bad one with `--only pX --seed N` after deleting it, or leave that shot static.
   Put `"clip": "reels/clips/<prefix>_<panel>.mp4"` on those shots, with `"mono": true` when H3 let colour in.
4. **Render.** `make.py <story> --version v3` (8 to 11 minutes; background). Then look at `_frames.jpg` (every word
   inside the box the apps leave free, y 270–1470, x 90–960; nothing spoils the ending in the first seconds) and read
   `_qc.txt` (no black or still stretch over 3 s, no silence, loud enough). Send the owner `_preview720.mp4` and the
   frames sheet; the owner listens with sound before it is posted.
5. **Changes.** Subtitle, timing, picture: edit shots.json and render again. Music or sound only: `--reuse`.

## What the engine does (scripts/reel.py, versions.py, sfx.py)

- Panels upscaled 2× and sharpened; screen and phone lettering drawn back into the picture.
- Camera: push, pull, pan_rtl, pan_down, static, snap. Effects: night tint, pulse (heartbeat vignette), chroma,
  darken, shake, glitch, fadein, film grain on V3.
- V3 電影感: full-screen moving shots, few subtitles on a dark strip, voices as words in the frame, H3 clips played at
  natural speed (slowed if the shot is longer). V1 漫動畫: the picture above, bubbles popping in order, narration
  under it. V2 說書快剪 (big captions) is shelved but still renders.
- Sound: generated brand samples (`brand/sfx`, Stable Audio 3 workflows in `assets/sa3_workflows/`) over synthesised
  fallbacks, music from `brand/music` (ACE-Step workflows in `assets/ace_m*.json`), ducked under marked shots,
  mixed and normalised to -14 LUFS; video H.264 capped at 10 Mbps.

## Improvements not done yet

From the owner's list (reel full note, 「可以再改進的地方」): an anime upscaler for sharper panels (needs the owner's
consent to download a model), voice-over, a loop from the last shot back to the first, A/B openings as trial Reels,
faster rendering, the weekly YouTube compilation.
