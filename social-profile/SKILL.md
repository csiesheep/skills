---
name: social-profile
description: Update the profile photo, display name, bio, Facebook Page cover photo, YouTube banner and channel links of the user's own accounts on Instagram, Threads, a Facebook Page, YouTube, TikTok and Pinterest, in the user's real Chrome (Claude in Chrome) where they are already signed in. Prepares the image sizes (avatar, 1640x624 cover, 2560x1440 banner) and checks every bio against each site's length limit first, checks that each site shows the right account before touching it, uploads through the page's file input, saves, reloads the public profile to confirm, switches a Facebook Page back to the personal profile, and reports a table. Use whenever the user asks to change, update or sync an avatar, profile picture, 大頭照, 大頭貼, 頭像, display name, 顯示名稱, 暱稱, bio, 簡介, 個人資料, 封面相片, cover photo, YouTube banner, 橫幅, channel links or a Page's public contact info on one or more of these sites, says "make all my accounts match", "換掉所有平台的頭像", "把簡介貼上去", "把頻道補齊", or has just made a new logo or avatar for a brand account, even if they name only one site. Not for creating accounts, logging in, posting content, or accounts the user does not own.
---

# Social profile

Puts one picture and a set of texts on several social accounts the user owns, through their own
Chrome. Every site's edit page is different and changes often; `references/platforms.md` has the
exact flow per site as it worked on 2026-10-18 (鬼唱詩, six sites, one sitting) and 2026-10-21/22
(小羊遊戲間: a second brand in the same Chrome, Facebook cover, YouTube banner and links), with the
traps met on the way. Read the section for each site before driving it.

## Before anything: what may and may not be done

- **The user asks, per site.** A profile change is an account-settings change on a public account.
  Do the sites and fields the user named; if they said "all", list the sites and fields you are
  about to change in one message and go. Anything they did not mention (a username, a link, the
  "AI-generated profile" toggle, privacy) stays as it is.
- **Never sign in.** No passwords typed, no "Continue with Google / Apple" for a site that is not
  signed in. A site that shows a login wall is skipped and goes in the report as "not signed in";
  the user signs in and asks again. One exception that needs no credentials: Threads offers
  "Continue as <account>" from the Instagram session already in Chrome. Use it only when the
  account shown is the target and the user asked for Threads.
- **Check the account before every change.** Chrome is the user's own browser: the personal
  Facebook, a personal Google account or someone else's TikTok may be the one signed in. Read the
  handle or channel name on the edit page and compare it with the target; a "Follow" button on the
  target's own profile means you are not it. Wrong account: stop on that site.
- **Leave Chrome as you found it.** Work in a new tab, close it at the end, and switch Facebook back
  to the personal profile after acting as the Page. Otherwise the user's next Facebook comment goes
  out as the brand. If Facebook was already acting as the Page when you arrived (the user switched
  earlier), leave it so, and say in the report that Chrome's Facebook is still the Page.
- **Several brands in one Chrome: each site has its own active account.** Signing Instagram in
  to brand B did not move Threads web off brand A, and opening `studio.youtube.com` opened brand
  A's channel (and made it YouTube's active account) while `youtube.com` had been on brand B.
  Switching between accounts that are already signed in, through the site's own menu, needs no
  password and is allowed when the target is listed there: Facebook's profile switcher, YouTube's
  avatar → Switch account. Say in the report which account each site is left on. Threads web has
  only "Log out", no switcher; logging out is fine only because its login page then offers
  "Continue with Instagram · <the account Instagram is on>" with no password (used on 2026-10-22,
  see game-promote references/accounts.md): switch Instagram first, then log out of Threads and
  continue. If the login page asks for a password instead, stop and ask the user.
- **A YouTube channel on a Google account that has none** may be created when the user asks for
  it by name and handle (youtube.com/account → Create a channel): it is a profile on an account
  already signed in, not a new account. Any other new account (Threads profile, TikTok, Pinterest,
  a Facebook Page) is the user's to create.

## Steps

1. **Collect the inputs.** One square picture (PNG, 1024 px or more), and per site: the handle (to
   check the account), the display name if it should change, the bio if it should change. Texts
   often already exist in the user's notes (a brand note with bio templates); use those verbatim
   rather than rewriting. Write them into a profile file like `assets/example_profile.json`.
   Optional wide pictures: `facebook.cover` (1640 x 624) and `youtube.banner` (2560 x 1440, with
   the text and face inside the centre 1546 x 423 that every device shows), and `youtube.links`
   (title and URL pairs). If the user already edited a profile by hand since the texts were
   written, read the live profile first and use their wording, not the older draft.
