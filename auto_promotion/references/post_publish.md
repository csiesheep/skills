# 發一篇 post pool 的貼文（Threads → Instagram → Facebook）

Posts come from `C:/Users/sheep/code/obsidian/Projects/auto promotion/posts/<#>.md` (written by the brand-post skill,
status 待發). Owner's approval (2026-10-25): post them at the fixed slots without asking per post. The first time
this was done by hand (post #1, 2026-10-25) these steps worked.

0. Lock: set the post's front matter `status: 發文中 <Taiwan time>` before touching Chrome. A post already 發文中
   within the last 2 hours belongs to another run: pick the next one. Never post a post twice on a platform: its
   「發文紀錄」 lists what is already done.
1. Load the Claude in Chrome tools in one ToolSearch (tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate,
   computer, find, get_page_text, javascript_tool, browser_batch, file_upload, read_page). One new tab; close it at
   the end. Never type a password; never click a button that opens the operating system's file picker (upload only
   through an existing input[type=file] with file_upload).
2. **Threads** (csiesheep.games): profile → 「What's new?」 opens the composer; check the composer shows
   csiesheep.games. Type part 1 (Return between lines), attach its image through the composer's file input. The
   composer may add a topic by itself (it once added 「Film Photography」): remove it and pick a fitting one
   (網頁遊戲, 遊戲, 歷史) from the suggestions. 「Add to thread」 for each next part: type, then upload its image to the
   NEWEST file input (find lists them in order). The last part is the link line. Before Post, check with JS that
   every part has its text and the right number of images. Post, wait until 「Posting…」 is gone (navigating away
   earlier shows a Leave-site dialog), then open the profile and take the newest post link.
3. **Instagram** (csiesheep.games; switch per ~/.claude/skills/game-promote/references/accounts.md and switch back
   at the end): Create → Post → the file input takes all cards at once (multiple) → crop icon → **Original** (the
   cards are 4:5) → Next → Next → caption (Return for line breaks) → leave Add AI label off → Share → wait for
   「Your post has been shared」. Link: newest /p/<code>/ on instagram.com/csiesheep.games/.
4. **Facebook**: avatar → 小羊遊戲間 (立即切換) → the Page composer 「小羊遊戲間，在想些什麼？」 → type the Facebook
   text (link inside) → its file input (multiple) takes all cards → check 新增 AI 標籤 is off and 貼文分享對象 is
   所有人 → 發佈. Switch back with avatar → 切換為<owner name> if Facebook was on the personal profile before. The
   permalink is hidden behind tracking parameters: record 「已發」 with the time; the Page's posts list has it.
5. Write each platform's link and time into the post's 「發文紀錄」 and set `status: 已發`. If a platform failed,
   keep the others, write the reason, and set `status: 待發` with 「部分已發：<platforms>」 so the next slot finishes it.
6. Any warning, removal, action block or rate limit: stop on that platform, write it in the post and the progress
   log as 警告.
