---
name: ghost-film
description: Make a ghost story into realistic Hong Kong horror film stills and a 9:16 short video with a narrator's voice, character lines, music, sound and subtitles, all on the local ComfyUI (the uncensored Qwen Image 2.1 GGUF for the stills, MiniMax H3 for the moving shots and the voices, ACE-Step for the score). The 鬼唱詩 brand's film line, beside the manga line (ghost-comic, ghost-reel). Use whenever the user asks for 寫實劇照、電影劇照風格、港片風格的漫畫或影片, a realistic or live-action-looking comic or video of a story, 配音的短影片, 有旁白的影片, a film poster cover for a story, or to change such a video's shots, voice, music, title or cover, even if they only say "做成影片" for a story that already has film stills. Not for manga-style comics or reels (ghost-comic, ghost-reel), numbering and captions (ghost-pack-film for these videos) or posting (ghost-post).
---

# Ghost film

Built on the first full run, 第 25 首〈靠門的下鋪〉 (2026-11-06 to 11-07, about 20 owner review rounds), and refined on
〈社辦門上的氣窗〉 v1 to v11 (2026-11-08 to 11-10), posted as 鬼唱詩劇場｜第 1 部 on 2026-11-11. The working folders of
upper_bunk and grandpa_wake were deleted on 2026-11-11 to free disk; the complete reference run is now
`C:/Users/sheep/Pictures/gui_chang_shi/backlog/transom_window/film/` (screenplay, board, vo, reel with make_v10/v11.py,
make_ig.py, music/build_bed.py). Every rule below came from a round; the why is in `references/lessons.md`. Read that
file before the first H3 shot and before writing narration.

## Before starting

- **One session per story.** Story, comic and film fit in one session, but 氣窗's film alone filled a whole session
  and was compacted. If the session is long by the time the comic is done, start the film in a new session in
  `C:/Users/sheep/Pictures/gui_chang_shi`: the skills hold everything learned, the folder holds the state.
