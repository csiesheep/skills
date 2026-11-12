#!/bin/bash
# H3 image-to-video clips, one after another, from <story>/film/reel: src/<name>.png + prompts/<name>.txt -> clips/<name>_s<seed>.mp4
# usage: run_clips.sh name:seconds:seed ...   (an existing clip is skipped; run it in the background, about 3-4 min a clip)
# Run ONE of these at a time: two loops on the same names submit the same jobs twice.
for spec in "$@"; do
  IFS=: read n s seed <<< "$spec"
  [ -f clips/${n}_s${seed}.mp4 ] && continue
  mkdir -p clips
  py -X utf8 "$HOME/.claude/skills/h3-image-to-video/h3_i2v.py" --image src/$n.png --prompt-file prompts/$n.txt \
     --seconds $s --seed $seed --out-dir clips --prefix ${n}_s${seed} > clips/${n}_s${seed}.log 2>&1
  f=$(ls -t clips/${n}_s${seed}*.mp4 2>/dev/null | head -1); [ -n "$f" ] && [ "$f" != "clips/${n}_s${seed}.mp4" ] && mv "$f" clips/${n}_s${seed}.mp4
  echo "$n done $(date +%T)"
done
