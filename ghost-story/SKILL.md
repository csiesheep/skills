---
name: ghost-story
description: Write a Taiwanese ghost story in the voice of a PTT marvel board (飄板) 經驗 post, from a skeleton sampled out of 9,395 annotated marvel posts, then self-review it, have an independent reviewer score it with the rubric, and fine-tune it round by round until the review is clean. By default it writes three stories from three different skeletons and delivers the one a blind pairwise judge ranks best (the count is an option). Takes options in plain Chinese — setting (校園、宿舍、當兵、夜班、醫院、山路…), horror mechanism (附身、事後才知道、身份錯置…), ending (開放、有解釋、反轉、淡出), how much the ghost shows, length (極短 to 超長 or a character count), narration style (PTT 鄉民、簡約、幽默、口述、文學、紀錄、長輩講古), taste (直接 or 留白) and free-form extra requirements. Use whenever the user asks for a 鬼故事, 靈異故事, 恐怖故事, 怪談, 經驗文, 飄板文, a scary story set in Taiwan, "write me a ghost story", "寫一篇鬼故事", "來個短篇靈異", or wants several ghost stories, a different style of one, or a story with a given setting or twist, even if they don't mention PTT. Not for real-world paranormal claims, ghost-story analysis, or translating an existing story.
---

# Ghost story (PTT marvel style)

Writes one story (or several) that reads like a post on PTT's marvel board: first person,
colloquial, specific about time and place, with the scare built on other people's reactions
and everyday detail. The structure comes from data, not taste: `assets/table.json` holds what
the most-pushed marvel posts look like (setting, mechanism, ending, beat proportions, how much
the ghost shows, length) and a pool of 550 one-line premises and detail types, paraphrased,
with no original text, titles or authors. `references/findings.md` explains what the data
showed and why the rules are what they are.

You are the writer. The script only samples the skeleton; the story, the review and the
revision are yours.

## A story for 鬼唱詩 (what it is for)

Most stories written here become a comic, a Reel or a film on the 鬼唱詩 accounts, and the point of those is to grow
the accounts: new follows first, then (shares + saves) / reach, then watch time on the Instagram Reel. The table is
what PTT readers pushed; the accounts' own numbers are in `C:/Users/sheep/Pictures/gui_chang_shi/brand/taste.md`
(weekly, rules in auto_promotion `references/ghost_feedback.md`). When the story is for 鬼唱詩:

- **Read taste.md before sampling.** For an option the request leaves open, use its first 偏好 instead of the table:
  ending → `--ending`, 鬼出現的程度 → `--ghost` (不出現 0, 暗示 1, 看到一部分 2, 正面出現 3), 場景 → `--setting`. On
  2026-11-09 that was 開放結局, 暗示, 老家 or 租屋, which is not what PTT pushes most (a clear ghost, an explained
  ending). An option the user or the producer task gives always wins, and so does an exploration run (ghost_make.md's
  30 %) or the week's experiment.
- **Do not write the same story again.** `ls stories backlog` and read `brand/story_tags.json` (`premise`, `twist`)
  first. taste.md stopped 「團體＋多一個人」 after seven of them (three titles end in 點名) with 0 to 1 follows each.
  A draft whose device (the count that is one too many, the guestbook, the roll call) matches one of the last ten
  stories is rewritten on another device before the judge sees it.
- **The screen test** (step 4): the story has to give a video its first three seconds.

A story for anything else (a one-off, another account) skips this section.

## Inputs

Map the user's words to options. Anything not given is sampled from the table, which is
what the data says works, so leave it out rather than guessing.

