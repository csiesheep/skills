---
name: china_life_person_reel
description: Make a 9:16 Reel about one person's life in 生在中國 (games.csiesheep.com/china_life) — a seed from the game's engine played and recorded in headless Chrome, with ink-wash portraits of that person growing up drawn on the local ComfyUI (one face from childhood to old age), a full-screen portrait card at each age and the same small portrait in the bottom-right corner of the gameplay, decision cards at reading speed, optional big route map from high-res map captures, generated music cut into a continuous bed, a stats card from engine simulations, 0.5 s dissolves, -14 LUFS, a 720p copy, a ≤9.5 MB upload copy and a portrait-grid cover, plus captions that leave suspense and posting to Instagram, Threads, YouTube and the Facebook Page when asked. Use whenever the user asks for a reel / short / 影片 about a person, a life, 一生, 某個人的一生, 古代女生的一生, 一生走了多遠, 從農民到當官, 同年同月生, or any of the china_life reel ideas that follow one life, or says "make a reel of seed N", even if they only describe the kind of life they want. Not for reels of other games (covervote), posting the reel (game-promote, social posts), or the ghost brand (ghost-reel).
---

# China life person reel

One life from the game, told so a stranger scrolling past understands it: who she was, what the game asked her at each
turn, what she chose, how long she lived. The game is the footage; portraits give the person a face; captions say only
what the screen shows. `references/lessons.md` has what the first two reels taught, including the owner's corrections:
read it before cutting.

Everything for one reel lives in one folder, outside the game repo:
`C:/Users/sheep/Pictures/csiesheep_games/reels/china_life/<N>/` with `rec/`, `portraits/`, `music/`, `cards/`,
`tools/build_plan.py`, `plan.json`, `out/`. `<skill>` below is `~/.claude/skills/china_life_person_reel`.

## Rules

- **Recording never counts as a player:** record.mjs always loads the game with `internal=1` (no GA, no 眾生簿 upload).
- **The person is the engine's.** Facts in captions come from the recording's own lines (timeline.py), numbers on a
  stats card from engine runs, marked 「遊戲模擬，不是史料統計」. Place names as the screen shows them.
- **Plain and respectful.** Child deaths, foot binding, famine and war are shown with the game's own text; captions do
  not dramatize, and portraits do not show bound feet or violence. Prefer lives that end before 1949.
- **Readable:** no zoom on gameplay, decisions at real speed with a hold, key rows held, 0.5 s dissolves, corner
  portrait one size, sfx -14 dB (lessons.md has the timings).
- Show the user a preview contact sheet and the finished 720p file; they decide what changes.

## Steps

### 1. Pick the life

If the user gave a seed and period, show it; otherwise scan for the kind of life they asked for:

    node <skill>/scripts/life.mjs show <seed> <period_id> [F|M] [status]
    node <skill>/scripts/life.mjs scan --periods ming_late,qing_mid --sex F --need footbind,flee_famine --min-age 50 --max-death-year 1945
    node <skill>/scripts/life.mjs periods

Pick a life whose turns carry the reel's idea (several decisions, a move, a family arc) and that lives long enough for
the portraits to age. Tell the user the person in two lines before recording. For a route reel, look for moves
(`--min-moves 2`); they are rare.

### 2. Record

    node <skill>/scripts/record.mjs life <reel>/rec/life --seed <seed> --extra "&period=<id>&sex=F" [--mapshots]
    node <skill>/scripts/record.mjs home <reel>/rec/home

About 6 minutes for a 70-year life (run in the background). `--mapshots` only when the reel needs the big map. Then:

    py -X utf8 <skill>/scripts/timeline.py <reel>/rec/life --ages 0,3,6,15,17,27,30,50,70

Read `rec/life/end_card.png` for the name, birthplace and the game's own summary.

### 3. Portraits

Write `<reel>/person.json` (shape in `templates/person.example.json`): a base description (age about 17–20, dynasty,
region, class, hair, clothes; no style words) and one line per age the reel will show, each tied to that age's event
in this life. Then:

    py -X utf8 <skill>/scripts/portraits.py <reel>/person.json base          # 4 candidates
    (look at them, pick the most natural face)
    py -X utf8 <skill>/scripts/portraits.py <reel>/person.json ages base2    # one Qwen run, all ages
    py -X utf8 <skill>/scripts/portraits.py <reel>/person.json clean

Check a contact sheet: same face, ages read right, no text. Redraw single ages by naming them after `base2`.

### 4. Music

Copy `<skill>/assets/ace_music.json` to `<reel>/music/`, set its slots with the comfy-mcp tools (`94.tags` for the
mood, `98.seconds` and `94.duration` to the video length + 15, `94.bpm`, `94.keyscale`, `3.seed` and `94.seed`,
`107.filename_prefix` `audio/china_life_<tag>`), run it, copy the flac from `ComfyUI/output/audio/` into `music/`, then:

    py -X utf8 <skill>/scripts/bed.py --check <flac>
    py -X utf8 <skill>/scripts/bed.py <reel>/music/bed.flac --min <video length + 10> <flac> [<another flac>]

### 5. Plan and render

Copy `templates/build_plan.py` to `<reel>/tools/`, fill the segments from the timeline (one portrait card per age, then
that age's decision or rows with `inset=P(age)`), and, if the reel has numbers, make the stats card with
`cards.py stats`. Then:

    py -X utf8 <reel>/tools/build_plan.py
    py -X utf8 <skill>/scripts/render.py <reel>/plan.json --preview
    py -X utf8 <skill>/scripts/finish.py check <reel>/out/preview.mp4 <a dozen times spread over the reel>

Look at `out/check.jpg`: captions not hiding the line they explain, corner portrait not on an option's text, big map
showing the route, no stray frames. Fix and preview again; then the full render (background, a few minutes):

    py -X utf8 <skill>/scripts/render.py <reel>/plan.json
    py -X utf8 <skill>/scripts/finish.py final <reel>/out/reel.mp4
    py -X utf8 <skill>/scripts/finish.py upload <reel>/out/reel.mp4      # reel_upload.mp4 ≤ 9.5 MB for posting from Chrome
    py -X utf8 <skill>/scripts/cards.py cover <reel>/out/reel_cover.jpg "<大標>" "<副標>" <4 portraits with :年紀>

### 6. Deliver

Send `out/reel_720p.mp4` and the cover with SendUserFile; say the length, loudness, and anything that is not the game's
(a real-world distance, a merged music bed). The user's notes go back into the plan; durable ones go into
`references/lessons.md`.

### 7. Captions and posting (when the user asks)

Write `<reel>/captions.md` for Threads, Instagram, YouTube (title + description), Facebook and TikTok in the format of
`reels/china_life/3/captions.md`. **Every caption leaves suspense** (owner, 2026-10-23): the hook, the person and the
first one or two turns, then 「她後來怎麼了？影片看到最後」, the link, 「肖像為 AI 繪製」 and the 遊戲模擬 note; never the
ending or how long they lived. Show the texts; post only after the user says so, one platform at a time, as
小羊遊戲間 / csiesheep.games, turning on each platform's AI label, then put every account back.
`references/posting.md` has the exact flow per site (cover upload, Original crop on Instagram, Threads' 15-minute edit
window, where Facebook hides 編輯貼文) and how to edit a caption after posting. Record the links in captions.md.
