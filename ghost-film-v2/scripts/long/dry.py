"""Timeline of a shot list without rendering: py -X utf8 dry.py shots_long.json [split ids...] -> out/<out>/_timeline.txt"""
import sys
sys.path.insert(0, "C:/Users/sheep/.claude/skills/ghost-film-v2/scripts")
import render as X
tl, total, *_ = X.build()
X.OUT.mkdir(parents=True, exist_ok=True)
with open(X.OUT / "_timeline.txt", "w", encoding="utf8") as f:
    for it in tl:
        if it["kind"] == "shot":
            f.write(f"{it['start']:6.2f} {it['dur']:5.2f}  {it['sh']['id']}\n")
print("total", round(total, 1), "s =", int(total // 60), ":", round(total % 60, 1), "shots", len(tl))
for m in sys.argv[2:] + ["end"]:  # optional split ids to print
    print(m, [round(it["start"], 1) for it in tl if it["kind"] == "shot" and it["sh"]["id"] == m])
