# What upper_bunk taught (2026-11-06 to 11-07)

## Stills
- Draw every panel in both shapes (`stills_both.py`). Portrait reel shots cut from landscape panels lost heads and kept
  the panels' dark walls and desks as bands top and bottom; zooming them in to hide that made them soft.
- A set reference makes the model copy the set whole; drop it when many things must change.
- Same-framing edits (「The same picture as <image1> … change only …」) are how a still gets a variant: normal feet
  instead of dead ones, the man gone and the dead legs stretched (an FL2VA last frame), the chair moved to the bed.
- A face edit with the character sheet alone kept the curly hair; using a picked still where his hair was right as the
  second reference fixed it.
- Write heights and scale: 「a grown man is about as long as the lower bunk bed」. Without it the man on the floor came
  out too big (owner: 「主角比例不對，太大了」).
- A secondary character in a new shot needs their own cast sheet as a reference (小傑 was replaced by a stranger
  until jie_3 was given).

## H3 moving shots
- Prompt template:
  `寫實港片電影感，35mm 底片顆粒，畫面維持跟第一幀完全一樣的色調、亮度、房間和人物長相，畫面中沒有任何文字。<scene>` then
  `[0s-2s] … [2s-4s] … [4s-6s] …`, then `overall_soundscape:` and `non_diegetic_music: N/A`.
- After 4 to 5 s H3 often cuts to a wider shot, and that shot shows the ghost's body (knees, trousers on the upper
  bunk). Always look at a frame strip and set `max_t`; say 「同一個鏡頭從頭到尾不切換」 and 「不出現膝蓋以上的身體」.
- Hair and faces drift after a big lighting change (the light switching on); add 「頭髮一直是第一幀那樣」.
- A person smiling at the end of a line (小傑 in v1) contradicts the story; 「表情一直嚴肅害怕，從頭到尾都沒有笑」 fixed it.
- Falls and other fast body actions: image-to-video made him fall forward toward the camera in five seeds. FL2VA with a
  last frame of the end state (empty chair, dead legs stretched) gave the backward fall, and the prompt 「就在他往後倒的
  同時，那雙死腳也跟著一起往下伸長」 made the legs move during the fall instead of after it. T8's render window must be
  on the 17n+5 grid (158 for 6 s; 148 fails).
- A clip shorter than its shot was slowed to the floor speed and then held its last frame: the owner saw people
  「定住不動一下下」. Keep `min_speed` at 0.35 (shots_vN.json), and give dialogue shots no tail past the clip.
- Two run_clips.sh loops on the same list submit everything twice; check with the process list before starting one.

## Voice
- No local Chinese TTS. Windows has English voices only; edge-tts's one Taiwanese male (zh-TW-YunJhe) returned no audio;
  the paid API nodes were not used. H3's speech nodes speak Chinese well.
- Every take must be checked by ASR. Words H3 kept misreading: 舍監 → 舌尖, 不排 → 不拍, and long lines lost their first
  half. Rewrite instead of retaking forever: 「宿舍的管理員」, 「那張床為什麼不給人睡」, split the line.
- Generated takes have a noise floor, so trimming by loudness either cut the quiet last syllable (a threshold at 38% of
  the peak ate every sentence end) or kept seconds of silence. Trim by ASR word times (`spans.py`).
- `vo_speed` 1.15 (atempo) kept the narrator natural and the video 10% shorter.
- Homophones in ASR (托/拖, 他/她/它) are not errors; read the transcript for missing words, not exact characters.

## Mix and render
- Music under the voice: `duck` 0.5, room sound dipped too, `music_level` evens out a score that starts very quietly;
  `music_cuts` silences it for the beat before the reveal.
- np.convolve with a 2-s window over 6 million samples took over 20 minutes; `movavg` (cumulative sums) does it at
  once.
- One subtitle at a time (two overlapping in a fade read as garbage), at one height, on a dark band, single line where
  it fits (commas become wide spaces).
- Hard cuts, not crossfades: the crossfade blends the last frame of the previous shot held still.
- A text overlay on a dark first frame does not read on a phone; the hook's first frame must show the person and the
  strange thing together.

