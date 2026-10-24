# Per-site flows

What worked on 2026-10-18 in Chrome on Windows, with the Claude in Chrome tools, for one brand (鬼唱詩)
on six sites, plus 2026-10-21/22 for a second brand (小羊遊戲間) in the same Chrome: Facebook cover
and contact info, YouTube channel creation, banner and links, and what Threads cannot switch. Labels are given in English and Traditional Chinese because the user's sites run in
different languages (Facebook was in 中文, the others in English). Marked **untested** where that run
did not go through a step; read the page before acting there. Sites change their pages; if a label
is missing, use `find` with a description of what it does rather than its old wording.

Contents: Instagram, Threads, Facebook Page, YouTube, TikTok, Pinterest, limits table.

## Instagram

- Edit page: `https://www.instagram.com/accounts/edit/`
- Account check: the header of the edit form shows the handle and name.
- Photo: `find` "file input" near "Change photo" gives a `type=file` button; `file_upload` it. It saves
  at once (toast "Profile photo added"); no crop dialog.
- Bio: textbox "Bio" with a counter `n / 150`. Click, type line by line with the Enter key between
  lines, then "Submit" at the bottom (toast "Profile saved").
- Not on this page: links ("Editing your links is only available on mobile"), the display name
  (Meta Accounts Center → Profiles → the account → Name; **untested**; reported limit two changes
  in 14 days). Leave the "AI-generated profile" toggle alone: it is for profiles whose subject is an
  AI-generated person, and the user did not ask.
- Verify: `https://www.instagram.com/<handle>/`, zoom on the header (photo, name, the bio lines, the
  Threads badge).

## Threads

- Profile: `https://www.threads.com/@<handle>`. If Chrome has no Threads session, a dialog offers
  the Instagram account already signed in ("Continue as <handle>"); clicking it signs in without a
  password. Only when that handle is the target.
- Account check: the profile shows "Edit profile" (yours) rather than "Follow".
- Photo: "Edit profile" → `find` "file input for profile picture" (next to "Add profile picture") →
  `file_upload` → "Done" at the bottom of the dialog. It did not follow the Instagram photo.
- Bio: in the same dialog, "Bio (+ Write bio)" opens a sub-dialog "Edit bio": click the textbox
  "Write a bio…", type, its "Done", then the main dialog's "Done". Two Done buttons; `find` tells
  them apart. Limit reported as 150.
