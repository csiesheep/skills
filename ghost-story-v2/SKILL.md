---
name: ghost-story-v2
description: Write one Taiwanese ghost story together with its short-film screenplay (one vertical video of 3 minutes or less), designed from the screen backwards for watch time, likes and shares on social platforms, then have independent reviewers score both with ghost-story's rubric and fine-tune them round by round. No sampled skeleton - the story starts from an everyday thing viewers do with friends, a picture for second 0 and two twists. Use whenever the user asks for a ghost story AND its film script or screenplay, 鬼故事加劇本, 3 分鐘影片的鬼故事, a story 給社群平台的影片用, a story made for 觀看長度、按讚、分享, says 不要用 ghost-story or 用 v2 寫, or wants a story for the 鬼唱詩劇場 film line, even if they only say "寫一個可以拍成短片的鬼故事". For a PTT-style story from the marvel data, or to score a story that already exists, use ghost-story. For stills, voices and the video itself, use ghost-film after the owner approves.
---

# Ghost story v2: a story and its screenplay, written for the screen

ghost-story starts from what PTT readers pushed and a story is adapted for video afterwards. This skill starts from
the video: the story and the screenplay are designed together, so the first picture, the count that carries the
middle and the last shot exist before the prose does. It was written from one run, 〈一中街的無人拍貼店〉
(2026-11-14): `assets/example_story.md`, `assets/example_screenplay.md`, and what its two review rounds changed in
`references/example_rounds.md`.

```
ghost-story-v2 (story + screenplay, reviewed) → owner reads and approves → ghost-film (stills, voice, video) → ghost-pack-film → ghost-post
```

It borrows, by path, and never copies:
- ghost-story (`~/.claude/skills/ghost-story/`): `scripts/ghost_plan.py count|surface|post`,
  `references/review_rubric.md`, `references/writing_direct.md` (or `writing_restrained.md`),
  `references/review_brief.md`, and its Rules (fiction only, no real targets, no copying a known post).
- ghost-film (`~/.claude/skills/ghost-film/`): `references/screenplay_short.md`, the rules a short screenplay is
  written to. Read it before step 3.

## Inputs

All optional; the defaults are what the first run used.

