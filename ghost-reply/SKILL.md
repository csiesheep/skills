---
name: ghost-reply
description: Grow a ghost-story or horror brand account by replying under other people's posts. Finds today's ghost, paranormal and horror posts on Threads and Instagram through the user's Chrome, writes three replies per post in the brand's storyteller voice (a cold one-liner, a short story told as something heard, a question that invites answers), saves them to a dated file and gives the user each post's link with the recommended reply, so the user posts them from their own phone (the owner's choice, 2026-10-20: Claude does not post replies), and records the links and the next day's numbers. Use whenever the user asks to reply to others, do the daily replies, 去別人底下回, 回覆別人的貼文, 互動, 留言, engagement, 養帳號, find posts to comment on, draft replies, run the 5 pm replies, or asks how to get the first followers with no budget, even if they do not name Threads or IG. Not for posting the brand's own stories (social-post), answering comments under the brand's own posts unless asked, profile changes (social-profile), or writing stories (ghost-story).
---

# Ghost reply

A new account with no followers is shown to almost nobody, however good its posts are. A good reply under a
busy post is shown to that post's readers; some of them like it, tap the avatar, and follow. This skill does that
work every day: find the right posts, write replies worth liking, let the user pick, post them, and keep score so
the styles that work get used more.

Brand words, colours and the account handle come from the brand file the user keeps (for 鬼唱詩:
`C:/Users/sheep/Pictures/gui_chang_shi/brand/brand.json`, with the voice described in the Obsidian note
`Projects/ghost story/ghost story brand.md` 2.2). Each day's work goes in `engagement/<YYYY-MM-DD>.md` beside the
brand folder.

## What may and may not be done

- **The user posts the replies, not Claude.** On 2026-10-20 the owner stopped Claude half way through posting
  and decided: "show me the post link and recommended comment, then I will post them by myself". So this skill
  finds, drafts, recommends and records; it does not type into a reply box. Only if the user explicitly asks
  Claude to post a specific reply in that conversation does step 4's old procedure apply (kept below for that case).
- **Check the signed-in account** before typing anything: the sidebar profile link must be `/gui.chang.shi/`.
  Chrome is shared with the games brand (csiesheep.games, game-promote), which switches the same Instagram account:
  on 2026-10-23 Instagram was on csiesheep.games when ghost-reply came to post. Note which account Instagram and
  Threads are on before touching anything, switch with game-promote's `references/accounts.md` (no password, with
  gui.chang.shi as the brand), check the handle on the page right before typing, and put both back as found. If
  the switch would need a password, stop and tell the user.
- **Fiction stays fiction.** The brand labels its stories as fiction, so a reply never presents a ghost story as the
  brand's own real experience. Short stories are told as heard ("聽過一個……說", "老一輩說"), never "我那晚……".
- **Reply in the post's language.** An English post gets an English reply. Chrome may show Chinese posts translated
  into English ("Translated from Chinese"), so judge by the original: the post page's tab title holds the original
  text, or press "See original".
- **No links, no "come see my page".** The reply itself has to earn the tap on the avatar. Promotion in a reply
  reads as spam and gets hidden.
- **Skip** posts about real deaths, accidents, disasters or crimes, politics, someone venting about real trauma or
  illness, and posts that use 鬼故事 as a metaphor (職場鬼故事, 交友軟體鬼故事, 裝潢鬼故事): a ghost line under
  those is tone-deaf.
- **Space the replies out.** On 2026-10-19 four Threads replies posted within three minutes from a new account
  with no followers, and Threads removed the last one: "We don't allow people to take actions at high volume that
  might bother others", under its spam rules. So: at least 15 minutes between two replies on the same platform,
  three a day per platform in the first weeks (raise it slowly once the account has followers and no removals),
  never the same line twice, one reply per post. Threads and Instagram count separately.
- **Stay on the post's topic.** The removed reply was the generic one: a question that could sit under any ghost
  post ("大家聽過最毛的是哪種？"). A reply has to answer this post: pick up a concrete detail from it (a name, a
  place, an object, a line the author wrote, a top reply) and build on that. If a reply would still make sense
  pasted under a different post, rewrite it. Question-style replies (C) are the most at risk of reading as
  engagement bait; give them a detail from the post or drop them.

## Steps

### 1. Find posts

Load the Chrome tools in one ToolSearch call (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate,
computer, find, get_page_text, read_page, browser_batch), call tabs_context_mcp, and work in one new tab.

`references/search.md` has the search URLs and which keywords return real paranormal posts and which return noise.
Aim for five to seven posts that:

- are from today (Threads: hours, not days) or, on Instagram, are still collecting comments;
- have readers (hundreds of views or likes, dozens of replies), because a reply is only as visible as its post;
- invite answers (a question, a "have you ever", a list to pick from) or tell a story a reply can lean on;
- **still have room near the top.** On 2026-10-19 every reply went under posts that already had 289 to 406
  replies; a new account's reply sank to the bottom and none got a like. Readers see the first screen of replies.
  Prefer a post 1 to 12 hours old whose likes are still climbing but whose replies are few (Threads under about
  100, Instagram 30 to 100), or, under a huge post, **a spot many people read but few have replied to**: the
  author's pinned update (chen.kenn's 673K-view post had a pinned update with 1 reply), or a top reply that tells
  its own story (taiwancasalin's 294-like story under a 46K-view thread had 4 replies). Reply there, not under the
  main post.

**Instagram first** (owner, 2026-10-20): unless asked otherwise, the day's list is Instagram posts, about ten
when the owner asks for a batch, ordered newest and least-commented first so they can post three a day.

Mix sources: two or three from keyword search, the rest from the fixed list of accounts the user approved (kept at
the bottom of the latest engagement file). Add any good account found today to the candidates there.

For each post, open it and keep the URL of **the post itself**: on a thread, use the timestamp link of the top post.
A search hit can be the author's own follow-up in the thread (a source link, "續👇"), and a reply posted there lands
under that follow-up instead of the story.

### 2. Draft three replies per post

Read the post and the top ten replies first, so the reply adds something instead of repeating what is there.
The aim is a like or a tap on the avatar, and both come from the people reading the replies, so:

- **Pick up the joke the replies are already making.** Under z.n_.studio's 「農路上的哥哥」 the top comments were
  all about the missing scary last page; a line that turns that into a chill fits the room better than one that
  only answers the post.
- **Give the author a reason to answer.** An author's reply lifts yours. A C-style question asks the author about a
  detail only they know (「洗衣機那時候是開著在轉嗎？」), never a general question for everyone.
- Short beats clever: one line people can read in passing.

- **A　冷句** — one line in the storyteller ghost's voice: quiet, short, no exclamation marks, no emoji, a turn at
  the end. It works by taking something in the post one step further.
Every reply, whatever the style, must refer to something specific in that post.

- **B　微型故事** — two or three sentences of a story told as heard, ending on the unsettling detail. It works when
  the post is itself a story or asks for stories.
- **C　接話** — a question that people want to answer under the post, ideally one with a small chill in it. It
  works on question posts and on busy threads where replies get replies.

`references/examples.md` has the first day's posts and replies, and which ones the user picked.

### 3. Write the day's file and send it

Run `py -X utf8 "<skill dir>/scripts/log.py" new <engagement folder>` for today's file with the sections, then fill
it: for each post, the platform, author, age and reach, the URL, two lines on what the post says, and the three
replies. Send it with SendUserFile, and also list the posts and replies in the message so the user can pick from a
phone. For each post the message gives, in this order: the link to open (the exact spot to reply: the author's
pinned update or a comment's own page when that is where the reply goes, and say so), the recommended reply as
plain text the user can copy in one press, then the two alternatives, and one line on why the recommended one.
Remind the user of the spacing (at least 15 minutes between two replies on one platform, three a day per platform)
and of the reading hours (12:00–13:30 and 19:30–23:00 Taiwan time, when a new reply is seen soonest), and ask them
to say which ones they posted so the results table can be filled. Name the day file by the Taiwan date (log.py's
default), since the audience and the games brand's files use it.

### 4. The user posts; Claude records

The user posts from their phone and says which ones went out (and any wording they changed). Fill the result
table from that; find each reply's link afterwards on `https://www.threads.com/@<brand>/replies` or under the
Instagram post. Only if the user asks Claude to post a reply itself in that conversation:

- **Threads**: on the post page, click the inline box "Reply to <author>...", type the reply, press the round
  "Reply" button beside it. Confirm on `https://www.threads.com/@<brand>/replies` that it is there, and copy its
  timestamp link.
- **Instagram**: on the post page, click "Add a comment…", type, press "Post". Reload and `find` the comment text
  under the brand's name.

Time them with game-promote's slot planner, which keeps the daily cap, the gap and the reading hours, and stays
clear of the games brand's replies from the same Chrome:

    py -X utf8 "<game-promote dir>/scripts/plan.py" slots <engagement folder> ig ig --gap 15 \
        --avoid C:/Users/sheep/Pictures/csiesheep_games/engagement

(one platform word per reply, in order). It reads the result table's 平台, 狀態 and 時間 columns, so first add each
approved reply there as 待發. A slot within the next few minutes: post it now. Each later slot: one
`create_scheduled_task` with `fireAt` at that time, and a self-contained prompt: the post URL (and the comment to
reply under), the exact approved text, that it posts as gui.chang.shi switching per game-promote's
`references/accounts.md` and puts Chrome's accounts back, that it stops without posting if the handle check fails,
the post is gone or the brand already replied there, and that it writes the outcome into the day file. One task per
reply: on 2026-10-21 a single scheduled run meant to post three replies 15 minutes apart posted the first, started
a background wait, and ended its turn, so the other two never went out. A task runs only while the Claude app is
open; one that fires late posts only if it is inside the reading hours and the gap still holds, else it
reschedules itself for the next slot.
Mark each row 排定 with its time, then 已發 with the time and link. Close the tab at the end.

If a platform removes a reply, open the notice ("We removed your comment" → "See why"), write the reason and the
reply into the day's file, and do not request a review or repost without the user's say. Post fewer and slower
for the next days.

### 5. Record

Fill the result table of the day's file: the account, the style picked, 狀態 (待發, 排定, 已發), the time, the
link. The next day, before finding new posts, open yesterday's replies and fill the likes and replies after 24
hours, and the account's follower change.
`py -X utf8 "<skill dir>/scripts/log.py" summary <engagement folder>` totals picks and results by style across
days; once a week, tell the user which style and which kind of post brought the most likes and follows, and lean
the drafts that way.

## Daily schedule

The user may want this every day at a fixed time (鬼唱詩: 17:00). A scheduled run does steps 1 to 3 and sends the
file with each post's link and recommended reply; the user posts them. A scheduled run never posts.
