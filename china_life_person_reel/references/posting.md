# Captions and posting (2026-10-23, Reel 3 古代女生的一生)

Posted as 小羊遊戲間 / csiesheep.games on Instagram, Threads, YouTube and the Facebook Page, one at a time, after the
owner said 都發. Links and the final texts are in `reels/china_life/3/captions.md`; use it as the format.

## Captions: leave suspense on every platform (owner, 2026-10-23)

The first captions retold the whole life (every age down to death at 70). The owner: 「Threads 上文案部分不要把一生全寫完，
留懸念」 and then 「所有文案都留懸念」. So every caption:

- opens with the hook question (the reel's title line),
- gives the person (name, year, place, class) and the first one or two turns only,
- stops on 「她後來怎麼了？影片看到最後」,
- then the game pitch and link, the AI-portrait note 「肖像為 AI 繪製」 and, if the reel has numbers,
  「數字為遊戲模擬，不是史料統計」,
- never the later ages, the ending, how long they lived, or the stats themselves.

A YouTube title that names the first two turns is fine. Write `captions.md` this way before posting; showing the user
the texts first is still the rule.

## Files

- `out/reel_upload.mp4` from `finish.py upload` (≤ 9.5 MB): Claude in Chrome's file_upload takes at most 10 MB.
- `out/reel_cover.jpg` (portrait grid) as the cover where the platform takes one.

## Accounts

Chrome holds two brands. Before touching anything, read which account each site is on and put each back after:
Instagram and Threads (gui.chang.shi or csiesheep.games; switch per game-promote `references/accounts.md`),
YouTube Studio (鬼唱詩 or 小羊遊戲間 channel: avatar → Switch account), Facebook (personal profile or the Page:
the Page's 立即切換; back via avatar → 切換為<name>). Check the handle on the page right before each post.

## Instagram (web)

Sidebar Create → Post → `find` the file input → upload. The crop step defaults to 1:1: open the crop icon
(bottom-left) and pick **Original**. Next → the Edit step has **Cover photo → Select from computer** (a file input:
upload the cover). Next → caption box (`find` "Add a caption"; typing with `\n` makes line breaks), leave
**Add AI label** off (see AI labels below), check that "Share to" does not cross-post, Share, wait for
"Your reel has been shared". Link: newest `/reel/<code>/` on `instagram.com/csiesheep.games/reels/`.
Edit later: open `instagram.com/p/<code>/` (not `/reel/`, which opens the reels feed), More options → Edit,
ctrl+a, Delete, type, Done.

## Threads (web)

New thread → the composer's file input → upload the video, click the text box, type, Post. The composer shows the
posting handle. **A Threads post can be edited only for 15 minutes**; after that the fix is delete and repost, and
deleting is the user's to do. Link: newest `/@csiesheep.games/post/<code>`.

## YouTube Studio

Upload (top right) → file input → title (ctrl+a over the default file name, type), description, **No, it's not
made for kids**, Next ×3, **Public**, Publish; the Short link is shown during the details step. Custom thumbnails
need phone verification on this channel (not done). Edit later: `studio.youtube.com/video/<id>/edit`, change,
Save, reload to check.

## Facebook Page

As the Page, `facebook.com/reels/create` → file input → in the uploaded item click **封面** → 選擇縮圖 dialog →
scroll down → its file input (上傳) takes the cover. Type the description in 「介紹你的 Reel」, 繼續, leave
**新增 AI 標籤** off, 發佈. The reel appears on the Page's Reel tab after about a minute.
Edit later: the reel player's ⋯ menu has no edit; use the Page timeline post's ⋯ → **編輯貼文**, change, 儲存,
and wait for 儲存中 to finish before navigating (a 「Leave site?」 dialog blocks it otherwise).

## Comments with the link

After posting, leave one comment as the brand with the game link (Facebook makes it a link card; Instagram shows the bare
URL as text). **Pinning is app-only**: the web comment menus on Instagram (Delete/Cancel) and on Facebook Reels, from the
player and from the Page timeline (編輯/刪除/檢舉留言), have no pin. Ask the user to pin from the app if other comments
arrive first.

## AI labels

Leave Facebook's 「新增 AI 標籤」 and Instagram's "Add AI label" off (owner, 2026-10-24: 「fb 不加上 ai 標簽，我們沒有產生
逼真的東西」). The platforms require them for realistic AI imagery; the ink-wash portraits are not. On Reel 3 they
were switched on at first; editing the Facebook post's text later reset its label to off (the 「AI 內容」 tag left the
header). The caption keeps 「肖像為 AI 繪製」.

## TikTok

No account yet (2026-10-23). Keep the TikTok caption in captions.md for when there is one.

## Links that people can tap (owner, 2026-10-24)

The games report showed Instagram and Facebook sending almost nobody to the game (4 and 7 visitors a day vs. 121
from Threads), so every post now carries a tappable link where the platform allows one:

- Facebook: the link goes in the post text itself, not only in the comment.
- Threads: the link is in the text, and after posting reply to our own thread with one line and the link
  (「這一生是遊戲裡真的跑出來的，你也投胎一次 👉 https://games.csiesheep.com/china_life/」) so a preview card shows.
- Instagram: captions cannot carry a tappable link. **Stories cannot be posted from desktop Instagram**, and the bio
  links are mobile-only ("Editing your links is only available on mobile"); the bio link points at
  games.csiesheep.com (the hub) as of 2026-10-24. Meta Business Suite (business.facebook.com) has 建立限時動態
  with scheduling, but Instagram is not connected to the 小羊遊戲間 Page there yet, and its upload opens the
  operating system's file picker (no input[type=file] in the page before the click), which Claude in Chrome
  cannot drive. So an Instagram Story with a link sticker is the owner's to post from the phone until that changes.

## Share cards

`node scripts/record.mjs cards <out> <seed>[,<seed>...] --extra "&period=<id>[&sex=F]"` plays each seed to the end
headlessly (internal=1, nothing reported) and saves `card_<seed>.png` (the card the ending screen shows),
`card_<seed>_post.png` (1080×1350, via `window.__shareCard()`) and `card_<seed>_story.png` (1080×1920 with the
QR, via `window.__storyCardBuild()`). The post card shows the age at death and the epitaph, so use it where the
ending is the point (Threads card posts), not as a reel cover.
