---
name: ghost-comic
description: Turn a ghost story (one from the ghost-story skill, or any story text the user gives) into black-and-white manga pages read right to left, with vertical Traditional Chinese lettering, drawn panel by panel with Qwen Image 2.1 on the local ComfyUI and laid out by a script. HxH-style paneling, bigger panels for what matters, a page-1 setup, and characters with memorable features. It runs as gates the owner decides at: style (3 examples), character and scene designs (3 versions each), then a wireframe of every page. Use whenever the user wants a story drawn as a comic, 漫畫, 鬼故事漫畫, 把這篇畫成漫畫, 漫畫化, 分鏡, 頁漫, 條漫, manga pages or a storyboard from a story, or wants panels of an existing comic redrawn, even if they do not name ComfyUI or Qwen. Not for single illustrations or for photos of real people.
---

# Ghost comic

Makes a comic out of a story: a storyboard file (`board.json`), character and scene sheets the owner
picks, panels generated against those sheets, and pages laid out with lettering by
`scripts/manga.py`. Everything the model draws is image only; every word on the page is drawn by
the script. The first full run (〈一個人在家開視訊〉, 7 pages, 33 panels) is the example in
`assets/`; its lessons are in `references/`.

Read before writing a board:
- `references/paneling.md`: how to cut a page, which panel gets to be big, page 1, dialogue,
  horror timing, how much of the ghost to show, lighting continuity.
- `references/prompting.md`: what each panel prompt contains, and a table of failures seen with
  their fixes. Most panel redraws come from ignoring a row of that table.
- `references/board_format.md`: every field of `board.json`.
- `references/qa_checklist.md`: what the independent checker looks for in every candidate, and how
  it reports.

## Requirements

- Local ComfyUI on `http://127.0.0.1:8188` (or `COMFY_URL`) with
  `qwen_image_2.1_int8_convrot.safetensors`, `qwen3vl_8b_int8_convrot.safetensors` and
  `qwen_image_2.1_vae_bf16.safetensors`. `manga.py check` says what is missing.
- Python 3.10+ with Pillow, run as `py -X utf8` on Windows. A CJK font with vertical punctuation
  forms (Microsoft JhengHei or Noto Sans/Serif TC).
- A work folder of its own, outside `AppData\Roaming\Claude\` (Python may not see files the
  desktop app writes there), e.g. `C:\Users\sheep\Pictures\ghost_comic\<story>`. All commands run
  from it; output goes to `out/`.

## Steps

The owner decides at three gates before any panel is drawn. Do not pick for them, and do not start
the panel run until all three are done: they asked for exactly this order after a run where the
style was wrong and the sheets were picked for them.

1. **Board.** Copy `assets/example_board.json` into the work folder as `board.json` and rewrite it
   for the story: characters with at least two memorable features each (`features` in Chinese,
   the same features in `desc` and in every panel prompt), scenes, the `consistency` block
   (fixed room layout, fixed heights), the `lights` states, pages, panel labels and lettering.
   Give every panel its `scene` and `light` explicitly, and a `cast` when a character is drawn
   from words alone. If the story came from
   ghost-story, carry its skeleton over: the mechanism sets the device (proxy_sighting means the
   ghost appears only inside the other person's screen), and the ghost cap sets how much of the
   ghost is drawn (paneling.md). Then run `py -X utf8 "<skill dir>/scripts/manga.py" check`.
2. **Gate 1: style.** `manga.py styles --panel <the main character's intro panel>` draws that
   panel and the first scene in every `style_options` entry. Send `out/pick_style.png`, describe
   each option in a line, recommend one, wait. Then `manga.py choose style=<key>`. Note any
   adjustments the owner asks for (the first owner said "the dog's lines simpler") in the
   descriptions.
3. **Gate 2: designs.** `manga.py sheets` draws 3 versions of every character and scene. Send
   `out/pick_characters.png` and `out/pick_scenes.png`; for each, say in a table what differs and
   what is wrong (two pairs of glasses, a white front view of a dark dog, a person's knees in a
   scene). Wait for numbers, `manga.py choose me=1 fang=3 room=3 ...`. Fix defects in the picked
   version with an edit (prompting.md shows the wording) and offer the fixed candidates. Then
   `manga.py refs`: references become one view and grayscale, plus `:head` and `:bust` crops.
   Use `me:head` for close-ups and `me:bust` for seated or waist-up panels: a full-body standing
   sheet makes the model draw the character standing.
4. **Gate 3: layout.** `manga.py plan` renders every page as numbered placeholders with the real
   lettering. Send `out/plan.png`; changing a panel's size, order or line now costs nothing.
