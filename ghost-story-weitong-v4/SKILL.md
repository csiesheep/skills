---
name: ghost-story-weitong-v4
description: Write one long Taiwanese ghost story (8 to 10 minutes read aloud, about 2,200 to 2,700 characters) in the 說書長篇 style distilled from all 209 stories crawled from a large Taiwanese animated ghost-story YouTube channel (微疼) - a narrator telling friends what happened, friends who tease each other, jokes front-loaded and withdrawn before the fear, a ghost hidden in the everyday, records and witnesses that do not match, a short ending that explains only half. Its mechanics only, never the channel's names, catchphrases, cast or stories. Checked with weitong_check.py and scored by independent reviewers round by round. Use when the user asks for ghost-story-weitong-v4, 微疼風格, 用微疼的寫法, 說書長篇, a long narrated ghost story for YouTube or a voice track, 8 到 10 分鐘的鬼故事, 長篇有笑點的鬼故事. For an under-3-minute video story with its screenplay use ghost-story-v3; for a PTT-style story use ghost-story.
---

# Ghost story, 說書長篇 (weitong)

One long story, told the way that channel tells them: a narrator who is talking to friends, people who tease each
other in the first half, then the jokes go away, the safety is taken off one layer at a time, and something the
narrator believed is overturned by a record or by someone else's account. 8 to 10 minutes read aloud.

Built with the nuwa method (`~/.claude/skills/nuwa-skill/`) as a **style skill, not a persona**: there is no role
play of the channel's host, and nothing of the channel's own (names, catchphrases, cast, stories) goes in. Sources,
all local, nothing fetched (2026-11-21):

| | what | where |
|---|---|---|
| numbers | 209 stories from 131 videos, extracted and statistically tested | `C:/Users/sheep/Pictures/gui_chang_shi/research/weiteng/findings_all.md` |
| close reading | 12 stories read in full on voice, humour and structure | `references/research/01-structure.md`, `02-voice.md`, `03-humour.md` |
| full check | the other 197 read in full, every draft rule ticked story by story; 14 new patterns | `references/research/04-crawl-check.md` |
| the rules | structure, mechanisms, endings | `references/style.md` |
| how he talks | his spoken words and their frequency, rhythm, a density example | `references/phrasebank.md` |
| how he jokes | joke constructions from all 1,499 of his jokes, with our own examples | `references/jokes.md` |
| voice numbers | particles, exclamations, intensifiers, questions, transitions, line length, over 205 stories | `references/fingerprint.json` (`scripts/voice.py`) |
| what not to take | names, fixed lines, series, his stories (common slang is allowed, owner 2026-11-21) | `references/avoid.md` |

**Why the voice files exist (2026-11-21):** the first trial story, 〈搬家打工的第十三箱〉, passed review at 7 but the
owner said it did not sound like him. Measured, it had 0.64 particles per 100 characters against his median 2.9
(lower than all 205 of his stories), no exclamations, and 12% dialogue against his 45%. The structure rules alone
do not carry a voice; the writer must work from his word frequencies and joke constructions, and a blind test
decides whether it sounds like him.

**His data does not show that this style gets more views** (findings_all §1). It is a taste the owner asked for.
Whether it works for us is measured on our own posts.

It borrows by path, and never copies:
- ghost-story (`~/.claude/skills/ghost-story/`): `references/review_brief.md`, `review_rubric.md`,
  `pairwise_judge.md`, `writing_direct.md`, and its Rules.
- ghost-story-v3: nothing but the line between them. v3 is the under-3-minute version of the same voice with a
  screenplay; this one is the long form, with his structure as well as his voice.

## Inputs

All optional; anything the owner says wins.