- **Disk.** One film's working files took about 26 GB (upper_bunk; grandpa_wake 10 GB unfinished), and C: was 98 %
  full with 44 GB free on 2026-11-11. Check `df -h /c` before stills; under about 40 GB free, tell the owner first.
  After a film is posted, offer (never do unasked: deleting needs the owner's yes) to remove its working files,
  keeping story.md, the screenplay, board.json and choices.json, vo script/picks, the final shot lists and scripts,
  the final `out/reel_vN/` and IG parts, the poster and `posts/`.
- **Shape.** Vertical 9:16 is the master on every platform (decided 2026-11-11): IG in parts, the Facebook Page as a
  Reel, YouTube as a normal video plus, optionally, the IG parts as Shorts for discovery. A 16:9 version cannot be
  cropped from the 9:16 film (1080×608 left); it means drawing `--wide` stills and new 16:9 clips, about double the
  GPU. Decide it before step 1, only if the owner asks or YouTube's watch time on the full video earns it.

```
ghost-story → ghost-film stills (comic pages) → ghost-film reel (this skill's video) → ghost-pack → ghost-post
                 ↑ manga.py via film.py             ↑ render.py
```

## Folder contract (one story)

```
<story>/film/                 board.json, choices.json, out/ (cast, sets, panels, pages)     film.py
<story>/film/reel_stills/     the same cells as 9:16 pages (stills_both.py)                   film.py
<story>/film/wide_stills/     the same cells as 16:9 pages, for the long video (--wide)
<story>/film/vo/              script.json (line id -> text), picks.json (line id -> take), spans.json
<story>/film/reel/            crops.json, src/, prompts/, clips/, music/, fx/ (video-only stills), shots_vN.json, out/reel_vN/
brand/music/licensed/         outside music with LICENSES.md (source, licence, date)
```

Scripts live in `<skill>/scripts/`; run them with `py -X utf8` from the folder named in each docstring.

## Steps

0. **Screenplay first.** Before any board, adapt the story into `film/screenplay.md` (`assets/example_screenplay.md`): numbered scenes (內/外, place,
   time), action in brackets, every line with its speaker (a Taiwanese line is still spoken in Mandarin in the video), the narrator as VO, a cast list and a
   **place map** (how the rooms connect, the route people walk, a sound that marks entrances, such as the screen
   door's 嘎——啪). Keep the story's backstory and flashbacks as scenes of their own, and list at the end what was
   added (a minor character, an inserted memory). Send it and wait for the owner. The first 〈幫阿公守夜〉 comic (15
   panels cut straight from the story) was rejected: 「漫畫少了很多故事的細節，像前情提要，阿公摺蓮花的背景，進出屋子的常見換的動作」;
   the comic cut from the screenplay (80 panels) read 8/10 with two blind readers.
1. **Stills, in both shapes.** Build the board from the screenplay, scene by scene (characters with features, sets;
   the page layout is free since 2026-11-07, 「漫畫分鏡不再規定一頁最多3張，請自由發揮」: one to four panels a page, sizes
   mixed, the reveal big and right after a page turn, three small panels for a routine). Render `film.py plan` and
   send it before drawing. Draw with `film.py panels`
   (uncensored Qwen 2.1 GGUF, colour kept, lettering in 微軟正黑 Light). **Then draw every panel again as a 9:16 still**:
   `stills_both.py` writes `reel_stills/` with the same prompts and references one cell per 9:16 page; run `film.py
   panels` there (owner, 2026-11-07: 「之後產生原圖時，同時產生直式跟橫式的圖。目前用橫式的圖，產生直式影片，人物會被切」). A 9:16
   crop of a landscape still cut 小傑's head and left dark bands top and bottom that read as black bars. Add `--wide`
   when a 16:9 long video is planned. Pick each panel's portrait take the same way as the landscape one (independent
   check, people's faces and heights).
   **Panels in a night story**: a cell's `look` replaces the board's style prefix (`film.py`), so daytime and
   flashback panels get a daylight look instead of the oil-lamp night. grandpa_wake's build_board.py did it with the
   board's style prefix `BASE` minus its night clause 「low light from practical sources only, deep real shadows that
   are never filled in.」, plus 「Soft natural daylight, neutral colours, no lamps lit, not night.」 (`DAYLOOK`) or
   「A memory: bright warm high-key daylight, soft and slightly faded like an old photograph, no lamps lit, not
   night.」 (`FLASHLOOK`). Check every batch with a fresh subagent and `film.py review <ids>` while the GPU draws the next;
   the checker notes, the prompt rules that came out of them, and how to fix a mouth or hide the eyes without a
   redraw are in references/lessons.md (「Comic from a screenplay」). Then the blind reader, as in ghost-comic, until
   it gets the story, every character and every speaker; fix what it trips on in the lettering first.
2. **Voice.** Write the narration in the story's words as short lines (`vo/script.json`, one id per line, 10 to 25
   characters). Voices are H3's own speech nodes (no TTS service; `speak.py`): pick a narrator among three described
   voices, then render every line with that take as the reference voice (`ref2va` model), so it stays one person.
   Check every take with `check.py` (faster-whisper large-v3-turbo) and retake or rewrite until it reads back right;
   then `spans.py` stores where speech starts and ends in each take, which render.py uses to trim. Characters' lines
   are spoken inside their own H3 clip (lip sync); find their start and end with `words.py` and an energy read.
3. **First frames and moving shots.** `crops.py` makes `src/<name>.png` from the portrait stills (zoom 1, nothing to
   cut). Write one H3 prompt per shot in `prompts/` (template in references/lessons.md: the look line, three timed
   beats, the sound, 「畫面中沒有任何文字」), run `run_clips.sh name:seconds:seed ...` in the background, one loop at a
   time, two or three seeds for anything with a body in motion. Look at every clip as a frame strip before using it.
   **Every shot is a clip**: a still with a push-in read as 「定格的圖，很奇怪」 to the owner, and so does a clip's held
   last frame (render.py warns about both). Characters speak Mandarin on screen, never H3's Taiwanese (owner,
   2026-11-08: 「台語的部份，配音很奇怪，改成說中文」). A line H3 gets wrong twice is spoken by `speak.py` over the
   muted clip instead; details in lessons.md 「Reel from a screenplay」.
   When image-to-video keeps getting an action wrong, pin both ends with `fl2va.py` (a first frame and a last frame).
   Video-only stills (a normal-feet version, a new angle, the end state for FL2VA) are drawn in `reel/fx/`, a small
   board of their own, as same-framing edits of picked stills.
4. **Music and sound.** Score: ACE-Step 1.5 (`music.py`; check with the spectrum, not ASR, which hallucinates lyrics on
   instrumentals). The 鬼唱詩 end theme is outside music the owner chose: Pixabay 〈小さなおばけのワルツ Waltz of Little
   Ghosts〉 (naginomori), first 12 s, in `brand/music/licensed/end_theme_12s.wav`. Or a bed cut from the brand's
   licensed library by situation (開場、一般生活、不安、懸疑、很緊張、餘韻; table in Obsidian `Projects/ghost story/
   ghost story music library.md`), with sections anchored to shot ids so cuts don't need re-timing; keep the hook at
   the owner's level and the music lower once the narration starts (lessons.md 「Music levels」). Sound effects:
   ghost-reel's sfx.py names (knock …), each clip's own H3 sound, and the stock picks in `brand/music/licensed/sfx/`
   as `file:` entries, trimmed into `sfx/cuts/` first; about 15 to 20 in a 5 to 6 minute reel, each tied to a shot.
