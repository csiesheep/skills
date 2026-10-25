# 生在中國 Reel：發一支做好的（發文排程用）

Owner's standing instructions (2026-10-24): post the reels to Instagram, Facebook (the 小羊遊戲間 Page) and Threads as
csiesheep.games, pre-approved without reviewing each caption. Since 2026-10-25 the posting task only posts reels the
making task marked `待發` in C:/Users/sheep/Pictures/csiesheep_games/reels/china_life/ideas.md, oldest first. Files:
the row's folder, its captions.md (texts, upload file and cover), cards/card_<seed>_story.png if present.

Chrome is yours only 18:30–19:25 Taiwan time (the games reply run posts from 19:30). Read
~/.claude/skills/china_life_person_reel/references/posting.md for the per-site flow.

1. Post with Claude in Chrome (load tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate, computer, find,
   get_page_text, javascript_tool, browser_batch, file_upload, read_page in one ToolSearch). Record which account
   Instagram, Threads and Facebook are on first and leave each exactly as found (switch procedures:
   ~/.claude/skills/game-promote/references/accounts.md and posting.md). Check the handle on the page right before
   each post; if it is not csiesheep.games / the 小羊遊戲間 Page, do not post there and report it. Never type a
   password. Never click a button that opens the operating system's file picker; upload only through an existing
   input[type=file] with file_upload.
   - Instagram: Original crop, the cover, the caption, AI label OFF, Share; then the comment
     「玩一次你的古代人生 👉 games.csiesheep.com/china_life 玩完把你的分享卡貼上來 👇」. Instagram Stories cannot be
     posted from desktop Instagram; only if Meta Business Suite shows Instagram connected to the 小羊遊戲間 Page, also
     post card_<seed>_story.png as a Story there with a link sticker if the composer offers one and an input[type=file]
     exists; otherwise skip the Story and say so.
   - Facebook (as the Page): facebook.com/reels/create, the default first frame as cover, the caption with the link in
     its text, 新增 AI 標籤 OFF, 發佈; then the same comment with the full https link.
   - Threads: new thread with the video and the Threads caption with its link line removed (owner 2026-10-25: own Threads
     posts carry no link; the first self-reply does); after it is posted, reply to our own thread with 「這一生是遊戲裡真的跑出來的，你也投胎一次 👉 https://games.csiesheep.com/china_life/」.
   Confirm each post is visible and keep its link. If a platform shows a removal, warning or rate limit, stop posting
   there and report it. At 19:25 stop whatever is left and note it; the rest posts at the next 18:30.
2. Update ideas.md: 狀態 已發 with the folder and the links (or keep 待發 with 部分已發：<platforms> if the time ran out).
   Append the links to captions.md.
3. Report: the idea, the person/seed, the links, anything skipped and why, the accounts Chrome was left on. Send
   out/<name>_720p.mp4 with SendUserFile if available.
