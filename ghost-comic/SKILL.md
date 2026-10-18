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
- `references/qa_checklist.md`: what the independent checker looks for in every candidate, how
  strict to be, and how it reports.
- `references/reader_check.md`: what a first-time reader of the finished pages is asked, given
  to a fresh subagent with nothing but the page images.

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

0. **Story first.** When one request asks for a story and its comic (產生鬼故事…畫漫畫), write
   the story with ghost-story, send it, and wait for the owner's OK before step 1. A comic costs
   one to two and a half GPU hours; the owner read 〈代班那台電梯一直超載〉 only after its seven
   pages were drawn, said 「這故事不好，放棄」, and all of it was thrown away. The next story was
   sent first and approved with one word. A story the owner supplies needs no gate.
1. **Board.** Copy `assets/example_board.json` into the work folder as `board.json` and rewrite it
   for the story: characters with at least two memorable features each (`features` in Chinese,
   the same features in `desc` and in every panel prompt), scenes, the `consistency` block
   (fixed room layout, fixed heights), the `lights` states, pages, panel labels and lettering.
   Write each room's layout as a floor plan, not a mood: which wall the window and the door are
   in, where each piece of furniture stands against which wall, which way the objects the story
   turns face. Check it against the story's own geometry (a knock "right next to my head" puts
   the window by the head of the bed). In the sixth comic the room was described loosely, and
   the window, the bed and the dresser moved from panel to panel until the owner pointed at it.
   Give every panel its `scene` and `light` explicitly, and a `cast` when a character is drawn
   from words alone. Name every speaking character in the panel where they are first drawn (a
   `tag` or a caption; `intro` points at another panel on the same page, `ghost: true` exempts
   the ghost), and draw anyone the dialogue needs the reader to recognise (a dead aunt as an
   old photo on the altar). If the story came from
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
   lettering, and prints `WARN lettering` for boxes in one panel that cover each other; move them
   first. Send `out/plan.png`; changing a panel's size, order or line now costs nothing.
After the three gates, quality is yours: the owner's words were 由你來檢查. Check every panel
before the owner sees it, and report what failed and how it was fixed as a table, not
candidate-by-candidate questions.

5. **Panels.** `manga.py lint` first: the prompting.md table as checks (a crossed-arms full-body
   shot, a reference never mentioned, a full-body sheet in a close-up, a head crop for a scared
   or crying face, a seated character with a scene reference, a scene sheet in a panel with
   people, a character unnamed where first drawn, words that draw walls, signs or photographic
   light). `panels` runs it too and refuses to draw on errors. Then
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
   rewrite and redraw the rest with `--only`, and check the redraws the same way with
   `review <ids> --new`, which lists only candidates no earlier brief did. The brief also lists
   the picked panels a candidate has to match (its `panel:` references, `continuity`, the
   nearest picked panel of the same scene). Then `manga.py panels --pass 2` (and 3) for panels
   that use other panels as references, and check again. Run the checker on one batch while the
   GPU draws the next; neither waits for the other. A candidate that is right except for one
   small thing (a collar, the hair, a hand) is fixed with `manga.py repaint <candidate> --box
   x0,y0,x1,y1 --prompt "..."`, which redraws only that area at crop size; an edit of the whole
   panel ignores details that small and changes what was right. Three things repaint cannot do
   are done by hand, each writing a new candidate: `manga.py fill <candidate> --box ...` turns
   solid black inside the box white (a daytime window the line art drew black; three repaints
   left it black), `tone --poly "x,y ..." --mode dots|strokes` puts screentone or stubble on the
   white paper inside a polygon (a buzz cut that read as bald; two repaints made it paler), and
   `crop --box ...` cuts a region out and enlarges it (the close-up four draws in a wide cell
   would not give). Look at the first few results of every batch before the rest draw: in the
   sixth comic page 1 showed everyone staring at the reader, and fixing the gaze before going on
   saved the other nine pages. When every panel is picked,
   `manga.py review --cast all` writes one brief per character: every picked panel they are in,
   beside their sheet. Give each to a fresh checker with the checklist's 跨格檢查. Checking panel
   by panel cannot see that a face or a hair colour changed between panels: in the fifth comic
   阿嬤's close-up, drawn from words, was not her face, and the boy's hair was black on one page
   and white on the next. Both had passed, and the owner found both; run blind on those panels,
   the cast check caught both, and a bangle on the wrong wrist in three more.
   `manga.py review --scene all` does the same for places: every picked panel set in a room,
   against its fixed layout, for the checklist's 場景跨格檢查. Redraw the room's wide shot first
   from the plan and make the later views of that room same-framing edits of a picked panel
   (the night view of the lit room is the day view with the light changed), so the layout is
   carried by a picture rather than redrawn from words each time.
7. **Pages.** `manga.py pages` writes `out/pages/page_NN.png`, `out/comic.pdf` and
   `out/overview.jpg`, and prints `WARN lettering` like `plan`. Look at every page yourself:
   text over a face, a bubble beside someone who is not speaking, a reading order that jumps, a
   crop that cuts off what matters (`focus`), a room whose light changes without a reason.
   Lettering fixes cost no GPU: `mirror` when the first speaker stands on the left, `zoom` to
   free room beside a close-up on a flat background.
