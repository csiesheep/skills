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
- **Not tested yet:**
  - a whole comic to the end;
  - `manga.py pages`, `export` and `reel` with `colour` on (the code keeps colour where it used to greyscale,
    but no page has been laid out in colour);
  - the checker and the blind reader on ink pages;
  - `tint`'s default wording with nothing written in `tint` or `scene_tint`, which came out too faint.