| | Default | Notes |
|---|---|---|
| length | 9 minutes, 2,200 to 2,700 characters | 7 to 12 minutes allowed. Under 6 minutes is not this skill (v3). The checker scales the joke count by length |
| setting, premise | free | not one of his recurring setups (avoid.md): no trio exploring a ruin on a dare |
| ghost entry | 先扮人 or 先出聲 | style.md §0 model 2; pick one |
| mechanisms | 2 or 3 from style.md §2 | not all of them |
| ending | one of the four in style.md §5 | |
| cast | 3 to 5 speaking parts, one of them the ghost or a third party | names made up for this story only |
| extra requirements | free | |

## Steps

Work in `C:/Users/sheep/Pictures/gui_chang_shi/backlog/<english_short_name>/`: `story.md` (the current text),
`plan.md`, and every earlier version in `drafts/` (`v1.md`, `v2.md`, ...).

### 1. The plan, before any prose

Read `references/style.md`, `references/avoid.md`, `references/phrasebank.md` and `references/jokes.md`. Write
`plan.md`, one line each:

1. **The everyday:** who, where, doing what, and the one rule or routine that will break (style.md §1).
2. **The safeties** that will be taken away, in order (a friend, the light, a lock, a charm, the time).
3. **The ghost's entry:** passing as a person (with its one flaw) or heard first; when it is seen (about .69).
4. **Mechanisms:** the 2 or 3 from style.md §2, and the record or witness that overturns the narrator.
5. **Twists:** two or three, each written as 「本來以為 A，其實 B」. The second rewrites something the narrator did.
6. **The biggest scare** (about .85): what is on the page, in one sentence; no face close-up.
7. **The third party** who explains half, and the physical proof that pins it.
8. **Jokes:** six to nine, each with who, its **construction from jokes.md**, rough position; mark which two or more
   come back and how (style.md §4). Most are banter between two people, not narrator lines.
9. **The ending:** which of the four, and the last line.

Then check line 4 to 6 against his stories: open `research/weiteng/story_json/` and search the titles and
`peak_scare_desc` for the same object and twist. The same pair is replaced, not reworded.

### 2. The story

Write `story.md`: first line `[經驗] <title>`, then the story as spoken text, paragraphs of short breath-groups.
Follow style.md §3 to §5, and write it **spoken**, at his density (phrasebank.md §7 shows the difference):
- **About half the text is dialogue.** Things happen through two people talking, one line each, not through the
  narrator summarising them. A friend's first reaction to anything strange is a particle (蛤？欸？).
- **Particles about 3 per 100 characters**, mostly at the ends of spoken lines (啦、喔、啊、欸、吧、耶、咧).
- **Exclamations and slang** in the first half (我靠、靠北、北七、哭喔、真的假的、不會吧), **intensifiers** in
  the narration (直接、根本、整個、到底).
- **Jokes are built** with the constructions in jokes.md, mostly friends going at each other for two to four lines,
  and the story moves on right after.
- When the fear rises, all of that drops away (style.md §3): the contrast is the point.

Put the markers from `scripts/weitong_check.py` (HTML comments: `<!-- 異狀 -->`,
`<!-- 鬼 -->`, `<!-- 反轉 -->`, `<!-- 驚嚇 -->`, `<!-- 收尾 -->`, `<!-- 笑 <type> <id> -->`, `<!-- 回收 <id> -->`) just
before the sentence they mark. Read `writing_direct.md` from ghost-story for the plain-prose rules.

Then:

```
python -X utf8 ~/.claude/skills/ghost-story-weitong-v4/scripts/weitong_check.py backlog/<name>/story.md
```

Fix every 必改 before the review, the voice rows (口氣、台詞佔比) included. A 注意 may stay with one sentence in the
round table saying why. The checker reads the markers the writer placed; the reviewer in step 3 counts without them.

Then the **blind voice test**, before any review round:

```
python -X utf8 ~/.claude/skills/ghost-story-weitong-v4/scripts/blind_test.py backlog/<name>/story.md \
    C:/Users/sheep/Pictures/gui_chang_shi/research/weiteng/nuwa_src/fp_all backlog/<name>/blind_vN
```

