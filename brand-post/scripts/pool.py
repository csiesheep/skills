"""The post pool in the Obsidian vault.

    py -X utf8 pool.py status              # counts by type and status, next id
    py -X utf8 pool.py next-id             # print the next free number
    py -X utf8 pool.py pick <popular|devnote>   # print the path of the oldest 待發 post of that type

Posts live in C:/Users/sheep/code/obsidian/Projects/auto promotion/posts/<#>.md with images in posts/<#>/.
Front matter keys read here: type (popular | devnote), status (草稿 / 待發 / 發文中 / 已發 / 退回), created.
"""
import re
import sys
from pathlib import Path

POOL = Path(r"C:/Users/sheep/code/obsidian/Projects/auto promotion/posts")


def meta(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"')
    return out


def posts():
    POOL.mkdir(parents=True, exist_ok=True)
    return sorted((p for p in POOL.glob("*.md") if p.stem.isdigit()), key=lambda p: int(p.stem))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ps = posts()
    if cmd == "next-id":
        print(max([int(p.stem) for p in ps], default=0) + 1)
    elif cmd == "pick":
        want = sys.argv[2]
        for p in ps:
            m = meta(p)
            if m.get("type") == want and m.get("status") == "待發":
                print(p)
                return
        print("")
    else:
        counts = {}
        for p in ps:
            m = meta(p)
            k = (m.get("type", "?"), m.get("status", "?"))
            counts[k] = counts.get(k, 0) + 1
        ready = {t: counts.get((t, "待發"), 0) for t in ("popular", "devnote")}
        print(f"待發 popular {ready['popular']}, devnote {ready['devnote']}; total 待發 {sum(ready.values())}")
        for (t, s), n in sorted(counts.items()):
            print(f"  {t:8s} {s:4s} {n}")
        print("next id", max([int(p.stem) for p in ps], default=0) + 1)


if __name__ == "__main__":
    main()
