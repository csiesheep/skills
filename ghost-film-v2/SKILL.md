---
name: ghost-film-v2
description: Make a ghost story into a vertical 9:16 film with a narrator's voice, character lines with moving mouths, music, sound and subtitles on the local ComfyUI (Qwen Image 2.1 stills, MiniMax H3 moving shots and voices, ACE-Step score) - a short of 3 minutes or less, or a long film of 10 minutes or more plus shorts under 3 minutes cut from it, with clips chained from the previous clip's last frame so the action never snaps back. ghost-film plus everything learned on 〈動物醫院的兩點十分〉 (2026-11-22 to 11-24); use it instead of ghost-film for every new film. Use whenever the user asks for 寫實劇照、港片風格或水墨漫畫風格的影片, 長片, 長影片加短片, 切成幾支短片, 配音的影片, 有旁白的影片, 嘴巴要動, 對嘴, a film poster cover, or to change such a video's shots, voice, music, title, end card or cover, even if they only say "做成影片" for a story that has stills or a comic. Not for manga Reels of a comic (ghost-reel), drawing the comic (ghost-comic-v2), numbering and captions (ghost-pack-film) or posting (ghost-post).
---

# Ghost film v2

**v2 = everything in ghost-film (kept word for word below, steps 0 to 8) + the long-film line (step 9) and the
rules learned on 〈動物醫院的兩點十分〉** (vet_night_xray, 2026-11-22 to 11-24: a 10:34 long film and four shorts
from a ghost-story-weitong-v4 story and its ghost-comic-v2 comic, ink-wash look). That run's whole notebook is
`references/lessons_long_film.md` (read it before step 9, and before any H3 clip of a long film); its builder scripts
are in `assets/vet_night_xray/`; its working folder is `C:/Users/sheep/Pictures/gui_chang_shi/stories/vet_night_xray/film/`
(`longcut/reel/` for the long film). Scripts are in `<skill>/scripts/` (v1's, with their paths pointing at v2) and
`<skill>/scripts/long/` (new).

**Generation runs in its own session.** When a story is approved for a film, start a new session in
`C:/Users/sheep/Pictures/gui_chang_shi` that loads this skill (`ghost-film-v2`) and does the generation; the session
that asked gets the report. One film filled two whole sessions here and was compacted twice.

Built on the first full run, 第 25 首〈靠門的下鋪〉 (2026-11-06 to 11-07, about 20 owner review rounds), and refined on
〈社辦門上的氣窗〉 v1 to v11 (2026-11-08 to 11-10), posted as 鬼唱詩劇場｜第 1 部 on 2026-11-11. The working folders of
upper_bunk and grandpa_wake were deleted on 2026-11-11 to free disk; the complete reference run is now
`C:/Users/sheep/Pictures/gui_chang_shi/backlog/transom_window/film/` (screenplay, board, vo, reel with make_v10/v11.py,
make_ig.py, music/build_bed.py); the second, 〈墾丁民宿的敲門聲〉 (第 2 部, 2:36, one cut, 2026-11-13), is
`backlog/kenting_knock/film/` (two-person dialogue clips, long FL2VA takes, a jump-scare ending). Every rule below came from a round; the why is in `references/lessons.md`. Read that
file before the first H3 shot and before writing narration.

## What it is for, and what the numbers say

The film exists to grow the 鬼唱詩 accounts: a stranger stops, watches to the end, shares or saves, follows. Judge
every choice (length, hook, where a part ends) by that, in this order: new follows, (shares + saves) / reach, average
watch time on the Instagram Reel. Numbers: Obsidian `Projects/games stats/social_posts.csv` (24 h, rows titled
鬼唱詩劇場) and `brand/taste.md`.

- 第 1 部（上）, 24 h on Instagram: 1,853 views, 59 follows, 37 shares, 16 saves, average watch 35 s. The manga Reels'
  median is 0.5 follows and 0.8 % quality, so one film part brought more follows than the manga line's best story
  (16). It is one film: a lead, not a rule. Read the newest 鬼唱詩劇場 rows before step 0 and update this list when a
  film's numbers are in.
- 第 1 部（下） got half of that (913 views, 17 follows). A second part loses half the audience, so a story that fits
  in 3 minutes is one cut (step 8), and a two-part film puts its strongest scare before the cut, not after.
- Average watch was 35 to 41 s of about 3 minutes, and 7 s on the Facebook Reel. Most viewers leave in the first
  half minute: the reveal flash, the person-plus-strange-thing first frame and the first rule of the setup all have to
  land inside it (lessons.md → 「Review rounds」, 「Scarier without new footage」).
- Threads (7 views) and YouTube (2) did nothing for the video itself; do not spend GPU on a 16:9 version for them.

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
- **Look: the film keeps the comic's look.** A story drawn with ghost-comic-v2 becomes a 水墨淡彩 film, the same
  brushwork, tints and ink-grey ghost as its comic (〈動物醫院的兩點十分〉). The realistic Hong Kong film-still look of
  steps 1 to 8 (`film.py`, the uncensored Qwen GGUF) is for a story with no comic, or when the owner asks for 寫實.
  One look for the whole film, never mixed. For an ink-wash film:
  - Every new or redrawn still (a 9:16 redraw of a wide panel, a master per camera, a same-framing edit) uses the
    comic's refs and ends its prompt with ghost-comic-v2's style text (`ink_tint.py`'s `INK` + `TINT`, written out
    as `STYLE` in `stories/vet_night_xray/comic/plan/masters3_jobs.py`).
  - `stills_both.py` runs in the comic folder and draws with ghost-comic's `manga.py`, never `film.py`: `film.py`
    switches to the realistic model.
  - Every H3 prompt starts with the look line of `scripts/long/chain.py` (`LOOK`, 「水墨淡彩漫畫風格的角色動畫，畫面維持跟
    第一幀完全一樣的筆觸、色調…」).
  - Every checker brief carries ghost-comic-v2's line: the picture is Chinese ink wash with faint tints, and a
    still that reads as watercolour illustration or photo fails.

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
   added (a minor character, an inserted memory). Write it as a film, not as a read-aloud (第 2 部's first cut was
   sent back for both): **a line said to someone in the room is dialogue with a speaker, and narration is only what
   nobody says aloud**; a scene that is one action is **one take** (mark it 「一鏡」), not a cut per sentence; and from
   the scene where the ghost is in the room, each scene says where she is and what she is doing, even when the scene
   is about something else. Write the ending as beats with seconds (lessons.md → 「The ending」).
   **Count the shots while writing**: about ten a minute at most, one take per conversation, and no picture used
   twice (第 3 部 went from 39 shots to 27 over four owner rounds: 「畫面太常切換了，多一點長鏡頭」; the cold open's
   ankle pull, repeated at the reveal, was cut). What the narration says is what the picture shows (「隔壁那床，一直
   空著」 over a closed curtain was sent back: 「場景換成照著空床」).
   **A floor plan for every room that has more than two shots**: a top-down sketch (walls, window, door, each bed
   or table, the curtain, one arrow per camera setup) drawn with PIL into `film/review/plan_<room>.png` and sent
   with the screenplay. The owner's 「平面圖對」 comes before any still of that room (lessons.md → 「第 3 部」).
   **A film that goes up whole as one Reel (3 minutes or less)** is written to `references/screenplay_short.md`
   (`assets/example_screenplay_short.md`): the time budget first (target 2:45 to 2:52, 280 to 320 characters of
   narration, seconds on every scene heading), the strongest picture with the hook as big text at second 0, the end
   promised by second 8, the first wrong thing by 0:25, the reveal held in silence instead of read aloud, and the
   last shot reusing the shot that planted the twist, with no end card. **Before the owner sees any screenplay**,
   give it with the story to a fresh subagent (ghost-story's `references/review_brief.md`, part 4), fix what comes
   back, and run a second reviewer who has seen nothing: the first draft of 〈一中街的無人拍貼店〉 ran 3:05 against a
   3:00 limit, opened on a picture too small for a phone and read its own reveal aloud, and its writer had noticed
   none of the three. Then send it, with the rounds as a table, and wait for the owner. The first 〈幫阿公守夜〉 comic (15
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
   **One master still per camera setup.** Draw the room's wide shot from the floor plan first (`fresh_draw.py`,
   four candidates, no source picture), pick it, and make every other still of that setup a same-framing edit of it
   (`edit_stills.py`: who is where, day or night). A new angle is a fresh draw from the plan, never an edit of
   another angle: an edit keeps the old perspective. 第 3 部 drew its ward stills one by one and was sent back three
   times for 「房間格局不統一」; rebuilt from one master, the layout was not mentioned again.
   **Props are fixed like sets**: one text block per prop that appears in more than one shot (the slipper, a
   bruise's finger count, glasses on or off), used in every prompt that shows it.
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
   voices, then render every line with that take as the reference voice (`ref2va` model), so it stays one person. Say in the report what the reference may control (timbre, speed) and what it must not bring (the emotion, room reverb or noise of the reference take); a reference nobody has listened to is not described from its file name.
   Submit them with `polite.py speech <jobs.json>` (Rules: the GPU is shared), with a story prefix on every take name
   (`KK_N01`). Check every take with `check.py` (faster-whisper large-v3-turbo) and retake or rewrite until it reads
   back right; then `spans2.py <PREFIX>` picks the best take per line and stores where the line starts and ends in
   it, which render.py uses to trim (ref2va takes often open with words of the reference sentence; the older
   `spans.py` only takes first word to last word of takes already in picks.json). Characters' lines
   are spoken inside their own H3 clip (lip sync); find their start and end with `words.py` and an energy read.
   When the narrator is also a character, her spoken lines are spoken inside the clip like everyone else's (since
   第 3 部: narrator-voice takes laid on her lips were sent back three times as 「像唸旁白」, also when re-recorded
   as room talk). Her talking voice then differs from the narrator's: say so in the report. `me_at` (a narrator
   take on her lip movement) is the fallback for a line H3 garbles in every take. **Run all voice jobs as one block**: mixed in
   with i2v clips they reload the models every job (50 s a clip became 110 to 280 s). A caller on a phone or a voice
   behind a door: `voice_fx.py phone=P1,P2 door=Q4` after the spans.
3. **First frames and moving shots.** `crops.py` makes `src/<name>.png` from the portrait stills (zoom 1, nothing to
   cut). Write one H3 prompt per shot in `prompts/` (template in references/lessons.md: the look line, three timed
   beats, the sound, 「畫面中沒有任何文字」). Past a dozen shots, write the prompts from a `reel/plan.py`
   (`assets/example_plan.py`, 第 2 部: the look, cast, set and light as named text blocks, one `sh(...)` row per shot,
   `plan.py prompts` and `plan.py list <round>`; pause.py reads it). Run `prompt_check.py prompts/<name>.txt:<seconds> ...` first (beats that do not add up to the clip length are cut off or slowed down; no 靜音 in the soundscape; lessons.md 「From drama-skills」), then `polite.py clips name:seconds:seed ...` in
   the background, one loop at a time (`run_clips.sh` is the same loop without the queue check: only when nothing
   else uses the GPU), two or three seeds for anything with a body in motion. Run `clip_check.py --asr` on every
   new clip first (a light jump, a cut H3 made inside the clip, speech where there should be none), then look at
   what is left as frame strips (`strips.py`, or `strips.py sheet` for both seeds of a shot on one picture): only a
   strip shows a wrong action or a movement in the wrong direction.
   **A conversation is one long take** (10 to 14 s, up to four lines, the prompt giving who speaks in which
   seconds and 「只有她的嘴在動」): five of six worked on 第 3 部 with two seeds each. H3 adds gibberish before the
   first line and after the last, and may say the first line twice: take each line's start and end from
   `words2.py`, list them as `talk` in clip_notes.json, and only those spans are heard (`assets/
   example_make_shots_long.py`). A scare from the victim's eyes continues the shot before it: its first frame is
   that clip's last frame (ffmpeg `-ss`), so no still is drawn.
   **Every shot is a clip**: a still with a push-in read as 「定格的圖，很奇怪」 to the owner, and so does a clip's held
   last frame (render.py warns about both). Characters speak Mandarin on screen, never H3's Taiwanese (owner,
   2026-11-08: 「台語的部份，配音很奇怪，改成說中文」). A line H3 gets wrong twice is spoken by `speak.py` over the
   muted clip instead; details in lessons.md 「Reel from a screenplay」.
   When image-to-video keeps getting an action wrong, pin both ends with `fl2va.py` (a first frame and a last frame).
   FL2VA is also how a **long take** is made (8 to 11 s: looking through the peephole until the eye fills it, a
   person coming in through the door seen from outside and then inside); cut inside it with `offset` and `max_t`
   only. A conversation is one **two-person clip** per exchange, both faces in frame, the prompt giving who speaks
   when. **Before any clip, put every still that shows the same set on one sheet** and compare the fixed parts (the
   door, its peephole and lock, lamps on or off); fix the odd ones with `edit_stills.py` (a jobs file of same-framing
   Qwen edits, the set's text block as a `{BLOCK}`, three candidates each), not with a new prompt.
   Video-only stills (a normal-feet version, a new angle, the end state for FL2VA) are drawn in `reel/fx/`, a small
   board of their own, as same-framing edits of picked stills.
4. **Music and sound.** Score: ACE-Step 1.5 (`polite.py music name seed seconds`, which runs `music.py`; check with the spectrum, not ASR, which hallucinates lyrics on
   instrumentals). The 鬼唱詩 end theme is outside music the owner chose: Pixabay 〈小さなおばけのワルツ Waltz of Little
   Ghosts〉 (naginomori), first 12 s, in `brand/music/licensed/end_theme_12s.wav`. Or a bed cut from the brand's
   licensed library by situation (開場、一般生活、不安、懸疑、很緊張、餘韻; table in Obsidian `Projects/ghost story/
   ghost story music library.md`), with sections anchored to shot ids so cuts don't need re-timing; keep the hook at
   the owner's level and the music lower once the narration starts (lessons.md 「Music levels」). Sound effects:
   ghost-reel's sfx.py names (knock …), each clip's own H3 sound, and the stock picks in `brand/music/licensed/sfx/`
   as `file:` entries, trimmed into `sfx/cuts/` first; about 15 to 20 in a 5 to 6 minute reel, each tied to a shot.
5. **Shot list and render.** `shots_vN.json` (format in references/shots.md; `assets/example_shots.json` is the final
   upper_bunk cut). Past a dozen shots, do not edit that file by hand: keep each clip's pick, offset and in-clip
   speech times in `clip_notes.json` and the order, lines and sounds in a `make_shots.py N` that writes the shot list
   (`assets/example_make_shots.py`, `assets/example_clip_notes.json`: 第 2 部, with dialogue clips;
   `example_make_shots_long.py`, `example_clip_notes_long.json`: 第 3 部, long takes with several spoken lines, a
   narration line before the first of them, a `still:` source and a `sub` line over a sound file). A new seed or a
   re-cut is then one edit, and every version stays reproducible. `render.py shots_vN.json` times every shot from its voice lines, draws one subtitle at a time on a
   dark band at 0.76 of the height, ducks music and room sound under the voice, mixes to -14 LUFS and writes
   `out/reel_vN/` (mp4, `_frames.jpg`, `_timeline.txt`); `--reuse` remixes the sound only, in about a minute.
   Before a scare, a shot's `music_cut` makes a real silence (music and room sound).
   `package.py` writes the 720p copy under 10 MB. `verify.py` lists the cuts where the sound moves over 10 dB (LISTEN) or the light over 20 (LOOK); sort them into deliberate (a hit, a planned silence, a flash) and not, and fix the second kind. Check the mix line by line with `asr_lines.py out/reel_vN/reel_vN.mp4`
   (one ASR window per subtitle line; a whole-file pass skips stretches). Every line must read back; a LOW on a
   muffled or filtered line (「開門啊」 behind a door read as 「太忙了」) and any laugh or scream are for the owner's ears:
   say which.
6. **Title and cover.** The title shot uses the poster title, animated (`title_fx.py`: 1 霧中浮現 is the owner's pick,
   2 訊號干擾, 3 垂吊搖晃), with the icon and 鬼唱詩 under it. The cover is a film poster (`poster.py`): the D title
   treatment (標楷, worn edges, cold glow; `scary_title.py` has A to D), a tagline at the top, and under the title one
   line only, icon + 鬼唱詩. No clear ghost and no spoiler on a poster: no reveal face, no twist line as tagline (owner,
   2026-11-10: 「poster 不要有清楚的鬼，不能爆雷」); use an ambiguous early image and a rule from the setup. For a body-horror object the owner liked a blend of the normal and the ghost version, normal
   where the light falls (`blend.py`, mode 2 光束 for 上鋪的腳).
7. **Review rounds.** Every cut goes to a blind reviewer before the owner sees it, also a cut that looks finished:
   第 3 部's v9 looked done to its maker and scored 5/10, with a face change, a cut inside a clip and a person
   missing after a cut, all real. Do the fixes that cost no GPU, list the rest, and only then send.
   Give the mp4, timeline and ASR to a fresh subagent with `references/review_brief.md` each round
   (fill every `{…}` in the brief for this film; it cannot hear: say so); it scores 1 to 10 for 「能不能直接公布」
   and names the second a stranger most likely swipes away and the scene worth sharing. Fix the swipe-away second
   before anything after it: average watch on 第 1 部 was 35 s. upper_bunk went 5 → 6 → 6.5 → 7 → 7 over v1 to
   v9, then the owner's own notes drove v10 to v20. Reviewers contradict each other on taste (a bright or a dark first
   frame, a headline or none); the owner decides those. Report numbers, send the 720p file, and say plainly that the
   voice, music and lip sync need the owner's ears.
   **Owner notes come as a numbered list** (12 on 第 2 部's v10). Answer each by number in the next cut's report:
   what changed, at which second, or why not. A scene the owner calls weak is cut, not repaired. For a choice of look
   (the ghost's face, the poster), draw three options and let the owner pick before spending clips on one.
   **Polish pass** (「再打磨一次，看有沒有…不合理…不連貫…不流暢」): `review_sheets.py` and two blind reviewers, one for
   the picture and one for the text (`references/review_split.md`). Verify every claim on a full-size frame before
   acting: v10's "two extra people" were a backpack and a cabinet. Free fixes (offset, zoom, lift, a clip swap,
   subtitle text) first, regenerations as one batch.

8. **Instagram parts and packing.** A film of 3 minutes or less is one cut everywhere (第 2 部, 2:36: Reel, Short,
   FB Reel, Threads video, Pinterest video pin); skip the parts. Over 3 minutes (the Reels limit), cut two parts at a cliffhanger, each under
   3:00: part 1 ends on 「上集完／下集：…」 (`end_title`, `end_question`), part 2 opens on the hook flash and the
   title shot with `headline` 「下集」. The music is the full bed sliced at the same point, with `music_gain`
   rescaled (transom_window's `make_ig.py`). Each part needs its own `_preview720.mp4` (`package.py`) under 10 MB:
   that is what Claude in Chrome uploads. Then the poster (`poster.py`, two or three candidates, the owner picks) and
   ghost-pack-film for the number 「鬼唱詩劇場｜第 N 部」 and the captions. Pinterest takes videos up to 300 s, so a
   film's video pin is IG part 1 when the full cut is longer (pack_film.py picks it).

9. **Long film and shorts (v2).** When the owner wants the whole story (8 to 12 minutes) plus shorts. The worked
   example is 〈動物醫院的兩點十分〉: 68 shots, 108 segments, 172 lines, 10:22 + a 12 s end card, four shorts of
   2:45 to 3:00. Details and numbers in `references/lessons_long_film.md`.
   - **Script.** Lines come from the story in its own words, every line once, in order (a builder script reads
     story_clean; new text only for the opening line and each short's opening line). Write the shorts' cut points
     into the screenplay (at a line that makes a cliffhanger: 她第一次開口／這個主意簡直天才／紅燈自己亮了). To
     shorten, delete only, never rewrite, and re-read what is left (deleting made sentences with no subject). Owner
     notes beat screenplay_short's defaults here: no headline and no ghost in the opening, a corner label n/4
     instead of a title card, an end card on every short. Every day and clock time agrees across the whole film.
   - **Floor plan, then one master per camera** (ghost-comic-v2's building_plan.py): the plan is taken from what most
     existing pictures already show, checked camera by camera for left/right (v4 of the plan was a mirror image of
     every still). Every still of a camera is a same-framing edit of its master.
   - **Voices.** Narrator and every character from H3 speech, the owner picks a version (C here: re-acted brighter
     takes, +1 semitone, 1.15x, `aresample=44100,asetrate=44100*2^(1/12),aresample=44100,atempo=1.15/2^(1/12)`, trimmed
     `start-.08` to `end+.22`). Direction texts short and in English (long Chinese ones were read aloud). A changed
     line gets a new take name: polite.py skips names that exist. When the narrator is the character 「我」, it is
     one voice.
   - **Talking clips: the speaker's mouth moves** (owner: 「配上影片時，讓角色的嘴巴也要動，不動很奇怪」). One 5 to 7
     s i2v clip per line, the speaker's face visible, the clip's own audio muted and the picked voice laid on the
     mouth movement. Prompts never quote the line (H3 draws it as subtitles), never name a language or a tone, never
     say 三腳架. 8 to 14 s clips pushed in or grew things: long lines ping-pong a 5 to 7 s clip. Check mouths on a
     zoomed head sheet (`assets/vet_night_xray/mouth_sheet.py`); picks go to `talk_final.json`.
   - **Silent clips** use the stable look line from the first clip on: 「鏡頭完全固定不動，不推近、不拉遠、不移動，
     人物在畫面中的大小從頭到尾不變…人物的腳一直在原地…畫面乾淨，沒有字幕、沒有對話框、沒有任何文字或符號」
     (6 of 8 held, against 19 of 26 with a shorter line). Never name in a prompt what must not appear (「水漬不變大」
     grew water in about 40 clips); no light changes in prompts (do them in the render); 「在遠處走一小步」, not 「往前走」.
     Try 3 clips and read their strips before a batch (one untested batch cost 2.5 GPU hours). Empty rooms and small
     distant cats are stills with a camera move: H3 pushes in on them every time.
   - **Chain the segments of a shot** (owner: 「連續的段落中，後面的段落應該要用前段落的尾幾幀當成頭幾幀」). Every segment
     after a moving one in the same shot is generated from the frame the previous segment shows at its cut:
     `scripts/long/chain.py plan`, then `chain.py round` in the background until "all done" (30 segments = 6 rounds,
     about 80 GPU minutes). Clips are 5 s (H3 refuses under 5 s; 7 s chained clips pushed in). Read every strip; a
     bad link is retaken with the links after it. A corridor-perspective start frame pushes in on every seed: keep a
     short push as a camera move, and for a long segment play the push once and hold the settled end
     (`hold_plate.py`). Check every chained cut with `cut_pairs.py` after the render.
   - **Build and render.** One builder (`assets/vet_night_xray/make_long.py`) writes `shots_long.json` from the shot
     table: plates (a clip trimmed or ping-ponged to its segment), labels (day and time), per-shot darkness by `lift`
     from the still's mean (never render.py's scene matching across a part), drawn camera plates for screens (an X-ray
     whose cage, hands and skull appear on their words, the skull masked until then), synthetic plates for a long
     still that carries an event (`polish.py`: a phone that lights and buzzes during the missed call), and the
     chain_map clips. `scripts/long/dry.py` gives the timeline without rendering; the music bed is cut to it with
     sections anchored to shot ids (`build_bed.py`). `scripts/long/run_parts.py shots_long.json <split ids>` renders
     in parallel parts (29 to 35 min against 1 h 50 m in one pass) and mixes the sound once with `--reuse`.
   - **Shorts without a second render.** Openers and cards are rendered once in an extras spec
     (`assets/vet_night_xray/make_extras.py`: the opener line with a corner label n/4, a 12 s 「下集：…」 card on the
     end-card background with the end theme), the long film's own end card once (`shots_endcard.json`, 本首完). Then
     `scripts/long/cut_shorts.py shorts_plan.json` joins opener + a stretch of the long film + card with ffmpeg, a
     12 s card when it fits under 3:00, else the card's first seconds with a 2 s fade (owner: 「每一個片尾，能放12秒，
     就放12秒／第三篇，就放片尾的前幾秒，最後2秒漸弱」), and a limiter on every output.
   - **Copies.** package.py's 9.3 MB target makes a 10-minute film unwatchable: the long film's review copies are
     720p crf 26 (about 67 MB) and 540p at 250 kb/s (about 27 MB, under 30 MB for the phone); shorts get their
     `_preview720.mp4`.
   - **Review.** `scripts/long/shot_sheet.py out/<v>` (one labelled frame per segment), `cut_pairs.py`, loudness
     (`ebur128`, about -15 LUFS, true peak under -1 dB), the longest silences in `_vo_only.wav`, `asr_lines.py`
     (homophones such as 阿斌/阿兵, 牠/他, 灰灰/輝輝 are not errors; a 0.0 is often a neighbouring line). List the
     lines ASR cannot confirm for the owner's ears.

## Scripts (`<skill>/scripts/`, each docstring has the full usage)

| Step | Script | What |
|---|---|---|
| 1 | `film.py` (`uc.py`), `stills_both.py` | manga.py commands with the film model and colour pages; every cell again as a 9:16 (and `--wide` 16:9) page |
| 1, 3 | `edit_stills.py` | same-framing Qwen edits from a jobs file, three candidates |
| 2 | `speak.py`, `check.py`, `spans2.py`, `spans.py`, `voice_fx.py` | takes; ASR check against script.json; best take and trim; phone and door filters |
| 3 | `crops.py`, `fl2va.py` (`fl_polite.sh` waits for an empty queue), `strips.py` | first frames; a shot pinned at both ends; frame strips of clips |
| 1, 3 | `fresh_draw.py`, `sheet.py` | a master still or a new angle with no source picture, four candidates; pictures side by side with their names |
| 3 | `clip_check.py [--asr]` | light jumps, cuts inside a clip, speech in a clip that should be silent |
| 3 | `prompt_check.py prompts/*.txt` (`name.txt:sec` to check the length) | H3 prompts before the GPU: beats contiguous from 0 s and ending at the clip length, 固定機位 with a move, the `non_diegetic_music:` block, 靜音 in the soundscape |
| 3 | `words.py`, `words2.py` | where a clip's own line starts and ends; every word with its time (for `speech`, `me_at`) |
| 2 to 4 | `polite.py speech / clips / music`, `pause.py pause / resume` | every GPU job, one at a time on an empty queue; hold a clip loop (needs the story's `plan.py`) |
| 4 | `music.py` | ACE-Step score |
| 5 | `verify.py out/reel_vN/reel_vN.mp4` | seam report: cuts where sound moves over 10 dB (LISTEN) or light over 20 (LOOK), single bad frames |
| 5 | `render.py`, `package.py`, `asr_lines.py`, `asr_mix.py` | the reel; the 720p copy; ASR per subtitle line; ASR of the whole mix with times (what the reviewers read) |
| 6 | `title_fx.py`, `scary_title.py`, `poster.py`, `blend.py` | animated title; title treatments; poster; normal and ghost stills blended |
| 7 | `review_sheets.py` | sheets and shots.txt for the two blind reviewers |
| 9 | `long/chain.py plan / round [seed]` (needs `chain.json`) | chained clips: each segment from the previous segment's shown last frame, round by round |
| 9 | `long/hold_plate.py clip settle out` | play a clip once, then ping-pong only its settled end (a push-in that must not pull back out) |
| 9 | `long/dry.py shots.json [ids]`, `long/run_parts.py shots.json <split ids> [--join-only]` | timeline without rendering; parallel part renders, joined, sound mixed once |
| 9 | `long/cut_shorts.py shorts_plan.json` | the long film with its end card, and shorts from openers + stretches + cards, limiter on all |
| 9 | `long/shot_sheet.py out/<v>`, `long/cut_pairs.py out/<v> [ids]` | one frame per segment; before/after frames at chained cuts |
| 9 | `assets/vet_night_xray/*.py` | the first long film's builders to copy and adapt: make_long, make_extras, build_bed, polish, make_talk3, make_motion3, mouth_sheet, make_preview, shot_table, make_lip_compare |

## Rules

- **Every GPU run and every wait is a background task that reports back when it ends.** 38 clips finished at 00:44
  with nothing to wake the session, and the owner found it idle 6.5 hours later.
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
- **Floor plan, then one master still, then everything else** (第 3 部; step 0 and step 1). Mirroring clips or
  patching single shots did not satisfy the owner; the layout has to hold in every shot.
- **Long takes and real dialogue** (owner on 第 2 部): a scene that is one action is one clip, not a cut per line, and
  a line said to someone in the room is lip-synced in a two-person clip, not read as narration, the
  narrator-character's lines included. lessons.md → 「What the
  owner sent back」.
- **After the ghost is in the room, every shot says where she is.** A background figure doing the wrong thing gives
  the twist away early.
- A jump-scare ending is one continuous clip: the ghost, recognisable as the character, rises from behind, a fast
  push-in to the full-screen face, black, the last line. lessons.md → 「The ending」.
- Fiction only; no real people or places that can be identified.

**Added in v2 (〈動物醫院的兩點十分〉):**

- **Owner notes beat this skill's defaults**, and a note given for one film holds for the next unless the owner says
  otherwise: no ghost or spoiler in the opening, no headline, an end card, long takes, nothing hanging from the
  ceiling, no air conditioner, dialogue that sounds in the room.
- **Every on-screen speaker's mouth moves**, also when the voice is dubbed.
- **Inside one shot, every later clip starts from the previous clip's last shown frame**, never from the shared still.
- **The strip is the check.** clip_check passed every push-in, subtitle drawn into a clip and growing puddle on this
  film; only frame strips (and a zoomed head sheet for mouths) caught them.
- **Every GPU job and every long render runs in the background** and the session waits for its notice; never poll.
- Say plainly in every report that voices, music, sounds and pacing need the owner's ears, and name the lines and
  sounds ASR or the eye could not confirm.
