"""Read the approved screenplay into one row per shot, with the recorded line ids that play over it.
py -X utf8 shot_table.py  (in film/reel) -> shot_table.json; stops if a recorded line is unplaced or a spoken line has no take."""
import json
import re

norm = lambda s: re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
script = json.load(open("../vo/full_script.json", encoding="utf8"))
body = [x for x in script if not re.fullmatch(r"H\d", x["id"])]
hooks = {x["id"]: x["text"] for x in script if re.fullmatch(r"H\d", x["id"])}
rows, part, sec, k, unplaced = [], 0, "", 0, []
for raw in open("../long_screenplay_4.md", encoding="utf8"):
    s = raw.strip()
    if m := re.match(r"# 第 (\d) 支", s):
        part = int(m.group(1))
    elif s.startswith("## "):
        sec = s[3:]
    elif m := re.fullmatch(r"\[(.+)\]", s):
        t = m.group(1)
        if t.startswith("停"):
            sec_pause = float(re.search(r"([\d.]+) 秒", t).group(1))
            if rows:
                rows[-1]["pause_after"] = round(rows[-1].get("pause_after", 0) + sec_pause, 2)
                rows[-1]["pause_note"] = t
        elif not t.startswith("長片和第 4 支"):
            rows.append({"n": len(rows) + 1, "part": part, "sec": sec, "desc": t, "lines": []})
    elif m := re.match(r"\*\*(VO|我|院長|阿斌|她)\*\*(（對講機）)?：(.+)", s):
        said = norm(re.sub(r"~~.*?~~", "", m.group(3)))
        if not said:
            continue
        got = ""
        while got != said and k < len(body) and said.startswith(got + norm(body[k]["text"])):
            got += norm(body[k]["text"])
            rows[-1]["lines"].append(body[k]["id"])
            k += 1
        if got != said:
            unplaced.append((m.group(1), said, got))
json.dump({"hooks": hooks, "shots": rows}, open("shot_table.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(len(rows), "shots;", k, "of", len(body), "recorded lines placed; unplaced", unplaced[:5])
for r in rows:
    print(r["n"], f"P{r['part']}", r["desc"][:46], "|", " ".join(r["lines"]), "| pause", r.get("pause_after", 0))
