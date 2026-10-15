---
name: ghost-story
description: Write a Taiwanese ghost story in the voice of a PTT marvel board (飄板) 經驗 post, from a skeleton sampled out of 9,395 annotated marvel posts, then self-review and revise it. Takes options in plain Chinese — setting (校園、宿舍、當兵、夜班、醫院、山路…), horror mechanism (附身、事後才知道、身份錯置…), ending (開放、有解釋、反轉、淡出), how much the ghost shows, length (極短 to 超長 or a character count), narration style (PTT 鄉民、簡約、幽默、口述、文學、紀錄、長輩講古), taste (直接 or 留白) and free-form extra requirements. Use whenever the user asks for a 鬼故事, 靈異故事, 恐怖故事, 怪談, 經驗文, 飄板文, a scary story set in Taiwan, "write me a ghost story", "寫一篇鬼故事", "來個短篇靈異", or wants several ghost stories, a different style of one, or a story with a given setting or twist, even if they don't mention PTT. Not for real-world paranormal claims, ghost-story analysis, or translating an existing story.
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

Common phrasings:
- **two places** (醫院夜班、宿舍頂樓): put the place the scariest scene happens in as
  `--setting` and the other in a `--note`. A comma list means "pick one of these", not both.
- **大概 1500 字**: `--length 1500`; a single number is the target, and the review allows
  20% either way. Use a preset only when the user names one (短、長).
- **不要把鬼寫得太清楚、克制一點**: that is `--taste 留白`, and it is enough on its own. Set
  `--ghost` only when the user names a level (完全不要出現 → 0, 只要一瞬間 → 2).

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
   the user or pick the closest. Add `--seed N` to reproduce a skeleton. For several stories,
   run it once per story without a seed so they differ.
2. **Read the rules for this taste and style.** `references/writing_direct.md` or
   `references/writing_restrained.md`, plus `references/styles/<style>.md` (for 留白 with
   簡約, read `minimal_restrained.md` instead of `minimal.md`). These are the full rules;
   the skeleton is the brief.
3. **Write the story** in Traditional Chinese with Taiwanese usage. First line is the title,
   then the body, nothing else, no Markdown. The title is `[經驗] 四到十二個字` unless the
   style file says otherwise (口述、文學、長輩講古 may use a plain title); the tag is part of
   the voice, and becomes `[創作]` only if the user says they will post it. Treat the anchor
   hints as kinds of detail to invent your own instances of, and the structural examples as
   shapes, never as events to retell. Hit the beat proportions roughly; never skip the denial
   beat, even in a short story.
4. **Review it.** Save the draft to a file, count with
   `python "<skill dir>/scripts/ghost_plan.py" count <file>`, then score it with
   `references/review_rubric.md`.
   - **Fails** (length off by more than 20%, an extra requirement missed, or below the pass
     rule): rewrite the whole story from your fix notes and review again. Two rewrites at most.
   - **Passes but the notes name something concrete and cheap** (a continuity slip, a reaction
     that should be a line of dialogue, length near the 20% edge): fix those in place, without
     a rewrite, then recount. That is not another round and needs no full re-score.
   - Keep the version with the highest overall score; on a tie, the later one. The rubric
     catches rule breaks and continuity errors well, but it is a poor judge of whether readers
     will like it (see its last section), so don't polish forever chasing its score.
5. **Deliver.** The story as plain text, then one line: setting / mechanism / ending /
   taste / style, and the character count against the target. Save it to a file only if
   the user asked or there are several. If the user wants to know which of two versions is
   scarier, use `references/pairwise_judge.md` — in a fresh subagent if you can spawn one,
   since judging your own draft is biased — and run it twice with A and B swapped.

## Rules

- **It is fiction.** A marvel `[經驗]` post is supposed to be a real experience. If the user
  wants to post a generated story, tell them to use `[創作]` and say it was written with AI;
  don't help present it as something that happened.
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
- An absolute 1–10 judge could not tell real top posts from real low ones (AUC about 0.5).
  Asking "which of these two" could, about 90% of the time. Use the rubric to check the
  rules, and comparison to choose.
