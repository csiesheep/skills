# What the first two person reels taught (2026-10-23)

Reel 3「古代女生的一生」（高巧兒，seed 126937323 qing_mid F）and Reel 4「一生走了多遠？」（楊子明，seed 1194751197 yuan）,
in `C:/Users/sheep/Pictures/csiesheep_games/reels/china_life/3` and `/4`. Their `tools/build_plan.py` are the worked examples.

## The owner's corrections (apply from the first cut)

- **Too fast to read.** v1 of Reel 3 was 49 s and nobody could read the game's lines. v2 was 94 s: decision cards at real
  speed, then a 1.4–1.8 s hold after the tap; key log rows held 1.2–1.8 s. Reels may run up to 3 minutes on Instagram.
- **Zooming cut the game's text.** Never zoom the gameplay frame. Only the separately composited big map may be magnified.
- **Hard cuts between portrait cards and gameplay looked bad.** Every segment dissolves 0.5 s from the previous segment's
  last frame (`"dissolve": 0.5` at plan level).
- **Game sound effects too loud.** `sfx_gain_db` -14 (v1 had -6).
- **Portrait in the corner for childhood too**, and **every corner portrait the same size**: `INSET_SIZE = 0.62` (about
  223x279 px plus frame) in the bottom-right corner, including on decision cards, where it only touches the edge of the
  second option box.
- The owner liked: portrait cards per age, same face across ages, the map changing dynasty under the route.
- **Captions told the whole story.** The first captions listed every age down to the death; the owner wanted suspense
  on every platform (「所有文案都留懸念」). The Threads post had to be deleted and reposted (edit window 15 minutes);
  IG, YouTube and Facebook were edited in place. See posting.md.
- **Upload size.** Claude in Chrome's file_upload takes at most 10 MB; the 94 s 720p copy was 11.6 MB. `finish.py upload`
  makes a two-pass ≤ 9.5 MB copy.

## Gotchas

- **Engine city ≠ screen city.** The engine said 南陽 for 高巧兒; the game screen and share card said 開封 and 濟南府.
  Captions use what the recording shows (timeline.py prints the screen text).
- **`--mapshots` corrupts some screencast frames.** Clip screenshots leaked into the screencast: about 30% of frames came
  out 1080x640 or 360x640, and four 1080x1920 frames were map crops. render.py keeps only 1080x1920 frames
  (good_frames.json); after the first render, also drop isolated outliers (a frame far from both neighbours while the
  neighbours match) and rewrite good_frames.json. Only record with `--mapshots` when the reel needs the big map.
- **ACE-Step music has holes.** A 95 s request ended at 88 s with 5 s of silence at the start; a 70 s request had 8 s of
  silence in the middle. Always run `bed.py --check`, then build `music/bed.flac` with `bed.py --min <video length + 10>`.
- **Lives that cross several regions are rare.** In 45,000 pre-1945 lives, none had three moves; moves are mostly
  `flee_famine`. Lives born in late Qing reach the PRC famine years; the owner wants history kept away from modern
  politics, so prefer lives that end before 1949.
- **Qwen corner seals.** Several portraits had a small red seal in the bottom-left: `portraits.py clean` crops it.
- **The map changes with the dynasty.** In Reel 4 the base map switched from 元 to 明 at 洪武元年 (place names too:
  平江→蘇州, 大都→北平) with the route still drawn. Find the switch by the row 「…歸了明」 or by the mean colour of
  the map shots changing.
- **Stats must be the game's.** Reel 3's stats card came from 20,000 engine lives (明中期–清中期 women who reached 15:
  94.5% married, median age 17, 3.7 births, 42% of children died young, 82% of mothers lost a child, 41.7% widowed,
  about one girl in five bound). The card says 遊戲模擬，不是史料統計. A real-world figure such as a straight-line
  distance is fine when it is true and worded as such.
- **Foot binding and child deaths.** Show the game's own cards and lines; the portrait shows the girl with the cloth,
  not the feet. Captions stay plain.

## Timings that worked

| Piece | Seconds |
|---|---|
| Opening portrait card (fade in 0.4) | 2.4 |
| 戶帖 with the hook caption | 3.2–4.0 |
| Age portrait card | 1.8–2.0 |
| Decision card | real speed (3–4) + hold 1.4–1.8 |
| Key row | 2–3 + hold 1.2–1.8 |
| Decades fast-forward (ramp ×3) | 2.6–3.6 |
| End card (slow pull from 1.6x) | 3.4–3.6 |
| Stats card | 4.6–5.0 |
| Home page with URL | 2.8–3.0 |