| Option | Flag | Values |
|---|---|---|
| setting | `--setting` | 校園、宿舍、當兵、夜班、山上、租屋、醫院、超商、老家、飯店、夜路、喪事、廟、公司、捷運、小時候、自家、廢墟、電梯、國外、海邊…; several, comma-separated, means "pick among these" |
| mechanism | `--mechanism` | 附身、事後、不是本人、對不上、在場、只有聲音、託夢、通靈、禁忌、循環、夢、物件、善意、失控、時間 |
| ending | `--ending` | 開放結局、有解釋、反轉、淡出 |
| ghost cap | `--ghost` | 0–3, or 不露面、間接、一瞬間、清楚 |
| length | `--length` | 極短 400–700、短 800–1200、中 1500–2500、長 3000–4500、超長 5000–8000, or `1500`, or `1500-2500` |
| style | `--style` | PTT 鄉民 (default)、簡約、幽默、口述、文學、紀錄、長輩講古 |
| style note | `--style-note` | free text, e.g. 像寫給朋友的信 |
| taste | `--taste` | 直接 (default) or 留白 |
| extra | `--note` (repeatable) | free text, e.g. 主角是護理師、發生在颱風夜 |
| count | `--count` | how many stories to write and compare, **default 3**; only the best one is delivered. 1 skips the comparison |

Common phrasings:
- **two places** (醫院夜班、宿舍頂樓): put the place the scariest scene happens in as
  `--setting` and the other in a `--note`. A comma list means "pick one of these", not both.
- **大概 1500 字**: `--length 1500`; a single number is the target, and the review allows
  20% either way. Use a preset only when the user names one (短、長).
- **不要把鬼寫得太清楚、克制一點**: that is `--taste 留白`, and it is enough on its own. Set
  `--ghost` only when the user names a level (完全不要出現 → 0, 只要一瞬間 → 2).
- **反轉 再反轉 (又再反轉)**: `--ending 反轉` and `--note 反轉兩次` (三次 for 又再反轉). The
  writing rules' 「好幾次反轉」 section then replaces "the twist turns once": every twist has to
  overturn what the narrator believed, with a clue planted before it.
- **How many**: 產生 5 個選最好的 → count 5; 只要一篇、寫一篇就好 → count 1; anything else → 3.
  The count is how many compete, not how many are delivered. If the user wants to read all of
  them (三篇都給我看), deliver all, ranked.
- **持續打磨、要有商業價值、讓人想從頭看到尾**: the usual run; step 5b's independent rounds run for every
  delivered story anyway, and these words mean all three rounds are used if the hole list is not empty sooner.
- **評分、用 ghost-story 來評分** (a story written elsewhere, by hand or by ghost-story-v2): skip steps 1–3 and 5,
  run step 4's `count` and `surface` and then step 5b on that file.

**Taste** is the one choice that changes how the scare works, so pick it from the user's
words: 克制、含蓄、留白、不要太直接、不要血腥 → 留白; otherwise 直接. 直接 follows what
PTT readers push most (the scariest moment shows what was seen, the narrator is sure);
留白 keeps the ghost under-described and leans on reactions, sound and doubt. One blind
reader preferred 留白 while the reader data and the pairwise judge preferred 直接, so both
are legitimate.

## Steps

1. **Sample the skeleton.** The script is stdlib-only Python 3.10+. `<skill dir>` is the
   folder this SKILL.md is in (installed copies are usually `~/.claude/skills/ghost-story`;
   on Windows that is `C:\Users\<you>\.claude\skills\ghost-story`). On Windows run it with
   `py` if `python` is not found:
   ```bash
   python "<skill dir>/scripts/ghost_plan.py" plan --setting 校園 --ending 開放結局 --length 短 --style 幽默
   ```
   `options` lists every value; an ambiguous word (「家」) errors with the candidates — ask
   the user or pick the closest. Add `--seed N` to reproduce a skeleton. `--count N` samples N
   different skeletons in one call (with `--seed`, the seeds run N, N+1, …); use the story count
   from Inputs, 3 by default.
2. **Read the rules for this taste and style.** `references/writing_direct.md` or
   `references/writing_restrained.md`, plus `references/styles/<style>.md` (for 留白 with
   簡約, read `minimal_restrained.md` instead of `minimal.md`). These are the full rules;
   the skeleton is the brief.
