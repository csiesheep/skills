---
name: ghost-comic-v2
description: Turn a ghost story into colour comic pages in the 水墨淡彩 style - Chinese ink wash brushwork with faint tints of colour on the living and an ink-grey ghost - drawn with Qwen Image 2.1 on the local ComfyUI and laid out by ghost-comic's manga.py (same board, gates, checker, reader check, export and reels). Adds what the style needs - the style said again at the end of every panel prompt, sheets drawn in plain ink and then tinted by editing the picked picture, colour kept through refs and pages, and the wording that keeps a lit ghost frightening. Use whenever the user asks for ghost-comic-v2, 水墨漫畫, 水墨淡彩, 淡彩漫畫, an ink-wash or colour version of a ghost comic, 用新風格畫漫畫, or wants a story drawn like 〈卡丁車的白色安全帽〉, even if they only say "用水墨風格畫成漫畫". For the black-and-white manga line art use ghost-comic.
---

# Ghost comic v2: 水墨淡彩

ghost-comic draws black-and-white manga line art. This skill draws the same comic in the style the owner chose on
2026-11-21 from a 16-style test (Obsidian `Projects/ghost story/comic styles.md`, images in
`C:/Users/sheep/Pictures/gui_chang_shi/research/style_test_2026-11-21/`):
- the brushwork of a Chinese ink wash painting (varied strokes, dry brush, grey washes on rice paper);
- faint transparent tints on the living (skin, lips, a few small things);
- the ghost left ink grey, the one colourless figure.

The style was refined in two steps:
- The first colour try was rejected: 「不行，風格變了，維持之前水墨風格，只是加上淡彩」.
- The tinted version was accepted: 「C」, then 「好，都加上淡彩」.

**Everything else is ghost-comic.** Read its `SKILL.md` and the references it lists, and follow its steps (story
gate, board, gates, panels, independent check, pages, reader check, fix round, export, reels) and its rules. This
file only says what changes. Scripts:
- `<v1>/scripts/manga.py` and `<v1>/scripts/from_screenplay.py`, where `<v1>` is the installed `ghost-comic`
  folder beside this one;
- `<this skill>/scripts/ink_tint.py`.

Run all of them from the comic's work folder.

## What changes, step by step

1. **Board.** Write it as ghost-comic says (from a v3/v2 screenplay with `from_screenplay.py`, or by hand), then:
   ```
   py -X utf8 "<this skill>/scripts/ink_tint.py" apply
   ```
   - **What `apply` does:**
     - adds the style as `style_options.ink_tint` and selects it in `board.json` and `choices.json`;
     - sets `"colour": true` and `"mono": false`;
     - appends `Drawn entirely in this style: <the style>` to every panel prompt, once.
   - **Why the style is said last:** on a long panel prompt (1,200 to 1,800 characters), Qwen dropped a style given
     only at the start, and three different styles came out as the same realistic illustration. Saying it again
     last brought the ink back; it did not help 厚塗, which this skill does not use.
   - **Board builders:** a board built by a script (`build_board.py`) is rewritten on every run, so run `apply`
     after it, or put the same three things in the builder.
   - **`ink_tint.py check`** (no GPU) lists light, scene and prompt words that pull back to manga line art
     (`line art`, `screentone`, `halftone`, `manga`, `cel shading`, `clean white`). Rewrite them as ink:
     「the light in dark ink wash」, 「a pale grey wash in the background」.
   - **`lint`:** with `colour` on, `manga.py lint` no longer warns about colour words and light words. Those two
     warnings exist for black-and-white pages.
2. **Gate 1, style.** Skip it: the style is fixed. Draw one panel for the owner only if they ask to compare
   (`manga.py styles --panel <id>` with the old options still in `style_options`).
3. **Gate 2, designs, in two passes.**
   1. `manga.py sheets` draws 3 versions of every character and scene in plain ink (the style's `sheet` text says
      "almost no colour"). The owner picks as in ghost-comic: `manga.py choose me=2 ...`.
   2. Then add the colour by editing the picked sheet:
      ```
      py -X utf8 "<this skill>/scripts/ink_tint.py" tint          (or: tint me zhe s1)
      ```
      Each picked sheet is redrawn with the prompt "keep its exact brushwork … add only faint tints over the ink on
      {where}", one image each, about 35 to 40 s. It is written as `<sheet>_tint.png`, and the pick then points at
      it.
   - **Why two passes:** written as words alone, "ink wash with light colour" became soft watercolour fashion
     illustration, with blue jeans and a different face, twice. Edited from the ink picture, the brushwork,
     poses and face stayed.
   - **Write where the colour goes**, or the tint is barely visible:
     - a character's `"tint"`, e.g. 「her skin and lips, a faint pale cream-pink on the puffer jacket, a faint pale
       blue on the jeans」;
     - `board.scene_tint.<scene>`, e.g. 「the lamp light (faint warm yellow) and the plastic chairs (faded pale
       blue)」.
     - With only the default wording, 阿哲's tint was near grey and a rest-area scene stayed grey.
   - **The ghost:** a character with `"ghost": true` is skipped and stays ink grey. Give her a `"tint"` only if
     the owner asks for colour on her.
   - **Then refs and the rest:** send the tinted sheets with what the tint added, then run `manga.py refs`. With
     `colour` on, refs keep their colour (ghost-comic makes them greyscale).