- Name: a Name row is in the dialog (**untested**; it may follow Instagram's name).
- Verify: reload the profile, zoom on the header.
- Second brand: Threads web keeps its own session. With Instagram switched to brand B, Threads web
  stayed on brand A (the left nav's Profile link `href="/@<handle>"` tells which). Its "More" menu
  has Appearance, Sounds, Settings, Report a problem and Log out, and no account switcher. Do not
  log out to switch; give the user the picture and text for the Threads app, or let them switch
  Threads web themselves. A Threads profile the user said they had just made showed "page not found"
  at `threads.com/@<handle>` for at least several minutes; ask them to check the handle in the app.

## Facebook Page

- Page: `https://www.facebook.com/<page username or profile.php?id=...>`
- Find the Page: `https://www.facebook.com/pages/?category=your_pages` lists the Pages the user
  manages; `find` "link to the Page named <name>".
- Account check and switch: as the personal profile, the Page shows a banner "Switch into <Page> to
  manage it / 切換為…的粉絲專頁並開始管理" with "Switch now / 立即切換". Click it; a dialog "Switch
  profile / 切換個人檔案" asks again: "Switch / 切換". Reload the Page; the top-right avatar is now the
  Page's and the buttons read "Creator dashboard / 創作者主控板", "Edit / 編輯".
- A new Page switched into for the first time skipped that dialog and showed "歡迎使用你的新版粉絲專頁"
  with two notification toggles (both on): press "使用粉絲專頁" and leave the toggles.
- The switch did not stick once: after one click elsewhere the Page view showed the personal
  avatar and the "立即切換" banner again. Switch again, then check the top-right avatar.
- Photo: click the profile picture → menu item "Choose profile picture / 選擇大頭貼照" → dialog with
  "Upload photo / 上傳相片" and "Add frame / 加上特效框". The file input exists once that dialog is
  open: `find` "file input inside the choose profile picture dialog" → `file_upload` → a crop dialog
  with a caption box and a zoom slider → "Save / 儲存". There was no toggle for sharing to the feed.
  The change posted "<Page> 更新了大頭貼照" on the Page.
- Cover: as the Page, "新增封面相片 / Add cover photo" (or "編輯封面相片" once there is one) at the
  bottom right of the cover opens a menu "選擇封面相片 / 上傳相片". `find` "file input in the 上傳相片
  cover menu item" → `file_upload` the 1640 x 624 picture → the cover shows in place with "拖曳或使用
  方向鍵來調整圖像的位置" and a bar "你的封面相片會公開顯示。" with "取消" and "儲存變更". A 1640 x 624
  picture filled the frame exactly with nothing to drag; "儲存變更". It posted "更新了封面相片" on the
  Page. Phones crop the cover's left and right sides, so keep text away from the outer edges.
- Contact info: About → "聯絡資料 / Contact info" shows 電話, 電子郵件地址, Messenger, WhatsApp, each
  with a pencil. The URL `?sk=about_contact_and_basic_info` redirected to `sk=directory_intro`, and
  `find` refs in the About sidebar went stale as it re-rendered; click the "聯絡資料" tab by
  coordinate from a fresh screenshot (URL becomes `sk=directory_contact_info`). Removing the phone:
  pencil → the row opens with an audience button, the number and "移除 / 儲存" → "移除" → dialog
  "確定要刪除此電話號碼嗎？" → "移除". The field then reads the empty placeholder "電話號碼". The first
  click on the pencil only scrolled the page; take a new screenshot before clicking again.
- Bio: as the Page, "編輯個人檔案 / Edit" opens the About tab → section "個人簡介 / Bio" → button
  "編輯個人簡介 / Edit bio" → textarea "自我介紹" with a counter `n/255` → "儲存 / Save". The old bio may
  end with a link line (the Threads URL was there): it becomes the clickable link under the bio, so
  keep link lines unless the user said to drop them.
- Saving the bio can leave a "Leave site?" prompt on the next navigation even though the save took
  (the About tab showed the new text); check the page, then navigate with `force`.
- Chrome may already be acting as the Page when you open it (top-right avatar is the Page, buttons
  read 創作者主控板 and 編輯): no switch needed, and leave it that way at the end.
- Switch back: top-right avatar → the list shows the Page, the personal profile and any other Pages
  → click the personal profile. Check the top-right avatar is the personal one again.
- Page username, if the long `profile.php?id=` URL bothers the user: Settings & privacy → Settings
  → Page setup → Name → Username "Edit" (中文：設定和隱私 → 設定 → 粉絲專頁設定 → 名稱 → 用戶名稱
  的編輯). A new Page may not be eligible for a few days; that is Facebook's rule, not a mistake.
- Never put the personal profile's address or phone on the Page: a new Page once showed both in its
  public About until they were deleted (About → Contact and basic info / 關於 → 聯絡資料和基本資料).

## YouTube

- Studio: `https://studio.youtube.com/`. Account check: top left reads "Your channel" and the
  channel name. A different channel means a different Google account is active in Chrome.
- Several Google accounts in Chrome: `studio.youtube.com` opened brand A's channel even though
  `youtube.com/account` had just said "Signed in as" brand B, and from then on youtube.com was on
  brand A too (the brand's own channel page showed "Subscribe"). Way back without a password:
  youtube.com avatar → "Switch account" → the list shows every signed-in Google account and its
  channel → click the target. Then open `youtube.com/@<handle>` → "Customize channel", which opens
  Studio for that channel in a new tab (get its tab id from the tool's tab list). Do not use "Add
  account" (that is a sign-in). Report which channel YouTube is left on.
- No channel yet: `youtube.com/account` shows "Signed in as <email>" and "Create a channel". The
  dialog "How you'll appear" has Name and Handle fields, filled from the Google profile, and
  "Select picture" (a button that opens the OS file picker; no file input was found, so set the
  picture in Studio afterwards). The handle field checks as you type: red "!" and "This handle
  isn't available. Try a different one." or a green tick. `@csiesheep.games` was refused although
  `youtube.com/@csiesheep.games` was a 404; `csiesheepgames`, `csiesheep_games` and
  `csiesheep-games` all got a tick. "Create channel" accepts YouTube's Terms of Service; the user
  asking for the channel is the consent. A first visit to Studio then shows "Welcome to YouTube
  Studio" → "Continue".
- Customization: `https://studio.youtube.com/channel/<channel id>/editing/profile` (the id is in the
  Studio URL). Sections: Banner image, Picture, Name, Handle, Pronouns, Description, Channel URL.
- Description: a box with a counter `n/1000` that already reads 1 when empty. `ctrl+a` sent right
  after the click typed a literal "a" into it once: click inside the box, then `ctrl+a`, Delete,
  BackSpace, and check the box is empty before typing. Two Enter presses make a blank line between
  paragraphs. Then "Publish". The public channel page showed the old empty "More about this
  channel" for about 15 seconds; reload `youtube.com/@<handle>?hl=zh-TW` and the first line of the
  description appears under the handle.
- Picture: `find` "file input in the Picture section" → `file_upload` the 800 x 800 version → dialog
  "Customize picture" with the full square selected → "Done" → "Publish" at the top right (toast
  "Changes published"). Nothing is live until Publish.
- Description limit 1,000; the first ~150 characters show in search. Seen: a five-line description
  of 69 characters (four line breaks counted) read 70/1000, the empty box's 1 included.
- Banner: `find` "file input in the Banner image section" → `file_upload` the 2560 x 1440 picture
  (it asks for at least 2048 x 1152 and 6 MB or less) → dialog "Customize banner art" shading three
  areas: "Viewable on TV" (all of it), "Viewable on desktop" (the full-width middle strip, 2560 x
  423) and "Viewable on all devices" (the centre 1546 x 423) → "Done" → "Publish". Put the name,
  the URL and the face inside the centre box. A banner made by extending a 1640 x 624 Facebook cover
  around a centre strip of 1099 x 423 kept everything inside it.
- Links: section "Links" → "Add link" → "Link title (required)" and "URL (required)" → "Publish".
  The first link shows under the description line on the channel page as "🔗 <domain>", clickable,
  which a URL inside the description is not.
- Studio screenshots timed out twice ("renderer may be frozen") right after navigation; wait a few
  seconds and take the screenshot again. The page had loaded.
- Handles may be written in Chinese (`@鬼唱詩`); YouTube allows 1 to 10 Han characters. Their URL is
  percent-encoded when copied.

## TikTok

- Profile: `https://www.tiktok.com/@<handle>`. Account check: "Edit profile" (yours) vs "Follow".
  A red "Log in" at the top right means no session: skip.
- "Edit profile" opens a dialog: Profile photo (pencil), Username, Name ("can only be changed once
  every 7 days"), Bio (`n/80`), Save.
- Photo: `find` "file input for profile photo" → `file_upload` → "Edit photo" with a zoom slider →
  "Apply".
- Name: triple-click the Name box, `ctrl+a`, type. Do not touch Username: it changes the profile URL.
- Bio: the textbox "個人簡介 / Bio" under Name; Enter makes a line break; counter `n/80`.
- "Save" → dialog "Set nickname?" when the name changed → "Confirm". A toast "個人資料已更新 /
  Profile updated" confirms the save even while the page still shows the old text.
- Verify: the profile served the old photo and name once; it was right after a second reload with
  `?lang=zh-Hant-TW`.

## Pinterest

- Settings: `https://www.pinterest.com/settings/` → "Edit profile". Account check: the Name field and
  the avatar at the top right.
- Photo: "Change" → dialog "Change your picture" with "Choose photo" → `find` "file input for
  choosing a profile photo" → `file_upload`. It uploads and saves by itself (a spinner on the
  avatar); "Save" at the bottom stays grey.
- Name, About, Pronouns, Website, Username: edit, then "Save" at the bottom (tested for About: a
  three-line About saved and shows on the profile, line breaks as spaces). About is reported as 160
  characters by most sources and 500 by some; the page showed no counter.
- Verify: `https://www.pinterest.com/<username>/` shows the avatar beside the name and the About
  text under it; `get_page_text` reads it.
- Website: the field saves (shown as `http://...` afterwards) but the public profile showed no link
  right away; Pinterest shows it once the site is claimed or verified (not tried).

## Limits

| Site | Bio | Name | Seen how |
|---|---|---|---|
| Instagram | 150 | changes limited, two per 14 days reported | bio counter seen; name rule reported |
| Threads | 150 | follows Instagram? | reported |
| Facebook Page | 255 | Page name changes go to review | bio counter seen |
| YouTube | 1,000 (description) | twice in 14 days (shown under Name in Studio) | both seen |
| TikTok | 80 | once per 7 days | both seen on the page |
| Pinterest | 160 (some say 500) | | reported |

`scripts/prep.py` uses the lowest figure where sources disagree, so a bio that passes it fits everywhere.

## Wide pictures

| Picture | Size used | What each device shows | Seen |
|---|---|---|---|
| Facebook Page cover | 1640 x 624 | desktop shows all of it; phones crop the sides | desktop |
| YouTube banner | 2560 x 1440 (min 2048 x 1152, max 6 MB) | TV all; desktop the 2560 x 423 middle strip; every device the centre 1546 x 423 | Studio's crop dialog |

Handles across sites need not match: Pinterest and itch.io allow no dots, and YouTube can refuse a
handle whose URL is a 404. One brand ended up `csiesheep.games` on Instagram and Facebook and
`csiesheepgames` on YouTube.
