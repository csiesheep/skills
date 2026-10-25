# 生在中國 Reel：做一支（製作排程用）

Owner's standing instructions (2026-10-24): pick an idea from the list, make the reel, post it to Instagram, Facebook
(the 小羊遊戲間 Page) and Threads, pre-approved without reviewing each caption. Since 2026-10-25 (「執行」) making and
posting are separate: this file is the making half. It uses no Chrome (the headless Chrome of record.mjs is a separate
browser and is fine). It ends with the reel marked 待發; the posting task posts it at 18:30 Taiwan time.

Read first: ~/.claude/skills/china_life_person_reel/SKILL.md and its references/lessons.md and references/posting.md
(pipeline, the owner's corrections). The idea list is C:/Users/sheep/Pictures/csiesheep_games/reels/china_life/ideas.md.
Reels live in C:/Users/sheep/Pictures/csiesheep_games/reels/china_life/<N>/ (next free number). Worked examples:
reels/china_life/3 (古代女生的一生, build_plan_v3.py) and reels/china_life/4 (一生走了多遠, build_plan_v2.py).

1. Lock. If ideas.md has a row marked 製作中 with a start time less than 10 hours ago, another run is making one: do
   not start. If one is 製作中 and older than 10 hours, mark it 跳過（上次中斷，<date>） and continue.
2. Pick. Take the first row whose 狀態 is 待做. Skip (and mark 跳過 with the reason) an idea that cannot be done now,
   e.g. #8 needs a viewer's comment naming a dynasty and none exists yet. If no 待做 row is left, write 10 new ideas
   into the table first (same columns; each with a cold-open first line; based on what the game can show: decisions,
   family, migration, famine, exams, dynasties changing, share cards, engine statistics; nothing about modern politics
   or post-1949 events; plain and respectful about death, foot binding, famine and war), then take the first new one.
   Mark it 製作中 with the start time and the reel folder.
3. Make the reel with the china_life_person_reel pipeline, adapting it to the idea (some ideas follow several lives or
   compare two). Rules from the owner, all mandatory: cold open (frame one is the strongest turn with a big line, then
   two or three turns at 0.8 s with hard cuts; no fade from black, no setup first); no zoom on gameplay; decisions at
   real speed with a 1.3–1.6 s hold; 0.5 s dissolves elsewhere; portrait cards per age and the same-size bottom-right
   portrait (ComfyUI ink-wash portraits via portraits.py) when the idea follows a person; sfx -14 dB; music bed via
   ACE-Step + bed.py; numbers only from engine runs, labelled 遊戲模擬; captions and on-screen place names as the game
   screen shows them. Aim for 60–80 s. Check a preview contact sheet before the final render; fix anything clipped or
   stray. Then finish.py final and finish.py upload (≤ 9.5 MB for posting) and a cover with cards.py. Also save the
   main person's share cards: node ~/.claude/skills/china_life_person_reel/scripts/record.mjs cards <reel>/cards <seed>
   --extra "&period=<id>[&sex=F]".
4. Captions: write <reel>/captions.md for Instagram, Facebook and Threads. Every caption leaves suspense: the hook, the
   person and the first one or two turns, then a question like 「他後來怎麼了？影片看到最後」, the link
   https://games.csiesheep.com/china_life/ in the body text (Facebook too, not only in a comment), 「肖像為 AI 繪製」
   when there are portraits, 「數字為遊戲模擬」 when there are numbers; never the ending or how long anyone lived.
   Threads at most 500 characters.
5. Mark it ready: 狀態 `待發 <YYYY-MM-DD HH:mm>` with the folder, and in captions.md a line `上傳檔：out/<name>_upload.mp4，
   封面：out/<name>_cover.jpg`. If something failed that you cannot fix, mark 跳過 with the reason; never mark 待發 a reel
   that did not pass its checks.
