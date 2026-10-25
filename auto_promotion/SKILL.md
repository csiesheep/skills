---
name: auto_promotion
description: The scheduled self-running promotion of csiesheep's brands — 小羊遊戲間 / csiesheep.games (生在中國 Reels, share cards, game replies for 生在中國, 蓋牌投票箱, 天地會) and 鬼唱詩 / gui.chang.shi (ghost stories with comic and Reel, replies) — where a producer task makes content around the clock into queues and posting tasks post it at fixed Taiwan times, every run writing its progress to the Obsidian log. Use when a scheduled task points here, when the user asks what the automation is doing, what is queued, why something did not post, to change the schedule, the queue sizes or the posting times, or to read or fix the progress log (自動推廣、排程、存貨、待發、進度紀錄), even if they only name one brand.
---

# auto_promotion

Since 2026-10-25 (owner: 「可以用 24 小時來產生，但定時 post」, then 「執行」): making and posting are separate.

```
producer (no Chrome, any hour)  →  queues (待發)  →  posting tasks (Chrome, fixed Taiwan times)
```

## Queues and targets

| Content | Queue (rows marked 待發) | Target | Make / post steps |
|---|---|---|---|
| 生在中國 Reel | `Pictures/csiesheep_games/reels/china_life/ideas.md` | 2 | references/china_reel_make.md / china_reel_post.md |
| 鬼唱詩 story (story + comic + Reel) | `Pictures/gui_chang_shi/ideas.md` | 2 | references/ghost_make.md / ghost_post.md |
| Post (brand-post skill; 熱門遊戲介紹 + 開發日記) | `obsidian/Projects/auto promotion/posts/<#>.md` (status 待發) | 4 + 4 | brand-post SKILL.md / references/post_publish.md |
| 生在中國 share card | `Pictures/csiesheep_games/threads_posts/cards/log.md` | 2 | references/cards_make.md / cards_post.md |

The producer (task `promo-producer`, every 2 hours) makes ONE thing per run, in this order: cards if fewer than 2 待發, a 生在中國 Reel first if none is ready,
(minutes), then one post if popular or devnote has fewer than 4, else a 生在中國 Reel if fewer than 2 (about 2 h), else a 鬼唱詩 story if fewer than 2 (about 10 h). A lock
file `C:/Users/sheep/Pictures/auto_promotion/producer.lock` (start time inside) keeps one producer run at a time, which
is also the GPU lock; a lock older than 14 hours is stale. No quiet hours (owner: 「不用設不製作時段」).

## Fixed posting times (Taiwan time; Chrome has one user at a time)

| Taiwan | Task | Account |
|---|---|---|
| 05:00–06:25 | promo-post-ghost (story) | gui.chang.shi |
| 06:30–07:25 search, 07:30–07:55 post | games-replies-morning-2 | csiesheep.games |
| 08:00–08:28 | promo-post-popular (熱門遊戲介紹 → Threads, IG, FB) | csiesheep.games |
| 09:00–09:50 search (+ leftover story platforms) | ghost-reply lunch | gui.chang.shi |
| 10:00–10:55 search | games-replies-lunch-2 | csiesheep.games |
| 11:30–11:58 | promo-post-devnote-1130 (開發日記 → Threads, IG, FB) | csiesheep.games |
| 12:00–13:00 post | games-replies-lunch-2 | csiesheep.games |
| 13:00–13:30 post | ghost-reply lunch (ghost-reply-post-1300/-1320) | gui.chang.shi |
| 13:30–15:25 | promo-threads-1330 (reply to comments with cards, follower counts) | csiesheep.games |
| 15:30–16:20 search (+ leftovers) | ghost-reply evening | gui.chang.shi |
| 16:30–17:25 search | games-replies-evening-2 | csiesheep.games |
| 17:30–17:55 | promo-post-cards | csiesheep.games |
| 18:30–19:25 | promo-post-china-reel | csiesheep.games |
| 19:30–19:55 post | games-replies-evening-2 | csiesheep.games |
| 20:00–20:55 | promo-post-popular (熱門遊戲介紹) | csiesheep.games |
| 21:00–21:15 | promo-threads-2100 (Mon/Wed/Fri birthday call, Tue/Thu/Sat data fact) | csiesheep.games |
| 21:20–21:57 | promo-post-devnote-2120 (開發日記) | csiesheep.games |
| 22:00–23:15 post | ghost-reply evening (ghost-reply-post-2200…2309) | gui.chang.shi |
| 23:20–01:00 | promo-post-ghost (story) | gui.chang.shi |

An empty queue means the slot is skipped and logged, never filled by rushing.

**Time gates.** The scheduler runs on this computer's clock (US Pacific, which changes on the first Sunday of
November) while the schedule is Taiwan time, so every task fires at both Pacific hours that can match its Taiwan slot
and its first step checks Taiwan time and quits outside the slot. Get Taiwan time with
`py -c "import datetime as d;print(d.datetime.now(d.timezone(d.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M'))"`.

## Progress log

Every task, after passing its time gate, writes progress lines with
`py -X utf8 ~/.claude/skills/auto_promotion/scripts/progress.py <task id> <開始|進度|完成|發文|跳過|失敗|警告> "<text>" [--link URL]`
to `C:/Users/sheep/code/obsidian/Projects/auto promotion/<Taiwan date>.md`: one 開始 line, a 進度 line at each big
step, one 發文 line per post with its link, and one 完成 / 跳過 / 失敗 line at the end with the reason. Runs that quit
at the time gate write nothing. Never put passwords, tokens or other people's private data in the log.

## Rules that hold everywhere

Check the handle on the page before every post; switch accounts only by the no-password routes in
~/.claude/skills/game-promote/references/accounts.md; put Instagram, Threads and Facebook back as found; never type a
password; never click a button that opens the operating system's file picker; stop posting on a platform at the first
warning, removal, action block or rate limit, and log it as 警告.

## Threads growth (owner, 2026-10-25)

Game promotion on Threads was cut: game replies 3 a day on Threads and 3 on Instagram (1 per block each); one share card a day.
Own Threads posts carry no link in the main post; the link goes in our first self-reply. promo-threads-2100 posts a birthday call
(Mon/Wed/Fri) or an engine data fact (Tue/Thu/Sat); promo-threads-1330 answers comments, gives every birthday commenter their own card,
and records the follower counts.
