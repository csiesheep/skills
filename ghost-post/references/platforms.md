# Platforms

Every section below was written from real posts: Instagram, Threads and Pinterest from 第 0 首 and 第 1 首
(2026-10-18/19); all six platforms from 第 2 首 (2026-10-20), the first full set, posted one by one through
Claude in Chrome with the owner's yes on each.

**Upload size.** `file_upload` takes at most 10 MB a call. The Reel full V3 at 1080p is about 93 MB, so the video
goes up as `reels/full_v3_cinema/full_v3_cinema_preview720.mp4` (about 9 MB, 720p). The owner looked at it and
chose it on 2026-10-20 ("720P 很清楚"); the alternative is the owner picking the 1080p file in the site's own file
dialog. Ask which when the 720p file is missing or the owner wants 1080p.

## Platform check (step 1, read only)

| Platform | Open | Ready when | Not ready → |
|---|---|---|---|
| Instagram | `https://www.instagram.com/<handle>/` | "Edit profile" and sidebar "New post" | user signs in |
| Threads | `https://www.threads.com/@<handle>` | "Edit profile" and "New thread" | "Continue as <account>" from the Instagram session may be used only for the brand's handle; otherwise the user signs in |
| Pinterest | `https://www.pinterest.com/<username>/` | "Edit profile" / "Edit", "Your saved ideas", no "Follow" | user signs in |
| YouTube | `https://www.youtube.com/` → avatar → "Switch account" (look only) | the brand's channel is listed (鬼唱詩 under gui.chang.shi.tw@gmail.com) | user signs the brand's Google account into Chrome |
| TikTok | `https://www.tiktok.com/tiktokstudio/upload`, then `https://www.tiktok.com/@<username>` | Studio shows "Select video" and a file input; the profile shows "Edit profile" | a login page means the user signs in |
| Facebook Page | `https://www.facebook.com/<page>` | the personal profile is signed in and the Page shows "切換為…的粉絲專頁並開始管理 / 立即切換" (or Chrome is already acting as the Page: "創作者主控板", "編輯") | user signs in, or is not an admin of the Page |

Do not open Accounts Center's "Your stories, reels and posts" sharing to fix Facebook: it asks to add a Facebook
profile to the brand's Meta account (an account merge the user declined on 2026-10-20).

## Threads (threads.com) — tested 2026-10-18, 第 1 首

1. Account check: `https://www.threads.com/@<handle>` shows "Edit profile". If Chrome has no Threads session, a
   "Continue as <account>" from the Instagram session may appear; use it only for the brand's handle.
2. Sidebar "New thread" (or "What's new?" on the profile) → dialog "New thread". The topic tag is the textbox
   "Community or topic" right of the handle: one per post (the brand uses 鬼故事). The box is narrow and clips the
   first character on screen; the posted thread shows the whole tag.
3. Body: 500 characters a post. Type line by line with Enter. To change one line, click it, End, shift+Home, type.
4. **An image and a text attachment cannot be in the same post.** "Attach text" (up to 10,000 characters) is gone
   once an image is attached. Choose per story:
   - Comic story: the hook plus one panel that gives nothing away, last line 「……全篇漫畫在 IG。」, then a reply with
     the Instagram link (step 6). The full text does not go on Threads. 第 1 首 went this way.
   - Text-only story: the hook plus the attachment and no image, or the image in the next post of the thread.
   Image: `find` the file input in the dialog and `file_upload` it.
5. "Post" (bottom right of the dialog) → a "Posted" toast with "View"; that link's href is
   `/@<handle>/post/<code>`. Open it to confirm the text, the tag and the image.
6. Reply with the link: on the post's page, the inline box "Reply to <handle>..." → type → the round arrow button at
   its right. It shows "Posting..." for a few seconds; after a reload the thread reads 1/2 and 2/2 and the reply
   carries the same topic tag. Record the first post's link, not the reply's.

