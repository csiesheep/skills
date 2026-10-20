---
name: ghost-post
description: Post one ghost story's finished, ready-to-post set on the user's own brand accounts through their signed-in Chrome — the Reel full on Instagram, YouTube Shorts, TikTok and the Facebook Page, the carousel on Instagram and the Page, the three-post Threads thread, the Pinterest pins, teasers as Instagram trial Reels — one post at a time with the user's yes on each, and record every link. It only checks and posts: always first it checks every platform (right account signed in, upload entry reachable), then checks the story folder for every ready-to-post file (number stamped, captions written, lengths and sizes right), and if anything is missing it stops and names the skill that makes it; it never makes or edits material itself. Use whenever the user wants to post, publish, 發文, 發第 N 首, 上架, put a story online, post to IG / Threads / YouTube / TikTok / FB / Pinterest, or check whether the accounts or a story are ready to post, even if they name only one platform. Not for numbering, stamping or writing captions (ghost-pack), writing stories (ghost-story), comics, carousels, pins or teasers (ghost-comic), the Reel full (ghost-reel), profiles (social-profile), or replying under others' posts (ghost-reply).
---

# Ghost post

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
| `reels/full_v3_cinema/full_v3_cinema.mp4` | Instagram Reel, YouTube Shorts, TikTok, Facebook Page |
| `posts/ig/01.jpg … NN.jpg`, `posts/ig/caption.txt` (01.jpg stamped; `01_nonumber.jpg` is ghost-pack's backup, never posted) | Instagram carousel, Facebook Page |
| `posts/threads/hook.txt`, `image.jpg`, `attachment.txt`, `link.txt` | Threads: hook with image → reply with attachment → reply with `link.txt` (the Instagram link) |
| `posts/pinterest/00_cover.jpg`, `NN_page.jpg` (pages before the reveal), `pins.txt` | Pinterest |
| `posts/cross_caption.txt` (`{ig_link}` filled after the Instagram post) | YouTube, TikTok, Facebook |
| `reels/teaser_A/`, `teaser_B/` | Instagram trial Reels (phone) |
| `README.md`, `brand/ledger.json` | links recorded here |

## What may and may not be done

- **One yes, one post.** Posting is public and cannot be cleanly taken back. Send the preview of each post (file plus
  exact caption) and post only after the user says yes to that post. A yes does not carry over to the next post,
  platform or a changed caption.
- **Never sign in, never merge accounts.** If a platform shows a login page, it is not ready; the user signs in.
  Do not add profiles to Meta's Accounts Center or link accounts to make cross-posting work: on 2026-10-20 the user
  chose to post on the Facebook Page as the Page instead, because Instagram's "share to Facebook" needs the owner's
  personal Facebook profile added to the brand's Meta account.
- **Check the account before every post**, on the page you post from: the brand's handle, "Edit profile" on its
  own profile, no "Follow" button.
- **Leave Chrome as you found it.** Work in a new tab and close it. YouTube: switch back to the account that was
  active. Facebook: switch back from the Page to the personal profile.
- **Fiction, labelled.** Every post carries the disclosure (`brand.json` → `disclosure`) and the site's AI label
  where it has one. No reveal panel in a cover, a Threads image, a teaser or a Pinterest pin.

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
720p preview copy) and the exact captions, and ask post by post.

### 4. Post (D is the posting day; the user's plan sets the time)

Instagram first, because every other platform links to it.

| Order | Platform | What | Notes |
|---|---|---|---|
| 1 | Instagram | Reel full, then the carousel | Web upload works for the Reel too: crop "Original", cover from `full_v3_cinema_cover.jpg`, sound on, AI label on; the carousel's link goes into every `{ig_link}` slot |
| 2 | YouTube Shorts | Reel full | Studio shows "Your channel 鬼唱詩"; title 「第 N 首｜title」; AI use "Yes"; not for kids; Public |
| 3 | TikTok | Reel full | Studio upload; AI-generated content on; decline "automatic content checks"; under review ~30 s before "Everyone" |
| 4 | Facebook Page | Reel full, then the carousel as a photo post | As the Page ("立即切換"); "新增 AI 標籤" on; switch back to the personal profile |
| 5 | Pinterest | The cover today; the pages before the reveal one a day after | Link to the Instagram carousel; Mark as AI-Modified and AI-generated person |
| 6 | Threads | One dialog, three posts: hook + image → full text as a text attachment → `link.txt` | The image and the attachment cannot share a post; "Add to thread" gives post 2 its "Attach text" |
| D+1, D+2 | Instagram trial Reels | Teaser A, B | From the user's phone; trial Reels are a toggle in the app |

Videos go up as `full_v3_cinema_preview720.mp4`: Claude in Chrome's `file_upload` takes 10 MB a call and the
1080p file is about 93 MB (`references/platforms.md` → "Upload size"). Captions are typed line by line, never pasted
from memory: read them from the files and check the posted text against them.

After each post: open it, confirm text, image or video and the AI label, copy the link.

### 5. Record

`py -X utf8 "<ghost-pack skill dir>/scripts/ledger.py" --brand-file <brand.json> posted N <platform> --url <link>` for every post, and the links in the story's `README.md`. Tell the
user the first hour of replies is theirs (ghost-reply can draft them). After 48 hours, put views, completion,
saves, shares and new followers into the brand's results table.

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