5. **Shot list and render.** `shots_vN.json` (format in references/shots.md; `assets/example_shots.json` is the final
   upper_bunk cut). `render.py shots_vN.json` times every shot from its voice lines, draws one subtitle at a time on a
   dark band at 0.76 of the height, ducks music and room sound under the voice, mixes to -14 LUFS and writes
   `out/reel_vN/` (mp4, `_frames.jpg`, `_timeline.txt`); `--reuse` remixes the sound only, in about a minute.
   Before a scare, a shot's `music_cut` makes a real silence (music and room sound).
   `package.py` writes the 720p copy under 10 MB. Transcribe the mix (`check.py` style ASR on the mp4): every line
   must read back whole.
6. **Title and cover.** The title shot uses the poster title, animated (`title_fx.py`: 1 霧中浮現 is the owner's pick,
   2 訊號干擾, 3 垂吊搖晃), with the icon and 鬼唱詩 under it. The cover is a film poster (`poster.py`): the D title
   treatment (標楷, worn edges, cold glow; `scary_title.py` has A to D), a tagline at the top, and under the title one
   line only, icon + 鬼唱詩. No clear ghost and no spoiler on a poster: no reveal face, no twist line as tagline (owner,
   2026-11-10: 「poster 不要有清楚的鬼，不能爆雷」); use an ambiguous early image and a rule from the setup. For a body-horror object the owner liked a blend of the normal and the ghost version, normal
   where the light falls (`blend.py`, mode 2 光束 for 上鋪的腳).
7. **Review rounds.** Give the mp4, timeline and ASR to a fresh subagent with `references/review_brief.md` each round
   (it cannot hear: say so); it scores 1 to 10 for 「能不能直接公布」. upper_bunk went 5 → 6 → 6.5 → 7 → 7 over v1 to
   v9, then the owner's own notes drove v10 to v20. Reviewers contradict each other on taste (a bright or a dark first
   frame, a headline or none); the owner decides those. Report numbers, send the 720p file, and say plainly that the
   voice, music and lip sync need the owner's ears.
   **Polish pass** (「再打磨一次，看有沒有…不合理…不連貫…不流暢」): `review_sheets.py` and two blind reviewers, one for
   the picture and one for the text (`references/review_split.md`). Verify every claim on a full-size frame before
   acting: v10's "two extra people" were a backpack and a cabinet. Free fixes (offset, zoom, lift, a clip swap,
   subtitle text) first, regenerations as one batch.

8. **Instagram parts and packing.** Over 3 minutes (the Reels limit), cut two parts at a cliffhanger, each under
   3:00: part 1 ends on 「上集完／下集：…」 (`end_title`, `end_question`), part 2 opens on the hook flash and the
   title shot with `headline` 「下集」. The music is the full bed sliced at the same point, with `music_gain`
   rescaled (transom_window's `make_ig.py`). Each part needs its own `_preview720.mp4` (`package.py`) under 10 MB:
   that is what Claude in Chrome uploads. Then the poster (`poster.py`, two or three candidates, the owner picks) and
   ghost-pack-film for the number 「鬼唱詩劇場｜第 N 部」 and the captions. Pinterest takes videos up to 300 s, so a
   film's video pin is IG part 1 when the full cut is longer (pack_film.py picks it).

## Rules

- **One set, one architecture.** Before drawing a set, write its fixed parts as one text block (the door, the window, what
  is on that wall) and pick one inside and one outside reference picture; put the block in every still, edit and H3 prompt
  whose frame shows it, and only there. 〈社辦門上的氣窗〉 drew the door three different ways and 26 reel stills, 18 comic
  panels and their clips were redone (owner: 「教室的門一直不是很統一」). Details in lessons.md.
- The GPU is shared: run every GPU job through `scripts/polite.py` (one job at a time, submitted only on an empty
  queue), and never mix Qwen and H3 jobs; pause a clip loop with `scripts/pause.py` before a block of Qwen edits.
- The owner posts; never post. Downloads (models, packages, music) need the owner's yes first; record outside music
  with its source and licence in `brand/music/licensed/LICENSES.md`.
- No number inside the video; the end card says 本首完, 追蹤 @gui.chang.shi and a comment prompt (「你的椅子，今天在哪？」).
- The ghost changes over the video when the story allows: the feet were normal in the first third and became the
  dead grey-blue feet only at the reveal (owner, 2026-11-07: 「腳隨著影片慢慢變鬼腳」).
- When a cut removes a line, search the rest of the script for anything that depended on it (橘子 and 雞排 callbacks).
- Hidden ghosts for a rewatch must agree with the twist (outside, if she was outside all along) and be findable at 720p.
- Fiction only; no real people or places that can be identified.
