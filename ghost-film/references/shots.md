# shots_vN.json

Top level:

| key | meaning |
|---|---|
| `out` | output folder name under `out/` and the mp4's name |
| `title` | the story title: title cards and the animated title shot (`title_fx`) |
| `music`, `music_gain`, `music_level` | score file (relative to reel/ or brand/music), its level, 2-s RMS leveling |
| `duck` | music level while someone speaks (0.5 = half) |
| `music_cuts` | `[[a, b], ...]` absolute seconds where the music is silent; prefer a shot's `music_cut`, which follows cuts |
| `amb_gain` | default level of each clip's own sound |
| `vo_gain`, `vo_speed` | voice level; voice tempo (atempo, pitch kept) |
| `lead`, `gap`, `tail` | default seconds before the first line, between lines, after the last |
| `min_speed` | slowest a clip may play before it holds its last frame (0.35) |
| `sub_y`, `sub_size` | subtitle height (fraction of the frame) and size |
| `vo_picks` | file in vo/ mapping line ids to takes (picks.json) |
| `end_question` | the end card's comment prompt |

A shot:

| key | meaning |
|---|---|
| `id` | name in the timeline |
| `clip` / `still` / `clip0` | an H3 clip; a still; a clip's first frame as a still |
| `offset`, `speed`, `max_t`, `min_speed` | clip start, forced speed, last usable second, slowest speed |
| `lines` | `["N01", {"clip_speech": [a, b], "text": "「…」"}]`: narrator line ids, or speech inside the clip (its own lip sync) |
| `dur` / `min` | fixed length / shortest length; otherwise the lines set it. A fixed `dur` shorter than its line lets the voice and subtitle run on over the next shot |
| `lead`, `gap`, `tail` | per shot; for a dialogue clip `lead` = speech start − `offset` |
| `motion`, `focus`, `amt`, `zoom` | push / pull / static / snap, centre, amount, start zoom (crops edges away) |
| `lift`, `tint`, `grain`, `vig` | gamma (< 1 brightens), RGB multiplier, grain, vignette |
| `fx` | ghost-reel effects: shake, negflash, static, vhs, flicker2, darken … |
| `sfx` | `[[name, at, gain]]`: a ghost-reel sfx.py name, or `"file:<path>"` (RMS-normalised over the whole file, ×gain, 1.2 s fade-out: trim long files first) |
| `music_cut` | `[a, b]` seconds of this shot (negative = from its end; `[-1.5, 0]` = the last 1.5 s) with no music and no room sound: a real silence before a scare |
| `amb` | this clip's own sound level |
| `tag`, `tag_sec` | a name plate for a speaker the first time we see them |
| `title_fx`, `title_fx_dur` | the animated title (1, 2 or 3 from title_fx.py) over this shot |
| `nosub`, `big`, `sub_y` | no subtitles; large centred subtitles; subtitle height |
| `scene`, `match` | a scene name: shots that follow each other with the same `scene` are colour-matched to the group's median (`match_strength` at the top level, default 0.7, 0 = off); `"match": false` leaves one shot alone (the lights come on). Shots with no `scene`, a `ghost_blend` or an end card are never touched |
| `ghost_blend` | 若隱若現: `{"mode": "curve", "curve": [[t, a], ...], "ref_t", "region": [x0,y0,x1,y1], "feather", "outside_ref", "tint", "scale", "anchor"}` — the ghost shows only where the clip differs from its empty frame at `ref_t`, at the opacity curve; `scale` shrinks it about `anchor` |
| `theme`, `theme_at`, `theme_gain` | a music file that starts with this shot (the end theme) |
| voice over a muted clip | `"amb": 0, "theme": "clips/line.wav", "theme_at": 0.3, "lines": [{"sub": "「…」", "dur": 1.6}]`: a line spoken by speak.py when H3 cannot say it |
| `end`, `bg_clip`, `bg_t`, `bg_zoom` | the end card, over a darkened frame of a clip |

A line id can reuse part of another line's take: add it to vo/script.json with the shorter text, to picks.json with
the same file, and to spans.json with the start of the kept words (ASR word times). render.py trims to the span.

## clip_notes.json and make_shots.py (assets/example_*)

`clip_notes.json` holds what was learned by looking at each clip, keyed by a source name the plan uses:

| key | meaning |
|---|---|
| `clip` | the picked seed's file |
| `offset`, `max_t`, `zoom`, `focus`, `motion`, `amt`, `lift`, `tint`, `amb`, `speed` | copied onto the shot |
| `speech` | `[a, b]`: where the clip's own lip-synced line starts and ends (words.py plus an energy read) |
| `me_at` | in a two-person clip, the second at which the other person's mouth starts to move: a narrator-voice take is laid there |
| `lead`, `tail` | seconds kept before the first line and after the last |

`make_shots.py`'s plan is one row per shot: `(shot id, source, lines, extra keys)`. `lines` is a list of narrator
ids, `"say"` (the clip's own line, text from `SAY`), or a tuple for a two-person clip: `("say", "M1")` when the
clip's speaker goes first, `("M2", "say")` when the narrator-voice line goes first; the script works out `offset`,
`lead` and `gap` from `speech`, `me_at` and the take's length so both lines sit on their lip movement.
The same clip used twice in a row (a rise, then a fast push-in) is two sources pointing at one file with touching
`offset` / `max_t` and the same `zoom` and `focus`.
