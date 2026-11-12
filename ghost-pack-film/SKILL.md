---
name: ghost-pack-film
description: Pack one finished realistic ghost video (made with ghost-film) for posting on the 鬼唱詩 accounts. It gives the video its own number in the film ledger, 「鬼唱詩劇場｜第 N 部」, which is separate from the comics' 「第 N 首」. It stamps that label on the film poster and on the Instagram part covers (（上）（下）). It writes every platform's caption from the brand file: the Instagram part captions, the full video's YouTube, TikTok and Facebook captions, Threads and Pinterest. It also lists the files to upload. Use whenever the user wants to number, 拿號, 包裝, 寫文案 or get ready to post a ghost-film video, a 寫實影片, a 鬼唱詩劇場 film or its IG two-part cut, even if they only say "準備發這支影片" or "幫影片寫文案". For comics, use ghost-pack. For making the video or the poster, use ghost-film. For posting, use ghost-post.
---

# Ghost pack film

The film line's version of ghost-pack. The owner decided on 2026-11-10 that realistic videos get their own series:
「a different serial number for realistic style video」, labelled 「鬼唱詩劇場｜第 N 部」. First was 〈社辦門上的氣窗〉 as
第 1 部. It has no comic number, although its comic exists.

```
ghost-story → ghost-film (stills, video, IG two-part cut, poster) → ghost-pack-film ← this skill → ghost-post
```

Like ghost-pack, the material is made without a number. The number goes only on the covers and in captions, never
inside the video. The label `第 N 部` uses 部 rather than 集 because a video posted on Instagram in two parts is
already 「上集」 and 「下集」.

## Run

```
py -X utf8 "<skill dir>/scripts/pack_film.py" <story folder> --brand-file C:/Users/sheep/Pictures/gui_chang_shi/brand/brand.json ^
    --cover <story>/film/reel/cover/<poster>.jpg --full <story>/film/reel/out/reel_vN/reel_vN.mp4 ^
    --parts <...>/reel_ig1/reel_ig1.mp4,<...>/reel_ig2/reel_ig2.mp4 --logline "<who, where, the strange thing>"
```

Pass Windows paths (`C:/...`). Git Bash rewrites only the first `/c/...` in a comma list, so a `/c/` second part
became `C:\c\Users\...` in the trial run.

| Writes | What |
|---|---|
| `brand/film_ledger.json` | number, title, `kind: film`, folder. ghost-pack's `ledger.py --ledger`; the same title keeps its number |
| `posts/film/cover.jpg` | the poster plus the label line under the brand line; the poster file itself is not changed |
| `posts/film/cover_part1.jpg`, `cover_part2.jpg` | the same with 「（上）」「（下）」, for the Instagram parts |
| `posts/film/caption_ig_part1.txt`, `_part2.txt` | heading, logline, 「下集在主頁，接著看。」 / 「上集在主頁。」 (both parts post the same day), disclosure, tags (`caption_ig.txt` without `--parts`) |
| `posts/film/caption_full.txt` | the full video: YouTube title and description, TikTok, Facebook |
| `posts/film/threads.txt`, `pins.txt` | Threads post with `{ig_link}`; Pinterest board 「鬼唱詩劇場｜台灣怪談短片」, cover pin and a video pin: the full cut if it is 300 s or less (Pinterest's limit), else IG part 1, else none |
| `posts/film/files.txt` | which file goes where, as absolute paths. The masters (~450 MB) are not copied |
| `posts/film/README.md` | heading, status, logline. The story's own README stays the comic's |

The words live in `brand.json`'s `film` block: `label`, `parts`, `title`, `part_lines`, `ig_lines`,
`youtube_lines`, `tiktok_lines`, `facebook_lines`, `threads_lines`, `pinterest`, `tags`. Placeholders are `{label}
{title} {heading} {logline} {disclosure} {handle} {ig_link} {part_line}`. To change wording, edit the brand file,
not the script.

## Before running

- **Inputs.** It needs the full master (1080×1920), the IG parts if the video runs over 3 minutes (Reels' limit; see
  ghost-film for the cut), and a film poster from ghost-film's `poster.py`. Long titles shrink to fit since
  2026-11-10. **No clear ghost and no spoiler on the poster** (owner, 2026-11-10: 「poster 不要有清楚的鬼，不能爆雷」).
  That means no reveal face and no twist line as the tagline. Use an early, ambiguous image, such as a head shadow
  in the dark glass or a silhouette knocking behind frosted glass, and a rule from the setup as the tagline
  (「沒聽到我的聲音，不要開門。」). Make two or three candidates and let the owner pick.
- **Logline.** Who, where and the strange thing, never the twist. Example: 「高二冬天，他每晚一個人在舊大樓三樓的吉他社練到
  十點。門上那片氣窗離地兩公尺半，裡面卻開始出現一顆頭的影子。」
- **Number.** The default is the film ledger's next free number. A story that also has a comic does not have to
  share anything with it. Pass `--number` only to reorder, and the ledger refuses a taken number.
- **Trial run.** To try it without touching the real ledger, run it on a copy of the story folder with
  `--ledger <copy>`.

## After running

- Read the report: the YouTube title must be within 100 characters and Threads within 500.
- Look at `cover.jpg` and one part cover.
- Show the owner the captions and covers before ghost-post. Nothing is public yet, but the number is taken.
- Posting is ghost-post's "Films" section: `check_film.py`, then one preview and one yes, then the posts, each recorded
  in the film ledger.
