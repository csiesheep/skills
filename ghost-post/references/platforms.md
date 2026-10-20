# Platforms

Instagram, Threads and Pinterest posting below was written from real posts (第 0 首, 第 1 首, 2026-10-18/19).
YouTube, TikTok and the Facebook Page were checked as ready on 2026-10-20 but not yet posted to: their posting steps
are the known facts plus the page's own labels; read the page before each click and rewrite the section from the
first real post.

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
- Reels: post from the phone app for the music (see SKILL.md). Trial Reels are a toggle in the app's Reel options.

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


## YouTube Shorts — checked 2026-10-20, not yet posted

- Switch: youtube.com → avatar (top right) → "Switch account" → the brand's channel. Note which account was active
  and switch back after posting.
- Upload in YouTube Studio (`https://studio.youtube.com/`): top left shows "Your channel <name>" — it must be the
  brand. A vertical video of 3 minutes or less becomes a Short. Title 「第 N 首｜title」; description from
  `reel.cross_lines` with the Instagram link (clickable in the description); audience "No, it's not made for kids";
  AI disclosure: answer "altered or synthetic content" yes. Changes stay in draft until "Publish".
- Expected: the file input sits behind "Select files"; use `find` "file input" and `file_upload`, never the button.

## TikTok — checked 2026-10-20, not yet posted

- `https://www.tiktok.com/tiktokstudio/upload` shows "Select video" and a file input (`find` "file input",
  `file_upload`; never the button).
- Caption from `reel.cross_lines`; links in captions are not clickable, so end with the Instagram handle. Turn on the
  AI-generated content label in the upload settings if offered. The Reel full carries its own music; no app sound
  needed.
- The web profile editor has only photo, username, name and bio: the Instagram link on the profile is set in the
  phone app.

## Facebook Page — posting as the Page, not yet posted

- The Page belongs to the owner's personal profile. Switch: on the Page, "立即切換" (confirm "切換" if a dialog
  asks); the top-right avatar becomes the Page and the left menu reads "管理粉絲專頁". Chrome may already be acting as
  the Page.
- Post the same Reel full (as a Reel or video) and the carousel images (as a photo post), text from
  `reel.cross_lines` with the Instagram link (clickable on Facebook).
- Switch back: top-right avatar → "切換為<personal name>"; the URL turns to the personal profile.
- See social-profile's platforms.md for the Page's edit pages.
