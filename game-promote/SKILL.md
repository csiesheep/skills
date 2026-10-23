---
name: game-promote
description: Promote one of csiesheep's web games (games.csiesheep.com — 生在中國 china_life, 蓋牌投票箱 covervote, 天地會 tiandihui, or any game added to references/games.json) by replying under other people's Threads and Instagram posts as the brand account csiesheep.games. Searches Chinese (Taiwan) posts whose topic the game fits, reads each whole post, drafts one reply per post that picks up a detail of the post and recommends the game with its link, shows the user the list with links and notes, and after the user picks, posts each approved reply at a good time (lunch or evening hours, 20+ minutes apart, at most three per platform per day) — the first now if it is in a window, the rest through one-time scheduled tasks — switching Chrome to csiesheep.games and back each time, then records the links and the next day's numbers. Use whenever the user asks to promote a game in other people's posts, 推廣 <game>, 找文章回覆推薦我們的遊戲, 去 Threads/IG 找人推 china_life / covervote / 天地會, reply to posts about a game's topic, or schedule those replies, even if they only name the game. Not for the brand's own posts (captions, reels), the ghost-story brand (ghost-reply), or profile changes (social-profile).
---

# Game promote

The games have no ad budget and the brand account has almost no followers, so its posts reach nobody. A reply
under a post whose readers already care about the game's topic reaches them: people talking about 科舉 are the
readers for 生在中國, people stuck arguing politics with their parents are the readers for 蓋牌投票箱. This skill
finds those posts, writes a reply that is useful there, and posts it slowly enough that Threads and Instagram do
not treat the account as spam.

Everything about the games (link, what a reply may claim, which posts fit, keywords, what to skip) is in
`references/games.json`. Each day's work goes in `<brand engagement folder>/<YYYY-MM-DD>.md` (from games.json:
`C:/Users/sheep/Pictures/csiesheep_games/engagement`), one section per game.

## Rules

- **The user approves every reply before it goes out.** Claude drafts and the user picks; post only the picked
  ones, in the user's wording if they changed it. Approval in one conversation does not carry to the next day's list.
- **Post as csiesheep.games and put Chrome back.** Read which account Instagram and Threads are on before
  touching anything, switch with `references/accounts.md`, check the handle on the page right before typing, and
  leave both as found. Never type a password.
- **Chinese (Taiwan) posts only** (owner, 2026-10-22). No English, Cantonese or Simplified-Chinese threads.
- **One reply per post, one link per reply, never the same text twice.** The reply has to be worth reading
  without the link: answer the post, use one concrete detail from it (a name, a line, a situation), then offer
  the game as the thing that fits that detail. If the reply would still make sense under a different post,
  rewrite it. Claims about a game come only from its `facts`.
- **Pace.** At most three replies per platform per day in the first weeks, at least 20 minutes apart on one
  platform, only in reading hours (12:00–13:30 and 19:30–23:00 Taiwan time). Threads and Instagram count
  separately; the count is for the brand, across all games. On 2026-10-19 the sister brand's fourth reply in
  three minutes was removed as spam, and a link makes a reply look more like spam, not less.
- **Skip** each game's `skip` list and posts about real death, illness or trauma. Under a post already past about
  100 replies a new account's reply sinks, so do not reply under the main post; look instead for a spot many read
  but few have answered — the author's pinned update, or a top reply (dozens of likes, few replies) whose point the
  game fits — and reply there. If there is none, skip the post. The sister brand learned this on 2026-10-19/20:
  replies under posts with 300–400 replies got nothing, while a reply that picked up what the top comments were
  already saying got 9 likes and a reply. For covervote, the reply stays neutral (games.json `neutral`); when the
  post itself is partisan, say so in the list so the user decides whether the brand should appear there.

## Steps

### 1. Pick the game and open the day's file

The user names the game (china_life, covervote, tiandihui, or a title). If it is not in games.json, read the game's
page and README and add an entry with the user before searching: url, pitch, facts, fits, keywords, skip, angles.
Then `py -X utf8 "<skill dir>/scripts/plan.py" new <engagement folder> <game>`.