4. **Gate 3, layout, then panels.** As in ghost-comic. Panels need **one pass**: drawn against tinted refs they
   came out ink and tint together, so nothing is drawn twice.
   - **Measured on 〈卡丁車〉 p2 and p17:** about 80 s per image with 2 or 3 references, 2 candidates per panel.
   - **Pages:** `manga.py pages` keeps the colour.
   - **Checker brief:** add one line to every `review` brief: "the picture is Chinese ink wash with faint
     colour; fail a candidate drawn as watercolour illustration, clean line art or full colour".

## From a ghost-story-weitong-v4 long story

The first whole comic in this style, 〈動物醫院的兩點十分〉 (2026-11-22), came from a v4 story: 2,868 characters
told aloud in about 10.6 minutes. It became 10 pages, 41 panels and about 100 GPU minutes. v4 writes no
screenplay, so:

1. **Write the comic script first.** Use the v3 screenplay format that `from_screenplay.py` reads, in
   `film/screenplay.md`:
   - the header with **長度** and **最大畫面**;
   - **人物**, with an English id for each person: 「**阿斌（bin）**：…」. Without ids they came out as c2, c3 and c5;
   - scenes and `[beat]` lines;
   - `**誰**（note）：text` lines. A line said through an intercom, a phone or a speaker (the note says 對講機, 電話,
     廣播 …) becomes a `voice` bubble.

   Then run `from_screenplay.py`. Every line it writes carries `who`.
2. **Cut the dialogue, not the story.** v4 is 35 to 45% dialogue, written as tagless speech that will not fit a
   bubble. Shorten each line to its point. Keep everything else:
   - every joke that comes back later, and the line it comes back in;
   - the twist sentences, and every day and time marker. `speakers.md` lists them under 「不能縮掉的句子」.
     Dropping 「我不記得我走進過倉庫」 made the CCTV twist unreadable for the blind reader;
   - who is in which panel.
3. **The ghost's face is the owner's call.** v4's 「不寫五官」 is a rule for the words only. Ask once, at the story gate.
4. **GPU:** v4's blind test uses H3 voices, and this skill uses Qwen. Finish the story, its blind test included,
   before drawing. Never interleave the two.

## When the owner hands over the gates

「you can decide everything until the comic is ready」 (2026-11-21): the story gate and gates 1 to 3 become mine.
Pick the sheets and the layout myself, with an independent checker on every pick, and note each choice in
`pipeline_notes.md`. The owner still gets the story and the finished pages, and the delivery says what was
accepted with a known flaw.

## Design gate rules (learned on the first whole comic)

- **Draw the ghost's sheet as a frightening adult from the start.** Her first sheet had big doll eyes. Every panel
  that used `ghost:head` came out cute, and the reveal panels had to drop her reference and describe "a grown woman
  of about twenty-five, not a child and not a doll: a long gaunt adult face, sunken cheeks…" in words. Reject a
  doll face at the design gate.
- **Sheets in rough dry brush.** Smooth sheets gave indoor panels that read as fine-line watercolour illustration.
  `ink_tint.py`'s sheet style now asks for rough, broken dry-brush strokes.
- **Scenes say "the walls are bare: no posters, no notices, no signs, no writing".** Without it, every indoor
  panel got a wall of fake notices, and a checker failed them all.
- **`scene_tint` names where each colour sits.** "the green snack packets" put pale green on the waiting room's
  bench cushions. Write "the green snack packet taped on top of each machine".
- **A picture that fills the frame has no scene.** An X-ray film, a phone screen or a radiograph on a light box gets
  `"scene": []` and "no room, no table, no walls". With the X-ray room's layout, p23 and p32 drew the whole room.
  `lint` warns about it now.

## Prompt rules for this style

