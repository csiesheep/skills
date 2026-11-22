---
name: ghost-story-v3
description: Write one Taiwanese ghost story together with its short-film screenplay (one vertical video under 3 minutes) in the 說書吐槽 voice - a narrator telling a friend what happened, friends who tease each other, jokes placed by rule (front-loaded, none near the biggest scare, at least one that comes back as a clue) - built on ghost-story-v2's screen-first design (second 0 picture, the promise by second 8, a device that counts, two twists, a ghost that is seen), then checked with its style_check script and scored by independent reviewers round by round. The voice and joke rules come from an analysis of 209 stories on a large Taiwanese animated ghost-story channel; the mechanics are borrowed, never its characters, catchphrases or stories. Use whenever the user asks for v3, 用 v3 寫, 說書吐槽, a funny-then-scary ghost story with its screenplay, 有笑點的鬼故事加劇本, 吐槽式鬼故事, 像那種邊講邊吐槽的鬼故事, or a 3-minute ghost video story with banter and callbacks, even if they only say "寫一個好笑又可怕、能拍成短片的鬼故事". For the plain v2 voice use ghost-story-v2; for a PTT-style story from the marvel data or to score an existing story use ghost-story; for stills, voices and the video use ghost-film after the owner approves.
---

# Ghost story v3: v2's screen-first story, told by a narrator who jokes

v3 is ghost-story-v2 with one change of voice and the rules that come with it. The film is still designed first (the
picture at second 0, the promise by second 8, the count that carries the middle, two twists, the ghost seen), but the
story is told the way a friend tells it over late-night snacks: plain spoken Taiwanese Mandarin, the narrator
teasing himself and his friends, the friends teasing back, and three or four jokes placed where they do not touch
the scare. One joke at least comes back later as a clue.

Where the joke rules come from: `C:/Users/sheep/Pictures/gui_chang_shi/research/weiteng/findings_all.md` (209
stories from 131 videos of one large animated ghost-story channel, 2023 to 2026) and `borrow.md` next to it. Read
`references/voice.md` for the voice and the numbers. **That channel's data does not show that this style gets more
views**; v3 exists because the owner asked for the style, and whether it works on our accounts is measured on our
own posts (step 6).

```
ghost-story-v3 (story + screenplay, style_check, reviewed) → owner reads and approves → ghost-film (stills, voice, video) → ghost-pack-film → ghost-post
                                                                  ↘ ghost-comic (`from_screenplay.py`) → ghost-reel → ghost-pack → ghost-post
```

It borrows, by path, and never copies:
- ghost-story-v2 (`~/.claude/skills/ghost-story-v2/`): steps 1 to 5 are v2's, changed only where this file says so.
  Its `assets/example_story.md` and `assets/example_screenplay.md` are the shape of the files (in v2's PTT voice,
  not this one) and `references/example_rounds.md` is what review rounds change.
- ghost-story (`~/.claude/skills/ghost-story/`): `scripts/ghost_plan.py count|surface|post`,
  `references/review_rubric.md`, `references/writing_direct.md`, `references/review_brief.md`,
  `references/pairwise_judge.md`, and its Rules.
- ghost-film (`~/.claude/skills/ghost-film/`): `references/screenplay_short.md`, with the budget changes in step 3.

Its own files: `references/voice.md` (the voice, the joke rules with their numbers, examples written for us),
`references/review_addendum.md` (part 5 added to the review brief), `scripts/style_check.py` (checks the
screenplay's joke table against the rules).

**Not borrowed from that channel, ever:** its host's name, its recurring characters, its opening and closing
catchphrases, its stories or their twists. The owner decided (2026-11-20) there is no recurring cast for now: each
story has its own people.

## Inputs

All optional.

| | Default | Notes |
|---|---|---|
| length of the video | 2:45 to 2:52 | never over 2:59; v3 is for videos under 3 minutes only. A shorter target scales the budgets in step 3 and `style_check.py --length` |
| twists | 2 | as v2 |
| ghost | clearly seen (cap 3), taste 直接 | as v2 |
| cast | **4 speaking parts at most, the ghost included, and one of them only heard** (a phone call, a voice through a door, a neighbour) | the joke style needs a friend to tease and be teased; the fourth voice adds a voice in ghost-film, not a face |
| jokes | 3 to 4 | step 3; `voice.md` has the reasons |
| language | story in Taiwanese Mandarin, every spoken line in Mandarin | |
| setting, premise, extra requirements | free | anything the owner says wins |

## Steps

Work in `C:/Users/sheep/Pictures/gui_chang_shi/backlog/<english_short_name>/` as in v2: `story.md`,
`film/screenplay.md`, every earlier version in `drafts/`.

### 1. The idea, on one page

v2's step 1 unchanged (check `stories` and `backlog` for used devices, the eight lines of `drafts/idea.md`, the two
facts of life), plus a ninth line:

9. **The jokes and the one that comes back.** Three or four jokes, each with who says it, its type (吐槽角色、旁白
   吐槽、自嘲、日常荒謬) and roughly where it falls. Then the callback: which joke's content becomes a clue, a
   weapon, a ghost's reply or comes true, and the moment it does. It may be the line twist 2 overturns (line 6). A
   joke the ghost answers back in its own words counts; a joke that is only on the same subject does not.

An idea whose jokes all sit in the last minute, or whose callback is only a repeated subject, changes line 9 before
any prose.

### 2. The story

