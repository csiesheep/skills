---
name: brand-post
description: Write one finished social post for the brand 小羊遊戲間 / csiesheep.games from a topic — a thread for Threads, a 4:5 carousel with caption for Instagram and a long post with album for the Facebook Page — in csiesheep's own voice (the csiesheep-perspective skill), with researched facts, images (game screenshots, engine numbers, locally generated art, rendered cards), and polished through judge rounds until it has a strong hook, concrete details and a story worth following; saved to the Obsidian post pool for the posting tasks. Use whenever the user or a scheduled task asks to write, draft or polish a post, 開發日記, dev note, 熱門遊戲介紹, a post about a popular game or one of our games, to fill the post pool, or gives a topic and wants Threads/IG/FB versions, even if they name only one platform. Not for replies under other people's posts (game-promote), ghost stories (ghost-*), reels (china_life_person_reel) or profile changes (social-profile).
---

# brand-post

One topic in, one post out: `C:/Users/sheep/code/obsidian/Projects/auto promotion/posts/<#>.md` plus its images in
`posts/<#>/`. Posting is done by the posting tasks (auto_promotion), not here, unless the user asks.

## Types

- **popular** — 熱門遊戲介紹: a game that is popular right now among Taiwan players (web or mobile, the last 30
  days: Threads/IG talk, app store charts, news). The post gives real value first (what it is, why people love it,
  one clever design detail, a tip), told through 小羊 playing it, then one short natural bridge to our games
  (「玩完這個，我做了……」 only where it truly connects). **Use plenty of the game's own images** (owner, 2026-10-25:
  「介紹熱門遊戲時，多用那遊戲的圖」): most cards and thread parts carry an official image of that game — its press kit /
  media kit, the official site, its App Store / Google Play screenshots, or the official trailer's frames. Download them
  into posts/<#>/src/ (the owner approved downloading official game images for these posts), keep them unedited apart
  from cropping and resizing, never remove watermarks or logos, and credit them on the card and in the text
  (「圖片來源：<遊戲名> 官方／<發行商>」). No fan art, no other creators' videos or screenshots, no leaked material, nothing
  that suggests a partnership. Our own game's images still go on the card that bridges to our game.
- **devnote** — 開發日記 of one of our games (生在中國 china_life, 蓋牌投票箱 covervote, 天地會 tiandihui, or a game
  in ~/code with a live page on games.csiesheep.com): one concrete thing from building it — a design decision, a bug,
  a number the engine produced, a player reaction, a tool (AI agents, ComfyUI) — with real details from the repo
  (git log, docs/design.md, the engine, the stats reports in Obsidian `Projects/games stats/`).

## Steps

1. **Pick the topic.** Given one, use it. For the pool: `py -X utf8 <skill>/scripts/pool.py status`; avoid any topic
   (same game + same angle) used in the last 30 posts (read their front matter `topic`).
2. **Research (no guessing).**
   - popular: WebSearch (and open the pages) for what the game is, who made it, platform, price, why it went viral,
     2–3 surprising facts; note every URL in Sources. If facts conflict or are thin, pick another game.
   - devnote: `git log --since=<30 days> --oneline` and the design doc in the game's repo; run the engine for numbers
     (china_life: ~/.claude/skills/china_life_person_reel/scripts/life.mjs); read the latest games stats report. Only
     real events; never invent a player, a quote or 小羊's feelings beyond what the owner has said in chat.
3. **Write as 小羊.** Load the csiesheep-perspective skill with the Skill tool and write in its voice (short lines,
   numbers, humble, 「有錯請指正 :p」 style, no marketing tone). Structure: hook → story with 3+ specific details → what
   the reader takes away → one natural line about our game → a question that invites replies + why to follow.
4. **Platform versions** (all in the post file, see the format below):
   - Threads: a thread of 4–7 parts, each ≤ 500 characters and one point; the main post has no link; the last part
     is the link line. One image per part where it helps.
   - Instagram: 5–7 carousel cards (1080×1350, `scripts/cards.py`), each one point in ≤ 2 lines; caption ≤ 600
     characters, ends with 「連結在主頁」 and 3–5 hashtags (no hashtag walls).
   - Facebook (Page): one long post with headings or emoji section markers, the link in the text, the same cards as
     an album.
5. **Images.** popular: the game's official images first (see Types), one per card where it fits, credited. devnote and the bridge card: our games' own screens (headless recordings: china_life
   record.mjs `cards` / `life`, or a Playwright/CDP screenshot of games.csiesheep.com with `?internal=1`), engine
   numbers drawn as a `big` card, era illustrations from the game's assets, new illustrations generated on the local
   ComfyUI (ink-wash or flat style, no real people, no other games' characters). Render the cards with
   `py -X utf8 <skill>/scripts/cards.py <spec.json>`; look at `contact.jpg` and fix anything clipped or unreadable.
6. **Polish (打磨).** Send a fresh subagent judge the three versions, the sources and `references/rubric.md`. Apply
   its edits that keep the facts true, re-score. Ready = every item ≥ 7 and average ≥ 8.0 (owner, 2026-10-25); at most 4 rounds, else mark
   the post 退回 with the notes. Record each round's scores in the file.
7. **Save** with status 待發 (or 退回). Report the id, title, type, scores and the contact sheet path.

## Post file format

```markdown
---
id: 12
type: devnote            # popular | devnote
game: china_life         # for devnote; the popular game's name for popular
topic: "生在中國：為什麼抽到清朝比秦朝多"
status: 待發              # 草稿 / 待發 / 發文中 / 已發 / 退回
created: 2026-10-25 14:10
score: 8.7
---
# <title>

## Threads
### 1
<text>
![[12/01.jpg]]
### 2
...
### 連結
玩一次你的古代人生 👉 https://games.csiesheep.com/china_life/

## Instagram
<caption>
卡片：![[12/01.jpg]] … ![[12/06.jpg]]

## Facebook
<long text with the link>
相簿：同 Instagram 卡片

## Sources
- <url or repo path> — what it supports

## 打磨紀錄
| 回合 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 平均 | 主要修改 |

## 發文紀錄
(filled by the posting task: time and link per platform)
```

## Rules

Brand accounts only post through the posting tasks or when the user asks. Facts need sources; 小羊's personal life
details only from what the owner wrote. No political stance (covervote stays neutral). Other games' images only from their official sources, credited (see Types). No AI-label toggles on IG/FB (owner's rule: the illustrations are not realistic); add 「圖為 AI 繪製」 when a
post uses generated illustrations.
