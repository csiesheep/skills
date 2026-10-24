"""錄影的時間軸：剪輯計畫要的每個秒數都從這裡抄（時間從 rec_start 起算，與 render.py 一致）。

    py -X utf8 timeline.py <reel>/rec/life [--ages 0,3,6,15,17,27,30,50,70] [--all]

印出：戶帖（card_ready、begin 的點擊）、每個年紀開始的秒數、抉擇卡出現（decision）與點下去（tap）、
紀錄裡的 choice／family／move／event／payoff／dying／death 列（遊戲畫面上的原文，字幕與地名照這裡寫）、ending。
--all 連 daily 日常句也印（找「纏過的腳一碰到濕地就痛」這種好句子用）。
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("--ages", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    d = Path(a.rec)
    ev = json.loads((d / "events.json").read_text(encoding="utf-8"))
    fr = json.loads((d / "frames.json").read_text(encoding="utf-8"))
    t0 = next(e["t"] for e in ev if e["type"] == "rec_start")
    ages = set(a.ages.split(",")) if a.ages else None
    print(f"frames {len(fr)}  錄影 {fr[-1]['t'] - t0:.1f} 秒")
    if (d / "mapshots.json").exists():
        ms = json.loads((d / "mapshots.json").read_text(encoding="utf-8"))
        print(f"mapshots {len(ms)}（大地圖可用）")
    kinds = {"choice", "family", "move", "event", "payoff", "dying", "death"}
    for e in ev:
        t = f"{e['t'] - t0:7.1f}"
        if e["type"] in ("card_ready", "decision", "ending"):
            print(t, e["type"].upper(), e.get("title", ""))
        elif e["type"] == "tap":
            print(t, "tap", e.get("label", ""))
        elif e["type"] == "age" and (ages is None or e["age"] in ages):
            print(t, "── 年紀", e["age"])
        elif e["type"] == "row":
            k = e["cls"].split()[0]
            if k in kinds or a.all:
                print(t, f"[{k}]", e["text"][:80])


if __name__ == "__main__":
    main()
