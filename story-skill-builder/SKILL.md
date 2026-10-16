---
name: story-skill-builder
description: Build a data-driven generator skill for one kind of short text (鬼故事, 笑話, 心靈雞湯, 糗事, any genre with a public corpus whose readers leave a signal such as PTT pushes or likes), the way ghost-story in this repo was built - scrape, have Claude label the structure, turn reception into weights, derive writing rules from the high-versus-low contrast, calibrate a pairwise judge on real pairs, blind-test with the owner, then package the result as a skill here. Use whenever the user wants a 產生器, "a skill that writes X", says 做一個笑話產生器, 像鬼故事那樣做一個…, 心靈雞湯產生器, or wants to rerun, extend or rebuild the ghost-story pipeline. Not for writing one piece of a genre that already has its own skill.
---

# Story skill builder

Turns one kind of short text into a generator skill shaped like
[`ghost-story`](../ghost-story/SKILL.md): a sampling table built from what readers of that
genre actually rewarded, a stdlib script that samples a skeleton from it, writing rules each
tied to a number in the data, a self-review rubric, and a pairwise judge that was checked
against real pairs before anyone trusts it. The builder does not write stories. It walks one
Claude Code session through building the thing that does, and stops where only the owner can
decide.

## What is here now

The pipeline that produced ghost-story, moved in whole and made genre-agnostic:
`scripts/storypipe/` (PTT scraping, corpus building, Claude annotation, statistics, planning,
writing, judging, judge calibration, blind A/B pages) with `genres/ghost-story/` as its first
genre. A genre is a folder: `genre.json` (the axes with their values and Chinese aliases, the
cap, the beats, the free-text fields, voice markers, length presets, rule sets, tastes,
styles, the judge's dimensions, the comment-signal keywords) plus `prompts/` (`annotate.md`,
`style_guide.md`, `judge.md`, `pairwise_judge.md`, one `styles/<style>.md` per style, and a
subfolder per extra rule set). Nothing about ghosts is in the code: the annotation schema,
the CLI flags, the weights table, the report and the planner are all built from the genre at
import time, and `STORYPIPE_GENRE` picks the folder. The tests prove it by running a
three-axis joke genre through options, annotate, stats and generate without a code change.
`references/genre_config.md` documents every field with the ghost values beside a joke sketch.

## Running the pipeline

