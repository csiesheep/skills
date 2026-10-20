---
name: ghost-post
description: Post one finished ghost story as a full set on the user's own brand accounts — the Reel full video on Instagram, YouTube Shorts, TikTok and the Facebook Page, the comic carousel on Instagram and the Facebook Page, the story text as a three-post Threads thread, cover and early pages on Pinterest, teaser Reels as Instagram trial Reels — through the user's signed-in Chrome, one post at a time with the user's yes on each. Always starts by checking every platform (right account signed in, upload entry reachable), then gives the story its number from the brand ledger, checks the story folder for every file the set needs, sends previews, posts in the right order and records each link. Use whenever the user wants to post, publish, 發文, 發第 N 首, 上架, put a story online, post to IG / Threads / YouTube / TikTok / FB / Pinterest, check whether the accounts are ready to post, or asks which number the next story is, even if they name only one platform. Not for writing stories (ghost-story), drawing comics or making Reels (ghost-comic), profile photos and bios (social-profile), or replying under other people's posts (ghost-reply).
---

# Ghost post

Turns one story folder into posts on six platforms and keeps the count. Written from the 鬼唱詩 account
(2026-10-18 to 10-20): first posts on Instagram, Threads and Pinterest, and a check of all six platforms before
第 2 首.

| Where | What |
|---|---|
| Brand folder (`C:/Users/sheep/Pictures/gui_chang_shi/brand/`) | `brand.json` (words, colours, captions), `ledger.json` (story numbers and links), `avatar/`, `music/`, `sfx/` |
| Story folder (`.../stories/<short name>/`) | `README.md`, `story.md`, `comic/` (ghost-comic work folder), `reels/<version>/`, `posts/ig|threads|pinterest/` |
| Plans | Obsidian `Projects/ghost story/ghost story posting.md` (per-story posting plans), `ghost story content plan.md` (which content goes where) |

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

### 2. Number

`py -X utf8 "<skill dir>/scripts/ledger.py" --brand-file <brand.json> reserve "<title>" --kind comic --folder
stories/<short name>` prints the story's number; the same title asked again returns the same number. Never count by
hand: a gap or a repeat on a public account is what readers notice first. `ledger.py ... show` lists all.

### 3. Files

`py -X utf8 "<skill dir>/scripts/check_story.py" <story folder> --number N` lists every file the full set needs and
what is missing or wrong (no 「第 N 首」, a Threads post over 500 characters, a pin not 1000 × 1500…). Make what is
missing with the tools that own it:

| File | Made by | Goes to |
|---|---|---|
| Story text with 「第 N 首｜title」 and disclosure; Threads hook (≤500, first sentence is the hook) and attachment (≤10,000) | ghost-story `ghost_plan.py post story.md --mode attach --brand-file … --number N` | `posts/threads/` |
| Carousel: cover, every page, end card; caption | ghost-comic `manga.py export --cover <panel> --number N` (cover panel gives nothing away) | `posts/ig/` |
| Reel full (the main video; V3 電影感 for 鬼唱詩), with 「第 N 首」 on the title | ghost-comic reel full engine (`scripts/reel_full/`) | `reels/full_v3_cinema/` |
| Teaser A, B (optional, for trial Reels) | `manga.py reel teaser <three panels before the reveal>` | `reels/teaser_A/`, `teaser_B/` |
| Pinterest: cover and pages before the reveal at 1000 × 1500, `pins.txt` with titles ≤100 | fit the pages on the paper colour | `posts/pinterest/` |
| Captions for YouTube, TikTok, Facebook | `brand.json` → `reel.cross_lines` (second line: the Instagram link once it exists) | `posts/cross_caption.txt` |

### 4. Check, preview, ask

Before any preview: number heading and disclosure on everything, no `[經驗]`, no real hospital, temple or shop named,
no reveal panel where it should not be, lengths within limits, words inside the app-safe area of the video
(y 270–1470, x 90–960). Then send the files (SendUserFile; a file over 30 MB does not reach the phone, so send a
720p preview copy) and the exact captions, and ask post by post.

### 5. Post (D is the posting day; the user's plan sets the time)

Instagram first, because every other platform links to it.

| Order | Platform | What | Notes |
|---|---|---|---|
| 1 | Instagram | Reel full, then the carousel | Original audio (the Reel has its own music); AI label on; crop "Original" for the carousel |
| 2 | YouTube Shorts | Reel full | Switch to the brand channel first, back afterwards; title 「第 N 首｜title」; description with the Instagram link |
| 3 | TikTok | Reel full | TikTok Studio upload; caption ends with the Instagram handle (links are not clickable) |
| 4 | Facebook Page | Reel full and the carousel | As the Page ("立即切換"), Instagram link in the text, switch back to the personal profile |
| 5 | Pinterest | Cover and the pages before the reveal | Link to the Instagram carousel; Mark as AI-Modified |
| 6 | Threads | Hook with one safe panel → reply with the full text attachment → reply with the Instagram link | An image and a text attachment cannot share a post, hence three posts |
| D+1, D+2 | Instagram trial Reels | Teaser A, B | From the user's phone; trial Reels are a toggle in the app |

After each post: open it, confirm text, image or video and the AI label, copy the link.

### 6. Record

`ledger.py ... posted N <platform> --url <link>` for every post, and the links in the story's `README.md`. Tell the
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
- TikTok web edits only photo, username, name and bio; the Instagram link on the profile is set in the app.
- A file over 30 MB is not delivered to a phone by SendUserFile; send a 720p copy.
