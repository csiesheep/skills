# 生在中國分享卡：做卡（製作排程用）

The owner approved on 2026-10-24 two Threads share-card posts a day, Claude picking the cards, and on 2026-10-25 asked
for **special people** on the cards (「分享卡選擇比較特別的人物」). This file makes cards and their texts; the posting task
posts them at 08:30 and 17:30 Taiwan time. No Chrome (record.mjs uses its own headless browser).

Log and queue: C:/Users/sheep/Pictures/csiesheep_games/threads_posts/cards/log.md. Rows with 狀態 `待發` are the queue.

1. Read the log. Never reuse a seed; avoid the period + sex + status combinations of the last 20 rows.
2. Find special lives, not ordinary ones. For each card, scan one period with the engine:
   node ~/.claude/skills/china_life_person_reel/scripts/life.mjs scan --periods <id> [--sex F|M] [--status <s>] --n 10000 --top 20
   and life.mjs show <seed> <period> [sex] [status] for the candidates. Special means rare in that period's 10,000
   lives, e.g.: a farmer's or craftsman's child who passed the exams or became an official; a woman who refused foot
   binding, or ran the household after being widowed young; someone who moved three or more times across the map;
   someone who lived through a dynasty falling or two famines and still reached old age; lived past 95, or died
   young after one striking turn; a 賤籍 or 僧道 life; an unusual death cause; a rich family that lost everything, or the
   reverse. Prefer the one-in-a-thousand over the merely eventful. Rotate eras from 戰國 to 民國 (life.mjs periods);
   never prc_* or post2000, no modern politics. Alternate women and men. Plain and respectful about death, famine
   and war.
3. Save the cards: node ~/.claude/skills/china_life_person_reel/scripts/record.mjs cards
   C:/Users/sheep/Pictures/csiesheep_games/threads_posts/cards/q_<YYYYMMDD-HHmm>_<seed> <seed> --extra
   "&period=<id>[&sex=F|M][&status=<status>]". Open card_<seed>_post.png (1080×1350) and look at it: name, era, place
   and the red hook line readable, nothing clipped. If the card looks wrong or the special turn is not on it, pick
   another life.
4. Write the Threads text into text.txt in that folder (at most 300 characters, Traditional Chinese, at most one emoji,
   no hashtag lists): one hook line built from the card's own facts that says why this life is rare (e.g. 「一萬個清朝人
   裡，只有 3 個像他這樣……」 only when the scan gives that number), one line that invites replies (「換作是你，會怎麼
   選？」), then 「你也投胎一次 👉 https://games.csiesheep.com/china_life/」. Facts only from the card and the engine.
5. Append a row to the 待發清單 table at the end of log.md: 做好時間, 狀態 待發, seed, period, sex, status, why special (one
   line), the hook line, the folder (發文時間 and 連結 empty). Make cards until there are 2 待發 rows.
