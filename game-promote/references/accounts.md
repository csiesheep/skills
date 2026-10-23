# Posting as the brand from the user's Chrome

The user's Chrome holds two Instagram accounts (gui.chang.shi, csiesheep.games) and one Threads session at a time.
Both brands share the same Chrome, so the account must be switched before posting and put back after. Record the
state you found (which account Instagram and Threads were on) before touching anything, and leave both as you
found them. On 2026-10-22 Instagram was on gui.chang.shi one hour and on csiesheep.games the next because the user
switched in between: never assume, read it each time.

## Which account is signed in

- **Instagram**: on any page, the sidebar profile link is `/<handle>/`:
  `[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).filter(h=>/^\/[\w.]+\/$/.test(h)).slice(0,4)`
  lists `/reels/ /explore/ /<handle>/ …`.
- **Threads**: the first `a[href^="/@"]` on the home page is the signed-in handle. gui.chang.shi also has the
  custom feed 鬼故事 in the sidebar.

## Instagram: switch accounts (no password)

Sidebar **More** (`find` "More menu button in sidebar") → **Switch accounts** → click the account row → wait
6 s → reload the post and check the handle again. The dialog has a check mark on the current account; if the
brand already has it, press Escape.

## Threads: switch to the brand (no password)

Threads web has no account switcher. It signs in through whichever Instagram account is active:

1. Instagram first: switch Instagram to csiesheep.games (above).
2. Threads: the ☰ menu at the top left (about x 217, y 37) → **Log out**.
3. The login page shows **Continue with Instagram · csiesheep.games**: click it, wait 8 s. Once on 2026-10-22 it
   landed on a page-not-found; open `https://www.threads.com/` again and check the handle.
4. Post.
5. Put it back: ☰ → Log out → Instagram: switch back to the account Threads had before → `threads.com/login` →
   **Continue as <that account>** → check the handle → then switch Instagram to whatever it was at the start.

Never type a password. If the login page asks for one, stop and tell the user.

## Facebook Page

Not used for replies (a Page commenting under strangers' posts looks like an ad). If ever needed: the Page's
**立即切換**, act, then avatar menu → the personal profile, and confirm the toast 「已切換為 <名字>」.