- On an English Chrome the post page shows "Translated from Chinese": `get_page_text` returns the translation, while
  the tab title holds the original text. Check the wording against the title or a zoomed screenshot.
- **Three separate posts (owner, 2026-10-23, after 第 6 首: 「Threads 故事，漫畫，reel 分別是3個貼文」).** Story:
  New thread → paste the hook → topic 鬼故事 → "Attach text" on the same post (no media) → paste the whole
  attachment → Done → Post. Comic: New thread → paste the carousel caption → topic → file input with all pages → Post.
  Reel: New thread → paste the IG Reel caption → topic → the 720p mp4 → Post. Verify each post's length+hash before
  its Post, and record the story post's link as the Threads link in the ledger (the other two in README.md).
- **Video, comic and full text in one thread (第 6 首, 2026-10-23; superseded by the three posts above; the owner: 「threads 也 post 文案，漫畫，動畫」).**
  Post 1 = hook (paste) + the topic 鬼故事 + `full_v3_cinema_preview720.mp4` on the dialog's file input; "Add to
  thread" → post 2 = 「全篇漫畫，由右往左、由上往下讀。」 + all carousel pages (`posts/ig/01..NN.jpg`, nine went in one
  file_upload) → "Add to thread" → post 3 "Attach text" with the whole attachment (empty post text) → "Add to thread" →
  post 4 = `link.txt`. One "Post" publishes all four. Before pasting into the "Text attachment" editor, click inside it
  and check `document.activeElement` is the editor (aria-placeholder "Say even more..."): the first paste of 第 6 首
  went nowhere because focus was still on the button. Verify every post's length+hash before "Post".
- **Image and full text in one go (tested 2026-10-20, 第 2 首; superseded by the four-post thread above).** In the New thread dialog: post 1 = hook text +
  image (the dialog's file input); "Add to thread" → post 2/2 shows "Attach text" (it is only gone from the post that
  has the image) → the "Text attachment" editor: type the whole `attachment.txt` line by line in the body, "Done";
  post 2's own text can stay empty → "Add to thread" → post 3/3 = `link.txt`. One "Post" publishes all three,
  each with the topic tag. Record the first post's link (`/@<handle>/post/<code>`). The hook's last line reads
  「……（全文在下一則）」 since the attachment is in the next post (owner's wording, 第 2 首).
- Topic: type 鬼故事 in "Community or topic" and pick 「鬼故事」 from the list.
- **Switching to the brand (第 5 首, 2026-10-23; the owner said 「Threads 也自己切帳號」).** Chrome's Threads was
  signed in as csiesheep.games. Threads' web menu has no "Switch accounts": menu (≡) → "Log out" → the login page
  offers the Instagram session's account (鬼唱詩 gui.chang.shi, when Instagram is on the brand) → click it, no
  password. Never use the username and password Chrome autofills on that page.
- **Do not log out of Threads at the end of a run (第 12 首, 2026-10-28).** Threads' "Log out" also logged Chrome's
  Instagram out of every account; gui.chang.shi came back without a password, csiesheep.games asked for one and the
  owner had to sign in. Leave Threads signed in as the brand; the next task switches it with the route above.
  If Instagram ever shows "Save your login info?", that is the owner's choice: answer "Not now" and tell the owner.
- **Paste instead of typing (第 5 首).** Focus a post body (or the "Text attachment" editor), then javascript_tool:
  `const dt=new DataTransfer(); dt.setData('text/plain', text); document.activeElement.dispatchEvent(new
  ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))`. The editor takes it with its line
  breaks: the 1,505-character attachment went in one call instead of four typing batches. The text in the call is
  still copied by hand, so the hash check is not optional: it caught 牵 for 牽. Fix by ctrl+a, Delete, paste again.
- Two halves (上半首 21:30, 下半首 23:00) are still untried: the second half would be a reply in the same thread.
- **Check the typed text against the file before "Post" (第 3 首, 2026-10-21).** Read each post's
  `contenteditable` back with javascript_tool: its `<p>` elements are the lines (innerText doubles the newlines),
  join them with `
` and compare length and a simple hash with the file's (`h = h*31 + codepoint`, 32-bit, in the
  page and in Python). It caught a wrong character (a typing slip, 瀧 for 瀏) in the 1,982-character attachment.
  The attachment editor takes Enter for a new line and two for a blank one; typing it took four batches.

