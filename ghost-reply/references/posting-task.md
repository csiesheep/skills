# 鬼唱詩 reply runs: find and reply in the same run

> **Two Chrome profiles since 2026-11-07** (owner 「好，用兩個 Chrome 的方案」): the 「csiesheep.games」 Chrome (deviceId ad2977e1-4f4e-4d58-9611-3f06aafa85c0) stays signed in as csiesheep.games on Instagram and Threads; the 「鬼唱詩」 Chrome (deviceId 79a72d3b-ce4f-4444-a4e0-6c5cbfdda6f9) stays signed in as gui.chang.shi on Instagram and Threads, with YouTube 鬼唱詩 and Pinterest guichangshi. Every run picks its brand's browser with select_browser and never switches Instagram or Threads accounts or logs out; the switching steps below are history. Facebook still goes Page → back to 傅道揚 inside that Chrome. Why: switching two IG accounts in one Chrome several times a day made Instagram log out and ask for a password about ten times between 10/30 and 11/05.


Used by the seven fixed daily reply runs of 鬼唱詩 (handle gui.chang.shi on Instagram and Threads):
ghost-reply-post-1300, -1320 (lunch) and -2200, -2218, -2236, -2253, -2309 (evening).

Owner 2026-11-01 (「好，7 項全做」, schedule items 2, 3, 6): the runs no longer post rows chosen hours earlier by
separate search runs (ghost-reply-daily-1700-bypass at 09:00 and ghost-reply-daily-0500 at 15:30 are disabled). Each
run finds fresh posts itself and replies on the spot, because a reply under a post from the last few hours is read;
one under a post from this morning mostly is not. Each task's prompt gives its start window, its last posting minute,
whether it also does 找故事 and whether it fills yesterday's numbers.

## 0. Before Chrome

- Taiwan time: `py -c "import datetime as d;print(d.datetime.now(d.timezone(d.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M'))"`.
  Outside the start window: stop at once, reply 「不在排程時段，略過」, no log line. Post nothing after the last
  posting minute (the next run takes Chrome then).
- Day file: C:/Users/sheep/Pictures/gui_chang_shi/engagement/<Taiwan date>.md. If missing, create it:
  `py -X utf8 C:/Users/sheep/.claude/skills/ghost-reply/scripts/log.py new C:/Users/sheep/Pictures/gui_chang_shi/engagement`.
  Count today's 已發 rows per platform: ordinary replies (用哪個 not 找故事) at most 15 a day on Instagram and 30 on Threads (owner 2026-11-07: 「Threads 從每天 14 則提高到 30 則，IG 從 7 則提高到 15 則」; was 7 / 14), 找故事 at
  most 4. Number new sections and rows after the highest number already in the file.
- Read C:/Users/sheep/.claude/skills/ghost-reply/SKILL.md (reply styles, what to skip) and its references/search.md
  (how to find posts, the 429 limit), and C:/Users/sheep/.claude/skills/game-promote/references/accounts.md
  (history only: since 2026-11-07 runs never switch accounts, see the note at the top).

## 1. Chrome and the account

Load the mcp__claude-in-chrome__ tools in one ToolSearch call (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp,
navigate, computer, find, get_page_text, javascript_tool, read_page, browser_batch) and work in one new tab. First select the 鬼唱詩 Chrome (select_browser, deviceId in the prompt). Check that Instagram (sidebar link /<handle>/) and Threads (first a[href^="/@"] on threads.com) are on
gui.chang.shi. If either is not, do not switch: post nothing on that platform, mark it 未發：帳號不對 and email the owner (the stuck rule in the prompt).

## 2a. Comments under our own posts (ghost-reply-post-1320 and -2200 only; owner 2026-11-01 「拉高 fb, IG, threads」)

Before the ordinary replies: open gui.chang.shi's posts of the last 3 days on Instagram and Threads (the -2200 run also the
Facebook Page 鬼唱詩, acting as the Page, then switch back to the personal profile) and answer every comment we have not
answered yet, at most 8 per run: short, in the 「我們」 voice, pick up what they said, no link, no emoji; a 「我也遇過」
comment gets a question back (「後來呢？」) and, if it is a story, note it in the day file under 「讀者的故事」 for the
owner. Skip spam, insults and anything about real deaths. Record each as a row with 用哪個 = 自己留言 (it does not count
toward the caps). At most 6 minutes; then go on to step 2.

## 2. Ordinary replies: the counts in the prompt (2026-11-07: Threads 3 per run, Instagram 0–2)

For each platform (Instagram first), unless today's ordinary cap is reached, post the number of replies the prompt gives for that platform (a prompt without numbers: Instagram 1, Threads 3). Each reply goes under a different post by a different author, at least 5 minutes after the previous reply on the same platform; Instagram and Threads may run in turn. If time runs short before the last posting minute, post fewer and note how many were left:
- Find: Threads keyword search with filter=recent (鬼故事, 靈異, 怪談, 撞鬼, 鬼壓床, 阿飄 …), posts from the last few
  hours; Instagram the newest posts of the fixed-list accounts at the bottom of the latest engagement files, then a
  keyword grid. At most about 10 page reads per platform, 10 s apart. Read the whole post and its top replies.
