---
name: ghost-post
description: Post one ghost story's finished, ready-to-post set on the user's own brand accounts through their signed-in Chrome — the Reel full on Instagram, YouTube Shorts, TikTok and the Facebook Page, the carousel on Instagram and the Page, the three-post Threads thread, the Pinterest pins, teasers as Instagram trial Reels — one post at a time with the user's yes on each, and record every link. It only checks and posts: always first it checks every platform (right account signed in, upload entry reachable), then checks the story folder for every ready-to-post file (number stamped, captions written, lengths and sizes right), and if anything is missing it stops and names the skill that makes it; it never makes or edits material itself. Use whenever the user wants to post, publish, 發文, 發第 N 首, 上架, put a story online, post to IG / Threads / YouTube / TikTok / FB / Pinterest, or check whether the accounts or a story are ready to post, even if they name only one platform. Not for numbering, stamping or writing captions (ghost-pack), writing stories (ghost-story), comics, carousels, pins or teasers (ghost-comic), the Reel full (ghost-reel), profiles (social-profile), or replying under others' posts (ghost-reply). Also posts the realistic videos 「鬼唱詩劇場｜第 N 部」 packed by ghost-pack-film (section "Films").
---

# Ghost post

**Since 2026-11-01 (owner 「取消tiktok」, 「拉高 fb, IG, threads」): no TikTok; the Facebook Page also gets the story as a text post (like Threads), and Instagram gets the trial version B when `reels/trial_B/` exists (auto_promotion references/ghost_post.md → "Which story").** The TikTok rows below are history.

**Since 2026-11-02 (owner: 審稿系統, 「跳過不發」): a story must be 已確認 on the review page https://monitor.csiesheep.com/ghost/review/ before any automatic posting.** The scheduled posting runs post only ideas.md rows that `C:/Users/sheep/code/monitor/tools/review_pull.py` turned into `待發` (the owner pressed 確認可發); a 待審 or 要修改 story is never posted, and no run confirms a story itself. Stories already 部分已發 before the gate finish as before. When the owner asks in chat to post a story by hand, check its status with `review_admin.py list` first and say so if it is not 已確認.

Takes a story whose files are ready and puts them on six platforms. It does not prepare anything: the owner
decided on 2026-10-20 that this skill only checks platforms, checks files and posts. Where it sits:

```
ghost-story, ghost-comic, ghost-reel   make the material, no number in it
ghost-pack                             numbers the story, stamps the covers, writes every platform's caption
ghost-post                             checks platforms and files, posts, records links   ← this skill
```

Written from the 鬼唱詩 account: first posts on Instagram, Threads and Pinterest (2026-10-18/19), then 第 2 首 on
2026-10-20, the first full set on all six platforms, posted one post at a time through Claude in Chrome. Every step
in `references/platforms.md` comes from those real posts.

The files it reads follow the folder contract in `C:/Users/sheep/Pictures/gui_chang_shi/README.md` (also in the
Obsidian note `Projects/ghost story/ghost story pipeline.md`). The parts this skill uses:

| File in `stories/<short name>/` | Posted to |
|---|---|
| `reels/full_v3_cinema/full_v3_cinema.mp4`, or for a long story `reels/full_v3_cinema_part1/…_part1.mp4` and `_part2` (the owner's choice, 2026-10-20: two short parts, not one long video; part 2 a day after part 1) | Instagram Reel, YouTube Shorts, TikTok, Facebook Page |
| `posts/ig/01.jpg … NN.jpg`, `posts/ig/caption.txt` (01.jpg stamped; `01_nonumber.jpg` is ghost-pack's backup, never posted) | Instagram carousel, Facebook Page |
| `posts/threads/hook.txt` + `attachment.txt`, `posts/ig/01..NN.jpg` + `posts/ig/caption.txt`, the Reel's 720p mp4 + the IG Reel caption | Threads, three separate posts (owner, 2026-10-23: 「Threads 故事，漫畫，reel 分別是3個貼文」): (1) the story: hook text with the full text as its text attachment; (2) the comic: the carousel caption with all pages; (3) the Reel: the IG Reel caption with the video. Each its own top-level post with the topic 鬼故事, no replies. `image.jpg` and `link.txt` are no longer posted |
| `posts/pinterest/00_cover.jpg`, `NN_page.jpg` (every page, the reveal included, since 2026-10-28), `pins.txt` (the story board, titles, the video pin) | Pinterest: the cover pin on the shared board, then the story's own board (whole comic + Reel) |
| `posts/cross_caption.txt` (`{ig_link}` filled after the Instagram post), or `cross_caption_part1.txt` / `_part2.txt` for the two parts: sections IG Reel, YouTube, TikTok, Facebook | the Reel's caption on every platform |
| `reels/teaser_A/`, `teaser_B/` | Instagram trial Reels (phone) |
| `README.md`, `brand/ledger.json` | links recorded here |

## What may and may not be done

- **One preview, one yes, then post all.** Posting is public and cannot be cleanly taken back, so nothing goes out
  before the owner has seen it. Since 第 5 首 (2026-10-23, 「以後先產生所有要發的東西給我看，確認後，然後自動發，不用再
  問我」) the owner sees every post of the story in one preview (every file, every platform's exact caption, Threads'
  three posts, the Pinterest pin) and one yes covers that whole set: post them all in order without asking again.
  The yes covers exactly what was previewed: a changed caption, a different file, or a post not in the preview needs
  a new yes. Stop and ask on anything unexpected (a wrong account, a sign-in page).
- **Never sign in, never merge accounts.** If a platform shows a login page, it is not ready; the user signs in.
  Do not add profiles to Meta's Accounts Center or link accounts to make cross-posting work: on 2026-10-20 the user
  chose to post on the Facebook Page as the Page instead, because Instagram's "share to Facebook" needs the owner's
  personal Facebook profile added to the brand's Meta account.
- **Check the account before every post**, on the page you post from: the brand's handle, "Edit profile" on its
  own profile, no "Follow" button.
- **Leave Chrome tidy.** Work in a new tab and close it. Instagram and Threads stay on gui.chang.shi at the end (brand blocks since 2026-11-01, game-promote accounts.md); the rest as below. YouTube: switch back to the account that was
  active. Facebook: switch back from the Page to the personal profile.
- **Fiction, labelled.** Every post carries the disclosure (`brand.json` → `disclosure`) and the site's AI label
  where it has one. No reveal panel in a cover, a Threads image or a teaser. Pinterest page pins are the exception
  (owner, 2026-10-28): the whole comic goes on the story's own board, the reveal page and those after it titled 「結局」.

## Steps

### 1. Check every platform (always first, read only)

Load the Chrome tools in one ToolSearch call (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate,
computer, find, get_page_text, read_page, browser_batch, file_upload), call tabs_context_mcp, open one new tab and
visit each platform. `references/platforms.md` → "Platform check" has the URL and what proves it is ready. Change
nothing in this step. Report a table:

| Platform | Ready? | How it will be posted |
|---|---|---|

and for each platform that is not ready, what the user has to do (sign in, switch an account in the app, decide a
way). Stop there for those platforms until the user has done it; the others can go ahead.

### 2. Check the files (read only)

`py -X utf8 "<skill dir>/scripts/check_story.py" <story folder> --number N` lists every ready-to-post file and what is
missing or wrong: the number not stamped, a caption missing, a Threads post over 500 characters, a pin not
1000 × 1500. An `{ig_link}` slot in the captions is ready, not missing (see below). The number comes from the ledger,
which ghost-pack keeps: `py -X utf8 "<ghost-pack skill dir>/scripts/ledger.py" --brand-file <brand.json> show` (the
ghost-pack folder sits next to this one); if the story has none, it has not been packed. Do not fix anything here.
Stop and tell the user what is missing and which skill makes it:

| Missing | Made by |
|---|---|
| Number, stamped carousel cover and Pinterest cover, any caption (IG, Threads first line, YouTube title and description, TikTok, Facebook, Pinterest titles) | ghost-pack |
| Threads hook or full-text attachment | ghost-story `post` |
| Carousel, Pinterest images, Threads image, teaser A/B | ghost-comic `export`, `export --pinterest`, `reel teaser` |
| Reel full | ghost-reel |

The one exception: the Instagram link that the other platforms' captions point to only exists after the Instagram
post. ghost-pack leaves an `{ig_link}` slot in `posts/cross_caption.txt` (YouTube, Facebook), `posts/threads/link.txt`
(the third Threads post) and the link line of `posts/pinterest/pins.txt`. After the Instagram carousel is up, put
its link into those slots in the text you post (and write it into the files, so the record shows what went out);
that is posting, not preparing.

### 3. Preview, ask

Before any preview, look at each file as a reader would: number heading and disclosure on everything, no `[經驗]`,
no real hospital, temple or shop named, no reveal panel where it should not be. If something is wrong, it goes back
to the skill that made it (step 2's table). Then send the files (SendUserFile; a file over 30 MB does not reach the phone, so send a
720p preview copy) and the exact captions of every post in one message, and ask once for the whole set. The
Instagram link only exists after the Instagram post: show the other captions with the `{ig_link}` slot, say it will
be filled with the carousel's link, and that counts as previewed.

### 4. Post (D is the posting day; the user's plan sets the time)

Instagram first, because every other platform links to it.

| Order | Platform | What | Notes |
|---|---|---|---|
| 1 | Instagram | Reel full, then the carousel | Web upload works for the Reel too: crop "Original", cover from `full_v3_cinema_cover.jpg`, sound on, AI label on; the carousel's link goes into every `{ig_link}` slot |
| 2 | YouTube Shorts | Reel full | Studio shows "Your channel 鬼唱詩"; title 「第 N 首｜title」; AI use "Yes"; not for kids; Public |
| 3 | TikTok | Reel full | Studio upload; AI-generated content on; decline "automatic content checks"; under review ~30 s before "Everyone" |
| 4 | Facebook Page | Reel full, then the carousel as a photo post | As the Page ("立即切換"); "新增 AI 標籤" on; switch back to the personal profile |
| 5 | Pinterest | The cover pin; then the story board (video, last page … page 1, the cover saved to it) always, after the other platforms; if the block ends first, README `- 待發：Pinterest 故事板` and the next 鬼唱詩 story run (05:00 / 23:20) finishes it | Link to the Instagram carousel; Mark as AI-Modified and AI-generated person; references/platforms.md → "Pinterest story board" |
| 6 | Threads | Three separate posts: story (hook + text attachment), comic (caption + pages), Reel (caption + video) | Media and a text attachment cannot share a post, which is why the story post has no picture |
| D+1, D+2 | Instagram trial Reels | Teaser A, B | From the user's phone; trial Reels are a toggle in the app |

Before every "Post", compare what the page holds with the file (`references/platforms.md`: the hash check on
Threads, the zoom on TikTok): on 第 3 首 TikTok's editor silently dropped half a line, and a wrong character
slipped into the 1,982-character Threads attachment; both were caught only by comparing.

Videos go up as `full_v3_cinema_preview720.mp4`: Claude in Chrome's `file_upload` takes 10 MB a call and the
1080p file is about 93 MB (`references/platforms.md` → "Upload size"). Captions are typed line by line, never pasted
from memory: read them from the files and check the posted text against them.

After each post: open it, confirm text, image or video and the AI label, copy the link.

### 5. Record

`py -X utf8 "<ghost-pack skill dir>/scripts/ledger.py" --brand-file <brand.json> posted N <platform> --url <link>` for every post, and the links in the story's `README.md`. Tell the
user the first hour of replies is theirs (ghost-reply can draft them). After 48 hours, put views, completion,
saves, shares and new followers into the brand's results table.

## Films: 鬼唱詩劇場｜第 N 部 (since 2026-11-10)

Realistic videos from ghost-film have their own numbers (`brand/film_ledger.json`, 「鬼唱詩劇場｜第 N 部」) and their own
folder, `posts/film/`, written by ghost-pack-film. Everything above holds (one preview and one yes for the whole set,
account checks, AI labels, Instagram first). What is different:

- **Gate.** Films are not on the review page. Post one only when the owner asks in chat, and check
  `README.md`'s status says 已包裝.
- **Files.** Run `py -X utf8 "<skill dir>/scripts/check_film.py" <story folder> --number N`. It checks the film ledger, the
  covers, every caption, and that each video in `posts/film/files.txt` has a 720p upload copy within 10 MB. What is
  missing goes back to ghost-pack-film (number, covers, captions) or ghost-film (videos, poster, the 720p copy).
- **What goes where.** A video over 3 minutes is not a Reel or a Short, so Instagram gets the two parts:

| Order | Platform | File | Caption |
|---|---|---|---|
| D, first | Instagram Reel | IG （下） 720p, cover `cover_part2.jpg` | `caption_ig_part2.txt` |
| D, right after | Instagram Reel | IG （上） 720p, cover `cover_part1.jpg` | `caption_ig_part1.txt` |
| D | YouTube | the full 720p. Over 3 minutes it posts as a normal video, not a Short. Thumbnail `cover.jpg` | title and description from `caption_full.txt` |
| D | Facebook Page | the full 720p, as the Page, AI label on. The composer turns it into a Reel (5:36 went up whole on 第 1 部); there was no custom thumbnail input, so the first frame is the thumbnail | the Facebook section of `caption_full.txt` |
| D | Threads | one post: `cover.jpg` + `threads.txt` (`{ig_link}` = the part 1 Reel) | topic 鬼故事 |
| D | Pinterest | `cover.jpg`, and a video pin on the board 「鬼唱詩劇場｜台灣怪談短片」. Pinterest refuses videos over 300 s (第 1 部, 2026-11-11), so a longer full cut cannot go; `pins.txt` names the file to pin (IG （上） when the full cut is longer). Pinterest creates the board inline in the pin form | `pins.txt` |
| optional | YouTube Shorts | the IG parts (each under 3 min), only when the owner says yes: Shorts are where new viewers find the channel, the full video is a normal video | title 「{label}（上）〈title〉」, the part captions |

Both parts go up the same day (owner, 2026-11-10: 「1，2 部一起發」). Post 下 first and 上 second: the profile grid
shows the newest post first, so it reads 上, 下 from the left, and part 1's caption says 「下集在主頁，接著看。」.
TikTok stays off (2026-11-01).

- **Record.** Each post goes into the film ledger, not the comic one:
  `py -X utf8 "<ghost-pack dir>/scripts/ledger.py" --ledger C:/Users/sheep/Pictures/gui_chang_shi/brand/film_ledger.json posted N <platform> --url <link>`.
  Also put the links in `posts/film/README.md`.

## Facts that cost a retry

- Instagram web: Escape on the crop menu opens "Discard post?"; the "Add AI label" switch reports "on" in either
  state, so check it on screen; pinning a post is only in the phone app.
- Threads: Chrome shows Chinese posts translated into English; the tab title holds the original text.
- Pinterest: typing `@handle` in a description opens a mention list; click blank space to close it.
- Facebook: saving the Page bio left a "Leave site?" prompt although the save took; check, then navigate with force.
- YouTube: the brand's Google account is signed in beside the owner's; "Switch account" in the avatar menu changes
  channel without a password. YouTube Studio shows "Your channel <name>": check it before uploading.
- TikTok has no Instagram field any more, in the app either; the bio names the handle. Links in TikTok captions and in
  YouTube Shorts descriptions are not clickable (YouTube's until the owner verifies the channel); the channel page's
  Instagram link is.
- Facebook: photos dropped onto the Page composer's "相片／影片" input hung on 「載入中……」; open the composer with
  「在想些什麼？」 first, then upload one image, then the rest. Claude in Chrome's `navigate` cannot force past "Leave
  site?": open a new tab and tell the owner about the stuck one.
- Pinterest and TikTok offer to connect Instagram or turn on automatic checks after posting: decline; those are
  account settings.
- A file over 30 MB is not delivered to a phone by SendUserFile; send a 720p copy.
