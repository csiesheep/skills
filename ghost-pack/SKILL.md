---
name: ghost-pack
description: Pack one finished ghost story for posting on the 鬼唱詩 accounts — give it its number in the ledger (「第 N 首」), stamp that number on the Instagram carousel cover and the Pinterest cover, and write every platform's caption from the brand file (Instagram, the Threads heading and link post, Pinterest titles and descriptions, YouTube title and description, TikTok, Facebook), then update the story's README. Use whenever the user wants to number a story, 拿號, 蓋號, 編號, 包裝, 寫文案, write captions or titles for a story, decide which story is next (第 N 首), move a story ahead of another, or get a story ready to post, even if they only say "準備發第 N 首" or "幫這篇寫文案". Not for writing the story (ghost-story), drawing the comic, carousel, pins, Threads picture or teasers (ghost-comic), the Reel full (ghost-reel), or posting (ghost-post).
---

# Ghost pack

The fourth of five skills (the plan is the Obsidian note `Projects/ghost story/ghost story pipeline.md`):

```
ghost-story, ghost-comic, ghost-reel   make the material, no number in it
ghost-pack                             numbers the story, stamps the covers, writes every caption   ← this skill
ghost-post                             checks platforms and files, posts, records links
```

Material is made without a number so it can wait in stock and the posting order can change. The number appears
only when a story is about to be posted, and only in captions, the Threads heading, the YouTube title, Pinterest
titles and the two cover strips; never inside a video (the owner decided on 2026-10-20).

## Run

```
py -X utf8 "<skill dir>/scripts/pack.py" <story folder> --brand-file C:/Users/sheep/Pictures/gui_chang_shi/brand/brand.json --logline "<one or two sentences>"
```

It reserves the number in the ledger (`scripts/ledger.py reserve`, by title: the same title asked again keeps its
number, so a rerun is safe), stamps the covers and writes the captions. What it touches, in the folder contract
(`C:/Users/sheep/Pictures/gui_chang_shi/README.md`):

| File | What happens |
|---|---|
| `posts/ig/01.jpg` | cover strip redrawn as 「鬼唱詩｜第 N 首」 with ghost-comic's own code, so it matches what `export --number N` draws; the unstamped original is kept as `01_nonumber.jpg` and every run stamps from it |
| `posts/pinterest/00_cover.jpg` | rebuilt from the stamped 01.jpg (`00_cover_nonumber.jpg` kept) |
| `posts/ig/caption.txt` | the brand's `caption` block |
| `posts/threads/hook.txt`, `attachment.txt` | first line becomes 「第 N 首｜title」 (the brand's `story.title`) |
| `posts/threads/link.txt` | the third Threads post, with an `{ig_link}` slot |
| `posts/pinterest/pins.txt` | board, a title (100 at most) and description per pin |
| `posts/cross_caption.txt` | the video's captions: Instagram Reel (the brand's teaser lines), YouTube title and description, TikTok, Facebook, with `{ig_link}` slots |
| `posts/cross_caption_<cut>.txt` | with `--cuts part1,part2`: the same per Reel cut, the cut's title (「（上）」「（下）」) and a 「下集待續」/「上集在主頁」 line; `--cuts-only` writes only these, for a story already posted elsewhere; `--ig-link` fills the slot when the carousel is out |
| `README.md` | heading 「第 N 首〈title〉」, status, the logline (later runs reuse it) |
| `brand/ledger.json` | the number, the title, the folder |

The Instagram post's link only exists once it is posted, so every caption that points to it carries `{ig_link}`;
ghost-post fills it after the Instagram post. That is the only edit left after packing.

## Before running

- **The material is there.** `posts/ig/` from ghost-comic `export --dest`, `posts/threads/hook.txt` and
  `attachment.txt` from ghost-story `post --dest`, `posts/pinterest/` from `export --pinterest`. Pack only adds the
  number and words; a missing file goes back to the skill that makes it.
- **Write the logline.** One or two sentences for Pinterest, YouTube, TikTok and Facebook: who, where, and the
  strange thing, the way 第 1 首's pins read 「大夜班護理師和十五床的阿嬤。阿嬤說：「妹妹，妳後面那三個是妳同事喔？」」.
  Never the reveal or the ending. Without `--logline` it takes the README's 「一句話」 or else the hook's first
  sentence, which is often too bare for a stranger scrolling Pinterest.
- **Which number.** Numbers are public and run across every story the account posts, so a gap or a repeat is the
  kind of mistake readers notice. Default is the ledger's next free number. To post a story ahead of one already
  numbered but not posted, give `--number`; the ledger refuses a number another story holds, and refuses to move a
  story that already has one: edit `ledger.json` by hand for that, with the owner's yes, then rerun pack for both.

## After running

Read the report it prints: the Threads hook must stay within 500 characters with the heading added (if not, rerun
ghost-story `post --dest` with a smaller `--limit`), Pinterest titles within 100. Look at `posts/ig/01.jpg`'s strip.
Then show the owner the captions and the stamped cover before ghost-post; nothing here is public yet, but the number
is now taken in the ledger.

To try it without touching the real ledger: `--ledger <a copy of ledger.json>` on a copy of the story folder.

## Brand file blocks

Words live in `brand.json`, not here. Pack reads `name`, `handle`, `disclosure`, `number`, `cover_strip`, `colors`,
`caption` (Instagram), `story.title` (Threads heading), `reel.tags` (video captions), and three blocks of its own:
`threads.link_post`, `pinterest` (`board`, `title_cover`, `title_page`, `lines`, `tags`) and `cross` (`title`,
`youtube_lines`, `tiktok_lines`, `facebook_lines`). Placeholders: `{name} {handle} {disclosure} {number} {title}
{logline} {ig_link}`, and `{k} {pages}` in a Pinterest page title. `scripts/pack.py` has defaults for the three
blocks, the ones 鬼唱詩 used for 第 1 and 2 首.

Needs Pillow and ghost-comic installed next to this skill (it draws the strip with ghost-comic's `manga.py`).
