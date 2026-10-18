# skills

Claude Code skills, distilled from real projects rather than written from
first principles. Each one exists because a specific way of working kept
paying off, or a specific way of failing kept recurring.

## Installing

Copy a skill's directory into `~/.claude/skills/`:

```bash
git clone https://github.com/csiesheep/skills.git
cp -r skills/agent-team-delivery ~/.claude/skills/
```

Claude Code picks it up on the next session. Invoke it by name, or let it
trigger on the phrases listed in its frontmatter.

## What's here

| Skill | What it's for |
|---|---|
| [`agent-team-delivery`](agent-team-delivery/SKILL.md) | Running several Claude sessions as a team: one orchestrator that prioritises, files issues, dispatches, verifies independently, and only then lands; peers that implement in their own worktrees. |
| [`initialize_a_game`](initialize_a_game/SKILL.md) | Turning a board game's name into a project ready to build for the games hub: rulebook digest, name and licensing call, plan note, phone mockups, repo scaffold, then stop and wait for the owner. |
| [`qwen21-three-view`](qwen21-three-view/SKILL.md) | One image of a person or character in, a front / side / back turnaround out (or five views with a 3/4 and the left profile; full body or head only), with Qwen Image 2.1 on a local ComfyUI. Reference frames for video generation. |
| [`h3-reference-to-video`](h3-reference-to-video/SKILL.md) | Several pictures of one character (e.g. a three-view) in, a video with sound out, with MiniMax-H3 reference-to-video on a local ComfyUI. The pictures hold the look; the prompt says what happens. |
| [`h3-multiframe-video`](h3-multiframe-video/SKILL.md) | Same engine, but pictures are pinned to seconds of the output (side at 2 s, back at 4 s...) and H3 fills the motion between them. |
| [`h3-character-replacement`](h3-character-replacement/SKILL.md) | A short clip plus a picture of a new character in; the same clip out with the subject redrawn as that character, keeping motion, timing and audio. SAM3 masks the subject, MiniMax-H3 reference-to-video does the rest. Consent-gated. |
| [`ghost-story`](ghost-story/SKILL.md) | A Taiwanese ghost story in the voice of a PTT marvel (飄板) 經驗 post, from a skeleton sampled out of 9,395 annotated marvel posts. Setting, mechanism, ending, length, narration style and taste (直接 or 留白) are options in plain Chinese; Claude writes it, reviews it against a rubric, and revises. |
| [`ghost-comic`](ghost-comic/SKILL.md) | A ghost story turned into black-and-white manga pages (right to left, vertical Chinese lettering) with Qwen Image 2.1 on a local ComfyUI: storyboard file, owner-picked style and character/scene designs, panels drawn against them with fixed scene layout and character heights, pages laid out by script with screen bezels, flashbacks and a PDF. |
| [`story-skill-builder`](story-skill-builder/SKILL.md) | Building a generator skill for one kind of short text (鬼故事, 笑話, 心靈雞湯…) from a corpus whose readers left a signal: scrape, label structure with Claude, weight by reception, derive rules from the high/low contrast, calibrate a pairwise judge, blind-test with the owner, package. The pipeline behind `ghost-story`, with gates where the owner decides. |

### agent-team-delivery

Written in Traditional Chinese. Roughly half of it is a **failure
catalogue** — the ways a verification instrument lies to you while you are
working carefully:

- a cached build feeding you the old bytes while you measure the new ones
- a check that derives its expected value from the thing it is checking, so
  breaking the rule breaks the expectation too and the test stays green
- validating an instrument in the range where it works, which says nothing
  about the range where it doesn't
- a true statement carrying a scope wider than the evidence supports
- a test name promising more than its assertions check
- an absence-claim that passes because the population was empty
- a dispatch that reports success without ever being delivered
- sampling a curve at the points where two rival explanations agree
- asking a peer to report back over a channel that has no return path
- a watcher that fires on activity rather than on completion
- a correct diagnosis that outlives the condition it diagnosed
- measuring someone else's server, because yours never bound to the port
- a peer blocked on a confirmation you never knew it was waiting for
- an index still holding the old tree after a rejected push, staged to revert
- averaging across a transient and comparing it against an instantaneous reading
- a drain-style API whose return value carries the measurement you discarded
- the guard you keep citing as authoritative, which no one ever made go red
- an absence-check whose observer is watching nothing, reporting a confident zero
- naming a bug as a class, writing it up, and never sweeping for the second copy
- publishing your own inference under the principal's name, in durable content
- proving you have a permission, when the fix is to need no permission
- relaying a peer's true-when-written measurement as the tree's current state
- specifying a dimension because it is easy to assert, when reachability is the property
- a viewport that "fits" because the overflow was silently discarded