## Owner decisions (upper_bunk)
- The hook headline was removed in favour of the narrator's own subtitle.
- Video title = the poster title, 霧中浮現, icon + 鬼唱詩 under it.
- Cover: poster 2 (the feet close-up) with the blend 2 光束, title D, one brand line under it.
- End theme: Pixabay 7 (Waltz of Little Ghosts), first 12 s. ACE-Step themes (five tries) were all rejected.
- Ending: the new room, the chair moving very slowly to the bed, the dead legs coming down above it, 若隱若現 as a slow
  breathing opacity (not a hard flicker, which looked like a broken file), clearest on the last line.

# Comic from a screenplay: 〈幫阿公守夜〉 v2 (2026-11-07)

20 pages, 80 panels (14 reused from v1, 66 new), about 2 GPU hours on the RTX 3090 with every redraw, five checker
batches beside the GPU; about half the new panels needed one or two redraws. Two blind readers: 8/10 each, both
retold the whole story and named everyone.

## Setup
- `file:cast/x.png:head` and `:bust` do not exist: manga.py's crops are only for character ids. The cast sheets are
  waist-up, so the sheet itself serves as the bust; cut head squares by hand (`out/cast/<id>_head.png`, about 460 px
  around the face, resized to 768) and point `:head` references at them.
- `film.py review` counts heads from `cast`; with characters given as `file:` references it writes 「剛好 0 人」.
  Tell the checker to count from the prompt ("Only one person", "Exactly three people", "Only the hand").
- Stopping a run halfway (to give later panels a new prompt) leaves those panels drawn once: their candidates are
  `_1` to `_3`, not `_4` to `_6`. Say which numbers to check.
- The board script can be rebuilt any time while a run is going; the running process keeps the prompts it loaded.

## Prompt rules from the checkers
- A scene sheet in a close-up copies the sheet's whole wide shot (the coffin-glass close-up came out as the whole
  tent). Leave the set out of close-ups and lock the object with a picked panel instead (`panel:g4` for the box).
- Continuity of one object across forty panels needs a written shape and a picked reference: 「the low square
  brushed-silver stainless-steel box with a small window on its front face」; without it the box became a long
  wooden coffin, a chest freezer or a tall cabinet.
- The cast sheets face the camera with a neutral face, and that wins over words late in the prompt: people stood
  when they should sit, stared at the camera instead of looking up, smiled calmly when terrified. Put the pose and the
  expression first: 「Head tilted back, eyebrows raised, mouth hanging open … 」, 「Both seated low on red stools …」.
- A farmhouse prompt drew a two-storey Western house; 三合院 needs its parts written out (single-storey U of three
  red-brick wings, curved clay tiles, swallowtail ridges, courtyard in front, 「not a Western house」).
- Children: write 「clearly the heaviest child」 and the age; otherwise the chubby 11-year-old came out a thin 6-year-old.
  Flashback 春聯 needed 「plain and blank, no characters」 or they carried fake calligraphy.
- 「Only the hand」 panels with one person's sleeve: say whose side the hand comes from, or it reads as the person's own.
- Ask for one physical state, not a story: 「a gap where several cigarettes are missing」 drew full packs; 「only four
  cigarettes left pushed to one side」 worked.

## Fixes without a redraw
- A toothless sunken mouth failed six times as a prompt (the model draws full lips). A same-framing edit of the closest
  candidate, 「Change only her mouth: no teeth at all …」, gave usable ones (`fixes2.py`).
- 「Eyes in shadow, only the lower face」 drew the whole face three times; cropping the candidate below the nose and
  darkening the top edge did it.
- A two-person shot from behind (both looking up at her) failed as text three times; an edit of the closest
  candidate with 「The camera is low, directly behind …」 got it on the first try.

## Blind readers
- Both trips found by the readers were cheap lettering fixes: a line nobody could place (add 「我遞了一張……」 or move
  it), a caption naming a thing the panel does not show (「椅子上的阿嬤」 when she seems to sit on the box), a cut
  between two places at once (「同一時間，阿凱從門縫看進去：」), a clue whose logic was missing (the dentures in the cup:
  add 「她睡覺從來不拿下來的」).