8. **Reader check.** `manga.py review --read` writes `out/review/read.md` (the page images in
   reading order, nothing else) and `read_key.md` (who everyone is, where they first appear,
   every line in order). Give a fresh subagent `read.md` and `references/reader_check.md` only:
   it retells the story, names every character, says who speaks each line and where it got
   stuck. Compare with `read_key.md` and the story; fix every mismatch before the owner sees the
   pages. Every panel of the third comic had passed the checker, and the owner still read the
   unnamed 阿嬤 as the 細姑 she was talking about. A blind reader of that version could not
   place her either, and also found an unattributable line, a retort read too early and a
   caption repeated on page 1. Never tell the reader what problems you suspect: the first
   reader was given this very example in its instructions and duly found it.
   After fixing, give the new pages to another fresh reader, and repeat until a reader gets the
   story, every character and every speaker right. The reader after the first fix round found
   two more: a caption describing an action the picture does not show, and a kinship word read
   from the wrong person's side. In the sixth comic the second reader still could not tell which
   way the photo faced, and the third got everything right. Where a caption and its picture
   disagree, change the caption: it costs nothing and the picture is what the reader trusts.
   Then send the pages and the PDF, and list the weak panels honestly with what a redraw would
   change.
9. **Fix round.** Map each note of the owner's to a panel id (if they name a page that does not
   contain what they describe, say which panel you think they mean), rewrite the prompt, redraw
   with `n: 3` (or `repaint` when the note is about one small area), re-lay out only the pages
   that changed (`pages --pages 3,5`), send them. When the
   note names a kind of defect (extra hands, the wrong lighting), sweep every picked panel for the
   same defect before replying, and add a row to prompting.md. A character added in a fix round
   (細姑's photo) still gets 3 or 4 versions for the owner to pick, with the checker's notes.
   When the owner asks for new story (「結局太弱，多一頁讓阿嬤描述故事」), write the dialogue first
   and send it as a table, panel by panel, before drawing; then lay the new page out, draw it,
   and give all the pages to a fresh reader again. New backstory moves the timeline of what is
   already drawn: once 阿嬤 said the photo only came out after the 頭七 eleven years ago, the
   eight-year-old who turned it on page 2 had to become a junior-high boy, and her flashback face
   could no longer be younger than the one on the new page. The reader caught both.

10. **Publish.** `manga.py export` turns the laid-out pages into an Instagram carousel in
   `out/export/ig/`: a cover (page 1, or `--cover <panel>` with the vertical title over one
   picked panel; never the reveal), every page whole on a 3:4 slide (`--ratio 4:5` for the
   older shape), an end card saying the story is fiction and drawn with AI (`--handle` adds
   the account), and `caption.txt`. A comic of more than 18 pages is split into parts, since a
   post holds 20 slides. Posting is the owner's: send the folder, never post for them.

When the owner asks to see progress mid-run, `manga.py status` gives the numbers (picked per
page, what is missing and how many candidates it has, GPU minutes counted from `exec_s`, which
leaves out time spent waiting in ComfyUI's queue) and `pages --pages 1,2` lays
out what is picked so far, unpicked panels as labelled placeholders; send that instead of saying
it is not ready.

Time on an RTX 3090: a panel with references takes 47 to 115 s per image and one without takes 23 to 36 s, with 2 to 3 candidates per panel; a `repaint` of 3 or 4 versions takes 1.3 to 2.3 minutes. GPU time from each log's `exec_s`: the first comic (33 panels, every gate and redraw) about 97 minutes, the second (32 panels) about 71, the third (28 panels, every candidate independently checked, 24 redraws) about 91, the fifth (10 pages, 37 panels, 9 characters) about 147, the sixth about 130 for its first 10 pages and 38 panels and about 178 after four owner fix rounds and an added page (11 pages, 44 panels; the reveal panel took 41 draws), with checker batches of 4 to 30 minutes each running beside the GPU. The fourth was thrown away after about 104 (step 0). State the estimate before each long run.

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
  mention every reference in the prompt. But a scene sheet in a panel with people shrinks them
  or leaves them out and brings its own camera: keep it for empty rooms and wide shots from its
  viewpoint, and describe the place in words otherwise.
- Bind scene layouts and lighting per panel (`scene`, `light`); inferring them from references
  put tents into a view from inside a tent and blacked out daytime backgrounds.
- The writer of the prompts is a poor checker of the images. An independent pass that counts
  heads, hands and feet catches what a glance does not.
- A panel can be drawn right and still be read wrong. Checking panel by panel does not show
  that an old woman was never named, or that a bubble sits beside the wrong person; a reader who
  has only the pages does.
- A reference brings its expression as well as its pose: a head crop of a grinning sheet kept
  the boy grinning in a scared panel. A scene sheet puts a seated character in its middle, on
  the coffee table. Same-framing edits keep the camera, not the colour of the wardrobe; write
  down everything that has to stay.
- A reference brings its gaze too: every character drawn from a front-view sheet stared at the
  reader until the prompt said "in profile, head turned toward the door". Dropping the reference
  to escape its pose fixes the pose and loses the face; a main character's close-up keeps
  `:head` and spells the expression out.
- Which way an object faces is the hardest thing to show. A photo "facing the window" was drawn
  front on (read as facing the bed), turned 45 degrees (unreadable), and from the back (the owner:
  it faces the wall, not the window). What read was a view from behind the frame with the window
  straight ahead of it, the same picture in every panel where it faces the window, alternating
  with the front view where it faces the bed.
- Mentioning a viewer draws the viewer: "as seen by someone lying on the bed" put a person in the
  middle of an empty window shot three times. Name the camera, not the person.
- Small details need a small canvas. Three whole-panel edits left a guard's shirt as it was;
  the same request on an enlarged crop (`repaint`) fixed it, and a collar, the hair and a hand
  after it. When even that fails (a
  radio on a drip stand), put the detail in the narration instead of burning more GPU.
- Each character has to be checked across panels as well as in each one (`review --cast`), and
  the picked sheet has to match what the owner has in mind: the boy's sheet had black hair, so
  his panels split between black and white, and a checker holding the sheet calls the white
  ones wrong.
