"""Final choice of talking clip per line, after two rounds of frame review.
Lesson: 8-10 s H3 clips push in or grow things whatever the prompt says, and the word 三腳架 gets drawn. So a long line plays a stable 5-7 s clip of the same
speaker from the same still forward, then backward, and so on: every pass returns to the first frame, so there is no jump.
py -X utf8 make_talk3.py  (in film/reel) -> src/tk3_s45_L105.png, prompts/tk3_s45_L105.txt, talk3_args.txt, talk_final.json {line clip: {file, voice_s, pingpong}}"""
import json
import shutil

PLAN = json.load(open("talk_plan.json", encoding="utf8"))
PICKS = json.load(open("long_picks.json", encoding="utf8"))
RETAKEN = {"tk_s08_L017", "tk_s33_L086", "tk_s56_L086", "tk_s63_L136"}
BORROW = {"tk_s16_L042a": "tk_s16_L040", "tk_s23_L062a": "tk_s23_L059", "tk_s24_L069": "tk_s24_L067", "tk_s45_L105": "tk3_s45_L105"}
LOOK = ("水墨淡彩漫畫風格的角色動畫，畫面維持跟第一幀完全一樣的筆觸、色調、房間、家具、人物長相和衣服。"
        "鏡頭完全固定不動，不推近、不拉遠、不移動，人物在畫面中的大小從頭到尾不變，同一個鏡頭從頭到尾不切換。"
        "人物的腳一直在原地，身體只有很小的動作。畫面乾淨，沒有字幕、沒有對話框、沒有任何文字或符號。")
beat = "[0s-4s] 穿白袍戴眼鏡的老醫生正在講話，嘴巴連續清楚地一開一合。穿灰色連帽外套的年輕男生嘴巴一直閉著，安靜看著他。[4s-5s] 講完，嘴巴閉上。"
END = "\noverall_soundscape: 日光燈很輕的嗡嗡聲，衣服摩擦的聲音。\nnon_diegetic_music: N/A\n"
shutil.copy(PICKS["s45"], "src/tk3_s45_L105.png")
open("prompts/tk3_s45_L105.txt", "w", encoding="utf8").write(LOOK + "\n" + beat + END)
open("talk3_args.txt", "w", encoding="utf8").write("tk3_s45_L105:5:97")  # 95 cut inside the clip, 96 smaller mouth


def path(clip):
    seed = {"tk_": 93, "tk2": 94, "tk3": 97}[clip[:3]]
    return f"clips/{clip}_s{seed}.mp4"


final = {}
for p in PLAN:
    c = p["clip"]
    use = BORROW.get(c) or (c.replace("tk_", "tk2_", 1) if c in RETAKEN else c)
    final[c] = {"shot": p["shot"], "who": p["who"], "ids": p["ids"], "file": path(use), "voice_s": p["voice_s"], "pingpong": c in BORROW}
json.dump(final, open("talk_final.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(len(final), "lines;", sum(v["pingpong"] for v in final.values()), "ping-pong")
