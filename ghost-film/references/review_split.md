# Blind review in two halves: picture and text

Use this for a polish pass after the owner says the cut is close (owner, 〈社辦門上的氣窗〉 v10:
「再打磨一次，看有沒有任何人物場景不合理的地方，影片不連貫的地方，文案不流暢的地方」). The 1–10 brief
(`review_brief.md`) asks "can it be posted"; this one asks "what is wrong", and two narrow reviewers find more than one
broad one. v10's picture reviewer found 22 picture problems, 4 of them contradicting the story. The text reviewer
found 3 subtitle breaks to fix and confirmed every twist clue was still planted after the cuts.

Make the material with `scripts/review_sheets.py out/reel_vN <dest>`. Then start two fresh subagents in parallel. Neither may
have seen the video. Give each the story in ten lines (who looks like what, the set's fixed architecture, which lights
are on when, the twist and the clues it uses), and say which effects are deliberate (hidden ghosts, smoke) so they
judge whether they make sense, not whether they exist.

## Picture reviewer

Inputs: the sheets, `shots.txt` and the video path. Tell it to pull its own full-size frames with ffmpeg for anything
suspicious, brightened if needed, rather than judging from thumbnails.

It checks for:
1. **Character consistency.** Face, glasses, clothes, the guard's cap. Watch for extra people or hands.
2. **Set logic.** The door and transom match the architecture block. The light is on or off as the story says.
   Stairs appear when the story climbs.
3. **Picture against narration.** The line says eyes closed but they are open. The line says the light goes on but
   it is lit from frame 0. The line says he crawls over to unlock, but the visitor is already inside.
4. **Continuity between shots.** Standing then sitting, a guitar or clipboard appearing and disappearing, a lighting
   jump, an empty chair where the hero should be.
5. **AI breakage.** Melting, morphing props, frozen frames.

It returns a table sorted by severity, with a fix for each row: an offset into the same clip, a crop, a lift, a cut,
a swap to another clip, or a regeneration.

## Text reviewer

Inputs: `shots.txt`, `asr.txt` and story.md. Tell it which lines were cut on purpose.

It checks for:
- Awkward sentences.
- Lines that depend on a cut line. In v10, 「那天，橘子也沒給」 had lost its setup.
- Repeated words.
- 她 vs 它 used consistently.
- Bad subtitle breaks.
- Whether the twist reads from the text alone, and whether every clue it uses is still planted.

For each fix it says whether it is subtitle-only (the voice still says the old words) or needs a new take or a cut.
ASR homophones are not errors.

## Before acting, verify every claim on a full-size frame

- **False positive:** v10's "two extra people behind him" in the fall shot were a backpack on a chair and a white
  cabinet.
- **Wrong time:** "no hidden ghost at 1:33" came from a time I gave that was 1 s off.
- **True positive:** "the face at 2:55 cannot be found" was right. Even at full size it was a smudge.

Then sort the confirmed items:
- **Free:** `offset`, `zoom`/`focus`, `lift`, a swap to another clip that shows what the line talks about, subtitle
  text.
- **GPU:** regenerations. Send these as one batch to the video agent with the shot, the line, what is wrong and what
  the new clip must show.

Low-value polish (a neat 「王」, the ghost's eye whites changing) goes to the owner as a list. Do not do it unasked.