| | Default | Notes |
|---|---|---|
| length of the video | 2:45 to 2:52 | never over 2:59 (Instagram's Reel limit); a shorter target scales the budgets in step 3 |
| twists | 2 | the owner: 「反轉再翻轉」 |
| ghost | clearly seen (cap 3), taste 直接 | the owner: 「我要有看到鬼」; 留白 only if asked |
| cast | 3 people at most, the ghost included | every extra face is stills, voices and continuity |
| language | story in Taiwanese Mandarin, every spoken line in Mandarin | |
| setting, premise, extra requirements | free | anything the owner says wins |

## Steps

Work in `C:/Users/sheep/Pictures/gui_chang_shi/backlog/<english_short_name>/` from the start: `story.md`,
`film/screenplay.md`, every earlier version in `drafts/`.

### 1. The idea, on one page, before any prose

First `ls stories backlog` in `gui_chang_shi` and read the titles (and `brand/story_tags.json`): no device the
brand has already used. On 2026-11-14 that ruled out roll calls and head counts, the lift, the dashcam, the video
call, the motion-sensor light and the protector twist (「其實他一直在擋」, three stories). Then write
`drafts/idea.md` with these eight lines. An idea that cannot fill a line is changed, not written around.

1. **The everyday thing.** Something the viewers do, with a friend, this month: a photo booth, a claw machine, a
   shared ride. It is what makes someone tag a friend, and it is the share.
2. **The device that counts.** Something in that place that already counts or repeats (four countdowns, floors, a
   queue number). Each count adds one wrong thing. It is the middle of the film.
3. **Second 0.** One picture with the person and the wrong thing in it together, and the sentence that goes on it,
   20 characters at most (a hand making a peace sign beside her face: 「這隻手不是我朋友的」).
4. **The promise.** What the viewer is told by second 8 that they will only get at the end (「拍攝過程的影片，我放在
   最後」).
5. **Twist 1** as 「本來以為……，其實……」, and the three clues planted before it.
6. **Twist 2**, the same way. It overturns something the narrator said in the first minute (「賺到」), not who the
   ghost is; a second twist that only moves the ghost or adds one fails the rubric.
7. **The last shot.** The shot that planted twist 2, seen again. If the film loops there, better.
8. **The ghost, seen.** The one picture where she is clear, and the marks (a jacket, wet hair, nail colour) that
   make her the same person in every form she takes.

Check the idea against two facts of life before going on: how the real thing works (a photo booth's payment,
countdown, prints and QR code), and what the narrator could not see or know. Where the idea needs the real thing to
behave differently, plan the sentence in which the narrator says so.

### 2. The story

Read ghost-story's `writing_direct.md` (or `writing_restrained.md`). Write `story.md`: first line `[經驗] title`
(4 to 12 characters, a plain topic, no 那), then the body, PTT voice, about **1,000 to 1,200 characters** for a
video of just under three minutes. On top of ghost-story's rules:

- The first line after the title is line 3 of the idea, as the narrator would say it.
- Other people react in their own words, and the last person to arrive asks the question the viewer has.
- The narrator has a week of her own (an exam just over, where the friend will sleep) and one or two details that
  lead nowhere (the shop's air conditioning, the music). Both reviewers of the example gave realism 3 until these
  were in.
- Where the device departs from the real thing, the narrator says it and shrugs (「舊舊的不知道哪一牌」, 「照理說會
  自己跳回首頁，那台就一直亮在那邊」). The second of those became the plant for twist 2.
- The mistake is the narrator's, not the ghost's cleverness: she saw a mask and called her friend's name. A ghost
  that matches a LINE message it never read gets 「鬼會看 LINE 喔」.
- What the story says the photographs or the footage show is only what that camera could have recorded.

Then `ghost_plan.py count story.md` and `ghost_plan.py surface story.md`: no more than one 必改. The usual two are
quotes (keep 「」 for the one or two lines that matter and report the rest; screen text is not a quote) and a quoted
last line.

### 3. The screenplay

Read ghost-film's `references/screenplay_short.md` and write `film/screenplay.md` in the shape of
`assets/example_screenplay.md`: the header with the target length and the totals (narration characters, seconds of
lines), the format notes, the cast with the ghost's shared marks, the place and **the rules of the device**, the
retention design in five lines, the scenes with their seconds in each heading, and the twists as one line each at
the end. The budgets for 2:52: 280 to 320 characters of narration, 20 to 26 seconds of lines and counts, the first
wrong thing by 0:25, the biggest picture between 1:45 and 2:15, nine seconds at most for the scene after it, the
last shot held four to five seconds, no title card and no end card.

Then add up each scene (narration characters / 4.2, plus lines, plus reading time for on-screen text) against its
seconds, and write anything the camera needed (a mark, a prop, a number) back into `story.md`.

### 4. Score and fine-tune

The writer's own read is not a review: the first draft of the example passed its writer and an independent reviewer
then listed eleven holes in the story and found the film 10 to 15 seconds too long.

Each round:
1. Copy `story.md` and `film/screenplay.md` into `drafts/` (`v1.md`, `screenplay_v1.md`, …).
2. Give a **fresh subagent** ghost-story's `references/review_brief.md`, filled in with both files, the brief
   (setting, mechanism, two twists, ghost cap, taste, style, target and actual characters) and the extra
   requirements, including what is deliberate fiction. It scores the story with the rubric and reads the screenplay
   as a short video (part 4 of the brief). Do not tell it what an earlier round found.
3. Apply every fix that costs a line or two, in both files, so they still agree. Rerun `count` and `surface`.
   How to weigh the advice (two reviewers pulling opposite ways, a hook the reviewer wants cut, a sub-score stuck at
   3) is at the end of review_brief.md.
4. Tell the owner in one table: the five scores and overall, the three guesses (retention, likes, shares), and what
   changed. Not the reviewer's text.

**Stop** when a round passes the rubric (overall 7 or more, realism, ghost and voice 3 or more, both twists
counted) and what is left on its 虛 list and its screenplay notes costs no more than a line each: apply those and
do not send them back for a re-score. Three rounds at most. A round that fails the rubric means the idea is wrong
somewhere: go back to step 1's page, not to line fixes. The example took two rounds and one unreviewed set of line
fixes; its overall was 7 both times and its guesses went 5/6/7 to 6/7/7.

What the numbers are worth: the rubric's absolute score does not separate real high-push posts from low ones (its
own last section says AUC about 0.5), and the three guesses are one reader's opinion. Their use is the list that
comes with them. Say this to the owner once, with the first table; do not present a 7 as a forecast.

When the owner asks for several ideas to choose from, run steps 1 and 2 for each, have one fresh subagent compare
them with ghost-story's `references/pairwise_judge.md` (each pair twice, both orders), and take only the winner
through steps 3 and 4.

### 5. Deliver and stop

Show the story as plain text and the screenplay in the reply (the owner reads them there), the rounds table, and
the folder. Run `ghost_plan.py post story.md --brand-file brand/brand.json --dest <story folder>` from
`gui_chang_shi` for `posts/threads/`. **Then wait.** ghost-film starts only after the owner has read both and said
yes: a film is several GPU hours, and a story the owner read only after its comic was drawn cost 1.7 of them.
Notes from the owner are line fixes in both files; a note that changes a twist goes through one more review round.

## Rules

ghost-story's Rules hold here unchanged: it is fiction (`[創作]` and an AI disclosure when posted, which
`ghost_plan.py post` adds), no real person, business, temple or hospital named as haunted (a district or a street
is the limit), and no retelling of a known post or film.

## What it learned

- Designing the film first changes the story. The hand in the photograph, four countdowns and a screen that says
  「已付款」 were chosen because they film; the prose was written around them.
- The share is in the setting, the like is in one picture, the watch time is in a promise made by second 8.
- A twist that the story explains in a sentence may be invisible on screen. The plant has to be a shot, and the
  ending has to show that shot again.
- Reviewers find what the writer cannot, and a second reviewer finds what the first did not reach. Neither can say
  whether people will watch.
