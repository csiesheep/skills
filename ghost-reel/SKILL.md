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

## What it is for

The Reel is where strangers meet the account, so it is judged on the Instagram Reel's numbers: new follows, then
(shares + saves) / reach, then average watch time (`brand/taste.md`, rules in auto_promotion
`references/ghost_feedback.md`). Read taste.md before step 2: it names the week's experiment (on 2026-11-09, which
opening is the main cut by story number: ghost face or the strange situation) and what the last one showed.

- Two kinds since 2026-11-01. 長篇: 80 to 95 s with the 8-second hook block below. 短篇: 35 to 45 s, never over 45.0 s
  in qc, the hook in the first 1.5 s (the creepiest frame with one big line), 4 to 6 moving shots, the jump scare and
  the lingering last panel kept. Every story also gets a trial cut B that changes only the opening
  (auto_promotion `references/ghost_make.md`).
- The median manga Reel brings 0.5 follows. The first realistic film with a narrator's voice (ghost-film, 第 1 部)
  brought 59 on one part. One film is a lead, not a rule, but voice-over is the first thing on the list at the end
  of this file to try here.

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
   panel before the reveal with tape noise (`vhs`), no title card, every lettered panel in reading order trimmed to
   about 85 s, the reveal (0.3 s of black before it, stinger, shake, `negflash`, `static`, music ducked) and the ending
   (darken, `vhs`, riser, stinger); a `"mono": true` board gives `"mono": true` and no "night" tint (〈帶國中遊學團去
   日本〉: "night" on an already-black panel left a shot almost pure black). The draft still knows nothing of the
   story's own jump scare, the character animation or the ghost close-ups: those are step 2–3 work. It refuses to overwrite an existing
   shot list (`--force` to start over) and refuses a board with no reveal mark.