- **Light the ghost, then say why she is frightening.** "The ghost's face is lit and clearly visible" alone made
  every ghost pretty or doll-like on Qwen. Follow it with the horror in plain words, in her `desc` and in the reveal
  panel: 「completely black eyes with no whites like two holes, grey-white dead skin with fine cracks and dark veins,
  sunken cheeks, cracked lips, not pretty and not doll-like」. Qwen still leans toward a pretty face. Check the
  reveal candidates for it, and say in the brief that a doll face fails.
- **Make a short-haired woman read as a woman.** In ink, very short hair drew a boy: in H3, in plain Qwen and in ink
  with feminine words. What worked was a colour mark that survives a helmet or a long shot: small gold hoop
  earrings, soft pink lips, red sneakers. Put the mark in her `desc` and in every panel that shows her.
- **Leave colour examples out of the style sentence.** A first draft listed "a red shoe, a gold earring" there,
  and red shoes appeared on the wrong design. The style says only "skin, lips and a few small details". Each
  colour belongs to the character or scene that has it.
- **Write a strong expression, then check it face by face.** The sheets are drawn "neutral expression". On
  〈動物醫院的兩點十分〉 the panels kept that face. Three checkers rated 25 of 40 faces weak (the narrator in 16 of 17
  panels, the vet in 7 of 8), one of them wrong. The owner's words: 「主角和院長表情都一樣，情緒太少」. Two rules:
  - **In the prompt:** spell out the face in each panel's prompt, in manga terms. For example: "eyes wide open with
    tiny pupils, eyebrows high, mouth open and trembling, cold sweat". Words like "scared" or "tense" alone are
    not enough.
  - **After picking:** have checkers rate every face against its intended emotion (ok, weak or wrong) and mark the
    face boxes on a 0.1 grid. Those boxes become the panel's `faces`. Fix each weak face with
    `manga.py repaint <pick> --box <face box widened by about 45%> --prompt "Change only the facial expression …"`,
    with `--n 2`. This changes the face and keeps the rest of the picture. It took p25 from calm to terrified in one
    run of about 40 s. Across 18 panels it took 19 GPU minutes, and every panel had one usable result.
  - **Don't name an accessory the face in the box doesn't have.** A fixed "keep the same … glasses" in the prompt
    put glasses on the narrator in 3 of 26 results (p11, p14, p17). List only what the people inside the box are
    actually wearing.
- **Lettering keeps clear of faces and names its speaker.** Give every speech and voice line a `who` and `pos:
  "auto"`, and give the panel its `faces` (ghost-comic `board_format.md`). The owner (2026-11-22) asked for three
  things:
  - 「字框儘量不要擋住人臉」;
  - a tail toward the speaker when two people in a panel talk;
  - a small face under the bubble when the speaker is outside the panel.
- **Keep ghost-comic's lettering, paneling and checks.** The style changes the picture, not the reading.

## Requirements

Those of ghost-comic: the local ComfyUI with the Qwen Image 2.1 models, Python 3.10+ with Pillow, and a work folder
outside `AppData\Roaming\Claude\`. `ink_tint.py` imports ghost-comic's `comfy.py`, so both skills must be installed
side by side (`~/.claude/skills/ghost-comic` and `~/.claude/skills/ghost-comic-v2`).

## What was tested (2026-11-21)

- **Tested:**
  - On 〈卡丁車的白色安全帽〉 (`backlog/kart_helmet/comic/`): sheets drawn in ink, tinted by editing the picked sheet
    (that comic used its own `tint_me.py`, the script this one was generalised from), refs, then p2 and p17 drawn
    once each against the tinted refs.
  - `ink_tint.py check`, `apply` (twice: the second run adds nothing), and `tint` on a copy of that board in
    a v1 state (style A, mono): 阿哲 and the rest area were tinted, and the ghost was skipped.
  - After `manga.py refs`, the refs kept their colour: mean saturation 4.1 for 阿哲 and 14.9 for the rest area,
    0 for the ink-grey ghost.
  - `tests/test_ink_tint.py` covers `apply` and `check` (no GPU).
  - ghost-comic's 51 tests pass with the `colour` flag.
  - **A whole comic, 2026-11-22:** 〈動物醫院的兩點十分〉 (`backlog/vet_night_xray/comic/`), 10 pages and 41 panels in
    colour.
    - GPU: sheets 13 min, panels 67 min, face repaints 20 min.
    - Four independent checkers rated every candidate. 11 panels were redrawn for story errors, and 27 were
      accepted with cosmetic flaws.
    - Four blind readers, two before the owner's review and two after it, followed the plot. Their speaker and
      reading-order trouble was fixed in the lettering.
    - `pages` keeps the colour.
- **Not tested yet:**
  - `export` and `reel` with `colour` on;
  - `tint`'s default wording with nothing written in `tint` or `scene_tint`, which came out too faint.