Give a fresh subagent only `blind_vN/blind.md` (never `key.json`) with this prompt: four excerpts, three by one
storyteller, one an imitation; which is the imitation, confidence 1 to 5, the three strongest reasons pointing at
lines, and the three lines that sound least like him rewritten as he would say them. **Pass** when the judge picks
one of his, or picks ours at confidence 2 or less. Otherwise apply the rewrites that fit, rerun the checker and
test again with a new seed and a new judge, up to three times. The judge's rewrites are the most useful voice notes
the skill gets; keep them in `drafts/blind_notes.md`.

### 3. Score and fine-tune

As in ghost-story step 5b:
- Save the text as `drafts/vN.md`. Give a **fresh subagent** ghost-story's `references/review_brief.md` filled in,
  **plus part 5 from `references/review_addendum.md`**, with the story stripped of markers (`<!-- ... -->` removed)
  and without `plan.md`.
- Apply every fix that costs a line or two; rerun the checker.
- A new subagent each round; never tell it what the last round found.
- **Stop** when a round passes (overall 7 or more, no sub-score under 3), the checker has no 必改, the blind test has
  passed on the current text, the reviewer found at least two callbacks it grades A, and nothing copies the
  channel's own names, lines or stories. Three rounds at most. A review fix that adds narration and drops dialogue
  is applied in dialogue instead.
- Report each round to the owner as one table: five scores, overall, the checker's 必改 count, the reviewer's joke
  count against the plan's, and its A-grade count. Then the list of what changed.

A round that fails the rubric is a rewrite from step 1, not a line fix.

### 4. Deliver and stop

Write `speakers.md` next to the story: the cast (one line each: who, voice, temperament), then a table of every line
of dialogue in order (number, its first words, who says it, its tone), then two or three notes for the voice actor
(the ghost's repeated line, where all laughter stops, any line that must fool the listener the first time). The story
itself keeps his tagless dialogue; the table is what makes it voiceable and drawable, because without his animation
and voice acting a reader cannot always tell who speaks (owner, 2026-11-21). Example:
`backlog/moving_box13/speakers.md`.

Give the owner: the story (markers removed) as plain text, `speakers.md`, one line of mechanism / ghost entry /
ending, the length in characters and minutes, the last round's table. **Then wait.** What it becomes (a voiced long video, a YouTube
story, or cut down with ghost-story-v3) is the owner's call.

## Rules

- ghost-story's Rules hold: fiction, posted as `[創作]` with the AI disclosure, no real person, business, temple or
  hospital named as haunted, no retelling of a known post or film.
- Nothing from avoid.md, and nothing a viewer of that channel would recognise as his: not his names, cast, fixed
  lines, series names, ghosts' lines, or any of his stories reworded. If the owner asks for something on that list,
  say why it is there and ask once.
- Quote his transcripts nowhere in the story or in this skill folder beyond the one short line per story already in
  `research/`. The transcripts stay in `gui_chang_shi/research/weiteng/`, outside the skill, because this folder is
  published.
- No role play as the channel's host and no claim that a story is his.

## Honest limits

- The rules describe his writing; they do not predict views (findings_all §1; a story in b09 kept all 24 rules and
  sat at the 37th view percentile).
- The rule check was done by readers, one per batch, each with its own thresholds; two batches flagged files that
  had changed on disk while they wrote. Trust the counts to about ±10%.
- Transcripts are Whisper ASR: names come out in many spellings, and the last line is cut off in some, so the
  counts of fixed lines are lower bounds.
- Nothing here measures his pictures, music or delivery, which carry much of an animated video. The skill writes
  the words only.
- The voice numbers come from ASR, which drops some particles and has no punctuation: his true rates are a little
  higher than fingerprint.json says. The blind test compares our punctuation-stripped text with his ASR, so ASR
  typos in his excerpts can give ours away; tell the judge so, and read its reasons, not only its pick.
- Research date 2026-11-21; his 2026 stories are longer, with more twists and slightly fewer jokes (findings_all
  Q7). Update by rerunning the crawl, not by memory.

> 本Skill由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 的方法生成（主題／風格變體，無角色扮演）