# Reel from a screenplay: 〈幫阿公守夜〉 v2 to v3 (2026-11-07 to 11-08)

Story folder `C:/Users/sheep/Pictures/gui_chang_shi/backlog/grandpa_wake/film/reel/` (`shots_v3b.json`,
`make_shots_v3.py`; the film folder was deleted on 2026-11-11 to free disk, the story and drafts remain). The owner's five notes on v2 and what fixed each:

1. 「有些片段，是定格的圖，很奇怪」: v2 had 28 stills with a push-in. v3 made a 5-s H3 clip of every one of them (38
   clips, about 2.7 min each, 1 h 50 min). A still with a camera move does not pass for film; plan a clip for every shot
   from the start. A clip shorter than its shot holds its last frame too: render.py now prints `WARN frozen tails` and
   writes them to `_timeline.txt`. Fix a frozen tail with a lower per-shot `min_speed` plus `motion: push`, a longer
   clip, or a shorter line, never by leaving it.
2. 「台語的部份，配音很奇怪，改成說中文，字也改成中文」: H3's Taiwanese sounds wrong to a native ear. Write every
   character's line in Mandarin (the screenplay can keep （台） as the flavour of the scene, but the line spoken and its
   subtitle are Mandarin) and prompt 「嘴巴配合說話，<who>用國語清楚地說：「…」」.
3. and 4. The sleeping 阿嬤 changed between the two bedroom shots, and the room light was on. Draw both shots from one
   picked still (the second as a same-framing edit of the first), and say the light stays off (「房間的燈一直是關的，只有
   門縫透進來一點點微光」). Even so H3 switched a lamp on after 3.3 s in both clips: look at the strip, set `max_t`.
5. 「胖子臉變白時，太白了，應該只是沒有血色而已」: 「臉色有點蒼白、沒有血色，膚色自然，不是白色」.

Dialogue clips:
- H3 often says a few made-up syllables before the line. `words.py` gives the whole span; read the word times instead
  and start the clip just before the first real word (`offset` = word start − `lead`).
- Two lines failed in every seed (3 each): 「不用擲了。」 (too short) and 爸's 「換班了，有沒有什麼事？」 after a yawn in the
  prompt (the yawn turned into words). Drop actions that use the mouth before a line. When a line still fails twice,
  stop retaking: make it with `speak.py` (a described voice, 2 seeds, ASR-checked) and lay it over a clip whose own
  sound is off (`amb: 0`, `theme` = the wav, `lines: [{"sub", "dur"}]`), with the speaker's face down or far away.
- A toothless mouth (阿嬤 possessed, no dentures) grew teeth as soon as the smile opened, in three seeds. Use the frames
  before the mouth opens, or prompt a closed-lip smile.
- A first frame that differs from the clip's second (g13) is a cut inside the clip: skip it with `offset`.

Process: every GPU run and every wait must be a background task the session is told about when it ends. In v3 the 38
clips finished at 00:44 and nothing woke the session; the owner found it idle 6.5 hours later.

# Reel from a screenplay: 〈社辦門上的氣窗〉 (2026-11-08 to 11-09)

Story folder `C:/Users/sheep/Pictures/gui_chang_shi/backlog/transom_window/film/reel/` (`plan.py` writes every H3 prompt
and the crops, `polite.py` runs one GPU job at a time, `make_shots.py` builds `shots_vN.json` from `clip_notes.json`).

## A set's architecture is one text block and two pictures, fixed before drawing
- The owner, twice in one night: 「氣窗部份，教室內看 和 走廊看 不一致。統一一下，只有門上有氣窗。」 and 「教室的門一直不是很統一」.
  The inside views had a long band of glass across the wall, the corridor views a door-width transom, the close-ups a
  transom wider than the door over a dark green door, and some corridor views two stacked bands of glass. Inside and
  outside views had been drawn from separate prompts and drifted apart in three ways.
