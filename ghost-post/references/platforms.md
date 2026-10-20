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
- **Image and full text in one go (tested 2026-10-20, 第 2 首).** In the New thread dialog: post 1 = hook text +
  image (the dialog's file input); "Add to thread" → post 2/2 shows "Attach text" (it is only gone from the post that
  has the image) → the "Text attachment" editor: type the whole `attachment.txt` line by line in the body, "Done";
  post 2's own text can stay empty → "Add to thread" → post 3/3 = `link.txt`. One "Post" publishes all three,
  each with the topic tag. Record the first post's link (`/@<handle>/post/<code>`). The hook's last line reads
  「……（全文在下一則）」 since the attachment is in the next post (owner's wording, 第 2 首).
- Topic: type 鬼故事 in "Community or topic" and pick 「鬼故事」 from the list.
- Two halves (上半首 21:30, 下半首 23:00) are still untried: the second half would be a reply in the same thread.

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
- Spread a comic's page pins over several days rather than all at once, and pin no page that shows the reveal.


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
4. Switch back: top-right avatar → the personal profile's name in the list; a toast 「已切換為…」.
- `navigate` in Claude in Chrome has no force option: a page stuck behind "Leave site?" needs the owner, or a new tab.