## Instagram (instagram.com) — tested 2026-10-18, 第 1 首 carousel

1. Account check: `https://www.instagram.com/<handle>/` shows "Edit profile".
2. Sidebar "New post" (Create) → menu item "Post" → dialog "Create new post". `find` "file input inside the Create
   new post dialog" (next to "Select from computer") and `file_upload` all slides in order in one call (12 slides,
   3 MB went in one call; the limit is 10 MB a call). The dots under the preview count the slides.
3. Crop: the default cut the top and bottom off a 3:4 slide. "Select crop" (bottom left) → "Original" keeps the whole
   3:4 slide, and it applies to every slide. Close that menu by clicking elsewhere, **not Escape**: Escape opened
   "Discard post?" (answer "Cancel" to keep the draft).
4. "Next" → Edit (filters; leave "Original") → "Next" → caption step.
5. Caption: click "Add a caption...", type line by line with Enter (two Enters for a blank line); the counter
   (`n/2,200`) matched `caption.txt` (91). Hashtags last, followed by a space, so no suggestion is picked.
6. "Add AI label" is a switch on this step (off by default); switching it on shows "AI content" under the handle on the
   post. Its accessibility name read "on" in either state, so check it visually.
7. "Share to" listed only Threads (the account, off), no Facebook while the Page's sharing across profiles is off.
   `find` called that Threads switch "Facebook": read the label on screen before touching it.
8. "Share" (top right) → "Sharing" → about 15 s → "Your post has been shared." → "Done".
9. The link: on the profile, `find` "link to the post in the profile grid" gives `/gui.chang.shi/p/<code>/`; open
   `https://www.instagram.com/p/<code>/` to confirm the caption and the AI label, then record it.

