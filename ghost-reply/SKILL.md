---
name: ghost-reply
description: Grow a ghost-story or horror brand account by replying under other people's posts. Finds today's ghost, paranormal and horror posts on Threads and Instagram through the user's Chrome, writes three replies per post in the brand's storyteller voice (a cold one-liner, a short story told as something heard, a question that invites answers), saves them to a dated file for the user to pick from, then posts the picked replies as the brand account only after the user's go, and records the links and the next day's numbers. Use whenever the user asks to reply to others, do the daily replies, 去別人底下回, 回覆別人的貼文, 互動, 留言, engagement, 養帳號, find posts to comment on, draft replies, run the 5 pm replies, or asks how to get the first followers with no budget, even if they do not name Threads or IG. Not for posting the brand's own stories (social-post), answering comments under the brand's own posts unless asked, profile changes (social-profile), or writing stories (ghost-story).
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

- **Nothing is posted without the user's pick.** A reply is a public message sent as the brand. Send the drafts,
  wait for the user's choice for each post (they often answer in one line, like `AAACC` for posts 1 to 5, or with
  their own wording), then post exactly that. A pick covers that reply on that post only.
- **Check the signed-in account** before typing anything: the sidebar avatar or name must be the brand's. If it is
  the user's personal account, stop and say so.
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
- **One reply per post**, never the same line twice, five to ten posts a day at most. Many identical-looking
  replies in a short time is what platforms flag as automation.

## Steps

### 1. Find posts

Load the Chrome tools in one ToolSearch call (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate,
computer, find, get_page_text, read_page, browser_batch), call tabs_context_mcp, and work in one new tab.

`references/search.md` has the search URLs and which keywords return real paranormal posts and which return noise.
Aim for five to seven posts that:

- are from today (Threads: hours, not days) or, on Instagram, are still collecting comments;
- have readers (hundreds of views or likes, dozens of replies), because a reply is only as visible as its post;
- invite answers (a question, a "have you ever", a list to pick from) or tell a story a reply can lean on.

Mix sources: two or three from keyword search, the rest from the fixed list of accounts the user approved (kept at
the bottom of the latest engagement file). Add any good account found today to the candidates there.

For each post, open it and keep the URL of **the post itself**: on a thread, use the timestamp link of the top post.
A search hit can be the author's own follow-up in the thread (a source link, "續👇"), and a reply posted there lands
under that follow-up instead of the story.

### 2. Draft three replies per post

Read the post and the top replies first, so the reply adds something instead of repeating what is there.

- **A　冷句** — one line in the storyteller ghost's voice: quiet, short, no exclamation marks, no emoji, a turn at
  the end. It works by taking something in the post one step further.
- **B　微型故事** — two or three sentences of a story told as heard, ending on the unsettling detail. It works when
  the post is itself a story or asks for stories.
- **C　接話** — a question that people want to answer under the post, ideally one with a small chill in it. It
  works on question posts and on busy threads where replies get replies.

`references/examples.md` has the first day's posts and replies, and which ones the user picked.

### 3. Write the day's file and send it

Run `py -X utf8 "<skill dir>/scripts/log.py" new <engagement folder>` for today's file with the sections, then fill
it: for each post, the platform, author, age and reach, the URL, two lines on what the post says, and the three
replies. Send it with SendUserFile, and also list the posts and replies in the message so the user can pick from a
phone. Say which one you would pick for each and why in a few words, then wait.

### 4. Post the picks

After the user's choice:

- **Threads**: on the post page, click the inline box "Reply to <author>...", type the reply, press the round
  "Reply" button beside it. Confirm on `https://www.threads.com/@<brand>/replies` that it is there, and copy its
  timestamp link.
- **Instagram**: on the post page, click "Add a comment…", type, press "Post". Reload and `find` the comment text
  under the brand's name.

Post one at a time and confirm each before the next. Close the tab at the end.

### 5. Record

Fill the result table of the day's file: the style picked, the time, the link. The next day, before finding new
posts, open yesterday's replies and fill the likes and replies after 24 hours, and the account's follower change.
`py -X utf8 "<skill dir>/scripts/log.py" summary <engagement folder>` totals picks and results by style across
days; once a week, tell the user which style and which kind of post brought the most likes and follows, and lean
the drafts that way.

## Daily schedule

The user may want this every day at a fixed time (鬼唱詩: 17:00). A scheduled run does steps 1 to 3 and sends the
file; posting waits for the user's answer in the conversation. Never post from a scheduled run without it.
