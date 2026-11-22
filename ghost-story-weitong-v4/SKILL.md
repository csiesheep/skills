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
| the retelling brief | the prompt for the fresh writer who retells the draft aloud (step 3) | `references/retell_brief.md` |
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

### 2. The structure draft

Write `drafts/v1.md`: first line `[經驗] <title>`, then the whole story from `plan.md`, every beat, clue, joke and
payoff in place. This draft is about **what happens**, not how it sounds; do not try to sound like him yet. Put the
markers from `scripts/weitong_check.py` (HTML comments: `<!-- 異狀 -->`, `<!-- 鬼 -->`, `<!-- 反轉 -->`,
`<!-- 驚嚇 -->`, `<!-- 收尾 -->`, `<!-- 笑 <type> <id> -->`, `<!-- 回收 <id> -->`) just before the sentence they mark.

```
python -X utf8 ~/.claude/skills/ghost-story-weitong-v4/scripts/weitong_check.py backlog/<name>/drafts/v1.md
```

Fix every structural 必改 (length, beats, jokes, distances, callbacks, avoid.md). **Ignore the 口氣 rows and 台詞佔比
here**: step 3 is what fixes those. Then read the draft once for logic only: who is where, who has which phone, what
was seen against what is said later. Moving_box13's first review found three such holes (2026-11-21); fixing them
before the retelling is cheaper than after.

### 3. Retell it aloud (a fresh writer)

Writing in his voice directly does not work. In moving_box13, drafts v4 to v7 were revised four times straight
from the judges' notes until every voice metric was inside his range, and judges still caught them in 5 of 6 blind
tests ("too clean, too designed"). v8, retold from scratch by a fresh writer who had first read three of his
transcripts, was the first version the owner accepted (2026-11-21).

Give a **fresh subagent** (Opus) this job:
- Read the structure draft (plot fixed: keep every beat, clue and payoff in order, and every marker), then
  `references/phrasebank.md` (especially §5b to §9), `references/jokes.md`, and `drafts/blind_notes.md` if one exists.
- Read **three of his transcripts in full** to hear him, choosing ones similar in setting or length, from
  `C:/Users/sheep/Pictures/gui_chang_shi/research/weiteng/nuwa_src/fp_all/` (local only, never copied into the story
  or the skill). Absorb rhythm and habits; copy no sentence, name, story or fixed line (avoid.md).
- Retell the story **as a young Taiwanese guy telling friends over late-night snacks**:
  - narration ends with 呢、啊、啦 every few lines, with 這樣 before a noun now and then;
  - leave traces of speech: a repeated phrase, a self-correction (「三台電鍋，喔不是，兩台是壞的啦」), fillers (嗯、
    呃、就是), an aside to the listeners (「你們阿嬤家應該也是這個味道吧」);
  - mock-epic self-roasting about past-you (「這個數學真的太天才了」);
  - description that serves the next action or turns into a comment, never still-life or a poetic metaphor;
  - banter that makes things happen (friends egging each other on, escalating; stammers when excited or scared),
    with jokes mostly one quick line carried by particles;
  - one or two unrelated everyday details next to each clue, so it is not obviously planted;
  - from the moment the ghost is known through the biggest scare, the voice goes quiet: short lines, almost no
    particles, no jokes; after it, plain speech, no joke in the last paragraph;
  - dialogue in 「」 without 「他說」 tags, 35 to 45% of the text; length 2,300 to 2,700 spoken characters.
- Write `drafts/v2.md`, run `weitong_check.py` on it, and fix every 必改, voice rows included, before returning. It
  returns the checker's table and five lines it thinks sound most spoken.

The full brief, ready to fill in, is `references/retell_brief.md` (the prompt that produced moving_box13's v8).
Copy the result to `story.md`.

### 4. Blind voice test

On the retold text, before any review round.

```
python -X utf8 ~/.claude/skills/ghost-story-weitong-v4/scripts/fair_asr.py backlog/<name>/story.md backlog/<name>/fair_vN
python -X utf8 ~/.claude/skills/ghost-story-weitong-v4/scripts/blind_test.py backlog/<name>/story.md     C:/Users/sheep/Pictures/gui_chang_shi/research/weiteng/nuwa_src/fp_all backlog/<name>/blind_vN     --ours-file backlog/<name>/fair_vN/ours_asr.txt
```

`fair_asr.py` speaks our excerpt with local H3 TTS (ComfyUI on 8188, ghost-film's speak.py) and transcribes it back
with faster-whisper, so our excerpt has the same kind of ASR errors as his. Without it, judges notice that only ours
has no typos (every judge in moving_box13 mentioned it). If ComfyUI is busy or down, run `blind_test.py` without
`--ours-file` and tell the judge that typos are not evidence.

Give a fresh subagent only the `excerpts.md` path the script prints (a neutral temp folder, so the story's folder name does not give the setting away; never `key.json`) with this prompt: four excerpts, three by one
storyteller, one an imitation; which is the imitation, confidence 1 to 5, the three strongest reasons pointing at
lines, and the three lines that sound least like him rewritten as he would say them. Run **two** tests with
different seeds and different judges. **Pass** when at least one judge picks one of his, or picks ours at
confidence 2 or less. Otherwise give the judges' reasons and rewrites to a new retelling (step 3, a new writer),
not to line edits: line edits were what failed in v4 to v7. At most two retellings. Keep every judge's reasons in
`drafts/blind_notes.md`.

If the blind test still fails after the second retelling, stop retelling. Run step 5 on the best retelling (the one
whose judges were least sure), then stop and give the owner the review table, every blind result (judge, pick,
confidence) and the judges' most common reason; the owner decides whether it ships as it is or is rewritten from
step 1. Deliver it only on the owner's word, and say in the delivery that it never passed the blind test
(study_room_b7, 2026-11-21: 8 fair tests, all caught; the owner chose to fix and ship).

### 5. Score and fine-tune

As in ghost-story step 5b:
- Save the text as `drafts/vN.md`. Give a **fresh subagent** ghost-story's `references/review_brief.md` filled in,
  **plus part 5 from `references/review_addendum.md`**, with the story stripped of markers (`<!-- ... -->` removed)
  and without `plan.md`.
- Review the **retold** text, so the scores are for the version that ships. Apply every fix that costs a line or two,
  written in the retold voice (dialogue rather than narration); rerun the checker. A fix that changes more than a
  few lines in the first half goes through the blind test again.
- A new subagent each round; never tell it what the last round found.
- **Stop** when a round passes (overall 7 or more, no sub-score under 3), the checker has no 必改, the blind test has
  passed on the retold text (or, after two failed retellings, the owner has decided as step 4 says), the reviewer found at least two callbacks it grades A, and nothing copies the
  channel's own names, lines or stories. Three rounds at most. A review fix that adds narration and drops dialogue
  is applied in dialogue instead.
- Report each round to the owner as one table: five scores, overall, the checker's 必改 count, the reviewer's joke
  count against the plan's, and its A-grade count. Then the list of what changed.

A round that fails the rubric is a rewrite from step 1, not a line fix.

### 6. Deliver and stop

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