2. **Edit it as a director, with the story open.** The draft knows panels, not the story. On 〈阿嬤說我後面跟了三個人〉
   it kept every speech panel and dropped the narration that carries the plot (the three patients who died on her
   shift). Read `story.md` and the pages, then:
   - **Let the story set the length.** A short story (第 2 首, 33 panels, one turn) fits 80 to 90 s. A longer one
     does not: 〈阿嬤〉 (37 panels, 10 pages) squeezed to 85 s lost its connecting narration and the owner found it
     too fast and not as smooth as the comic. Follow the comic's order and keep its narration, two to three
     subtitles a shot with 「／」, 4 to 5 s a shot; under 3 minutes it still goes on Reels, Shorts and TikTok. For
     longer stories make a part 1 and part 2 as cuts — **the owner chose on 2026-10-20 to post a long story as
     the two parts, not the long version** (〈阿嬤〉: 1:24 and 1:39) — (`"cuts"` in shots.json, `make.py --cut part1`): part 1 ends
     on the strongest turn before the reveal with 「下集待續」 on the end card; part 2 opens with a one-shot recap of
     that turn, then the title with 「（下）」.
   - subtitles in the story's words (the engine wraps at about 14 characters a line, two lines), spoken lines in
     「」; no subtitle where the picture says it.
   - **the opening is an 8-second hook block (A/B tested, 第 6 首, 2026-10-24; the owner: 「A is better」).** The
     analytics on v4 showed a 3-second view rate of about 24% and retention falling from 23% to 13% by 4 s: the
     cold open was a dark grey picture under tape noise with a vague line (「那趟日本，有個小孩」), and at 3.2 s it cut
     to a calm daytime shrine. Version A won against B (a phone ringing, then a question 「在日本拿了地藏前的石頭，
     你知道怎麼還嗎？」). Build every opening like A, then the comic's setup in order, untouched:
     1. 0–0.5 s: the scariest ghost image as a flash (a video-only ghost close-up clip, bright and high-contrast,
        `static` + `negflash`, a stinger). The first frame must read on a phone at a glance; never a dark mush.
        **Changed 2026-11-17 (owner 「改規則」, from the Insights of 32 Reels): the flash must carry the first line.**
        Of 27 comic Reels, the 13 whose first shot had no subtitle (a 0.5–0.8 s wordless flash, then the line) never
        passed 294 views (median 191, 11 new follows in all); of the 14 whose first frame had a line, three passed 1,000
        (第 32、46、48 首) and together they brought 75 follows. Those three open on one whole, concrete line that
        says what is wrong, over the object itself: 「爸媽就兩個人，杯子裡卻有三支牙刷。」, 「阿嬤說燈不能關。」,
        「最後一排，有人跟著我們唱。」. So: shot 1 has a `sub` from frame 0, one sentence a stranger can repeat in one
        breath (a fact or a rule, not a mood, not half a sentence), and the picture shows that thing (第 46 首 had no
        flash at all). A flash and a stinger may stay, but only under that line; never a wordless flash before it.
        `make.py` (and `--check`) now refuses a V3 shot list whose shot 1 has no sub. This is a hypothesis from small numbers (a line in frame 0 is
        necessary in this data, not sufficient: nine reels with one still sat at 187–269): the next three Reels follow
        it, then compare their views, shares and follows with the 13 wordless ones.
     2. 0.5–3.5 s: the strange, concrete thing with a sound (the phone ringing, `ring`), its words in big centred
        text (`"voice": true`): 「來電顯示：612」. A fact, not a mood.
     3. 3.5–6 s: the narrator's reaction (a character-animation clip: frozen, sweating) with the line that turns the
        fact into a threat: 「那是我的房間。」
     4. 6–8 s: one line that points back to the start: 「事情要從那顆石頭說起。」 over the object.
     The cold-open picture the old way used (the ghost rummaging) moves to where it belongs in the story. A question
     to the viewer ("你知道怎麼……嗎？") lost: state the strange fact instead. `ring` is a synthesised old desk-phone
     bell in sfx.py. Render alternatives as `"cuts"` in shots.json (`make.py --cut hookA`) and give the owner the
     720p files to post as Instagram trial Reels from the phone (trial Reels cannot be set on the web); compare the
     3-s view rate and the 4-s and 10-s retention after 48 hours.
   - a hook on a still face with a line that only makes sense later (「等一下，還沒好。」) scored 6/10 with an
     independent editor; the same hook on a moving shot scored 7. The hook block's shots are clips, never stills.
   - **the title card costs viewers.** The draft used to put a 2-s title card after the cold open (it no longer does); on a black ground it was the
     likeliest swipe point (qc flags "black 2.2s at 3.0s"). Drop it (the title is in the caption and the cover), or give
     the TITLE shot a `"clip"` so the title sits over moving footage.
   - for a one-turn story aim for 80 to 90 s with the reveal by about 60% (第 6 首: 0:52 of 1:26); a first cut that
     followed the comic page by page ran 2:05 with the reveal at 1:25, and the editor cut the slow setup first.
   - the reveal gets about 4 s and, if the picture needs it, the one line that makes it land. Keep its `black` short
     (0.3 s); a full second of black reads as the video ending.
   - **a jump scare is two shots, not one** (〈帶國中遊學團去日本〉, editor 6.5/10: "only half lands"). One shot
     with the ghost, its setup subtitle and a stinger at 0.0 gave the scare away at once and then stared at it for
     3.8 s; a 9:16 crop of a wide reflection panel also lost the TV frame that made it a reflection. Split it on the
     same panel: shot A pushes in on the victim's face with the setup line (「我抬頭，看到黑掉的電視螢幕。」),
     `focus` on him so the ghost is still out of frame, heartbeat that stops before the cut; shot B is `snap` with
     `focus` on the ghost, `"sub": ""`, `shake`, the stinger alone (no whoosh ahead of it), about 1.8 s, then
     `black` 0.5. A cold open that already shows the ghost is fine if the jump-scare shot shows it closer and new.
   - **What the owner signed off on (第 6 首〈帶國中遊學團去日本〉, 2026-10-23, 「可以」, posted as v4):** a 92-s cut
     that kept the comic's setup, 12 moving shots (5 scene clips, 7 character animations), a two-shot jump scare with
     a 0.8-s ghost-face hit after it, a 1.6-s staring ghost face after the last line, `vhs` on the cold open and the
     ending, `flicker2` on the phone and the empty room. Four versions went out for comparison (v1 editor 6.5 →
     v2 two-shot scare → v3 character animation → v4 scarier ghost); the owner asked for v3 and v4 themselves, which
     is the order to try next time: animate the people, then make the ghost frightening, then polish.
   - **make the ghost frightening, not just present** (owner, 2026-10-23: 「鬼加強特效 jump scare or 雜訊不好之類的，目前鬼的
     形象太不嚇人」). The comic's ghost (hair over the face, a wet dress) read as sad, not scary. Two fixes, both in
     〈帶國中遊學團去日本〉 v4: (1) draw one or two extra horror close-ups of the ghost's face for the video only, in a
     small board of their own (`reels/fx/`: copy the comic's board.json with one page of new cells, its choices.json
     and out/refs + out/sheets, then `manga.py panels --only g1,g2 --force`): one huge staring eye with a pinpoint
     pupil through parted wet hair, a mouth open far too wide, hollow black eye sockets, hands lunging at the viewer.
     Turn each into a short clip with `reel.frame_crop` (a fast zoom in the first 0.3 s for a lunge, a slow creep
     for a stare; lift the levels first, horror close-ups come out very dark) and cut them in as subliminal hits:
     0.8 s right after the jump-scare reveal, and 1.6 s after the last line, before the end card. (2) the noise fx in
     reel.py, all grey so a mono comic stays black and white: `vhs` (tape grain, scanlines, a rolling band, tears;
     on the cold open, the ending and the hits), `static` (TV snow over the first 5 frames of a cut), `negflash`
     (negative frames on the cut), `flicker2` (the light drops out; phone ringing, the empty room), and `glitch`,
     whose noise is now grey too. `black` is the black BEFORE a shot, so `black` on the shot after a scare is the
     silent beat.
   - **hold a twist image back until its line.** A panel that shows the twist (a passport with the ghost's face) must
     not be on screen before the sentence that names it. Cut it into shots with crops: build 9:16 clips from regions
     of the picked panel with ffmpeg `zoompan` (first the harmless part, then the twist on the punchline with a
     stinger, then a slow push in on it under the last line) and play them as `"clip"` shots.
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
   a slow push), black-and-white manga line art kept, faces kept still. Then,
   with ComfyUI up, `clips.py run <story>` (about 3 minutes per 5-second clip, in the background; it resumes after a
   crash). Look at each clip (a contact sheet of a frame every second or so): on 〈阿嬤〉 five of six were usable; a
   blanket turned into rippling water (p28, left static) and the cold-open room drifted toward grey rendered shading
   with a touch of colour. Redo a bad one with `--only pX --seed N` after deleting it, or leave that shot static.
   Put `"clip": "reels/clips/<prefix>_<panel>.mp4"` on those shots, with `"mono": true` when H3 let colour in.
   - **H3 drifts toward the end of a clip.** In 第 6 首 a dark ghost hand turned into her own white hand, cheeks got
     a blush and the line art turned to rendered shading in the last 1 to 1.5 s. Use the first 3 to 3.5 s (shot
     `sec` ≤ 3.5, or `clip_offset` to skip a bad start), and put "不要臉紅、不要寫實光影" and what must stay as it is
     ("那隻手一直是黑色的影子") into the prompt.
   - **H3 renders objects realistically and invents text.** The passport-on-the-table clip came out as a real
     passport with fake lettering, which also gave the twist away: leave document and screen shots static.
   - **Check the hook shot's anatomy yourself, frame by frame.** The owner caught a selfie with the screen facing
     the camera and an extra hand at her bangs in the first shot; the frames-sheet reviewer had passed it. A selfie is
     side-on: the phone's back and lens toward the viewer, its screen toward her face.
   - **Character animation (the owner, 2026-10-23: 「多加一些人物的動畫，眨眼 呼吸 流汗 發抖 等，更像動畫一些」).**
     Scenery-only clips read as a slideshow; give most character panels a clip too (〈帶國中遊學團去日本〉 v3: 12
     moving shots in 90 s, 7 of them people). The prompt that worked: HEAD 「黑白日式漫畫線稿風格的角色動畫…鏡頭固定
     不動，人物的臉、髮型、眼鏡和五官形狀完全不變，只有細微的動作，不要出現任何文字」, then three beats of small
     motion matched to the panel's emotion: blink, chest rising with breath, a sweat drop sliding down the temple,
     lips or hands trembling, swallowing, shoulders shaking with a held-back laugh or a sob, eyes sliding sideways,
     mouth moving when they speak. Close-ups held up (a frozen face with sweat; a sobbing boy); 8 of 11 were usable.
     The three that failed: invented text floating in the air beside a pointing hand (any gesture that "writes" or
     points at nothing invites lettering), a background that turned into a photo of an airport (busy real-world
     backgrounds drift), and a jump-scare panel whose victim changed expression (keep the scare panel static).
     A phone display also grew fake characters, and an empty room drifted to grey daylight photo by 1.5 s: drop
     those clips. Recheck each crop first: `clips.py plan` centres the crop, which cut the crying boy out of a
     group panel (recut src by hand at his x). `clips.py plan` rewrites plan.json with only the panels you name;
     already-made clips stay on disk.
   - **A clip can be wrong the way a drawing is** (owner's review comments, 第 24, 42, 43 首). A chair passed
     through the man's legs from 2 s on (kept the first 1.7 s, slowed to fill the shot); a hand grew larger than
     the box it came out of (new clip from a redrawn still, the box whole in frame, only the fingers moving under
     the tape); a head turned past the shoulder (still redrawn, clip remade without the turn). Look for bodies
     passing through things, sizes changing and joints bending wrong on every strip; cut with `sec` or
     `clip_offset` first, and fix the still before remaking a clip.
   - **A busy GPU hangs ComfyUI.** Three H3 runs hung at VAE decode (GPU at 0%, VRAM full) while a llama-server held
     23 GB on the same card. `nvidia-smi` first; on this two-3090 machine ComfyUI runs on GPU 0 (`--cuda-device 0`)
     and llama-server on GPU 1.
4. **Render.** `make.py <story> --version v3` (8 to 11 minutes; background). Then look at `_frames.jpg` (every word
   inside the box the apps leave free, y 270–1470, x 90–960; nothing spoils the ending in the first seconds) and read
   `_qc.txt` (no black or still stretch over 3 s, no silence, loud enough). Its level is a mean in dBFS (about
   -17 is normal); the mix is already normalised to -14 LUFS, so a reviewer asking to "raise it to -14" has
   mixed the two units. `_qc.txt` also has a `seams:` line: the cuts where the sound moves over 10 dB, found from the picture's hard cuts
   (a hit or a planned silence shows as a pair at the same second; sort them into deliberate and not, and listen to the second kind first;
   `qc.py --light` adds the brightness jumps, which a Reel's flashes make 20 to 50 entries long). Send the owner `_preview720.mp4` and the frames sheet; the owner listens with sound before
   it is posted.
4b. **Polish** (when the owner asks for 商業價值 or 打磨). A fresh subagent as a short-form horror editor gets the
   frames sheet, shots.json, qc and the comic pages, and returns a 1–10 score, the best first 3 s, a length call and
   ranked shot-list edits, each tagged **hard** (a defect if left: a changed face, a cut-off line), **craft** (better if fixed) or
   **taste** (both ways defensible: a bright or dark first frame; recorded, the owner decides). Apply them, render, and give the new frames sheet to a fresh editor; stop at "ship it" or
   after three rounds. 第 6 首 went 6 → 7 in two rounds; the edits were a moving hook, no title card, an 86-s cut,
   a held-back twist, and readable subtitles. The editor cannot hear: the owner still listens before posting.
   〈灰外套的男人〉 went 6/5 → 6.5/7.5 in two rounds (part 1 / part 2). What the editors caught: a voice shot with
   「／」 printed the slash and cut the line off (fixed in versions.py: voice text now wraps and splits into beats
   like subtitles); an end-card line over about 10 characters runs off both edges; part 2 must not open on 「上集：」
   (strangers swipe) but restate the premise in one beat; a character revealed in part 2 (the 阿伯) must appear in
   part 1, or the twist reads as invented; end part 1 on a question the next part answers (「我們抓到跟蹤狂了。」,
   end card 「下集：抓到的，不是他。」). Cutting a bright shot between two night shots made qc flag "black":
   keep a light shot between dark ones.
   **The editors' score is not the owner's.** 〈東河河口的鈴鐺〉 went 6 → 6.5 → 7 (est. 8) in three rounds, 80 s →
   65 s, by cutting the setup (quitting the job, the landlady) and opening on the climax; the owner compared them and
   kept the 80-s version (「上一版1:20s的比較好」). Keep every earlier version in `drafts/` and let the owner compare;
   prefer edits that keep the comic's setup to ones that cut it for length. A full-height crop cannot
   zoom: for a tighter face (a comic 阿伯 on a scooter read as a joke) or a pan along a line from her to the bell,
   render the shot yourself with `reel.frame_crop` on a crop of the panel, pipe the frames to ffmpeg, and play it as
   a `"clip"`. Two editors in a row can contradict each other (keep 阿凱 / cut 阿凱): keep the one with the reason
   the story needs. An editor may also ask to put back a clip you dropped for drifting or fake text: it only sees the
   frames sheet, so keep it dropped and say why.
   **Too fast is a note too** (owner on 第 24 首, a 短篇: 「節奏有點太快」). Inside the 45 s, drop two texture
   shots and give the shots after the turn 0.4 to 0.6 s more each (the last one 1.4 → 2.4 s) rather than keep
   every panel at the same short length.
5. **Changes.** Subtitle, timing, picture: edit shots.json and render again. Music or sound only: `--reuse`.

## What the engine does (scripts/reel.py, versions.py, sfx.py)

- Panels upscaled 2× and sharpened; screen and phone lettering drawn back into the picture.
- Sounds a shot can name (`make.py --check` refuses others): stinger (the jumpscare sample), riser, whoosh, ping,
  ring (an old desk phone's bell, synthesised), whisper, heartbeat, drone, wind, insects, rustle, zipper, footsteps,
  page, pop.
- Subtitles: white with a 7-px black stroke on a dark strip, fading in within 0.3 s (the first version's grey,
  3-px text was unreadable on light panels and still faint at the 1.5-s frame samples).
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

## 審稿後修改 (since 2026-11-02)

Every 鬼唱詩 story is reviewed by the owner on https://monitor.csiesheep.com/ghost/review/ before it posts. Comments on the Reel carry a time (正式版 mm:ss or 試驗版 B mm:ss): find that shot in reels/shots.json (the frames sheet helps), edit it, `make.py --check`, render, read qc (短篇 still ≤ 45.0 s). A change after the opening goes into `cuts.trialB` too, and B is re-rendered with `--cut trialB` into reels/trial_B/. The whole loop: ~/.claude/skills/auto_promotion/references/ghost_revise.md.
