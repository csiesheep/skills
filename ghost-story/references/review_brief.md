# Independent review brief (score and fine-tune rounds)

The prompt for the fresh subagent of each round (SKILL.md step 5b). Fill the `<...>` parts and send it whole. A
round's reviewer has never seen the story, an earlier version or an earlier review, and is never told what you
suspect is wrong: a reviewer given the suspected flaw finds that flaw and stops looking.

```
You are an independent reviewer of one Taiwanese ghost story (PTT marvel style)<and its short-film screenplay>.
You did not write it and have seen no earlier version. Be harsh and honest. Reply in Traditional Chinese.

Read these files first:
- Rubric: <skill dir>/references/review_rubric.md
- Writing rules for this taste: <skill dir>/references/writing_<direct|restrained>.md
- Story: <story folder>/story.md
<- Screenplay: <story folder>/film/screenplay.md>

Brief the story was written to:
- setting / mechanism / ending (and how many twists) / ghost cap / taste / style
- target_chars <N>, actual <M> (counted by the skill's script)
- Extra requirements: <each one, as the owner said it>
<- What in the story is deliberate fiction and says so in the text (an invented machine, an unnamed brand)>

Do, in this order:
1. Score the STORY with the rubric exactly: the five 1–5 scores, overall 1–10, pass or fail by the rubric's pass
   rule, each twist as one line 「本來以為……，其實……」 (does it overturn a belief; was a clue planted before it),
   and at most five concrete fix notes (which line, what is wrong, the replacement sentence). Only fixes that matter.
2. Facts and continuity: every point a PTT reader would push 「虛」 at, real-world facts included, and every
   internal contradiction (who was where, who left first, the times, what was seen then against what is said later).
3. First-time reader: do the first three lines hook; the line where a casual reader most likely stops; every
   sentence that has to be read twice.
<4. The SCREENPLAY as a short video for social platforms: does it fit its target length, scene by scene (narration
   at about 4.2 Chinese characters a second, plus lines, countdowns and silences); what a muted viewer gets in the
   first 3 seconds; where viewers drop; is the reveal clear on a phone; every mismatch with the story; at most four
   concrete fixes. Then three 1–10 guesses with one sentence each: retention, likes, shares.>

Return only: the scores table, pass/fail, the twist lines, the story fix notes, the 虛 list, the reader notes
<, the screenplay notes with the three guesses>. Do not edit any file.
```

## Reading what comes back

- **Fix what costs a line or two**, all of it, in place. Keep each version in `drafts/` (`v1.md`, `v2.md`, …)
  before editing.
- **Two reviewers' advice can pull opposite ways.** Round one of 〈一中街的無人拍貼店〉 said to write times as
  digits; doing so tripped `surface`'s digits check (24.6 against a top-post range up to 11.8). Rerun `count` and
  `surface` after every round, and let `surface` win on how the page looks.
- **A hole in the story's device is turned into a clue, not defended.** 「主流拍貼機沒有人臉框」 and 「付款後畫面會自己
  跳走」 were both true; the fix was for the narrator to say so (「那台舊舊的不知道哪一牌」, 「照理說會自己跳回首頁，
  那台就一直亮在那邊」), which made the second one the plant for the last twist.
- **A line the reviewer wants cut may be the hook.** The same reviewer said the first line gave away the first
  twist and that the first line was what kept them reading. Keep the hook; make sure a later twist is still unspoiled.
- **The score moves little; the hole list is the result.** That story scored 7 in both rounds while the 虛 list went
  from eleven points to ones the first round had not reached. A flat score with a new, smaller list is progress; the
  same points coming back means the fixes did not land.
- **A sub-score both rounds leave at 3** (realism there: 「敘事者沒有自己的生活」) is not a hole to patch. Add what it
  names (two lines of the narrator's own week, one detail that leads nowhere) rather than another continuity fix.
