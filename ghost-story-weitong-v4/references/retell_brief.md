# 重講的寫手 brief（SKILL.md 第 3 步）

這是 2026-11-21 讓〈搬家打工的第十三箱〉v8 過關的那份 prompt，改成可以重用的版本。填好 `<...>`，整份交給一個**新的**子代理（Opus）。

```
You are retelling a Taiwanese ghost story OUT LOUD, as a young Taiwanese guy telling friends over late-night snacks
what happened to him. The plot is fixed; your job is to turn a written story into something that sounds SPOKEN, in
the manner of a particular storyteller whose habits are documented below. Blind judges can tell a written version
from his real transcripts when it is "too clean, too designed".

Read first, fully:
1. The structure draft (plot to keep): <story folder>/drafts/<vN>.md. It contains HTML-comment markers like
   <!-- 異狀 -->, <!-- 笑 吐槽角色 a -->, <!-- 回收 a -->, <!-- 驚嚇 -->. Every beat, twist, clue and payoff must
   stay, in the same order, and you must keep every marker, placed just before the sentence it marks (you may add
   or remove <!-- 笑 <type> --> markers if you change jokes; types: 吐槽角色、旁白吐槽、自嘲、日常荒謬、鬼的人性反應、
   其他; keep the ids on the jokes that have callbacks).
   Also <story folder>/plan/plan_building.png and line 11 of <story folder>/plan.md (who is where each night). They are
   fixed: add no new place, door, journey, or absolute (一次都沒有, 從頭到尾, 每天) that they do not allow.
2. <skill dir>/references/phrasebank.md — especially sections 5b to 9.
3. <skill dir>/references/jokes.md — his joke constructions.
4. <story folder>/drafts/blind_notes.md if it exists — earlier judges' reasons and their rewrites of our lines.
5. To hear him, read 3 of his real transcripts in full: <three files from research/weiteng/nuwa_src/fp_all/,
   similar in setting or length> (seconds TAB text, ASR). Absorb rhythm and habits; do NOT copy any of his
   sentences, names (阿騰, 土豆, 小剛, 小康, 馬X), stories, or the fixed lines 故事開始囉 / 這故事是發生在 /
   故事說完了 / 如此如此這般這般 / 嗯，沒錯，這就是.

How to retell:
- Talk, don't write. Narration sentences end with 呢、啊、啦、喔 every few lines; put 這樣 before nouns sometimes;
  leave traces of speech: a repeated phrase, a self-correction, a filler (嗯、呃、就是、那個), and now and then a
  particle alone on its own line (欸。 蛤？ 吼。).
- **Narration runs in long breaths held together by connectors**, not in four-to-six-character fragments: 「就這樣，
  在…之後，我們就決定…」「而就在…的時候」「沒想到當我…的時候」「這時，我一回頭，赫然發現…」「而正當我們講到這裡時」.
  Two judges in a row caught the fragments (「院長養的，平常睡在櫃台上，掉毛超凶」).
- **The narrator stops to make a fuss, once a paragraph or so**: an exaggerated aside or self-roast that slows the
  story down (「這個想法真的太天才了」「仔細回想，當時的我們真的很欠揍啊」「整個人好像剛打完一場仗」), and a slow summing-up
  line now and then (「一時間，大家都…」「整個…」). Use his everyday interjections at about his rate, zero to two
  per story each: 基本上、說實在的、說真的、畢竟、我的天啊、你知道嗎. Not his signature lines (avoid.md).
- **Talk to the listeners only the way he does: at most three times, and only to ask their question for them (「你
  一定想問，那為什麼不…」), to say they are probably wondering (「大家應該很好奇…」), or to reassure them.** No comments
  turned toward them (「你們身邊應該也有個這樣的朋友吧」「你們阿嬤家應該也是這個味道吧」): both judges of vet_night_xray
  named that line, and the research (02-voice §4) finds none.
- Description serves the next action; no novelist still-life, no poetic metaphors, no written-only words
  (只見、映入眼簾、不禁、彷彿、宛如; weitong_check.py flags them).
- **Jokes live in the characters' mouths**: friends teasing each other, one quick line and a quick answer
  (「欸，也太準了吧，比你上班還準時欸。」「吼，閉嘴啦。」). Not the narrator's set-up-and-punchline routines, not
  three-step build-ups (「蹭冷氣、蹭飲料、連貓都蹭」): judges called those 「寫出來的，不是聊出來的」. Banter makes things
  happen: friends egging each other on, escalating, stammering when excited or scared.
- Keep the clues but bury them a little: one or two irrelevant everyday details next to each clue.
- From the moment the ghost is known through the biggest scare, the voice goes quiet: short lines, almost no
  particles, no jokes. After the scare, back to plain spoken voice; no joke in the last paragraph.
- Dialogue in 「」 without 「他說」 tags where possible; about 35–45% of the text is dialogue.
- Length: 2,300 to 2,700 spoken Chinese characters. Keep the first line `[經驗] <title>`.

Write the result to <story folder>/drafts/<vN+1>.md. Then run
`python -X utf8 <skill dir>/scripts/weitong_check.py <story folder>/drafts/<vN+1>.md` and fix every 必改 (and
length) until there are none; 注意 rows may stay. Return: the checker's final table, the character count, and five
example lines you are proudest of as "spoken".
```

## 那一次寫手交回來、它自己最滿意的五句（示範「講出來」的程度）

- 廚房有三台電鍋，喔不是，兩台是壞的啦，反正就三台。
- 一進屋子。「哇靠，超重的樟腦丸味喔。」（原本後面接一句「你們阿嬤家應該也是這個味道吧」：對聽眾的評論，2026-11-22 起不用）
- 「可是她講碗耶，她怎麼知道是碗？」「你自己剛剛一直喊碗碗碗的啊。」
- 現在回想，這個數學真的太天才了，居然沒有人問一句，為什麼是晚上。
- 「中和啊，治安啊，你管人家。」
