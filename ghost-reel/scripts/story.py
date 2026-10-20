"""A comic's shot list, `reels/shots.json` in its story folder: what each Reel version shows, says and sounds like.

The file is meant to be read and edited by hand (one shot per line). Its keys:

    title    the comic's title (title card)
    comic    the ghost-comic work folder, relative to the story folder (usually "comic")
    music    {"v1": file, "v3": file}: a track in the brand's music folder for each version
    beds     [{"from": pid, "to": pid, "bed": name, "gain": g}]: ambience under a run of panels (reading order)
    v3_beds  [{"bed", "gain"} over the whole V3 film, or with "from"/"to" panels]: V3's ambience
    v1       漫動畫: {"hook": [{"panel", "sec", "sfx"}], "panels": {pid: options}, "say": {pid: [lines]},
             "skip": [pids]}. Every panel is shown in reading order unless skipped; "say" replaces its lettering
             with shorter lines.
    v2       說書快剪 (shelved): [{"panel", "caption", options}]; "／" splits a caption into beats
    v3       電影感: [{"panel", "sec", "sub", options}] in the order they play; panel "TITLE" is the title card.
             "／" in a sub shows its parts in turn on that shot.
    cuts     other V3 cuts of the same comic: {name: {"v3": [...], "title", "end": [lines], "music", "v3_beds"}},
             rendered with make.py --cut name (a long version, a part 1 and part 2)

Options: motion (push, pull, pan_rtl, pan_down, static, snap), focus [x, y], fx (night, pulse, chroma, darken,
shake, fadein, glitch), sfx [[name, at seconds, gain]], hold (extra seconds, v1), black (seconds of black before),
duck (music dips), clip (an H3 video, path relative to the story folder), clip_offset, mono (strip the colour
H3 lets into a clip), voice (v3: the line is a
voice in the middle of the frame, not a subtitle), voice_y.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace


def _opts(d: dict, story_dir: Path, skip=()) -> dict:
    o = {k: v for k, v in d.items() if k not in skip}
    if "sfx" in o:
        o["sfx"] = [tuple(x) for x in o["sfx"]]
    if "focus" in o:
        o["focus"] = tuple(o["focus"])
    if o.get("clip"):
        o["clip"] = str((story_dir / o["clip"]).resolve())
    return o


def load(story_dir: str | Path, brand: dict | None = None, cut: str | None = None) -> SimpleNamespace:
    """The shot list as the engine reads it (the attribute names of the prototype's per-comic Python file). With
    `cut`, V3 and its title, end card, music and beds come from that entry of "cuts"."""
    d = Path(story_dir).resolve()
    j = json.loads((d / "reels" / "shots.json").read_text(encoding="utf-8"))
    c = {}
    if cut:
        if cut not in j.get("cuts", {}):
            raise SystemExit(f"shots.json has no cut {cut!r} (cuts: {', '.join(j.get('cuts', {})) or 'none'})")
        c = j["cuts"][cut]
        j = {**j, "v3": c["v3"], "title": c.get("title", j["title"]), "v3_beds": c.get("v3_beds", j.get("v3_beds", [])),
             "music": {**j.get("music", {}), **({"v3": c["music"]} if c.get("music") else {})}}
    v1 = j.get("v1", {})
    return SimpleNamespace(
        DIR=d,
        COMIC=str((d / j.get("comic", "comic")).resolve()),
        TITLE=j["title"],
        NUMBER=None,
        END=c.get("end"),  # the end card's lines, when a cut needs others (「下集待續」)  # never a number inside a video: the owner's rule of 2026-10-20
        SEAL=(brand or {}).get("seal"),
        HANDLE=(brand or {}).get("handle", ""),
        DISCLOSURE=(brand or {}).get("disclosure", "AI 輔助創作｜故事純屬虛構"),
        MUSIC=j.get("music", {}),
        BEDS=[(b["from"], b["to"], b["bed"], b["gain"]) for b in j.get("beds", [])],
        V3_BEDS=[(b.get("from"), b.get("to"), b["bed"], b["gain"]) for b in j.get("v3_beds", [])],
        HOOK=[(h["panel"], h["sec"], None, [tuple(x) for x in h.get("sfx", [])]) for h in v1.get("hook", [])],
        V1={k: _opts(v, d) for k, v in v1.get("panels", {}).items()},
        V1_SAY=v1.get("say", {}),
        V1_SKIP=set(v1.get("skip", [])),
        V2=[(s["panel"], s.get("caption", ""), _opts(s, d, ("panel", "caption"))) for s in j.get("v2", [])],
        V3=[(s["panel"], s["sec"], s.get("sub"), _opts(s, d, ("panel", "sec", "sub"))) for s in j.get("v3", [])],
    )


def dump(doc: dict) -> str:
    """JSON with one shot, bed or panel per line, so a person can read and edit it."""
    one = lambda x: json.dumps(x, ensure_ascii=False)  # noqa: E731
    out = ["{"]
    keys = list(doc)
    for n, k in enumerate(keys):
        v = doc[k]
        end = "," if n < len(keys) - 1 else ""
        if k == "cuts" and isinstance(v, dict):
            out.append(' "cuts": {')
            names = list(v)
            for m, nm in enumerate(names):
                cv = v[nm]
                out.append(f'  "{nm}": {{')
                ck = list(cv)
                for q, kk in enumerate(ck):
                    e3 = "," if q < len(ck) - 1 else ""
                    if kk == "v3":
                        out.append('   "v3": [')
                        out += [f"    {one(x)}" + ("," if i < len(cv[kk]) - 1 else "") for i, x in enumerate(cv[kk])]
                        out.append(f"   ]{e3}")
                    else:
                        out.append(f'   "{kk}": {one(cv[kk])}{e3}')
                out.append("  }" + ("," if m < len(names) - 1 else ""))
            out.append(f" }}{end}")
        elif k in ("beds", "v3_beds", "v2", "v3") and isinstance(v, list):
            out.append(f' "{k}": [')
            out += [f"  {one(x)}" + ("," if i < len(v) - 1 else "") for i, x in enumerate(v)]
            out.append(f" ]{end}")
        elif k == "v1" and isinstance(v, dict):
            out.append(' "v1": {')
            sub = list(v)
            for m, sk in enumerate(sub):
                e2 = "," if m < len(sub) - 1 else ""
                sv = v[sk]
                if isinstance(sv, dict) and sv:
                    out.append(f'  "{sk}": {{')
                    items = list(sv.items())
                    out += [f"   {one(a)}: {one(b)}" + ("," if i < len(items) - 1 else "") for i, (a, b) in enumerate(items)]
                    out.append(f"  }}{e2}")
                elif isinstance(sv, list) and sv and isinstance(sv[0], dict):
                    out.append(f'  "{sk}": [')
                    out += [f"   {one(x)}" + ("," if i < len(sv) - 1 else "") for i, x in enumerate(sv)]
                    out.append(f"  ]{e2}")
                else:
                    out.append(f'  "{sk}": {one(sv)}{e2}')
            out.append(f" }}{end}")
        else:
            out.append(f' "{k}": {one(v)}{end}')
    out.append("}")
    text = "\n".join(out) + "\n"
    json.loads(text)  # the hand layout must still be valid JSON
    return text


def save(story_dir: str | Path, doc: dict) -> Path:
    p = Path(story_dir) / "reels" / "shots.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(dump(doc).encode("utf-8"))
    return p
