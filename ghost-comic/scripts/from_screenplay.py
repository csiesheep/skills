"""Turn a ghost-story-v3 (or v2) screenplay into a draft comic board.

    py -X utf8 from_screenplay.py <story folder> [--force] [--max-per-page 5] [--max-text 3]

Reads  <story>/film/screenplay.md  (and checks <story>/story.md exists).
Writes <story>/comic/board.json   a skeleton: characters, scenes, pages with one panel per bracketed beat, the
                                   lettering already filled from the VO and the spoken lines, the reveal marked.
       <story>/comic/brief.md     what the board still needs from a person, and what was carried over from the film
       <story>/comic/brief.json   machine-readable carry-over (hook line, reveal panel, jokes with the panel they
                                   fall in, device rules): ghost-reel's draft step reads it later.

It draws nothing and uses no GPU. Every panel it writes has "todo": true and an empty prompt, and every scene and
character description starts with "TODO"; `manga.py lint` refuses to go on while any are left, so a skeleton cannot be
drawn by mistake. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BEAT = re.compile(r"^\[(.*)\]\s*$")
LINE = re.compile(r"^\*\*(?P<who>[^*]+?)\*\*(?P<note>(?:[（(〔][^）)〕]*[）)〕])*)[：:]\s*(?P<text>.+)$")
HEAD = re.compile(r"^## (?P<n>\d+)\. (?P<title>.+)$")
TIME = re.compile(r"(\d+):(\d\d)\s*[–\-]\s*(\d+):(\d\d)")
STAMP = re.compile(r"(\d+):(\d\d)")
POS = ["tr", "ml", "bc", "bl"]  # a lettering ladder: reading goes top-right first, each box lower than the last


def secs(s: str) -> int:
    m = STAMP.search(s)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else -1


def mmss(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def parse(md: str) -> dict:
    lines = md.splitlines()
    head: dict[str, str] = {}
    for ln in lines:
        m = re.match(r"^\*\*(長度|旁白|台詞|開口角色|最大畫面)\*\*[：:]\s*(.*)$", ln)
        if m:
            head[m.group(1)] = m.group(2).strip()
    title = next((re.sub(r"\s*劇本.*$", "", ln.lstrip("# ")) for ln in lines if ln.startswith("# ")), "")
    # jokes table
    jokes = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.startswith("|") and len(cells) == 5 and STAMP.fullmatch(cells[0]):
            jokes.append({"at": secs(cells[0]), "type": cells[1], "who": cells[2], "line": cells[3].strip("「」"),
                          "callback": "" if cells[4] in ("—", "-", "") else cells[4]})
    # cast: bullets between **人物 and **場景
    cast, rules, scene_notes = [], [], []
    mode = ""
    for ln in lines:
        if ln.startswith("**人物"):
            mode = "cast"
            continue
        if ln.startswith("**場景"):
            mode = "scene"
            continue
        if ln.startswith("**留住觀眾") or ln.startswith("---") or ln.startswith("## "):
            mode = ""
        if mode == "cast" and ln.startswith("- **"):
            m = re.match(r"^- \*\*(.+?)\*\*[：:]\s*(.*)$", ln)
            if m:
                desc = m.group(2)
                feats = re.findall(r"\*\*(.+?)\*\*", desc)
                cast.append({"name": m.group(1), "desc": re.sub(r"\*\*", "", desc), "features": feats,
                             "voice_only": ("只出聲" in desc or "不算角色" in desc),
                             "ghost": "鬼" in desc.split("。")[0] or m.group(1) in ("她", "他", "它") and "鬼" in desc})
        if mode == "scene" and ln.strip().startswith("-"):
            (rules if ln.startswith("  ") and not ln.strip().startswith("- **裝置") else scene_notes).append(
                re.sub(r"\*\*", "", ln.strip().lstrip("- ").strip()))
    # scenes with beats
    scenes: list[dict] = []
    cur = None
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        h = HEAD.match(ln)
        if h:
            t = TIME.search(h.group("title"))
            name = TIME.sub("", h.group("title")).strip()
            parts = [p for p in re.split(r"[　\s]+", name) if p]
            loc = re.sub(r"^[內外]．", "", parts[0]) if parts else name
            cur = {"n": int(h.group("n")), "title": name, "loc": loc,
                   "start": int(t.group(1)) * 60 + int(t.group(2)) if t else 0,
                   "end": int(t.group(3)) * 60 + int(t.group(4)) if t else 0, "items": []}
            scenes.append(cur)
        elif cur is not None and ln:
            b = BEAT.match(ln)
            if b and re.match(r"^(疊字|畫面疊字|字幕)[：:]", b.group(1).strip()):
                cur.setdefault("overlays", []).append(b.group(1).strip())  # post-production text, not a picture
            elif b:
                cur["items"].append({"k": "beat", "text": b.group(1).strip()})
            else:
                m = LINE.match(ln)
                if m:
                    who, note, text = m.group("who").strip(), m.group("note"), m.group("text").strip()
                    cur["items"].append({"k": "say", "who": who, "note": note.strip("（）()〔〕"), "text": text,
                                         "voiceover": who == "VO" or who.startswith("VO"),
                                         "offscreen": "只出聲" in note})
        i += 1
    return {"title": title, "head": head, "jokes": jokes, "cast": cast, "rules": rules, "scene_notes": scene_notes,
            "scenes": scenes}


def build(sp: dict, story_rel: str, max_text: int, max_page: int) -> tuple[dict, dict]:
    chars: dict[str, dict] = {}
    names: dict[str, str] = {}
    ghost_id = ""
    voice_names = set()
    for k, c in enumerate(sp["cast"]):
        if c["voice_only"]:
            voice_names.add(c["name"])
            continue
        cid = "me" if c["name"] == "我" else ("ghost" if c["ghost"] and not ghost_id else f"c{k + 1}")
        if cid == "ghost":
            ghost_id = cid
        names[c["name"]] = cid
        chars[cid] = {"name": c["name"], "features": "＋".join(c["features"]) or "TODO: two memorable features",
                      "views": "TODO", "desc": "TODO English description from: " + c["desc"],
                      "keywords": [], **({"ghost": True} if cid == "ghost" else {})}
    scene_ids: dict[str, str] = {}
    scenes_out, layout = {}, {}
    for s in sp["scenes"]:
        if s["n"] == 1 and not re.match(r"^[內外]", s["title"]):
            continue  # the cold open lives wherever its picture says
        if s["loc"] not in scene_ids:
            sid = f"s{len(scene_ids) + 1}"
            scene_ids[s["loc"]] = sid
            scenes_out[sid] = f"TODO background art, no people: {s['loc']}"
            layout[sid] = ("TODO floor plan: which wall the door and window are in, where each piece of furniture "
                           f"stands, which way the objects the story turns on face ({s['loc']})")
    # beats -> panels
    panels: list[dict] = []
    big_t = secs(sp["head"].get("最大畫面", ""))
    hook = ""
    for s in sp["scenes"]:
        beats = [it for it in s["items"] if it["k"] == "beat"]
        sid = scene_ids.get(s["loc"])
        # attach each spoken line to the beat before it (or the first beat)
        groups: list[dict] = []
        for it in s["items"]:
            if it["k"] == "beat":
                groups.append({"beat": it["text"], "says": []})
            else:
                if not groups:
                    groups.append({"beat": "", "says": []})
                groups[-1]["says"].append(it)
        span = max(s["end"] - s["start"], 1)
        for gi, g in enumerate(groups):
            t = s["start"] + span * gi / max(len(groups), 1)
            stamp = STAMP.search(g["beat"][:8])
            if stamp:
                t = secs(stamp.group(0))
            texts = []
            for sy in g["says"]:
                if sy["voiceover"]:
                    texts.append({"kind": "narration", "text": sy["text"]})
                elif sy["who"] in voice_names or sy["offscreen"]:
                    texts.append({"kind": "voice", "text": sy["text"]})
                else:
                    texts.append({"kind": "speech", "text": sy["text"]})
            big = big_t >= 0 and bool(stamp) and abs(t - big_t) < 2
            if not hook and s["n"] == 1:
                m = re.search(r"大字[：:]\s*([^\]。]+)", g["beat"])
                if m:
                    hook = m.group(1).strip()
            chunks = [texts[i:i + max_text] for i in range(0, len(texts), max_text)] or [[]]
            for ci, ch in enumerate(chunks):
                for k, e in enumerate(ch):
                    e["pos"] = POS[k % len(POS)] if e["kind"] != "narration" else ("tr" if k == 0 else "bl")
                label = re.sub(r"\s+", " ", g["beat"]) or "（只有字）"
                label = (label[:34] + "…") if len(label) > 34 else label
                p = {"id": f"p{len(panels) + 1}", "label": ("（續）" if ci else "") + label, "refs": [], "prompt": "",
                     "todo": True, "text": ch, "_t": t, "_scene": s["n"]}
                if sid:
                    p["scene"] = sid
                guess = [cid for nm, cid in names.items() if nm != "我" and nm in g["beat"] + " ".join(x["who"] for x in g["says"])]
                if re.search(r"我", g["beat"]) or any(x["who"] == "我" for x in g["says"]):
                    guess.insert(0, "me")
                if ghost_id and re.search(r"她|鬼|女生", g["beat"]) and ghost_id not in guess:
                    guess.append(ghost_id)
                if guess:
                    p["cast"] = list(dict.fromkeys(guess))
                if big and ci == 0:
                    p["reveal"] = True
                    p["_big"] = True
                if panels == [] and ci == 0:
                    p["_big"] = True  # the cold open's picture is the first panel and the cover candidate
                panels.append(p)
    if not any(p.get("reveal") for p in panels) and panels and big_t >= 0:
        near = min(panels, key=lambda p: abs(p["_t"] - big_t))
        near["reveal"] = True
        near["_big"] = True
    # pages: break at scene changes once a page has 3, at max_page, and put the reveal at the top of a page
    pages_p: list[list[dict]] = []
    cur: list[dict] = []
    for p in panels:
        if cur and (len(cur) >= max_page or (len(cur) >= 3 and p["_scene"] != cur[-1]["_scene"]) or p.get("reveal")):
            pages_p.append(cur)
            cur = []
        cur.append(p)
    if cur:
        pages_p.append(cur)
    pages = []
    for pg in pages_p:
        big = next((i for i, p in enumerate(pg) if p.get("_big")), None)
        rows: list[list[dict]] = []

        def chunk(xs: list[dict]) -> None:
            k = 0
            while k < len(xs):
                left = len(xs) - k
                n = 3 if left == 3 and rows else 2 if left > 1 else 1
                rows.append(xs[k:k + n])
                k += n

        if big is None:
            chunk(pg)
        else:
            chunk(pg[:big])
            rows.append([pg[big]])
            chunk(pg[big + 1:])
        if len(rows) == 1 and len(rows[0]) > 1:  # never a page that is one row of tall columns
            rows = [rows[0][:1], rows[0][1:]]
        hs = {}
        bigrow = next((i for i, r in enumerate(rows) if len(r) == 1 and r[0].get("_big")), None)
        other = len(rows) - (1 if bigrow is not None else 0)
        bigh = 0.55 if bigrow is not None and rows[bigrow][0].get("reveal") else 0.42
        for i in range(len(rows)):
            hs[i] = bigh if i == bigrow else (1 - (bigh if bigrow is not None else 0)) / max(other, 1)
        norm = sum(hs.values())
        out_rows = []
        for i, r in enumerate(rows):
            if len(r) == 1:
                ws = [1.0]
            elif len(r) == 2:
                ws = [0.6, 0.4] if i % 2 == 0 else [0.4, 0.6]
            else:
                ws = [0.34, 0.33, 0.33]
            out_rows.append({"h": round(hs[i] / norm, 3), "cells": [dict(w=w, **{k: v for k, v in c.items() if not k.startswith("_")})
                                                                     for c, w in zip(r, ws)]})
        pages.append({"rows": out_rows})
    if pages and pages[0]["rows"]:
        first = pages[0]["rows"][0]["cells"][0]
        for e in first["text"]:  # the title takes the top right
            e["pos"] = "bl" if e["pos"] == "tr" else e["pos"]
        first["text"] = [{"kind": "title", "text": sp["title"], "pos": "tr", "per_col": 5, "scale": 0.9}] + first["text"]
    # carry-over: where each joke and callback falls
    def panel_at(t: float) -> str:
        return min(panels, key=lambda p: abs(p["_t"] - t))["id"] if panels else ""

    jokes = []
    for j in sp["jokes"]:
        key = j["line"][:6]
        seed = next((p["id"] for p in panels if any(key in e["text"] for e in p["text"])), panel_at(j["at"]))
        cb = secs(j["callback"]) if j["callback"] else -1
        jokes.append({**j, "panel": seed, "callback_panel": panel_at(cb) if cb >= 0 else ""})
    board = {"title": sp["title"], "story": story_rel, "direction": "rtl", "page": [1200, 1700], "margin": 56,
             "gutter": [18, 24], "style_options": {"A": {"name": "TODO copy style A from a finished board",
                                                          "panel": "TODO", "sheet": "TODO"}},
             "characters": chars, "scenes": scenes_out, "consistency": {"scene": layout, "scale": {}},
             "lights": {}, "pages": pages}
    for p in (c for pg in pages for r in pg["rows"] for c in r["cells"]):
        pass
    brief = {"title": sp["title"], "length": sp["head"].get("長度", ""), "big_picture": sp["head"].get("最大畫面", ""),
             "hook_line": hook, "first_panel": panels[0]["id"] if panels else "",
             "reveal_panel": next((p["id"] for p in panels if p.get("reveal")), ""),
             "device_rules": sp["rules"], "jokes": jokes, "voice_only": sorted(voice_names),
             "overlays": [o for s in sp["scenes"] for o in s.get("overlays", [])],
             "panels": [{"id": p["id"], "t": round(p["_t"]), "scene": p["_scene"]} for p in panels]}
    return board, brief


def write_brief(sp: dict, board: dict, brief: dict, n_panels: int) -> str:
    o = [f"# 漫畫簡報：{sp['title']}", "",
         f"由 `film/screenplay.md`（{sp['head'].get('長度', '?')}，最大畫面 {sp['head'].get('最大畫面', '?')}）自動產生，"
         "不畫圖。`board.json` 是骨架：每格 `todo: true`、prompt 空白，`manga.py lint` 在 TODO 清完前會擋。", "",
         f"- {len(board['pages'])} 頁、{n_panels} 格。長篇漫畫的慣例是 6–8 頁、25–30 格；超過 32 格就先砍鋪陳格，不要把每個鏡頭都畫成一格。",
         f"- 第一格 `{brief['first_panel']}`：冷開場的畫面（封面候選，Reel 的第 0 秒）。"
         + (f"大字：「{brief['hook_line']}」。" if brief["hook_line"] else "劇本沒有標大字。"),
         f"- 揭露格 `{brief['reveal_panel'] or '（沒找到，手動標 reveal）'}` 已標 `reveal: true`，放在頁首。", ""]
    o += ["## 要人補的（照順序）", "",
          "1. **角色**：每個 `TODO` 的 `desc`、`views`、`keywords`（英文，至少兩個記憶點）；ghost-comic 的預設是鬼比活人小、臉大半在陰影裡。"
          "劇本寫的是「清楚看到鬼」，`brand/taste.md` 的偏好是暗示：由擁有者決定，沒決定前照 SKILL.md 的克制版。",
          "2. **場景**：每個 `scenes`、`consistency.scene` 的 TODO 寫成平面圖（哪面牆有門窗、家具靠哪面牆、故事轉的物件朝哪）。",
          "3. **「這樣才對」**：下面每條裝置規則，對每個用到它的物件寫一句物理事實，放進顯示它的格子的 prompt。",
          "4. **畫風、光線**：`style_options`、`lights`（從已做完的 board 複製）。",
          "5. **每格 prompt、`refs`、`cast`、`heads`**：`cast` 是從文字猜的，要看過。完成的格子刪掉 `todo`。",
          "6. 劇本寫的「一鏡到底」拌嘴，在漫畫裡是一個寬格加幾個框，不要一句一格；`plan` 看框有沒有互相蓋住。",
          "7. 只靠聲音的拍點（劇本寫「馬達聲切掉、沒有旁白停三秒」）漫畫沒有聲音：用沒有字的大格或 `fill: black` 格撐住。",
          "8. 螢幕、手機、照片上的字：模型不畫字，用 `screen`／`phone` 框。", ""]
    o += ["## 裝置的規則（劇本）", ""] + [f"- {r}" for r in sp["rules"]] + [""]
    o += ["## 笑點與回收（漫畫要保留種子那一格）", "",
          "| 秒 | 誰 | 句子 | 在哪一格 | 回收 | 回收在哪一格 |", "|---|---|---|---|---|---|"]
    for j in brief["jokes"]:
        o.append(f"| {mmss(j['at'])} | {j['who']} | 「{j['line']}」 | {j['panel']} | {j['callback'] or '—'} | {j['callback_panel'] or '—'} |")
    o += ["", "回收格是用秒數估的（每場平均分配），要對照劇本看。種子格的字不能為了篇幅砍掉。", ""]
    o += ["## 版面草稿", "", "| 頁 | 格 | 一句話 |", "|---|---|---|"]
    for pi, pg in enumerate(board["pages"], 1):
        for r in pg["rows"]:
            for c in r["cells"]:
                o.append(f"| {pi} | {c['id']}{' ★揭露' if c.get('reveal') else ''} | {c['label']} |")
    if brief["overlays"]:
        o += ["", "後製疊字（不是格子，Reel 的承諾字幕要用）：" + "；".join(brief["overlays"])]
    if brief["voice_only"]:
        o += ["", f"只出聲的角色（沒有角色卡，畫面只拍到手或背影）：{'、'.join(brief['voice_only'])}。"]
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("story", help="story folder with film/screenplay.md")
    ap.add_argument("--force", action="store_true", help="overwrite an existing comic/board.json")
    ap.add_argument("--max-per-page", type=int, default=5)
    ap.add_argument("--max-text", type=int, default=3, help="lettering boxes per panel before it continues in the next panel")
    a = ap.parse_args()
    d = Path(a.story).resolve()
    sp_file = d / "film" / "screenplay.md"
    if not sp_file.exists():
        raise SystemExit(f"{sp_file} not found: this reads a v2/v3 screenplay")
    out = d / "comic"
    if (out / "board.json").exists() and not a.force:
        raise SystemExit(f"{out / 'board.json'} exists; --force to start over")
    sp = parse(sp_file.read_text(encoding="utf-8"))
    if not sp["scenes"]:
        raise SystemExit("no '## N. title  m:ss–m:ss' scene headings found")
    board, brief = build(sp, "../story.md", a.max_text, a.max_per_page)
    n = sum(len(r["cells"]) for pg in board["pages"] for r in pg["rows"])
    out.mkdir(exist_ok=True)
    (out / "board.json").write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "brief.md").write_text(write_brief(sp, board, brief, n), encoding="utf-8")
    print(f"{out / 'board.json'}: {len(board['pages'])} pages, {n} panels, reveal {brief['reveal_panel'] or 'NOT FOUND'}, "
          f"{len(board['characters'])} characters, {len(board['scenes'])} scenes")
    print(f"{out / 'brief.md'}  {out / 'brief.json'}")


if __name__ == "__main__":
    sys.exit(main())