Every entry happened. The governing idea:

> The value of verification is not "I looked at it." It is "I made it go red
> once."

## Licence

MIT.

### initialize_a_game

One command, `/initialize_a_game <board game name>`, produces a decision
package rather than code: a rulebook digest in the owner's own words with
every table and the unclear points listed, a name-and-licensing proposal
(rules are not copyrightable, the title is a trademark, so pick an own name
*before* the repo exists), an implementation plan on the M0–M5 shape the
sibling games share, a canvas of phone mockups in both languages, and a
scaffolded repo copied from the newest sibling. Then it stops. The
`references/` folder carries the platform, repo, vault and deploy
conventions the hub expects, and the plan template.

### qwen21-three-view

Give it one picture (photo or drawing, standing or seated) and it writes the
prompts itself and returns three full-body views on white: front, right
profile, back. The bundled script carries the angle instructions that held
up in testing; the skill only describes the subject. What it learned the
hard way:

- one-sided accessories (one earring, a bag on one shoulder) get mirrored
  unless you name the side of the *image* they appear on, per view
- a turned source pose leaks into the "front" view as 3/4 unless the prompt
  says *squarely* facing the camera
- raising CFG straightens the pose but beautifies the face away from the
  person, and at CFG 1 the negative prompt does nothing
- the text encoder must be a Qwen3-VL 8B; a 32B one fails on a 5120 vs 4096
  shape mismatch, and GGUF encoders without a vision tower cannot see the image

### h3-reference-to-video and h3-multiframe-video

Two skills over one script and one graph: ComfyUI's MiniMax-H3 reference-to-video
template, taken from a successful run with an uncensored model set swapped in. With
references only, H3 decides the timing; each `--keyframe picture@seconds` adds a guide
node that pins that picture to that moment. Fed the three views from
`qwen21-three-view`, a character turns a full circle with its face, outfit and
one-sided earring intact. The skills refuse pictures of children (the model has an
explicit LoRA merged in) and say so. Lessons kept in them:

- a plain background drifts into an invented room unless the prompt pins it in every
  sense, including the sound line ("indoor ambience" seemed to summon a living room)
- the template's Lightning LoRA stays off: the fused model already has a turbo merged
  in, and 8 steps is enough
- keyframe order sets the spin direction; space keyframes about 1.5 s apart

### h3-character-replacement

The R2V graph with a masking front end: SAM3 finds the subject from a word ("person"),
the subject is filled gray, and the masked clip goes to H3 as the video to edit, prompted
as `[video editing + reference generation + audio reuse]` per MiniMax's guide. In the test
the identity and the action carried over; whether the subject's size on screen followed
the source depended on the seed.
Because it swaps identities in real footage on an uncensored model set, it requires the
consent of every real person involved and refuses minors, sexual content of real people
and deceptive impersonation before it runs.

### ghost-story

Distilled from a pipeline that scraped PTT's marvel board (2003 to 2026: `[經驗]`,
`[真實]`, `[翻譯]` posts and the digest), merged serials, deduplicated, and had Claude
Opus 5.5 label 9,395 units for setting, horror mechanism, ending, beat proportions, how
much the ghost shows, and voice. Push counts were turned into percentiles within the same
year and tag, so 2015's push-happy board and 2025's quiet one compare fairly. The skill
ships the resulting sampling table (structure and paraphrased one-line premises only, no
original text, titles or authors) and a stdlib script that samples a skeleton from it;
the writing, review and revision are Claude's. What the data said:

- PTT readers push concrete stories: dialogue (80% of top posts, 57% of low ones), a
  specific place, a ghost that actually shows up. A ghost that never appears scores
  lowest on pushes and on how often readers write 好毛
- popular is not scary: explained endings get more pushes but fewer 好毛 and more 虛;
  twist endings get fewer pushes and the most 好毛
- a 1-10 judge could not tell real top posts from low ones (AUC about 0.5); asking
  "which of these two" picked the more-pushed post 91% of the time and the scarier one
  93% of the time, with no position bias
- one blind reader preferred restrained stories while the reader data preferred direct
  ones, so taste is an option (`--taste 直接|留白`) rather than a rule

Generated stories are fiction. The skill tells the user to post them as `[創作]` with an AI
note, never as a `[經驗]` that happened.

### story-skill-builder

