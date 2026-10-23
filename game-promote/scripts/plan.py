"""The day's engagement file and the posting slots.

    py -X utf8 plan.py new   <engagement folder> <game> [--date 2026-10-23]
    py -X utf8 plan.py slots <engagement folder> <platform> [<platform> ...] [--now 2026-10-23T14:05] [--cap 3] [--gap 20]

`new` adds a section for <game> to <folder>/<date>.md (creating the file if needed) with the candidate list and
the result table. The same day file serves every game, so the daily cap counts all of the brand's replies.

`slots` gives one time per approved reply, in order, e.g. `slots <folder> threads ig ig`. It reads today's result
tables (rows whose 狀態 is 已發 or 排定), keeps the per-platform cap for the day, at least --gap minutes between two
replies on the same platform (counted from the last posted or scheduled one), and only uses the hours people in
Taiwan read social media (12:00-13:30, 19:30-23:00 local). What does not fit today rolls to tomorrow. Times print as
ISO 8601 with +08:00, ready for the scheduled-task tool's fireAt. `--avoid <folder>` (repeatable) names another
brand's engagement folder that posts from the same Chrome (ghost-reply's gui_chang_shi/engagement uses the same
result-table columns): no slot lands within --avoid-gap minutes (default 10) of one of its posted or scheduled
replies on any platform, because both switch the same Instagram account. Day files are named by the Taiwan date.
Standard library only.
"""
import argparse
import datetime as dt
import random
import re
from pathlib import Path

TZ = dt.timezone(dt.timedelta(hours=8))
WINDOWS = [((12, 0), (13, 30)), ((19, 30), (23, 0))]
PLATFORMS = {"threads": "Threads", "ig": "IG", "instagram": "IG"}

SECTION = """
## {game}（{title}）｜{date}

規矩：每則都要接原文一個具體細節；連結只放一次；一則貼文只回一則；中文（台灣）貼文才回。

### 候選

| # | 平台 | 貼文 | 原文重點（看完整篇後寫） | 多久前、讚、回覆 | 註記（立場、風險） |
|---|---|---|---|---|---|
| 1 | | | | | |

### 擬稿

- 1：

### 結果

| # | 遊戲 | 平台 | 貼文 | 狀態 | 時間 | 我們的回覆連結 | 24h 讚 | 24h 回覆 |
|---|---|---|---|---|---|---|---|---|
"""


def cmd_new(a) -> None:
    import json
    games = json.loads((Path(__file__).resolve().parent.parent / "references" / "games.json").read_text(encoding="utf-8"))
    g = games["games"].get(a.game)
    if not g:
        raise SystemExit(f"unknown game {a.game}; known: {', '.join(games['games'])}")
    folder = Path(a.folder)
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{a.date}.md"
    text = p.read_text(encoding="utf-8") if p.exists() else f"# {a.date} 回覆別人的貼文\n"
    head = f"## {a.game}（"
    if head in text:
        print(f"{p} already has a {a.game} section")
        return
    p.write_text(text.rstrip() + "\n" + SECTION.format(game=a.game, title=g["title"], date=a.date), encoding="utf-8")
    print(p)


def booked(folder: Path, day: dt.date):
    """(platform, datetime) of every reply already posted or scheduled on `day`, from all result tables."""
    p = folder / f"{day.isoformat()}.md"
    if not p.exists():
        return []
    out = []
    lines = p.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if not (line.startswith("|") and "狀態" in line and "時間" in line):
            continue
        head = [c.strip() for c in line.strip().strip("|").split("|")]
        ip, ist, it = head.index("平台"), head.index("狀態"), head.index("時間")
        for row in lines[i + 2:]:
            if not row.startswith("|"):
                break
            c = [x.strip() for x in row.strip().strip("|").split("|")]
            if len(c) <= max(ip, ist, it) or not re.search(r"已發|排定", c[ist]):
                continue
            plat = PLATFORMS.get(c[ip].lower(), c[ip])
            m = re.search(r"(\d{1,2}):(\d{2})", c[it])
            when = dt.datetime.combine(day, dt.time(int(m[1]), int(m[2])), TZ) if m else None
            out.append((plat, when))
    return out


def next_in_window(t: dt.datetime) -> dt.datetime:
    while True:
        for (h0, m0), (h1, m1) in WINDOWS:
            start = t.replace(hour=h0, minute=m0, second=0, microsecond=0)
            end = t.replace(hour=h1, minute=m1, second=0, microsecond=0)
            if t <= end:
                return max(t, start)
        t = (t + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def cmd_slots(a) -> None:
    folder = Path(a.folder)
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=TZ) if a.now else dt.datetime.now(TZ)
    rng = random.Random(now.toordinal())
    state: dict[tuple[str, dt.date], list[dt.datetime | None]] = {}

    def day_list(plat: str, day: dt.date):
        key = (plat, day)
        if key not in state:
            state[key] = [w for p, w in booked(folder, day) if p == plat]
        return state[key]

    # The other brand posts from the same Chrome and switches the same Instagram (and through it Threads) account,
    # so two posts must not overlap there, whatever the platform; they do not count towards this brand's cap.
    others: dict[dt.date, list[dt.datetime]] = {}

    def clash(t: dt.datetime) -> dt.datetime | None:
        if t.date() not in others:
            others[t.date()] = [w for f in a.avoid for _, w in booked(Path(f), t.date()) if w]
        for w in others[t.date()]:
            if abs(t - w) < dt.timedelta(minutes=a.avoid_gap):
                return w
        return None

    for raw in a.platforms:
        plat = PLATFORMS.get(raw.lower())
        if not plat:
            raise SystemExit(f"platform must be threads or ig, not {raw}")
        t = next_in_window(now + dt.timedelta(minutes=2))
        while True:
            used = day_list(plat, t.date())
            if len(used) >= a.cap:
                t = next_in_window((t + dt.timedelta(days=1)).replace(hour=0, minute=0))
                continue
            last = max([w for w in used if w], default=None)
            if last and t < last + dt.timedelta(minutes=a.gap):
                t = next_in_window(last + dt.timedelta(minutes=a.gap + rng.randint(0, 9)))
                continue
            w = clash(t)
            if w:
                t = next_in_window(w + dt.timedelta(minutes=a.avoid_gap))
                continue
            break
        used.append(t)
        print(f"{plat}\t{t.isoformat(timespec='minutes')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("folder")
    n.add_argument("game")
    n.add_argument("--date", default=dt.datetime.now(TZ).date().isoformat())
    s = sub.add_parser("slots")
    s.add_argument("folder")
    s.add_argument("platforms", nargs="+")
    s.add_argument("--now")
    s.add_argument("--cap", type=int, default=3)
    s.add_argument("--gap", type=int, default=20)
    s.add_argument("--avoid", action="append", default=[], metavar="FOLDER",
                   help="another brand's engagement folder sharing this Chrome; keep clear of its replies")
    s.add_argument("--avoid-gap", type=int, default=10)
    a = ap.parse_args()
    {"new": cmd_new, "slots": cmd_slots}[a.cmd](a)


if __name__ == "__main__":
    main()