### 2. Find posts

Load the Chrome tools in one ToolSearch call (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate,
computer, find, get_page_text, javascript_tool, browser_batch). Read-only searching does not need the brand
account; any signed-in account works.

Search the game's keywords on the platform(s) the user named (both if not named), with `references/search.md`
(URLs, the one-call extractor for Threads, the og:description reader for Instagram, the 429 limit). Aim for four to
six candidates: today or this week, readers still coming in, few enough replies to be seen, and a topic the game
answers. Open each candidate and read the **whole** post and its top replies; the search line is cut short and once
hid the part that mattered. Keep the URL of the post itself (the top post's timestamp link, not a follow-up in the
thread). Fill the 候選 table.

If a platform has nothing that fits (Instagram election keywords on 2026-10-22: one usable post out of five
searches), say so; never stretch a reply onto a post that does not fit.

### 3. Draft and show

One reply per post, Taiwanese Mandarin, one to three short sentences, then `👉 <url>` (Instagram links are not
clickable, so there write the bare `games.csiesheep.com/<game>`). Pick the angle from games.json that matches the
post. Use the first-person plural for the maker (「我們做了一個…」): it is honest that the brand made it.

Write two drafts per post: the recommended one and one with a different angle (or a different spot: the main
post versus a top reply), so the user has a real choice and the results show which angles work. Read the top
replies first and, where they share a joke or a complaint, let the reply pick it up: that is what readers of the
replies like. Write the drafts into the day file and show the user a table (platform, linked post, what it says in
one line, age and reach, any note), then each draft in full, the recommended one first with one line on why. Say
how many each platform can still take today and which you would post today versus tomorrow. Ask which to post.

### 4. Post at a good time

For the approved ones, run `py -X utf8 "<skill dir>/scripts/plan.py" slots <engagement folder> threads ig …
--avoid C:/Users/sheep/Pictures/gui_chang_shi/engagement` (one platform word per reply, in the order to post). It
returns a time for each, already respecting the day's cap, the gap and the windows, rolling the rest to the next
day, and keeping 10 minutes clear of the ghost brand's posted or scheduled replies: both brands switch the same
Instagram account in the same Chrome, and two tasks switching at once would post as the wrong brand.

- A slot within the next few minutes: post it now (below).
- Later slots: one `create_scheduled_task` per reply with `fireAt` at that time. The prompt must be self-contained:
  the post URL, the exact approved text, the platform, that it posts as csiesheep.games with the switch procedure
  in `~/.claude/skills/game-promote/references/accounts.md`, that it must leave Chrome's accounts as it found
  them, that it must stop without posting if the handle check fails, the post is gone, or the brand already
  replied there, and that it writes the outcome into the day file's 結果 table. Tell the user the times, and that a
  task runs only while the Claude app is open (a missed one runs at next launch, which may land outside the window:
  the task should then post only if the current time is inside a window, else reschedule itself for the next one).
- Add each reply to the 結果 table as 排定 with its time.

Posting itself:

- **Threads**: on the post page, click the inline box "Reply to <author>…", type, check the text in the box,
  press the round arrow button. Confirm with `a[href^="/@csiesheep.games/post/"]` on the page, and keep that link.
- **Instagram**: `find` "Add a comment textarea", click, type, check `document.querySelector('textarea').value`,
  `find` "Post button for comment" and press it. Confirm the comment shows under csiesheep.games.

Change the row to 已發 with the time and link. If a platform removes a reply or warns the account, stop all
scheduled replies on that platform (`update_scheduled_task` to disable), write the notice into the day file, and
tell the user; do not appeal or repost without them.

### 5. Report and follow up

Report a short table: what was posted where (links), what is scheduled when, what was skipped and why, and the
accounts Chrome was left on. The next time the skill runs, first open yesterday's replies and fill 24h likes and
replies, and note which angles and kinds of post did better; lean the drafts that way.