- Before drawing a set, write its fixed architecture once (here: 「a single dark-brown wooden door about 90 cm wide with
  one frosted glass panel in its upper half; directly above it one clear glass transom exactly as wide as the door and
  about 40 cm tall, in the same dark-brown frame; plain wall around it, no other glass」), and pick one inside and one
  outside reference picture. Put the block in every still prompt, every edit and every H3 prompt whose frame shows it.
- Fixing it afterwards: same-framing Qwen edits with the still as <image1> and the reference (inside or corridor) as
  <image2>, 「Change only the door, its frame and the transom glass above it」 plus the block and the light state; a fresh
  checker with the block and both references picks per still. Reel: 7 stills for the transom, 14 more for the door, 4
  close-ups replaced by one re-cut close-up; comic: 7 panels for the transom, 18 for the door (12 pages re-laid).
- Edits of near-black close-ups lose what is inside the glass (the head shadow vanished in all three candidates of four
  close-ups). A close-up cut from the fixed wide still and re-rendered by a same-framing edit kept the head and the door.
- Only put the block in prompts whose frame shows the door. Added to every room prompt, it made H3 cut from a boy's
  close-up to a bright metal door with a window band (three clips in a row).

## H3
- H3 speaks words written in the soundscape: 「只有這一句對白」 came out of 王伯's mouth after his line. Never describe the
  dialogue there; name only the sounds.
- Very short lines (「要不要吃橘子？」, 「王伯，掰掰！」) came out as other sentences in every clip, even made longer; a
  speak.py take of the short line, played as a line id with its own subtitle, was quicker.
- Dark first frames often cut to a bright room after 0.5 s (a third of the night clips). Look at frame 0.5 of every strip;
  use `offset` past the jump when the bright part is usable, else reseed. Lifting the first frame (gamma 0.65, render
  `lift` 1.25 takes part of it back) did not stop the jumps by itself.
- Other recurring H3 inventions: a door that opens and a stranger walks in (twice), a fried-chicken stall sign with
  fake Chinese (cut before it or prompt 「招牌上沒有字、模糊、看不清」), a page flip showing fake text, eyes opening on a
  character who must keep them closed, the ghost's black eyes getting whites after 4.5 s. All are `max_t`/`offset` cuts.
- Two speakers in one clip: the line pair came with 3 s of mumble between them; use the clip twice as two shots, each
  starting at its own line.
- A phone voice in a clip came out garbled; a speak.py take placed as a line before the clip's own speech in the same
  shot (`pre` in speech.json) keeps the boy's lip-synced answer.

## Voice
- `ref2va` takes of short narration lines often start with words of the reference take's sentence (「高二那年冬天」 in
  front of 「就貼在門上面那片氣窗」). `vo/spans2.py`: ASR word times, the word range that best matches the script
  line gives the start (the end is always the last word), the cut is transcribed again and must read back.
- ASR returns simplified characters for some takes (当, 还会); a character-level match then cut 「還會喘」 off the end. Keep
  every word to the end of the take; junk only comes before the line.
- `MiniMaxH3SpeechStudioT8` refuses `render_seconds` under 5.17.
- A ComfyUI restart in the middle of a 90-line run left one line with `error` and no file; check the log for anything
  but `success` before building the picks.

## GPU shared with other sessions
- Another session's H3 loop submits its next job within seconds of the last one finishing; a polite loop that wants the
  queue empty for 45 s never gets in. Poll every 0.7 s and submit on the first empty read (`polite.py`).
- To pause a running clip loop without losing the job in flight, touch empty placeholder files for the clips it has not
  made yet (`pause.py`): the loop skips existing files. Do not touch the one in flight: the final rename fails on Windows.
- Never re-run crops.py over names whose src was edited by hand (lifted, re-cut): pass only the new names.

## Things H3 would not do in this story (stop reseeding)
- Three seeds each: a dark close-up of a phone (cut to a bright room), the boy frozen in the dark clubroom (cut to a daylit
  classroom), the black-mirror transom shot (opened the door onto a lit classroom), the empty lit transom (opened the door
  and walked a woman in). After two failures, use FL2VA with the same closed-door still as first and last frame (it held the
  door shut, `fl_polite.sh`), cut with `max_t`, or give the line to another clip of the same scene.
