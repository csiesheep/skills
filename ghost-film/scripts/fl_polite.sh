#!/bin/bash
# fl2va one shot when the queue is empty: fl_polite.sh name chain first last prompt seconds seed
n=$1; chain=$2; first=$3; last=$4; prompt=$5; sec=$6; seed=$7
wait_empty() { while true; do c=$(curl -s 127.0.0.1:8188/queue | py -X utf8 -c "import json,sys;d=json.load(sys.stdin);print(len(d['queue_running'])+len(d['queue_pending']))" 2>/dev/null); [ "$c" = "0" ] && return; sleep 1; done; }
wait_empty
t0=$(date +%s)
py -X utf8 "$HOME/.claude/skills/ghost-film/scripts/fl2va.py" $chain $first $last $prompt $sec $seed
sleep 5; wait_empty; sleep 5; wait_empty
f=$(ls -t /c/Users/sheep/code/ComfyUI/output/minimax_h3_t8_long_video/$chain/assembled/*.mp4 2>/dev/null | head -1)
[ -z "$f" ] && f=$(ls -t /c/Users/sheep/code/ComfyUI/output/ghost_film/${chain}*.mp4 2>/dev/null | head -1)
[ -n "$f" ] && cp "$f" clips/${n}.mp4
echo "$n $(( $(date +%s) - t0 ))s ${f:-NOFILE}"