After the three gates, quality is yours: the owner's words were 由你來檢查. Check every panel
before the owner sees it, and report what failed and how it was fixed as a table, not
candidate-by-candidate questions.

5. **Panels.** `manga.py lint` first: the prompting.md table as checks (a crossed-arms full-body
   shot, a reference never mentioned, a full-body sheet in a close-up, words that draw walls,
   signs or photographic light). `panels` runs it too and refuses to draw on errors. Then
   `manga.py panels` (pass 1, 2 candidates each, `n` in the board overrides). If the first few
   results of a batch share one flaw, stop the batch and fix the cause before it spends the GPU
   on the rest.
6. **Independent check.** For each finished batch, `manga.py review --page N` (or `--unpicked`,
   or ids) writes a brief: head count, each character's features and scale, light, scene, what the
   panel must show, and every candidate's path. Spawn a fresh subagent with that brief and
   `references/qa_checklist.md`; it opens every candidate, counts heads, hands and feet, and
   returns pass or fail per image with a suggested pick. You wrote the prompts and will see what
   you meant to draw: the four-handed 學長 passed your own look and was caught by the owner. Pick
   only among candidates the checker passed and that you agree with (`manga.py choose p5=2 ...`);
   rewrite and redraw the rest with `--only`, and check the redraws the same way. Then
   `manga.py panels --pass 2` (and 3) for panels that use other panels as references, and check
   again.
7. **Pages.** `manga.py pages` writes `out/pages/page_NN.png`, `out/comic.pdf` and
   `out/overview.jpg`. Look at every page yourself before sending: text over a face, a reading
   order that jumps, a room whose light changes without a reason. Send the pages and the PDF, then
   list the weak panels honestly with what a redraw would change.
8. **Fix round.** Map each note of the owner's to a panel id (if they name a page that does not
   contain what they describe, say which panel you think they mean), rewrite the prompt, redraw
   with `n: 3`, re-lay out only the pages that changed (`pages --pages 3,5`), send them. When the
   note names a kind of defect (extra hands, the wrong lighting), sweep every picked panel for the
   same defect before replying, and add a row to prompting.md.

When the owner asks to see progress mid-run, lay out what is picked so far (`pages --pages 1,2`;
unpicked panels show as labelled placeholders) instead of saying it is not ready.

Time on an RTX 3090: a panel with references takes 47 to 115 s per image and one without takes 23 to 36 s, with 2 to 3 candidates per panel. The first comic (33 panels, every gate and redraw) took about 81 minutes of GPU time, the second (32 panels) about 61. State the estimate before each long run.

## Rules

- **Fiction only, no real people.** Characters are invented; never draw a real, identifiable
  person or a recognisable business, temple or hospital. If the user supplies a photo of a real
  person as a character, decline that part.
- **Paneling, not style.** Borrow paneling principles from manga the owner names; never put an
  author's name or a work's title into an image prompt, and do not imitate a living artist's
  drawing style.
- **The ghost stays restrained by default.** Even at ghost cap 3, the ghost is smaller than the
  living characters and its face mostly in shadow. The owner prefers 留白 and asked for exactly
  this after seeing a large, clear one. Draw it clearly only if the user asks.
- **No text from the model.** No signs, posters, screens with writing or labels in prompts;
  lettering is the script's job.

## What it learned

- A two-figure character sheet used as a reference makes two of the same person in a panel.
  Crop it to one view (`refs`) and say "Only one person in the frame".
- Lighting stays consistent only if every panel of a story beat is drawn against an approved
  panel in that lighting state, not against a daytime scene sheet.
- Write positions and what is visible ("standing between the sofa and the coffee table"), not
  abstract actions ("halfway through sitting down") or optics ("his reflection").
- Size consistency has to be written down: fixed heights, "her head is no bigger than his head",
  "the same size in the frame as in <image2>".
- Same-framing edits work: keep the camera angle and composition, add only the ghost. That is the
  strongest horror device a comic version has.
- A reference image brings its whole composition and pose, not just the face or the room: a panel
  of four hikers put two 小美 in the next one, a standing sheet kept a seated friend standing.
  Crop characters to `:head` or `:bust`, use the empty scene sheet instead of a busy panel, and
  mention every reference in the prompt.
- Bind scene layouts and lighting per panel (`scene`, `light`); inferring them from references
  put tents into a view from inside a tent and blacked out daytime backgrounds.
- The writer of the prompts is a poor checker of the images. An independent pass that counts
  heads, hands and feet catches what a glance does not.
