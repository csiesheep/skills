"""Third pass on the silent motion clips: the 8 shots pass 2 lost (s04 s14 s21 s26 s28 s38 s60 pushed in or changed the light, s44 failed when ComfyUI dropped the connection).
Uses the look line of the talking clips, which held the framing in 42 of 42 kept takes: figure size unchanged, feet in place. One small action, 5 s, seed 103.
Any clip that still fails becomes a still with a camera move in the render; no fourth pass.
py -X utf8 make_motion3.py  (in film/reel) -> src/mo3_*.png, prompts/mo3_*.txt, motion3_args.txt"""
import json
import shutil

P = json.load(open("long_picks.json", encoding="utf8"))
LOOK = ("水墨淡彩漫畫風格的角色動畫，畫面維持跟第一幀完全一樣的筆觸、色調、房間、家具、人物長相和衣服。"
        "鏡頭完全固定不動，不推近、不拉遠、不移動，人物在畫面中的大小從頭到尾不變，同一個鏡頭從頭到尾不切換。"
        "人物的腳一直在原地，身體只有很小的動作。畫面乾淨，沒有任何文字或符號。")
END = "\noverall_soundscape: 日光燈很輕的嗡嗡聲。\nnon_diegetic_music: N/A\n"
SHUT = "嘴巴一直閉著。"
A = {
    "s04": "年輕男生坐著，肩膀放鬆，輕輕點一下頭。" + SHUT,
    "s14": "年輕男生站著低頭看手機，拇指慢慢滑動。" + SHUT,
    "s21": "躺著的胖男生肚子緩緩起伏；遠處的女生站著。",
    "s26": "年輕男生站著，輕輕眨一下眼；灰貓耳朵轉一下。" + SHUT,
    "s28": "女生低頭站著；年輕男生的眼睛慢慢往下看。" + SHUT,
    "s38": "年輕男生站著，低頭看長椅，肩膀輕輕起伏。" + SHUT,
    "s44": "胖男生低著頭坐著，肩膀很慢地起伏。" + SHUT,
    "s60": "床上的人睡著，胸口緩緩起伏。",
}
args = []
for shot, act in A.items():
    name = f"mo3_{shot}"
    shutil.copy(P[shot], f"src/{name}.png")
    open(f"prompts/{name}.txt", "w", encoding="utf8").write(f"{LOOK}\n[0s-5s] {act}{END}")
    args.append(f"{name}:5:103")
open("motion3_args.txt", "w", encoding="utf8").write(" ".join(args))
print(len(args), "clips")
