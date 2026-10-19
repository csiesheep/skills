# Per-site flows

What worked on 2026-10-18 in Chrome on Windows, with the Claude in Chrome tools, for one brand (鬼唱詩)
on six sites. Labels are given in English and Traditional Chinese because the user's sites run in
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

## Facebook Page

- Page: `https://www.facebook.com/<page username or profile.php?id=...>`
- Account check and switch: as the personal profile, the Page shows a banner "Switch into <Page> to
  manage it / 切換為…的粉絲專頁並開始管理" with "Switch now / 立即切換". Click it; a dialog "Switch
  profile / 切換個人檔案" asks again: "Switch / 切換". Reload the Page; the top-right avatar is now the
  Page's and the buttons read "Creator dashboard / 創作者主控板", "Edit / 編輯".
- Photo: click the profile picture → menu item "Choose profile picture / 選擇大頭貼照" → dialog with
  "Upload photo / 上傳相片" and "Add frame / 加上特效框". The file input exists once that dialog is
  open: `find` "file input inside the choose profile picture dialog" → `file_upload` → a crop dialog
  with a caption box and a zoom slider → "Save / 儲存". There was no toggle for sharing to the feed.
- Bio (Intro): "Edit / 編輯" on the Page (**untested**). Limits reported between 101 and 255; trust the
  page's counter.
- Switch back: top-right avatar → the list shows the Page, the personal profile and any other Pages
  → click the personal profile. Check the top-right avatar is the personal one again.
- Page username, if the long `profile.php?id=` URL bothers the user: Settings & privacy → Settings
  → Page setup → Name → Username "Edit" (中文：設定和隱私 → 設定 → 粉絲專頁設定 → 名稱 → 用戶名稱
  的編輯). A new Page may not be eligible for a few days; that is Facebook's rule, not a mistake.
- Never put the personal profile's address or phone on the Page: a new Page once showed both in its
  public About until they were deleted (About → Contact and basic info / 關於 → 聯絡資料和基本資料).

## YouTube

- Studio: `https://studio.youtube.com/`. Account check: top left reads "Your channel" and the
  channel name. A different channel means a different Google account is active in Chrome; stop and
  ask, switching Google accounts is the user's business.
- Customization: `https://studio.youtube.com/channel/<channel id>/editing/images` (the id is in the
  Studio URL; it redirects to `.../editing/profile`). Sections: Banner image, Picture, then name,
  handle and description further down (**untested**).
- Picture: `find` "file input in the Picture section" → `file_upload` the 800 x 800 version → dialog
  "Customize picture" with the full square selected → "Done" → "Publish" at the top right (toast
  "Changes published"). Nothing is live until Publish.
- Description limit 1,000; the first ~150 characters show in search.
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
- "Save" → dialog "Set nickname?" when the name changed → "Confirm".
- Verify: the profile served the old photo and name once; it was right after a second reload with
  `?lang=zh-Hant-TW`.

## Pinterest

- Settings: `https://www.pinterest.com/settings/` → "Edit profile". Account check: the Name field and
  the avatar at the top right.
- Photo: "Change" → dialog "Change your picture" with "Choose photo" → `find` "file input for
  choosing a profile photo" → `file_upload`. It uploads and saves by itself (a spinner on the
  avatar); "Save" at the bottom stays grey.
- Name, About, Pronouns, Website, Username: edit, then "Save" at the bottom (**untested** in that
  run except Username, which the user changed themselves). About is reported as 160 characters by
  most sources and 500 by some; trust the counter.
- Verify: `https://www.pinterest.com/<username>/` shows the avatar beside the name.

## Limits

| Site | Bio | Name | Seen how |
|---|---|---|---|
| Instagram | 150 | changes limited, two per 14 days reported | bio counter seen; name rule reported |
| Threads | 150 | follows Instagram? | reported |
| Facebook Page | 101 to 255 by source | Page name changes go to review | reported |
| YouTube | 1,000 (description) | changes limited | reported |
| TikTok | 80 | once per 7 days | both seen on the page |
| Pinterest | 160 (some say 500) | | reported |

`scripts/prep.py` uses the lowest figure where sources disagree, so a bio that passes it fits everywhere.
