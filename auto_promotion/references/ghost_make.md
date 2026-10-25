# 鬼唱詩：做一支故事（製作排程用）

Owner's standing approval (2026-10-23, in their words): "Create a scheduled task to pick a ghost story from the list. If no idea in it, generate 10 ideas and append the list and then pick one idea. then generate the story, comic, reel, then post to platforms." Since 2026-10-25 (「執行」) making and posting are separate: this file is the making half. It uses no Chrome. It ends with the story packed and marked 待發; the posting task posts it at a fixed time.

Work in Traditional Chinese for all story content.

Root folder: C:/Users/sheep/Pictures/gui_chang_shi (folder contract in its README.md; brand file brand/brand.json; ledger brand/ledger.json). Skills (load each with the Skill tool when you reach its step and follow it): ghost-story, ghost-comic, ghost-reel, ghost-pack, ghost-post. Scripts run with `py -X utf8`.

## 0. Preconditions (stop early if one fails)
- Only one story at a time: if C:/Users/sheep/Pictures/gui_chang_shi/ideas.md has any row whose status starts with `寫作中` dated within the last 30 hours, another run is still making one: do not start a story.
- ComfyUI must answer at http://127.0.0.1:8188/system_stats. If it does not, start it in the background (run_in_background) from C:/Users/sheep/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI with:
  "C:/Users/sheep/code/ComfyUI/.venv/Scripts/python.exe" -s ComfyUI/main.py --base-directory C:/Users/sheep/code/ComfyUI --user-directory C:/Users/sheep/code/ComfyUI/user --database-url sqlite:///C:/Users/sheep/code/ComfyUI/user/comfyui.db --enable-manager --extra-model-paths-config "C:/Users/sheep/AppData/Roaming/Comfy Desktop/instance-model-paths/inst-1786312354964.yaml" --input-directory C:/Users/sheep/code/ComfyUI/input --output-directory C:/Users/sheep/code/ComfyUI/output --cuda-device 0 --port 8188
  and poll until it answers (up to 3 minutes). Never stop llama-server (GPU 1).
- Never `git add -A`, never commit or push anything.

## 1. Pick the idea
Open ideas.md. Take the first row whose status is `待寫`. If there is none, invent 10 new ideas in exactly the same table format (numbers continue; Taiwan settings, varied mechanisms, each with a one-line premise, a twist a first-time reader can retell in one line, and the single creepiest drawable panel; no real people, shops, temples or hospitals; not a retelling of a known story) and append them, then take the first new one. Set its status to `寫作中 <YYYY-MM-DD HH:mm>` and save immediately.

## 2. Story (ghost-story skill)
Use the idea as `--note` (premise + twist), `--ending 反轉`, count 3, default PTT style and 直接 taste. Follow the skill fully: three drafts, count/surface review, a fresh subagent judge with the rubric and pairwise, apply the winner's cheap fixes. Each draft must stay within 20% of its target length. Work in backlog/<english_short_name>/ (drafts/ from the start), deliver story.md, and run `ghost_plan.py post story.md --brand-file brand/brand.json --dest <folder>` (check the hook it picked; pass --hook when it picked setup; the hook post must stay ≤ 485 characters so the numbered heading still fits in 500).

## 3. Comic (ghost-comic skill)
The owner delegated every gate for these runs: pick the style, the designs and the layout yourself.
- Style: the black-and-white style A from stories/grey_jacket/comic/board.json (style_options.A) plus the strict-mono line, and `"mono": true` in the board. A good template for build_board.py is backlog/kids_prank/comic/build_board.py (helpers, lights, consistency, FOUR-boys style group handling, ME_NB-style variants of a look).
- 6–8 pages, about 25–30 panels. Mark the reveal panel `reveal: True`. Give the ghost a creepy, specific design and draw it clearly in at least one big panel before the reveal (the owner asked for creepier ghosts and jump-scare moments), plus a final panel that lingers.
- Run lint, sheets (pick the best of 3 per character/scene yourself), refs, plan (fix every lettering WARN), panels, then independent checker subagents per page with qa_checklist.md; pick only what passes; fix the rest by rewriting prompts, `repaint` for small areas, or hand edits (always blend; never leave a visible seam or square). Watch for: duplicated or missing people in group panels, characters copying another's look, a prop in two places, colour, drawn letters.
- Pages, then a blind reader (reader_check.md, read.md only) with twist retelling and 1–10 scores; fix every confusion (prefer lettering fixes), re-run pages, and a second fresh reader. At least one full polish round is required. Save each version under drafts/comic_v1, comic_v2…
- Export: `manga.py export --cover <the creepiest panel before the reveal> --pinterest --brand-file ../../../brand/brand.json --dest ..` from the comic folder. Look at posts/ig/01.jpg; if the title box covers a face, re-export with --no-cover-title.

## 4. Reel (ghost-reel skill)
draft.py, then rewrite reels/shots.json as a director: about 80–90 s (the owner preferred an 80 s cut that kept the comic's setup over a 65 s over-trimmed one, so never cut the setup for length), `"mono": true`, an 8-second hook block exactly as ghost-reel step 2 describes (A/B winner, 2026-10-24): a 0.5-s flash of a video-only ghost close-up, the strange concrete fact in big centred text with its sound, the narrator's frozen reaction with the line that makes it a threat, one line pointing back to the start; then the setup; no title card, subtitles in the story's words with 「／」, a real jump scare (a push-in with a setup line and a beat of silence, then a snap cut to the ghost with no subtitle, stinger alone, ~0.5 s black), the reveal, and a lingering ending with darken. Plan H3 clips (`clips.py plan/run`) for 4–5 scene panels and for most character panels too (the owner wants it to feel like anime: blinking, breathing, sweat sliding down, trembling, swallowing, shoulders shaking; follow ghost-reel's 'Character animation' note and its prompt header), about 10–12 moving shots in total; keep the jump-scare panel itself static. Rewrite every prompt, look at a contact sheet of every clip and drop any that drift to photographic, add colour, or invent lettering. Render, check the frames sheet and qc. Then one polish round: a fresh subagent as a short-form horror editor (frames sheet, shots.json, qc, story, pages; 1–10 score and ranked edits), apply the edits that keep the setup, render again, check again. Keep reel versions in drafts/reel_v1, reel_v2.

## 5. Pack (ghost-pack skill)
Move backlog/<name> to stories/<name>. Run pack.py with the brand file and a logline (who, where, the strange thing; never the reveal). It takes the ledger's next number. Run ghost-post's check_story.py with that number; fix whatever it reports (e.g. regenerate the Threads hook with a smaller --limit, then rerun pack).

## 6. Mark it ready
Set the idea's status in ideas.md to `待發 第 N 首 stories/<name> <YYYY-MM-DD HH:mm>` (the time it became ready). Do not post. If any step failed in a way you cannot fix, set `失敗 <date>: <one-line reason>`, leave all files in place, and never mark something 待發 that did not pass its checks.