The pipeline that built `ghost-story`, moved into the repo as a skill of its own: PTT
scraping with a high-push set plus a random low-push control group, serial merging and
deduplication, Claude annotation against a structure schema (with the served model and the
cost recorded per call), push percentiles within tag and year, high-versus-low contrasts
with p-values, a planner that samples skeletons from the resulting table, judge calibration
on real pairs, and the owner's blind A/B page. `SKILL.md` is the seven-phase playbook with a
gate at the end of each phase (axes approved, counts seen, cost agreed, judge calibrated,
taste chosen) and the numbers ghost-story set for them. Every genre-specific word lives in
that genre's `genre.json` and prompts, never in the code; the tests run a second, three-axis
joke genre through the whole chain to keep it that way.

### ghost-comic

A story in, manga pages out: `board.json` describes every page (rows, stacked columns, insets),
every panel (prompt, reference images, lettering) and the fixed scene layout and character
heights; `manga.py` draws sheets and panels with Qwen Image 2.1 on the local ComfyUI and lays
out right-to-left pages with vertical lettering, bubble shapes that say where a voice comes
from (said in the room, through a screen or phone, narration), screen bezels with a
picture-in-picture, faded flashbacks, a PDF. The owner decides at three gates before any panel
is drawn: style (three examples of one panel), character and scene designs (three versions
each), and a wireframe of every page with the real lettering. Learned on the first run
(7 pages, 33 panels, about 97 GPU minutes):

- a two-figure character sheet used as a reference draws two of the same person; references
  are cropped to one view and turned grayscale
- lighting only stays consistent when each story beat is drawn against an approved panel in
  that lighting state, not a daytime scene sheet
- prompts describe positions and what is visible; "halfway through sitting down" put the hero
  on the coffee table and "his reflection" put him in front of the laptop
- character size has to be written down: the ghost came out larger than the hero until her
  height and "her head is no bigger than his" were in every prompt
- the strongest device is the same framing three times empty and a fourth time with the ghost,
  seen only inside the other person's screen

After the second comic (6 pages, 32 panels, about 71 GPU minutes) the pitfalls became tools:
`lint` checks prompts against the failure table before any GPU time (crossed arms in a
full-body shot, a reference the prompt never mentions, a full-body sheet in a close-up, words
that draw walls, signs or photographic light) and `panels` refuses to draw on errors; `refs`
adds head and bust crops, which stopped a standing sheet from keeping a seated friend standing;
panels name their `scene` and `light` instead of having them inferred from references; and
`review` writes a brief for a fresh subagent that opens every candidate and counts heads,
hands and feet, because the four-handed club leader got past the one who wrote the prompts.

The third comic (7 pages, 28 panels, about 91 GPU minutes, every candidate checked) showed
that a panel can be drawn right and still be read wrong: the owner took an unnamed grandmother
for the dead aunt she was talking about. So `review --read` now hands a fresh subagent nothing
but the page images; it retells the story, names every character and says who speaks each
line, and the answers are compared with the story before the owner sees anything. Run blind on
the comic as first delivered, a reader could not tell who the old woman was until a later panel
named her, could not say who asked about the door (an off-panel hand with its sleeve under the
bubble), read a retort before the answer it was meant to follow, and noticed a caption
repeated on page 1. `lint` warns when a character is first drawn without a name, when a head crop is
asked for a frightened face (the sheet's grin came along) and when a seated character carries
a scene sheet (he landed on the coffee table); `plan` and `pages` warn about lettering that
covers lettering; panels can be mirrored or shrunk on their own background for lettering
without editing files; `review --new` lists only redrawn candidates and every brief names the
picked panels a candidate has to match; `status` says what is picked and how much GPU it took.

The fourth comic was drawn before the owner had read its story, and was thrown away with it
(about 104 GPU minutes): a story written for a comic is now shown first and drawn only after an
OK. The fifth (10 pages, 37 panels, nine characters, about 147 GPU minutes) passed every panel
check and two blind readers, and the owner still found two faults, both the same character
looking different from one panel to the next: a grandmother's close-up drawn from words alone
had someone else's face, and a boy's hair was black on one page and white on the next.
`review --cast` now lines up every picked panel of each character beside their sheet for a
fresh checker. Run blind on the panels as first delivered, it caught both: the grandmother's
close-up was called a different face, and the boy's hair split between panels (the checker,
holding a black-haired sheet, called the white ones wrong), plus three panels with her bangle on
the wrong wrist; a control character got no false alarms. `repaint` redraws one small area on an enlarged crop: it fixed a
uniform shirt that three whole-panel edits had left alone, then a collar, the hair and a
beckoning hand; `lint` warns about scene sheets in panels with people (they came out tiny or missing,
and the sheet's camera came with them); a panel's `heads` counts people who are no character;
`review --new` skips candidates drawn from an earlier version of a prompt; and `status` counts
GPU time without the wait in ComfyUI's queue, which had doubled the figure.