- The comic's hand-in-the-door-gap still had too little hair to read as hair; a prompt cannot add it in the clip. Fix such a
  prop in the still first.

## Review rounds
- Round 1: 7/10 (hook too small on a phone, title shot too dark, stingers over key lines, door shots with a tall white
  window). Round 2: 6/10 (the title still not readable, sign text, length). Reviewers always ask to cut to about 4:30;
  the setup lines carry the rules the twist depends on, so cut texture scenes (phone call, classmates) first.
- An ASR file read while it is still being written is empty: write the ASR before calling the reviewer.
- A 1.4 s flash of the reveal face before the first narrated shot answers the "hook too weak" note without losing the
  person-plus-strange-thing first shot.
- A seven-character title shrank to fit and `erode` (fixed 4-px blur, k 0.32) wore its thin strokes into scattered dots;
  two reviewers read it as garbage. `title_fx.py` now erodes less as the title shrinks (k grows with (200/size)^2).

# 〈社辦門上的氣窗〉 v8 to v11 (2026-11-09 to 11-10): music, stock SFX, cuts, polish

## Music levels (owner: 「音樂太大聲了，開頭還可以，後面開始說話，就小聲一點」)
- render.py normalises the whole music file to one RMS, so lowering part of the bed also raises the rest unless
  `music_gain` comes down with it. In `build_bed.py`, put a gain ramp after the hook (×0.6 from 14 to 15.5 s). Then
  set `music_gain` so the opening RMS equals the old one: new = old × (rms_new / rms_old) × (open_old / open_new).
- `duck` changes the opening too. Moving it from 0.5 to 0.35 made the hook 2.5 dB quieter than the owner had approved.
  Keep duck and change the bed.
- Measure, don't guess. Compare `_mix − vo_gain × _vo_only` with the previous version's over the hook, a narrated
  stretch, and the climax. Remember `vo_gain`: `mix − vo_only` still holds half the voice when vo_gain is 1.5.

## A music bed by situation, anchored to shots
- The bed is cut from the brand library by situation (開場, 一般生活, 不安, 懸疑, 很緊張, 餘韻; the table is in
  Obsidian `Projects/ghost story/ghost story music library.md`), loudness-matched, with 1.5 s crossfades.
- The transom story's `music/build_bed.py` started with absolute seconds. Every cut shifted them, and they were
  re-timed by hand twice. It now takes `(shot id, seconds from that shot's start)` and reads the times from
  `out/reel_vN/_timeline.txt`:
  1. Render once with the old bed.
  2. Run `build_bed.py <timeline> <bed>`.
  3. Run `render.py --reuse`.
  Copy that pattern into the next story.

## Stock sound effects (Pixabay, `brand/music/licensed/sfx/`, listed in the Obsidian library note)
- The owner wanted common trailer sounds, not only sounds from the scene (「像是 登登 的鼓聲」). There are 21 picks
  across hits, risers, whooshes, a suck-out, drones, ear ringing, a heartbeat, breathing, glitch, power-down, whispers,
  a clock, a bell and a tick.
- **Fetching.** Pixabay search and track pages return 403 to curl. Read them with the built-in browser's fetch. The CDN
  mp3 downloads fine with a browser user agent and `-e https://pixabay.com/`.
- **Trimming.** render.py's `file:` sfx are RMS-normalised over the whole file. A long file with silence comes out hot,
  so always trim each pick into `sfx/cuts/<code>.wav` first (a cap and a 0.8 s fade).
- **Placing.** Note the onset and the loudest 0.4 s window (`sfx/cuts/make_cuts.py`). Place a riser so its loudest
  part lands on the hit, and a suck-out so its peak lands on the music cut.
- **Levels.** Hits should sit about at the voice level; beds (clock, heartbeat, breathing, whispers) 9–14 dB under it.
  A window measured over a hit can include the voice, so check what else is there before turning a hit down.
- **How many.** The owner rejected 28 placements as too many (「28個太多」). 15 to 20 for a 5–6 minute reel was fine.
  Attach each one to a shot (`sfx` with `at`), never to absolute time.