- Skip real deaths, accidents, crimes, politics, trauma, ads, metaphor uses of 鬼故事, restricted comments, and posts
  where gui.chang.shi already commented (search the last 14 day files for the URL too).
- Write A/B/C, pick the single best yourself: it picks up a concrete detail of the post or the joke its top comments
  are making, fiction told as heard, no links, no emoji, never a line used before (check earlier day files).
- Write a section 「## N. <平台>｜<作者> <主題>｜<多久前>，<讚、回覆>」 with the URL, 原文重點, A/B/C with the chosen one
  marked （選這個）, and a result row.
- Before posting, open the author's profile once: if it already shows 「Follow back」／「追蹤回去」 (they follow us), write 原本就追蹤 in the row's 帶來追蹤 cell now.
- Post: check the handle is gui.chang.shi right before typing, type, check the box text equals the chosen line, post,
  reload and confirm it shows under gui.chang.shi, get the link (Threads: https://www.threads.com/@gui.chang.shi/replies).
  Never type a password; a password or login page means stop that platform (and the email rule in the prompt).
- Mark the row 已發 with the Taiwan time and link, or 不發／未發：<reason>.

## 3. 找故事 (only the runs whose prompt says so)

After the ordinary replies, at most one reply per platform under someone asking for ghost stories, per
C:/Users/sheep/.claude/skills/ghost-reply/references/seekers.md (who counts, where to look, the reply, the mention
list). Threads first. Start a platform only with at least 5 minutes before the last posting minute; none good: skip it.
Gap: 3 minutes after this platform's previous reply.

## 4. Yesterday's numbers (only the run whose prompt says so: ghost-reply-post-1300)

After posting, if time remains before the last posting minute: open the previous Taiwan day's file and fill 24-hour
likes and replies of every 已發 row (Threads: https://www.threads.com/@gui.chang.shi/replies; Instagram: the post page).
What is not reached stays empty; write 「24h 數字補到第 N 列」 in today's file.
Then 帶來追蹤 for the same rows (owner 2026-11-01, item 7: 「回覆要看有沒有帶來追蹤」): for every 已發 row of the
previous day whose 帶來追蹤 is empty (一般 and 找故事 alike, not 自己留言), open the author's profile (for 找故事 the
seeker): 「Follow back」／「追蹤回去」 shown → 是, otherwise 否. Leave 原本就追蹤 as it is. Not reached → empty; the
23:20 story run fills the rest after its posting (promo-post-ghost-night step 2c).

## 4b. Profile: pins and bio (done by promo-post-ghost-night after its posting, step 2c; owner 2026-11-01, item 6)

- **Monday night run** (the 23:20 run on a Monday): read C:/Users/sheep/Pictures/gui_chang_shi/brand/pinned.json (written by the weekly review that morning:
  three stories with their Instagram, Threads and Facebook links, best first). If it differs from what is pinned now,
  pin those three, best one last so it shows first: Instagram post ⋯ → 「Pin to your profile」／「釘選到你的個人檔案」
  (Reel or carousel, whichever pinned.json names); Threads post ⋯ → 「Pin to profile」; Facebook Page post ⋯ →
  「置頂貼文」 acting as the Page, then switch back. Unpin what drops out. A platform whose web page has no pin option:
  skip it and write 「<平台> 網頁不能置頂」 in the day file once. Record 「置頂：第 a、b、c 首」 in the day file.
- **Bio, once**: if C:/Users/sheep/Pictures/gui_chang_shi/brand/profile_2026-11.done does not exist, set the bio of
  Instagram gui.chang.shi, Threads gui.chang.shi and the Facebook Page 鬼唱詩 (its 簡介) to exactly these four lines,
  following the social-profile skill (check the account first, type line by line, compare the counter, save, reload),
  and change nothing else (not the name, photo or links):
  鬼唱詩｜台灣怪談漫畫
  每天兩首台灣鬼故事，漫畫＋影片
  05:00 長篇・23:20 短篇
  AI 輔助創作｜故事純屬虛構
  Then create that .done file with the date and what changed. Not finished in this run: the next night run continues.
- Both after the story is posted, before 01:00; the story comes first.

## 5. Warnings

If a platform removes a reply or warns the account: stop posting on that platform today, write the notice in the day
file, report; do not appeal or repost.

## 6. End

Close your tabs. Add one line to the day file: 「<task label>：IG <x>（找故事 <y>）、Threads <x>（找故事 <y>）、自己留言 <z>」.
Progress log (mandatory, owner 2026-10-25):
`py -X utf8 ~/.claude/skills/auto_promotion/scripts/progress.py <task id> <發文|跳過|失敗|警告|完成> "<text>" [--link URL]`:
one 發文 per reply (platform, 找故事 or not, the post it answers) with --link to our reply, and 完成 with the counts
(or 跳過 「沒有合適的貼文」, 警告/失敗 with the reason).
