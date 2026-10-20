# reel full (prototype)

A whole comic as one 9:16 Reel, in three versions, built for the 鬼唱詩 account on 2026-10-20 from
〈半夜叫我全名的人〉. A prototype: paths and the shot lists are still written into the files; the plan is to fold
it into `manga.py reel full` with one shot-list JSON per comic.

- `reel.py` — engine: panels (2x upscale, screen text drawn back in), camera moves, effects (flicker, heartbeat
  vignette, darken, shake, glitch, chroma), bubbles and narration boxes, big captions with red-box accents,
  subtitles, H3 clip playback, title and end cards, render, mux (H.264 capped at 10 Mbps, sound at -14 LUFS).
  `py -X utf8 reel.py v1|v2|v3 <out dir> --music <track> [--reuse]`
- `versions.py` — V1 漫動畫 (picture + popping bubbles, narration under it), V2 說書快剪 (big captions),
  V3 電影感 (full-screen moving shots, grain, few subtitles). All words inside the app-safe area
  (y 270–1470, x 90–960).
- `story_name_call.py` — the director's script for one comic: per-panel motion, effects, sounds, captions,
  hooks, which H3 clip plays where.
- `sfx.py` — synthesised sounds and a mixer; uses generated samples when present.
- `qc.py` — checks a finished video: length, size, black or still stretches, silence, loudness, first frame.
- `ace_m*.json` — ACE-Step 1.5 music workflows (three brand tracks).
- `sa3_workflows/` — minimal Stable Audio 3 workflows for the twelve sound effects (the gallery template's
  category menu has no options on this install, so these bypass it).

Write-up, review rounds and the list of improvements: Obsidian `Projects/ghost story/ghost story reel full.md`.