## A real silence before a scare
- Per shot, `music_cut: [a, b]` (negative counts from the shot's end; `[-1.5, 0]` is the last 1.5 s). It mutes the
  music and also the clips' room sound, so it is a real silence. A music-only cut left the room tone at −35 dB.
- Pair it with a `lead` (silence, then the knock) or a `tail` (silence, then the cut to the face with a hit). Three in
  the transom reel: before the knock, after 「寫的是一個王」 (the hit's tail decays into it), and 1.2 s before the
  face.

## Cutting a long reel
- Cutting a line can orphan a later one. Removing 「要不要吃橘子」 and 「掰掰」 left 「那天，橘子也沒給 / 那晚我雞排沒買」
  with no setup.
- Keep part of a take instead of re-recording. Add a new line id with the same file in picks.json, and set its
  spans.json start from ASR word times. N51b, 「騎車回家，一路都在想那個字」, is the tail of N51's take.
- What could go:
  - texture: the 倉庫, 「我常常抬頭看它」;
  - his rationalising: 「我第一個想法…」, 「我想說是對面大樓的燈」;
  - the fake clues the twist overturns anyway: the dripping vent, the hairs on the music stand.
- What had to stay: every rule the twist uses (the light first, the black mirror, the wheezing, the keys, the iron
  door). 6:15 became 5:37. The 4:30 the reviewers ask for would have cut clues.
- When the owner asks to cut the last line, ask whether the shot under it goes too. The e3 epilogue lost its line,
  then its shot (「也移除影片…都在門外，然後就接片尾」).

## Scarier without new footage
- A clear ghost face gets less scary the longer it is held (13.7 s over two shots in v9). Hold the close-up 2 s with
  no line, and put the description (「額頭上一圈發紫的勒痕」) on the hero's frozen face. The new reaction clip must
  continue the shot before it: standing stays standing, no guitar appearing.
- End on the threat. After the last line, the light dips and the head shadow is in the transom. Use FL2VA from the
  empty last frame to a same-framing edit with the head, and make the end card's background that frame.
- Hidden ghosts for a rewatch must be outside if the twist says "she was outside all along", never on the ceiling.
- H3 turns a faint face into one or two clear women leaning in (both seeds). Paste the face from the edited still onto
  every frame of the original fixed-camera clip instead (`comp46.py`).
- Check visibility at 720p. The first composite was invisible even to a reviewer at 3× brightness. The second reads
  as a pale face only to someone looking for it, which is the target.
- `lift` is a gamma: 1.25 darkens, 0.8 or 0.65 brightens. The fake 王伯's stairs, at 1.25, were black on a phone.

## render.py fixes in this round
- **Title.** `title_fx.py` read the title from `GF_TITLE` and fell back to 上鋪的腳, so every other story's title
  shot said 上鋪的腳 (owner: 「第15秒 標題錯了」). render.py now sets it from `title`. **Re-check the title shot of
  any film rendered before 2026-11-10.**
- **Subtitle breaks.** `chunks()` now cuts at the comma that leaves the most even pieces. Before, 「對啊，那片玻璃本來就會
  照到教室裡面」 left 「裡面」 alone, and 「…勒痕，眼睛睜開，沒有眨」 left 「沒有眨」 alone. A bare 「王」 in a sentence
  reads as "king": quote it in script.json (寫的是一個「王」).

## Blind polish review (references/review_split.md)
- The picture reviewer caught what a writer never sees:
  - the line says 「我閉著眼睛」 while his eyes are open;
  - his eyes close during the shot before 「我把眼睛睜開」;
  - the fake visitor already stands inside before the door is unlocked;
  - the light-on line plays over glass that was lit from frame 0;
  - the knocker is capless and reads as a teenager.
- Five of the six regenerations worked first time. The standing reaction clip drifted into a smile after 3 s, so it
  uses `max_t` 3.
- Free fixes covered the rest:
  - an `offset` past a guitar fading into his hands;
  - an `offset` to where his eyes are already shut;
  - a swap to the black-mirror transom clip under 「腦袋想的全是那片黑色的鏡子」.
- Zoom did not crop the chair out of two door shots. It sits too low in the source; that needs a regenerate or
  acceptance.