3. **Write the story** in Traditional Chinese with Taiwanese usage. First line is the title,
   then the body, nothing else, no Markdown. The title is `[經驗] 四到十二個字`, plain like a topic
   (麵攤的阿伯、重修微積分的學長), not 「XX那YY」 (那晚、那張、那個禮拜): 3% of real top titles
   have 那, four in ten of our drafts did. That holds unless the
   style file says otherwise (口述、文學、長輩講古 may use a plain title); the tag is part of
   the voice, and becomes `[創作]` only if the user says they will post it. Treat the anchor
   hints as kinds of detail to invent your own instances of, and the structural examples as
   shapes, never as events to retell. Hit the beat proportions roughly; never skip the denial
   beat, even in a short story. Write long: `count` leaves out punctuation and line breaks, and
   three first drafts written "to the target" came in 40 to 45% under it. Let the first two or
   three lines pay off the title (the thing that is wrong, not the backstory); a reviewer
   marked the breakup-and-moving opening as where a casual reader leaves.
4. **Review it.** Save the draft to a file, then these checks in this order:
   - **Count**: `python "<skill dir>/scripts/ghost_plan.py" count <file>`.
   - **Surface**: `ghost_plan.py surface <file>` compares how it looks on the page with real top
     posts (`assets/surface.json`, 957 posts, numbers only): line length, lines that stop
     mid-sentence, how much sentence length varies, quotes, ellipses, ? and !, digits, and three
     habits real posts rarely have (a disclaimer opening, a quoted line as the last line, 那 in
     the title). For the default PTT style, at most one 必改 and three 建議; a real top post's
     median is one and two, the first generated drafts had three to five 必改 each, and the owner
     picked out every one of them in a blind read. Fix those by re-breaking lines and changing
     numerals in place, not by a rewrite. Too few open lines and too little sentence spread
     usually have one cause, a 。 or ， at the end of every line: drop the end mark on every line
     of a paragraph except its last, and both come into range. Other styles (文學、紀錄、長輩講古)
     may ignore the line breaks.
   - **Read it through once as a reader** (the rubric's 通順 check): every person is introduced
     once, in one sentence that says who they are to the narrator; every 他/她 has one possible
     owner; nothing said about where and when contradicts an earlier line. The owner sent 第 28 首
     back with 「不夠流暢」 for a three-person introduction nobody could follow and a line about
     where the narrator slept that the story had already contradicted; the rubric had passed it.
   - **Rubric**: score it with `references/review_rubric.md`.
   - **Screen test** (鬼唱詩 stories): write three lines to `drafts/<draft>_screen.txt`. The hook:
     the first sentence after the title, 40 characters at most, that already holds the wrong
     thing (it becomes `hook` in story_tags.json and the Reel's first subtitle). The first frame:
     one picture with the person and the strange thing in it together. The story in one line a
     viewer could tell a friend (the twist as 「本來以為……，其實……」 when there is one). A draft
     that cannot fill a line is fixed in place until it can. The Reels' watch time is lost in
     the opening, and a text overlay on a dark first frame did not read on a phone.
   - **Fails** (length off by more than 20%, an extra requirement missed, or below the pass
     rule): rewrite the whole story from your fix notes and review again. Two rewrites at most.
   - **Passes but the notes name something concrete and cheap** (a continuity slip, a reaction
     that should be a line of dialogue, length near the 20% edge): fix those in place, without
     a rewrite, then recount. That is not another round and needs no full re-score.
   - Keep the version with the highest overall score; on a tie, the later one. The rubric
     catches rule breaks and continuity errors well, but it is a poor judge of whether readers
     will like it (see its last section), so don't polish forever chasing its score.
   With several stories, do steps 2–4 for each, saving each draft as its own file
   (`s1.md`, `s2.md`, …); every one has to pass on its own before the comparison.
5. **Pick** (count 2 or more). Judge in a fresh subagent, not yourself: you wrote all of them and
   will favour the one you like. Give it the drafts as A, B, C… with each one's brief (mechanism,
   ghost cap, target and actual length) and the paths to `review_rubric.md`,
   `pairwise_judge.md` and the writing rules, and ask for:
   - the rubric for each story (five scores, overall, pass or fail, at most three fix notes);
   - every pair judged twice with `pairwise_judge.md`, once in each order, recording the
     popular and scary winner each time, then the win counts per story.
   For a twist ending, the rubric also states each twist in one line (「本來以為……，其實……」).
   The winner is the story with the most **scary** wins; ties go to more popular wins, then to
   the higher rubric overall. For a 鬼唱詩 story, also give the judge each draft's screen-test
   lines and ask which one it would stop scrolling for and which it would send to a friend, with
   a reason; report that beside the wins, and use it to break a tie before the popular wins. It
   is an untested question (the pairwise judge was checked against PTT pushes, not against
   follows), so it does not overrule the scary wins. A winner that the judge's rubric fails cannot be delivered as it
   is: apply its fix notes if they are cheap and have a fresh subagent recheck that point, or
   take the best story that passed. The hospital story with three twists won on scary wins and
   failed for its third twist, which only put one more figure behind the narrator; its fix note
   made that twist overturn who was protecting whom. Pairwise comes first because it picked the right real post about
   90% of the time, while the absolute rubric did no better than chance (AUC about 0.5). If the
   two disagree, say so in one line. Apply the winner's fix notes in place if they are concrete
   and cheap (step 4's rule), then recount.
5b. **Score and fine-tune** (every story that is delivered; before 2026-11-14 this ran only when asked). Your
   own rubric score in step 4 is the writer marking their own work, so the delivered story gets at least one
   independent round, and rounds repeat until it is clean:
   - Save the current text as `drafts/vN.md`, then give a **fresh subagent** `references/review_brief.md` filled in
     (rubric, writing rules, the story, its brief; the screenplay too when there is one). It returns the rubric, the
     twist lines, every point a PTT reader would push 虛 at, where a reader stops, and line-level fixes.
   - Apply every fix that costs a line or two, in place. Rerun `count` and `surface`; `surface` wins when it and the
     reviewer disagree about how the page looks.
   - Next round with a **new** subagent that has seen nothing earlier. Never tell it what the last round found.
   - **Stop** when a round passes and its 虛 list has nothing left that costs more than a line, or after three
     rounds. A round that fails the rubric is step 4's rewrite, not a line fix.
   - Report each round to the owner as one table (five scores, overall, and for a film the three guesses) and the
     list of what changed, not the reviewer's full text.
   The 美女 story took three rounds: round one failed it on the requirement, round two found a dead fact in the twist
   (台灣身分證沒有效期) and two contradictions the writer missed, round three found the ghost should have been in the
   selfies. 〈一中街的無人拍貼店〉 took two: overall stayed 7 while round one's eleven holes were closed and round two
   found five the first had not reached (a friend with a dead phone who still sent a LINE, a camera that could not
   have filmed its own screen). Every fix was a line or two; none was a rewrite. How to read a review, and what to
   do when two reviewers disagree: the end of `references/review_brief.md`.
6. **Deliver.** The winning story as plain text, then one line: setting / mechanism / ending /
   taste / style, and the character count against the target. With several stories, add a
   short table of all of them (title, mechanism, rubric overall, scary and popular wins), one
   sentence on why the winner won, and the folder where every draft is saved. Everything goes
   in the 鬼唱詩 backlog, not a scratch folder: `C:/Users/sheep/Pictures/gui_chang_shi/backlog/
   <english_short_name>/`, laid out like a story under `stories/` (folder contract in that
   tree's `README.md`): the delivered story as `story.md`, every other draft, version and losing
   story in `drafts/`, and `posts/threads/hook.txt` + `attachment.txt` from `ghost_plan.py post
   story.md --brand-file brand/brand.json --dest <folder>` (run from `gui_chang_shi`; read the
   hook it picked, and pass `--hook 1` when the story's own opening is the hook). Leave
   `README.md`, the number and the captions to ghost-pack. Work in drafts there from the start
   (`drafts/s1.md`, …) rather than copying them over at the end; the owner asked for this after
   one run left everything in the session scratchpad. If the user later wants to know which of two
   versions is scarier, use `references/pairwise_judge.md` the same way: a fresh subagent, run
   twice with A and B swapped. If the request also asks for a comic (畫漫畫、產生漫畫), stop
   here and ask whether to go on; start ghost-comic only after the owner's OK. The owner read
   one story only after its comic was drawn, rejected it, and about 1.7 GPU hours went with it.


## 審稿後修改 (since 2026-11-02)

Every 鬼唱詩 story is reviewed by the owner on https://monitor.csiesheep.com/ghost/review/ before it posts. Comments on the story text (target 全文 第 a–b 行, line numbers count every line of story.md) are fixed by editing those lines, then `ghost_plan.py post … --dest <story folder>` again (keep the hook within 485 characters) and ghost-pack's pack.py. The whole loop (reply, push, back to 待審): ~/.claude/skills/auto_promotion/references/ghost_revise.md.

## Rules

- **It is fiction.** A marvel `[經驗]` post is supposed to be a real experience. If the user
  wants to post a generated story, tell them to use `[創作]` and say it was written with AI;
  don't help present it as something that happened. `ghost_plan.py post <file>` does both and
  cuts the story for the platform: `--mode attach` (default) is one Threads post of 500
  characters ending on a sentence, with the whole story as a text attachment; `--mode chain`
  is numbered Threads posts of 500 at most, cut between paragraphs or sentences; `--mode ig` is
  an Instagram caption within 2,200. For an account with a brand file (the same `brand.json`
  ghost-comic's export reads), add `--brand-file brand.json`: the disclosure and sign-off
  (鬼唱詩's 「收驚。」) and tags come from the file, and the heading is the bare title. No number:
  in the 鬼唱詩 pipeline ghost-pack numbers a story only when it is about to be posted and adds
  「第 N 首」 itself; `--number N` still exists for a one-off.
  The attach post opens on the hook, not the setup: by default the strongest sentence or colon
  clause in the first third of the story (a rule, a voice calling, something that is not there;
  if the line before it is also strong, such as the question that 「我回頭」 answers, it starts
  there). Read what it picked. When it picked setup (it did for three of five 鬼唱詩 stories),
  pass `--hook <the sentence to start at>` or `--hook <paragraph number>`. `--hook 1` gives the
  old behaviour, the story from its first paragraph.
  `--dest <story folder>` also writes the post and the attachment to `posts/threads/hook.txt` and
  `posts/threads/attachment.txt`, the names in the folder contract
  (`C:/Users/sheep/Pictures/gui_chang_shi/README.md`), where ghost-pack and ghost-post look.
- **No real targets.** Keep places at the level the rules allow (縣市、區、路段、某國中)
  and never name a real person, a real business, or a specific temple or hospital as haunted.
- **Don't copy.** The pool is paraphrase on purpose. Don't reconstruct a known marvel post,
  even if the user asks for "the one about…"; write a new story in its shape instead.

## What it learned

- The structure every rule rests on: dialogue (80% of top posts vs 57% of low ones), a
  specific place, and a ghost that actually shows up. A ghost that never appears scores
  lowest both on pushes and on how often readers say 好毛.
- Popular is not the same as scary. Explained endings get more pushes but fewer 好毛 and
  more 虛; twist endings get fewer pushes and the most 好毛.
- A twist has to be retellable in one line by a first-time reader. 「結局看不太懂」 sank a
  whole story and its comic; with several twists, each one must overturn the last belief, not
  add one more ghost.
- The writer's own score is not a review. Two independent rounds on one story found sixteen holes its writer had
  passed, at a flat overall of 7: read the hole list, not the number.
- An absolute 1–10 judge could not tell real top posts from real low ones (AUC about 0.5).
  Asking "which of these two" could, about 90% of the time. Use the rubric to check the
  rules, and comparison to choose.
- A twist must not meet a requirement by overturning it. Asked for a pretty narrator, the
  best story made her plain and her beauty the ghost's face; it won every pairwise vote and
  failed the rubric. Kept the twist by making her pretty already and having people notice she
  looked *different*: the requirement held and the reactions became the clues.
