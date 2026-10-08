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