Read `references/voice.md` and ghost-story's `writing_direct.md`. Write `story.md` as in v2 (first line `[經驗]
title`, 1,000 to 1,200 characters), in the 說書吐槽 voice instead of PTT's. On top of v2's step 2 rules:

- The first line after the title is still idea line 3, the second-0 claim. **The second sentence** is the plain
  when-and-where (「那是我大二暑假的事。」); the channel opens on that in 66% of its stories, but our first second
  belongs to the hook.
- The jokes from line 9 are in, placed as step 3 will time them: the first within the first fifth of the text, most
  of them in the first half, none in the paragraph of the biggest picture, at most one after it (a single complaint
  from the narrator, never a ghost's quip).
- The friends tease each other in their own words. The narrator teases himself too. The ghost is not the butt of a
  joke; at most one 鬼的人性反應 in the whole story, and only after a scare.
- After the biggest picture, a third person (a landlord, a shop owner, a mother) explains in one or two lines what
  the narrator could not know, where the story allows it.
- The last line does not become a joke. 「或許……吧」 or one question is allowed, not required.

Then `ghost_plan.py count story.md` and `ghost_plan.py surface story.md` as in v2. The 說書吐槽 voice uses more
particles and 「」 than PTT; `surface` flags of quotes that are spoken jokes may stay, and say so in the round
table.

### 3. The screenplay

Read ghost-film's `references/screenplay_short.md`. Write `film/screenplay.md` as in v2, with these budget changes
for 2:52:

| | v2 | v3 |
|---|---|---|
| narration | 280 to 320 characters (70 to 76 s) | **200 to 240 characters** (48 to 57 s) |
| character lines and counts | 20 to 26 s | **40 to 50 s** |
| total speech | about 95 s | about the same: v3 moves speech from the narrator to the people |
| jokes | not budgeted | **3 to 4**; first between 0:10 and 0:25; the last before the biggest picture at least 25 s before it; none within 5 s of it; at most one after it |
| callback | not required | at least one; its payoff is a shot on screen, as the last twist's plant is |

Everything else in v2's step 3 and in screenplay_short.md holds (the first wrong thing by 0:25, the biggest picture
between 1:45 and 2:15, nine seconds at most after it, the last shot held four to five seconds, no title or end card,
the long takes ghost-film asks for: banter is played in one take, not cut line by line).

The header carries these lines exactly, for `style_check.py`:

```
**長度**：2:50
**旁白**：226 字
**台詞**：44 秒
**開口角色**：4（只出聲 1）
**最大畫面**：1:58
**笑點**：
| 秒 | 類型 | 誰 | 句子 | 回收 |
|---|---|---|---|---|
| 0:14 | 吐槽角色 | 阿凱 | 「你錢包比我臉還乾淨。」 | 2:31 物證：錢包裡的收據 |
| 0:41 | 自嘲 | 我 | 「我的人生就是一直在排隊。」 | — |
```

Types are 吐槽角色、旁白吐槽、自嘲、日常荒謬、鬼的人性反應、其他. A joke line in the scene text carries a tone note
for the voice (〔不耐煩〕〔假裝鎮定〕), so ghost-film's voice takes are chosen by it.

Then add up each scene against its seconds as in v2, write anything the camera needed back into `story.md`, and run:

```
python ~/.claude/skills/ghost-story-v3/scripts/style_check.py backlog/<name>/film/screenplay.md
```

It prints a table: each rule, the screenplay's value, the channel's reference, and 必改 / 注意 / ok. Fix every 必改
before the review; a 注意 may stay with one sentence in the round table saying why. It checks the table the writer
filled in, not the prose: the reviewer in step 4 makes the independent count.

### 4. Score and fine-tune

v2's step 4 unchanged, with two additions:
- The review brief gets **part 5** from `references/review_addendum.md` (the reviewer lists every joke it finds with
  its second and type, which ones come back and how, whether any sits on the scare, and whether the voice reads as
  a friend telling it). Fill the `<...>` of both and send them as one prompt.
- The round table to the owner adds two columns: style_check's 必改 count, and the reviewer's joke count against
  the header's. A gap of more than one joke means the header is wrong; recount before the next round.

The stop rule is v2's, plus: no 必改 left in style_check, and the reviewer found at least one callback it would
grade as a real one (the joke's content comes true or becomes a clue).

### 5. Deliver and stop

v2's step 5 unchanged. **Then wait** for the owner before ghost-film.

**Which line next** (the owner picks; the first trial, 2026-11-21, is the comic): the same story and screenplay feed
both. For the comic, `py -X utf8 ~/.claude/skills/ghost-comic/scripts/from_screenplay.py backlog/<name>` writes
`comic/board.json` (cast, scenes, one lettered panel per beat, the reveal marked, jokes and their callbacks mapped to
panels) and `comic/brief.md` (what a person still has to write); ghost-comic's step 1 says what carries over and what
does not. Two things to settle before drawing: the screenplay shows the ghost clearly (cap 3) while a comic defaults
to a restrained ghost, and a film's beats outnumber a comic's panels. The screenplay's headline numbers (the second-0
picture, the 最大畫面 second, the joke table) stay in `comic/brief.json` for ghost-reel's draft step.

### 6. The trial (the first stories only)

Until the owner says the trial is over, each v3 story is written beside a v2 story of the same idea (v2's steps 1 to
4 on the same `idea.md` lines 1 to 8), both are compared by one fresh subagent with ghost-story's
`pairwise_judge.md` (both orders), and the owner reads both. The result goes in one line to
`brand/taste.md` (idea, judge's pick, owner's pick). Once films of both versions are posted, their 3-second
retention, completion, likes and shares are recorded there too. Stop the trial after three pairs, or earlier if the
owner says the jokes drown the scare.

## Rules

ghost-story's Rules hold unchanged (fiction, `[創作]` and the AI disclosure when posted, no real person, business,
temple or hospital named as haunted, no retelling of a known post or film), and so does the line above: nothing of
the analysed channel's own (names, catchphrases, stories) goes into a story.