- Pinning: the web post's "More options" menu has no "Pin to your profile" (2026-10-19, 第 0 首); pin from the phone app.
- Screenshots timed out twice on this site while the page was busy; `find` and `get_page_text` kept working.
- Reel (tested 2026-10-20, 第 2 首): the same "New post" → "Post" dialog takes the mp4; a notice "Video posts are now
  shared as reels" → "OK". Crop "Original" keeps 9:16. The Edit step has "Cover photo" with its own file input
  (`find` "file input for Cover photo", `file_upload` `reels/full_v3_cinema/full_v3_cinema_cover.jpg`), "Trim" and
  "Sound on" (leave on: the Reel's own music). The caption step reads "New reel"; AI label as for a carousel. Sharing
  takes about 40 s ("Your reel has been shared."). Link: `/gui.chang.shi/reels/` → `find` "/reel/" →
  `https://www.instagram.com/reel/<code>/`; the post shows "AI content".
- Reel caption: the carousel's `caption.txt` says 「漫畫由右往左、由上往下讀。」; for the Reel the owner swapped that
  line for 「全篇漫畫在主頁。」 (第 2 首). Until ghost-pack writes a Reel caption, ask.
- Clicking outside the dialog (to close the crop menu) also opened "Discard post?": answer "Cancel". Click blank space
  inside the dialog's dark margin instead.
- Trial Reels are a toggle in the phone app's Reel options only.
- **The signed-in account can change between sessions (第 4 首 part 2, 2026-10-22).** The day after posting as
  gui.chang.shi, Chrome's Instagram was signed in as csiesheep.games: the brand profile showed "Follow", and the
  caption step's header named csiesheep.games. Check the handle above the caption box before "Share"; if it is not
  the brand, discard and switch: More → Switch accounts → gui.chang.shi switched without a password (the owner said to, 2026-10-22). If it asks for a password, stop: that is the owner's.
- 第 3 首 (2026-10-21) went as documented: Reel then carousel, crop "Original", the Reel cover through the Edit
  step's "Cover photo" file input, "Share to" Threads left off. The grid on `/<handle>/reels/` needed a few seconds
  before `find` saw the new `/reel/` link.

## Pinterest (pinterest.com) — tested 2026-10-18, 第 1 首 cover pin

1. Account check: `https://www.pinterest.com/<username>/` shows "Edit profile" (and "Your saved ideas"), no
   "Follow".
2. Board, once: the red "Create" on the profile → "Board" → dialog "Create a board": "Board name", "Make this board
   private" (leave off: boards are public by default) → "Create". A "Save some Pins to your new board" panel follows;
   "Done" closes it.
3. Pin: `https://www.pinterest.com/pin-creation-tool/`. `find` the file input ("File Upload") and `file_upload` the
   2:3 image. The form then shows "Title", "Description", "Link", "Board" (it picked the board just made), "Tagged
   topics", "Mark as AI-Modified", "More options". It saves a draft as you go ("Changes stored!", "Pin drafts").
4. Description: type line by line with Enter. Typing `@handle` opens a mention list of unrelated accounts (ASOS,
   Amazon…); click blank space to close it, never Enter or a list item. The text stays plain.
5. AI label: switch on "Mark as AI-Modified" (click it by its `find` ref; a coordinate click missed after the page
   scrolled), then "This Pin includes an AI-generated person" becomes clickable; the brand ticks both for comics with
   drawn people. "More options" holds "Allow people to comment" and "Show similar products" (both on by default) and
   "Alt Text".
6. "Publish" (top right) → "Your Pin has been published!" with "View" (`/pin/<id>/`) and a browser-extension promo
   dialog (close it with its X). Open the pin: "AI modified" on the image, "Visit site" points to the link. Record
   `https://www.pinterest.com/pin/<id>/`.

- Sections inside a board were not tried; the 第 1 首 pin went to the board without one.
- ~~Spread a comic's page pins over several days, and pin no page that shows the reveal.~~ Replaced 2026-10-28
  (owner: the whole comic and the Reel, one board per story; reveal pages titled 「結局」). See below.

## Pinterest story board — tested 2026-10-28, 第 8 首 (board + video + 8 pages + cover, 08:30–08:52)

Files: `posts/pinterest/NN_page.jpg` for every page (`manga.py pins --dest ..` from the comic folder for a story
exported before 10/28) and `pins.txt` (`pack.py --pins-only --ig-link <carousel>`): board name, board text, every
title, the video section and the pinning order.

1. Board: profile → the red "Create" at the bottom right → "Board" (the "+" at the top right is the profile cover
   image, not a board) → name from `pins.txt` → "Create" → "Done". Board text: board page → "…" → "Edit info and
   settings" → Description (a textarea, Enter makes a line) → "Done".
2. Order: a new pin goes FIRST on the board, which reads left to right. Pin the video, then the last page down to
   page 1, then open the existing cover pin and save it to this board (its board picker → the story board; it
   becomes a new pin id on that board). Result on 第 8 首: cover, 1/8 … 8/8, video.
3. Each pin on `/pin-creation-tool/`: tag the file input with an aria-label in JS, `find` it, `file_upload` (the
   720p Reel copy, 8.7 MB, uploads as a video pin, 1:32 kept); the board picker keeps the last board used.
   Title, then description: line 1, Enter, the disclosure line. Typing `@gui.chang.shi` opens a mention list:
   click blank space, WAIT 1 s, click back into the description, ctrl+End, wait 1 s, and only then Enter and the
   tags. On page 4 an Enter pressed while the list was still open swapped the handle for "@asos".
   Link, then the AI switches (clicking the checkbox labelled "Mark as AI-Modified", then "This Pin includes an
   AI-generated person", works from JS).
4. Before Publish, compare in JS: title in the inputs, the contenteditable's innerText equal to the file's text,
   the link, both AI boxes checked, the board name on the page; throw if any differ (that check caught the @asos).
5. Publish stays grey while the link field has focus: click blank space, wait 2 s, then "Publish". Done when the
   empty "Upload your media" form comes back. No published-pin link is shown: read the ids off the board page
   (`a[href*="/pin/"]`, each link's aria-label is the title).
- A pin page shows its own "Impressions" (last 30 days) to the owner, so the stats run can read pins there.
- "Publish at a later date" exists on the form (not used).
- 第 3 首's cover pin (2026-10-21) went as documented. In step 1 the profile's accessibility tree had no "Edit
  profile"; `get_page_text` showing "Your saved ideas" and the brand's own bio was the proof.


## YouTube Shorts — tested 2026-10-20, 第 2 首

1. Account: YouTube Studio top left must read "Your channel 鬼唱詩". Switching accounts: youtube.com → avatar →
   "Switch account" → 鬼唱詩 (gui.chang.shi.tw@gmail.com). On 2026-10-20 the owner chose to stay on the brand
   channel afterwards; ask before switching back.
2. Studio "Create" → "Upload videos" → `find` "file input in the Upload videos dialog" → `file_upload`. It saves as a
   private draft at once; a vertical video under 3 minutes is a Short (the link reads `/shorts/<id>`).
3. Details: title box (ctrl+a, Delete, type 「第 N 首｜title」); description from `cross_caption.txt`. Typing a hashtag
   opens a suggestion list: type a space, then click the Details heading. Under the description: "To make external
   links clickable, first complete a one-time verification" — the Instagram link stays plain text until the owner
   verifies the channel with a phone (Studio → Settings → Channel → Feature eligibility). The channel's own
   Instagram link (Customization → Profile → Links, added 2026-10-20) is clickable regardless.
4. Audience: "No, it's not made for kids". "Show more": Paid promotion "No"; **AI use** ("Was AI used to generate or
   edit your content…") → "Yes" (it adds YouTube's AI label). Next ×3 → Visibility "Public" → "Publish".
5. "Video published" dialog shows the link; open `https://www.youtube.com/shorts/<id>` to check title and channel.
- **"Switch account" did not take (第 4 首, 2026-10-22).** Twice the avatar stayed on the owner's channel and Studio
  kept opening it. `https://studio.youtube.com/?authuser=3` (the brand's Google account is the 4th in Chrome) opened
  "Your channel 鬼唱詩" directly and left youtube.com on the owner's channel, so nothing needed switching back.
- The Description box can show a red outline with empty alerts right after typing; it is not an error ("Checks
  complete. No issues found." and Publish went through, 第 3 首).

## TikTok — tested 2026-10-20, 第 2 首

1. `https://www.tiktok.com/tiktokstudio/upload`; the top-right avatar must be the 鬼唱詩 seal. `find` "file input
   for selecting video" → `file_upload`.
2. A dialog "Turn on automatic content checks?" may appear: it is a lasting setting; "Cancel" unless the owner says
   otherwise. A "New editing features" tip: "Got it".
3. Description: click it, ctrl+a, Delete, type `cross_caption.txt`'s TikTok part with shift+Enter between lines.
   `@gui.chang.shi` followed by a space stayed plain text (no mention). Hashtags one at a time each followed by a
   space, then click the Details heading to close suggestions. The cover defaults to the first frame.
4. Settings: When "Now", Who can see "Everyone"; "Show more" → "AI-generated content" switch → dialog
   "Labeling AI-generated content" → "Turn on". → "Post".
5. Studio's Posts list shows "Content under review" and privacy "Only me" for about 30 s, then "Everyone". The
   link is the post's href: `https://www.tiktok.com/@guichangshi/video/<id>`.
- Profile links: TikTok removed the Instagram/YouTube fields (reportedly 2025-11; the owner's app has none either);
  the website field needs 1,000 followers. The bio names the handle instead: 「全篇漫畫在 IG @gui.chang.shi」.
- **The description editor drops text (第 3 首, 2026-10-21).** Typed in one call, the logline line vanished; typed
  again, everything after its full-width comma 「，」 was lost. Type 「，」 as its own `type` call and the rest after
  it, then zoom on the description and compare it with the file before "Post". The AI-generated content switch
  turned on directly this time, without the "Turn on" dialog. Step 1: the profile's buttons have no names in the
  accessibility tree; a screenshot shows "Edit profile".

## Facebook Page — tested 2026-10-20, 第 2 首 (posting as the Page)

1. `https://www.facebook.com/gui.chang.shi` → "立即切換": the left menu reads "管理粉絲專頁", the avatar is the seal.
2. Reel: `https://www.facebook.com/reels/create` (placeholder 「鬼唱詩，在想些什麼？」 proves the Page) → `find`
   "file input" → `file_upload` the video → description box 「介紹你的 Reel……」 (shift+Enter for lines) → "繼續" →
   分享對象「所有人」, "新增 AI 標籤" switch on → "發佈". Link: the Page's Reel tab → `/reel/<id>/`; shows "AI 內容".
3. Photo post: on the Page, the composer's "相片／影片" button **is** a file input; `file_upload` to it opened the
   dialog but the photos hung on 「載入中……」 for minutes, and the dialog then would not close ("Leave site?" blocked
   navigation; the tab had to be left for the owner). What worked in a fresh tab: click 「在想些什麼？」 first, then
   `file_upload` one image to the dialog's file input, wait for it to show, then the rest (they append: "+4").
   Text, then 「已關閉 AI 標籤」 → "新增 AI 標籤" switch (click by position; the ref click did not take) → 「知道了」
   → the header reads 「已開啟 AI 標籤」 → "繼續" → "發佈". Dismiss the "make a Reel from your photos" offer with
   「稍後再說」. Link: the post's id from the feed → `https://www.facebook.com/gui.chang.shi/posts/<id>`.
4. Switch back: top-right avatar → the personal profile's name in the list (`find` 「切換為<name>」; a click by position on 第 6 首 landed on another Page, 小羊遊戲間); a toast 「已切換為…」. Check the composer on facebook.com reads 「<personal name>，在想些什麼？」.
- `navigate` in Claude in Chrome has no force option: a page stuck behind "Leave site?" needs the owner, or a new tab.
- **New composer (第 3 首, 2026-10-21).** 「在想些什麼？」 on the Page now opens a full page `/post/create`: its
  「新增相片或影片」 file input took one image, then a second file input (「新增更多」) took the other ten in one
  call, no 「載入中……」 hang. Type the text with the 「，」 split as on TikTok, then the AI switch (click by position)
  → "發佈". A 「直接與用戶對話」 offer to add a contact button follows: 「稍後再說」. The post's link: on the Page,
  hover the post's 「剛剛」 timestamp, then read the `a[href*="/posts/"]` href (`/gui.chang.shi/posts/pfbid…`) with
  javascript_tool; it is empty until hovered.
- A new Reel shows in the Page's Reel tab after about 20 s; `/reel/<id>/` shows 「AI 內容」.
- **The sidebar is not proof (第 4 首, 2026-10-22).** The Page showed 「管理粉絲專頁」 in the left menu while Chrome was
  still acting as the personal profile; the Reel dialog had reached its last step before the account menu (top-right
  avatar) showed the personal name on top. Check the avatar is the seal, or the composer reads 「鬼唱詩，在想些什麼？」,
  before uploading. Switching from inside the dialog discards the draft. Switch back afterwards from the same menu.