2. **Prepare.** `py -X utf8 "<skill dir>/scripts/prep.py" profile.json` makes `avatar_1024.png` and
   `avatar_800.png` (YouTube wants 800 x 800, under 4 MB) next to the profile file, warns when the
   picture has content in the corners (every site crops it to a circle), counts each bio the way
   the sites count (Instagram showed 65/150 for a four-line bio of 62 characters plus 3 line
   breaks), and prints the per-site limits and name-change cooldowns. With a cover or banner it
   writes `cover_1640x624.png` / `banner_2560x1440.png`, cropped to the right shape from the
   centre, and says how much was cut. Fix anything over a limit before opening a browser, and look
   at the cropped wide pictures: a crop from the centre can cut the top of a head.
3. **Open Chrome.** Load the Chrome tools in one ToolSearch call: tabs_context_mcp, tabs_create_mcp,
   tabs_close_mcp, navigate, computer, find, read_page, get_page_text, file_upload, browser_batch.
   Call tabs_context_mcp, then work in one new tab.
4. **Each site, in turn** (platforms.md has URLs and labels in English and 中文):
   1. Open its edit page; check the account (above).
   2. Photo: find the `type=file` input with `find` ("file input for profile photo") and give it the
      picture with `file_upload`. Do not click "Upload", "Change photo" or "Choose photo" buttons:
      they open the operating system's file picker, which the extension cannot see and which
      blocks the tab. Some sites need a menu opened first so the input exists (Facebook). A crop
      dialog may follow: keep the default full square and press its Apply / Done / Save.
   3. Text: click the field, `ctrl+a`, Delete, type. For a multi-line bio, type each line and press
      the Enter key between lines (it made a line break on all six sites). Put the Chinese into the
      type action as the characters themselves, copied from profile.json, never as hand-written
      `\u` escapes: one wrong escape turned 王士禎 into 王士秎 in a classical quote, which a glance
      does not catch. Zoom on the field and compare the page's own counter with prep.py's count
      before saving; a mismatch means a stray or missing character.
   4. Save, and answer the site's confirmation (TikTok asks before a nickname change because it
      locks the name for 7 days; say yes only if the user asked for that name).
   5. Verify: reload the public profile and zoom on the header. TikTok served the old picture and
      name from cache for about 10 seconds; reload once more with `?lang=zh-Hant-TW` added before
      calling it failed.
   Batch the predictable clicks of a site with browser_batch; take a screenshot before any click by
   coordinate.
5. **Clean up.** Facebook back to the personal profile, close every tab you opened.
6. **Report** as a table, one row per site: what changed, how it was confirmed, or why it was
   skipped. Then mention side effects the user may not expect: a Facebook Page photo or cover change
   puts an "updated their profile picture / cover photo" post on the Page; a name change starts the
   site's cooldown; a site left on a different account than before. Also mention any personal
   contact detail you saw in public (a new Facebook Page listed the owner's mobile number and
   personal Gmail under Contact info); remove it only when the user says so. If the user keeps a
   checklist for these accounts, tick it.

## Facts that cost a retry the first time

- Threads keeps its own picture and bio. Changing them on Instagram did not change Threads, even
  though Threads was created from the Instagram account.
- Instagram on the web edits photo and bio, not the name (Accounts Center) and not links (app only).
- A Facebook Page photo can only be changed while acting as the Page: "Switch now / 立即切換", then
  confirm "切換" in a dialog.
- YouTube Studio shows "Your channel <name>" at the top left; that is the account check. Changes
  stay in draft until "Publish". Reach a brand's Studio from its channel page ("Customize
  channel", which opens Studio in a new tab), not from `studio.youtube.com`, which opens whichever
  Google account Studio defaults to.
- A handle free by its public URL (404 / "page not found") may still be refused when you claim it:
  YouTube refused `@csiesheep.games` that way. Pinterest and itch.io take no dots at all. Check
  the alternatives in the site's own handle field (a green tick) and let the user pick.
- A Facebook Page switch did not stick once: the next page load showed the personal profile
  again. Check the top-right avatar after switching, and switch again if needed.
- Pinterest saves the photo as soon as it uploads; the text fields need "Save" at the bottom.
- TikTok's public page is cached briefly after a save.
- File paths given to `file_upload` must be absolute and readable by this session.
