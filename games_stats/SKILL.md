---
name: games_stats
description: Check how csiesheep's web games are doing today versus yesterday — 生在中國 (china_life) and 蓋牌投票箱 (covervote) on games.csiesheep.com — games finished, players, page visitors, games per player and where visitors came from (Threads, Instagram, Facebook, LINE in-app browsers vs. plain browsers), in Taiwan days, from the games' Cloudflare D1 databases and Cloudflare zone analytics, and optionally write the day's report with an hourly log into the Obsidian vault. Use whenever the user asks how many games were played, how many people played, 今天玩了幾局, 多少人玩, 玩家數, traffic, 數據, stats, 從哪裡來, referrers, 流量來源, today vs yesterday, or wants a games report, for china_life, covervote or "both games", even if they name only one game. Not for the in-game 眾生簿 statistics page, for social media insights (Threads/IG/FB), or for promotion.
---

# games_stats

One script does the work: `scripts/games_stats.py` (Python 3, standard library; uses `npx wrangler` for D1).

```bash
py -X utf8 "<skill dir>/scripts/games_stats.py"                 # report to stdout
py -X utf8 "<skill dir>/scripts/games_stats.py" --report "C:/Users/sheep/code/obsidian/Projects/games stats/daily report"
py -X utf8 "<skill dir>/scripts/games_stats.py" --json          # raw numbers
```

`--report <folder>` writes `<folder>/<Taiwan date>.md`: the full report on top and a `## 每小時紀錄` table that
keeps one row per run (today's running totals at that time; a second run in the same minute replaces its row).
`--yesterday` does the same for the previous Taiwan day with its full 24 hours (log row `24:00`); run it
once right after Taiwan midnight so yesterday's file ends with whole-day numbers. It takes about 30 seconds.

## What the numbers are

Days are **Taiwan days** (UTC+8): the players are in Taiwan, while this computer is on US Pacific time. The report
compares today so far with yesterday up to the same time, and shows yesterday's full day.

| | china_life | covervote |
|---|---|---|
| games | rows in D1 `china_life_stats.lives` (one per finished life; identical replays dedupe) | Cloudflare count of `POST /covervote/api/play` answered < 400 (includes the owner's `internal=1` test plays; the D1 `counters` total excludes them) |
| players | distinct client IPs with a finished game (`POST /china_life/api/life`) | same, on `/covervote/api/play` |
| visitors | distinct client IPs that requested `/china_life/` | `/covervote/` |
| total | `MAX(rowid)` of `lives` | `SUM(n)` of `counters` keys `p:<race>:n` |

| visitors by source | the app whose in-app browser opened the page, from the user-agent (`SOURCES` in the script) | same |

**Sources.** The Free plan has no referrer field (`clientRefererHost` is refused), so the script reads each
visitor's user-agent: Threads (`Barcelona`), Instagram, Facebook (`FBAN`/`FBAV`/`FB_IAB`), Messenger, LINE, TikTok,
X, Discord name themselves in their in-app browsers. Everything else, including Google search, a typed address and
links from other websites, is "一般瀏覽器"; say so when reporting. Bots and link-preview crawlers
(`facebookexternalhit` and the like) are dropped from visitors. A player's source is the app that address used to
open the page. To get real referrers (search engines, websites), the owner would have to turn on Cloudflare Web
Analytics for the site or have the games report `document.referrer`; both are changes the owner decides.

Neither game stores a user id, IP or cookie (privacy is a product rule in both repos), so **players are an estimate**:
distinct IPs, IPv6 grouped by /64. A household on one Wi-Fi counts once; a phone that changes address counts twice.
Day-to-day comparison is still sound. Never write IP addresses into a report; the script prints only counts and
the top five per-player game counts.

## Access

- D1 goes through `npx wrangler d1 execute <db> --remote` run in the game's repo (`~/code/china_life`,
  `~/code/covervote`). The wrangler OAuth login (csiegoat@gmail.com account) must be valid; wrangler refreshes it.
  A one-off `7403 not authorized` happens; the script retries three times.
- Cloudflare analytics uses the same OAuth token (read from wrangler's `default.toml`) against the GraphQL API,
  zone `csiesheep.com` (Free plan): `httpRequestsAdaptiveGroups` grouped by `clientIP` (and `userAgent` for the page), all in **one** request per run: a burst of single queries ran out the zone's analytics budget ("try again after 5 minutes"), and the script then waits 30 s and 5.5 min before giving up. The Free plan has no
  `clientRequestQuery`, so `internal=1` cannot be filtered out, and keeps only a few days, so only today and
  yesterday are reliable. If Cloudflare samples (sampleInterval > 1), the report says so.
- If the token has expired and wrangler cannot refresh it, the script fails with "run `npx wrangler login`": tell
  the owner, do not try to log in.

## Adding a game

Add an entry to `GAMES` in the script: its D1 database and repo, the POST path that means "finished a game", the
page path, and either `games_from: "d1"` (write the per-day SQL) or `"cf"` (count the POSTs) with a `total_sql`.

## Reporting to the owner

Lead with the comparison in one or two sentences (games up/down, players up/down, by how much), then the table.
Point out anything unusual, like a few players making most of the games (the top-five line) or zero games
(a broken endpoint). Keep the caveat about players being an estimate to one line.