Work in a folder of its own, never in this repo: `data/` under the current directory holds
that genre's raw posts, corpus, annotations and reports, and none of it may be committed
(the raw text is other people's writing; the shipped table is paraphrase only). Python 3.10+,
`pip install -r scripts/requirements.txt`. On Windows run with `py -X utf8` so Chinese
survives the console.

```bash
py -X utf8 "<skill dir>/scripts/pipe.py" --help
```

Commands, in pipeline order: `index` (list pages of a PTT board search, no bodies),
`fetch` (bodies for every post above a push threshold plus a random low-push control group),
`fetch-early` and `digest` (pre-search-era posts and the board digest), `corpus` (merge
serials, deduplicate), `annotate` (Claude labels structure against the genre's schema; retries
on rate limits, records the model actually served and the cost from token counts),
`batch-report` and `compare` (one batch's cost, time and distributions; agreement between
annotation runs), `stats` (percentiles within tag and year, high-versus-low contrasts with
p-values, weights, the report), `generate` (plan, write, judge, revise) and `options`.
Standalone modules run from `scripts/` as `py -X utf8 -m storypipe.<name>`: `calibrate` and
`pairwise` (absolute and pairwise judges against real high/low pairs), `scare` (a second
quality signal mined from push text), `ab`, `ab_pairwise` and `blind_page` (owner blind
reading), `repair_titles`, `show`.

Environment: `STORYPIPE_GENRE` is the genre folder (default `genres/ghost-story`);
`STORYPIPE_LLM_BACKEND` is `cli` (Claude Code's own login, `claude -p` with a JSON schema;
what ghost-story used), `sdk` (`ANTHROPIC_API_KEY`) or `fake` (tests). The tests need neither
network nor money:

```bash
py -X utf8 -m unittest tests.test_pipeline
```

## The seven phases

Each phase ends at a gate. Stop there and show the owner numbers, not transcripts.

1. **Define.** Ask what the genre is, what a good one does to its reader, who reads it, and
   for two or three pieces the owner likes. Draft the genre config (next section) from that.
   Gate: the owner approves the annotation axes. They are the language of everything after.
2. **Sources and scraping.** Find corpora where readers left a signal. PTT boards work with the
   scraper as is; anything else needs an adapter and a feasibility check before any code. Aim
   for at least 1,000 usable units with a signal; ghost-story used 9,395. Gate: counts and the
   year range.
3. **Annotate.** Label 60 first and look at the distributions: an axis whose values are all
   "other", or spread over 40 values, is a bad axis, so fix the schema now, not after 9,000
   calls. Then estimate the full run (ghost-story: Claude Opus 5.5, about US$55 per 1,000
   units of 1,500 characters, a day of wall time with 8 threads). Gate: the owner agrees to
   the cost.
4. **Statistics and rules.** Score each unit as a push percentile within its own tag and year,
   contrast the top quartile against the bottom 40% on every axis, and write rules v1 where
   every rule cites its contrast. Mine the comments for a second signal (ghost-story's 毛率:
   readers writing 好毛 versus 虛), because popularity and quality part ways.
5. **Generator and judges.** Planner samples a skeleton from the table; the writer gets the
   rules and the skeleton; the rubric checks rule-following and continuity. Calibrate the
   pairwise judge on real high/low pairs: below 85% it does not go into the loop (an absolute
   1-10 judge scored 50% for ghost stories, a coin flip). Gate: the calibration numbers.
6. **Blind test and tastes.** The owner reads A/B pairs blind (the `blind_page` artifact).
   Where the owner and the reader data disagree, keep both as a taste option rather than
   picking a winner. Gate: the owner chooses.
7. **Package.** Scaffold the product skill, build the table with titles, ids, urls and
   authors stripped, add the README row, write the tests, run the product with and without
   the skill and let the pairwise judge compare, open the PR.

## What each genre decides

| Field | ghost-story | a joke genre might say |
|---|---|---|
| unit | one post, serials merged | one joke; reposts deduplicated |
| sources and signal | PTT marvel, pushes | PTT joke and StupidClown, pushes |
| axes | setting, mechanism, ending, ghost cap, beat shares, length | form, mechanism of the laugh, topic, setup-to-punchline share, offence cap, ending |
| second signal | 毛 / 雞皮疙瘩 versus 虛 | XD / 笑死 versus 冷 / 老梗 |
| tastes | 直接, 留白 | 冷, 鬧 |
| floor | fiction, no real places named | no groups targeted, no real people |

Every genre needs one "cap" axis, the analogue of how much the ghost shows: a numeric ceiling
the planner hands the writer and the rubric checks. It was the single most useful constraint
in ghost-story.

## Weak-signal genres

Some genres live where scraping is not allowed (心靈雞湯's best sources are Facebook pages
and Threads). Then the builder runs in taste mode: the owner rates about 100 pieces, or picks
in 50 pairs, and that replaces pushes as the signal. The product has the same shape; only the
weights come from one reader instead of thousands, and `findings.md` says so.

## What ghost-story taught

- An absolute 1-10 judge could not tell real top posts from real low ones (AUC about 0.5).
  "Which of these two" picked the more-pushed post 91% of the time and the scarier one 93%.
- Popular is not the same as good: explained endings got the pushes, twist endings got 好毛.
- Readers reward concreteness: dialogue, a specific place, a scare that actually arrives.
- One blind reader preferred the restrained taste while the data preferred the direct one.
  Both shipped.
- The first title-repair pass deleted 1,181 translation posts' original-title lines; back up
  before any pass over the raw data, and make the rule require two markers, not one.

## Rules

- The product is fiction. If a genre pretends to be real experience (PTT `[經驗]`), the
  product skill must tell its user to post as `[創作]` with an AI note.
- No original text, titles, ids, urls or author names leave the data folder. The table is
  paraphrase on purpose. Check this before the PR, with a script, not by eye.
- No real people, businesses, temples or hospitals as targets in anything generated.
- Spend only after the owner has seen the estimate.
