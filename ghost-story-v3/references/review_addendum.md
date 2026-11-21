# Review brief, part 5: voice and jokes (v3 only)

Append this to ghost-story's `references/review_brief.md` prompt, after part 4, and add 「the joke list, the callback
grades and the voice notes」 to its "Return only" line. Do not send the screenplay header's joke table as the
answer: the reviewer counts on its own, and the writer compares the two counts afterwards.

```
5. Voice and jokes. Read <skill dir of ghost-story-v3>/references/voice.md first.
   a. List every joke you find in the SCREENPLAY, in order: its second, who says it, its type (吐槽角色、旁白吐槽、
      自嘲、日常荒謬、鬼的人性反應、其他), and the line in at most 15 characters. A line that is only scary or only
      informative is not a joke; a line that made you smile is.
   b. For each joke, does it come back later? Grade it A (its content comes true, becomes a clue or a weapon, or
      the ghost answers it in its own words), B (the same subject or object comes up again, nothing comes true),
      or C (no). Give the second where it comes back.
   c. Does any joke fall within 5 seconds of the biggest picture, or in the last scene? Does the ending turn into a
      joke? Does any joke make the ghost less frightening?
   d. Does the voice read as a person telling a friend what happened (spoken Taiwanese Mandarin, the narrator
      teasing himself and his friends), or as an essay? Name the two lines that sound least like speech.
   e. At most three concrete fixes for the jokes or the voice (which line, what is wrong, the replacement).
```

## Reading part 5

- **The reviewer's joke count against the header's.** More than one apart means the header was filled in from the
  plan, not from the scenes. Recount and fix the header before rerunning `style_check.py`.
- **No A grade from the reviewer** means the callback the writer meant did not land: either the plant is not
  heard as a joke, or the payoff is not on screen. Fix the payoff shot first; it is the cheaper of the two.
- **"The jokes drown the scare"** from any reviewer is a stop signal for the trial (SKILL.md step 6), not a line fix.
