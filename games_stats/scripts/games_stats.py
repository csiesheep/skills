"""games_stats: today vs yesterday for csiesheep's web games (games.csiesheep.com).

Days are Taiwan days (UTC+8); the players are in Taiwan. For each game:
  games    finished games (china_life: rows in D1 `lives`; covervote: POST /covervote/api/play answered 204)
  players  distinct client IPs that finished at least one game (IPv6 grouped by /64), from Cloudflare analytics
  visitors distinct client IPs that opened the game page
No IP is printed or written; only counts.

Usage:
  py -X utf8 games_stats.py                       # markdown report to stdout
  py -X utf8 games_stats.py --json                # raw numbers
  py -X utf8 games_stats.py --report "<dir>"      # write/update <dir>/<Taiwan date>.md (summary + hourly log)
  py -X utf8 games_stats.py --yesterday --report "<dir>"   # close yesterday's file with full-day numbers (row 24:00)
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

ZONE = "68ca769cac3903df92ae9ce8d4c43087"          # csiesheep.com
TW = dt.timezone(dt.timedelta(hours=8))
CODE = Path.home() / "code"
GAMES = [
    {"id": "china_life", "name": "生在中國", "repo": CODE / "china_life", "db": "china_life_stats",
     "play": "/china_life/api/life", "page": "/china_life/", "games_from": "d1"},
    {"id": "covervote", "name": "蓋牌投票箱", "repo": CODE / "covervote", "db": "covervote",
     "play": "/covervote/api/play", "page": "/covervote/", "games_from": "cf",
     "total_sql": "SELECT SUM(n) AS n FROM counters WHERE key LIKE 'p:%:n'"},
]
WRANGLER_CFG = Path(os.path.expandvars(r"%APPDATA%")) / "xdg.config" / ".wrangler" / "config" / "default.toml"


def d1(db, sql, repo):
    """Run SQL on a remote D1 through wrangler (which also refreshes the OAuth token). Retries: 7403 happens now and then."""
    cmd = ["npx.cmd" if os.name == "nt" else "npx", "wrangler", "d1", "execute", db, "--remote", "--json", "--command", sql]
    err = ""
    for i in range(3):
        p = subprocess.run(cmd, cwd=repo if repo.exists() else None, capture_output=True, text=True, encoding="utf-8")
        out = p.stdout[p.stdout.find("["):] if "[" in p.stdout else ""
        try:
            return json.loads(out)[0]["results"]
        except Exception:
            err = (p.stdout + p.stderr)[-400:]
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"D1 {db} failed: {err}")


def token():
    t = re.search(r'^oauth_token\s*=\s*"([^"]+)"', WRANGLER_CFG.read_text(encoding="utf-8"), re.M)
    if not t:
        raise RuntimeError("no wrangler OAuth token; run `npx wrangler login`")
    return t.group(1)


def cf_batch(parts):
    """parts: {alias: (start, end, path, method_or_None, with_ua)} → {alias: rows}. One GraphQL request per run:
    the zone's analytics budget is small (a burst of single queries got 'Rate limiter budget depleted, try after 5 minutes')."""
    sub = []
    for alias, (start, end, path, method, with_ua) in parts.items():
        f = f'datetime_geq:"{iso(start)}", datetime_lt:"{iso(end)}", clientRequestPath:"{path}"'
        if method:
            f += f', clientRequestHTTPMethodName:"{method}", edgeResponseStatus_lt:400'
        dims = "clientIP userAgent" if with_ua else "clientIP"
        sub.append(f'{alias}: httpRequestsAdaptiveGroups(limit:10000, filter:{{{f}}}) {{ count avg {{ sampleInterval }} dimensions {{ {dims} }} }}')
    q = '{ viewer { zones(filter:{zoneTag:"%s"}) { %s } } }' % (ZONE, " ".join(sub))
    last = None
    for wait in (0, 30, 330):          # the budget refills after 5 minutes
        time.sleep(wait)
        try:
            r = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", json.dumps({"query": q}).encode(),
                                       {"Authorization": f"Bearer {token()}", "content-type": "application/json"})
            d = json.load(urllib.request.urlopen(r, timeout=90))
            if d.get("errors"):
                raise RuntimeError(d["errors"])
            return d["data"]["viewer"]["zones"][0]
        except Exception as e:
            last = e
    raise RuntimeError(f"Cloudflare GraphQL failed: {last}")


# Which app a visitor opened the link in, from the browser's user-agent. In-app browsers name themselves;
# the Free plan has no referrer, so search, typed address and links from other sites all land in "browser".
SOURCES = [
    ("bot", re.compile(r"bot|crawl|spider|facebookexternalhit|preview|externalhit|curl|python|headless|wget|okhttp|go-http|node-fetch|axios|monitor|lighthouse", re.I)),
    ("Threads", re.compile(r"Barcelona", re.I)),
    ("Instagram", re.compile(r"Instagram", re.I)),
    ("Messenger", re.compile(r"Messenger|FBAN/MessengerFor|FB_IAB/MESSENGER|\bOrca-Android", re.I)),
    ("Facebook", re.compile(r"FBAN|FBAV|FB_IAB|FB4A|FBIOS|\[FB", re.I)),
    ("LINE", re.compile(r"\bLine/", re.I)),
    ("TikTok", re.compile(r"TikTok|musical_ly|Bytedance|trill", re.I)),
    ("X", re.compile(r"Twitter", re.I)),
    ("Discord", re.compile(r"Discord", re.I)),
]
SOURCE_ORDER = ["Threads", "Instagram", "Facebook", "Messenger", "LINE", "TikTok", "X", "Discord", "browser"]


def source_of(ua):
    for name, rx in SOURCES:
        if rx.search(ua or ""):
            return name
    return "browser"


iso = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ms = lambda t: int(t.timestamp() * 1000)
ipkey = lambda ip: ":".join(ip.split(":")[:4]) if ":" in ip else ip


def per_ip(rows):
    agg = {}
    for g in rows:
        k = ipkey(g["dimensions"]["clientIP"])
        agg[k] = agg.get(k, 0) + g["count"]
    return agg


def collect(yesterday=False):
    now = dt.datetime.now(TW).replace(microsecond=0)
    if yesterday:          # close the previous Taiwan day: its full 24 hours vs the day before
        now = now.replace(hour=0, minute=0, second=0) - dt.timedelta(seconds=1)
    mid = now.replace(hour=0, minute=0, second=0)
    y0 = mid - dt.timedelta(days=1)
    spans = {"today": (mid, now), "same": (y0, y0 + (now - mid)), "yday": (y0, mid)}
    out = {"generated": now.isoformat(), "date": mid.date().isoformat(), "games": []}
    parts = {}
    for gi, g in enumerate(GAMES):
        for k, (a, b) in spans.items():
            parts[f"g{gi}_{k}_play"] = (a, b, g["play"], "POST", False)
            parts[f"g{gi}_{k}_page"] = (a, b, g["page"], None, True)
    # D1 first: wrangler refreshes the OAuth token on that call; the GraphQL request reuses the token from
    # wrangler's config, so asking Cloudflare first with an expired token gives 401 (seen 2026-10-25 00:07).
    d1(GAMES[0]["db"], "SELECT 1 AS n", GAMES[0]["repo"])
    z = cf_batch(parts)
    seen = est = 0
    for gi, g in enumerate(GAMES):
        res = {"id": g["id"], "name": g["name"]}
        if g["games_from"] == "d1":
            rows = d1(g["db"], f"SELECT CASE WHEN t < {ms(mid)} THEN (CASE WHEN t < {ms(spans['same'][1])} THEN 'same' ELSE 'late' END) "
                               f"ELSE 'today' END AS k, COUNT(*) AS n FROM lives WHERE t >= {ms(y0)} GROUP BY k", g["repo"])
            n = {r["k"]: r["n"] for r in rows}
            d1_games = {"today": n.get("today", 0), "same": n.get("same", 0), "yday": n.get("same", 0) + n.get("late", 0)}
            res["total"] = d1(g["db"], "SELECT MAX(rowid) AS n FROM lives", g["repo"])[0]["n"]
        else:
            d1_games = None
            res["total"] = d1(g["db"], g["total_sql"], g["repo"])[0]["n"]
        for k in spans:
            play, page = z[f"g{gi}_{k}_play"], z[f"g{gi}_{k}_page"]
            for r in play + page:
                seen += r["count"]; est += r["count"] * (r["avg"]["sampleInterval"] or 1)
            # each visitor's app: the first non-bot source seen for that address (an app wins over a plain browser)
            src = {}
            for r in page:
                ip, s = ipkey(r["dimensions"]["clientIP"]), source_of(r["dimensions"]["userAgent"])
                if s == "bot":
                    continue
                if src.get(ip, "browser") == "browser":
                    src[ip] = s
            ips = per_ip(play)
            vis_by, ply_by = {}, {}
            for ip, s in src.items():
                vis_by[s] = vis_by.get(s, 0) + 1
            for ip in ips:
                s = src.get(ip, "browser")
                ply_by[s] = ply_by.get(s, 0) + 1
            games = d1_games[k] if d1_games else sum(ips.values())
            res[k] = {"games": games, "players": len(ips), "visitors": len(src),
                      "top": sorted(ips.values(), reverse=True)[:5], "visitors_by": vis_by, "players_by": ply_by}
        out["games"].append(res)
    out["sampled"] = bool(seen) and est / seen > 1.05
    return out


def pct(a, b):
    if not b:
        return "—"
    return f"{(a - b) / b * 100:+.0f}%"


def source_table(T, Y):
    names = {"browser": "一般瀏覽器（搜尋、直接輸入、其他網站）"}
    rows = ["| 從哪裡來（打開連結的 App） | 今天訪客 | 今天玩家 | 昨天全天訪客 | 昨天全天玩家 |", "|---|---|---|---|---|"]
    for s in SOURCE_ORDER:
        v = [T["visitors_by"].get(s, 0), T["players_by"].get(s, 0), Y["visitors_by"].get(s, 0), Y["players_by"].get(s, 0)]
        if any(v):
            rows.append(f"| {names.get(s, s)} | {v[0]:,} | {v[1]:,} | {v[2]:,} | {v[3]:,} |")
    return rows


def markdown(d):
    t = dt.datetime.fromisoformat(d["generated"])
    L = [f"# 遊戲數據 {d['date']}", "",
         f"更新：{t:%Y-%m-%d %H:%M}（台灣時間）。「今天」是台灣時間 00:00 到現在；「昨天同時段」是昨天 00:00 到同一時刻。", ""]
    for g in d["games"]:
        T, S, Y = g["today"], g["same"], g["yday"]
        gpp = lambda x: f"{x['games'] / x['players']:.1f}" if x["players"] else "—"
        L += [f"## {g['name']}（{g['id']}）", "",
              f"| | 今天 | 昨天同時段 | 變化 | 昨天全天 |", "|---|---|---|---|---|",
              f"| 玩完的局數 | **{T['games']:,}** | {S['games']:,} | {pct(T['games'], S['games'])} | {Y['games']:,} |",
              f"| 玩家（玩完至少一局） | **{T['players']:,}** | {S['players']:,} | {pct(T['players'], S['players'])} | {Y['players']:,} |",
              f"| 打開遊戲頁的人 | {T['visitors']:,} | {S['visitors']:,} | {pct(T['visitors'], S['visitors'])} | {Y['visitors']:,} |",
              f"| 每位玩家局數 | {gpp(T)} | {gpp(S)} | | {gpp(Y)} |", "",
              *source_table(T, Y), "",
              f"今天玩最多的五位各玩了 {'、'.join(map(str, T['top'])) or '—'} 局。累計總局數 {g['total'] or 0:,}。", ""]
    L += ["## 怎麼算的", "",
          "- 局數：生在中國取自遊戲資料庫（每一生一筆，完全相同的重玩不重算）；蓋牌投票箱取自 Cloudflare 的「送出結果」請求數"
          "（內部測試 `internal=1` 也算在內，資料庫累計數不含）。",
          "- 玩家、打開頁面的人：Cloudflare 流量裡不同的網路位址（IPv6 以 /64 算一戶）。遊戲不記使用者，這是估計：同一個 Wi-Fi 的一家人算一位，"
          "手機換位址會算兩位。報告不寫任何位址。",
          "- 從哪裡來：看訪客的瀏覽器標記。Threads、Instagram、Facebook、LINE 等 App 用內建瀏覽器開連結時會標明自己；"
          "Cloudflare 免費方案不給來源網址，所以搜尋、直接輸入網址、從其他網站點進來都算「一般瀏覽器」。"
          "連結預覽機器人不算訪客。玩家的來源是同一位址打開遊戲頁時的 App（找不到就算一般瀏覽器）。"]
    if d["sampled"]:
        L.append("- 注意：這次 Cloudflare 有取樣，玩家與訪客數偏低。")
    return "\n".join(L) + "\n"


LOG_HEAD = "## 每小時紀錄"


def write_report(d, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{d['date']}.md"
    log = []
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if LOG_HEAD in old:
            log = [l for l in old.split(LOG_HEAD, 1)[1].splitlines() if re.match(r"^\| \d\d:\d\d ", l)]
    t = dt.datetime.fromisoformat(d["generated"])
    cells = " | ".join(f"{g['today']['games']:,} | {g['today']['players']:,}" for g in d["games"])
    hhmm = "24:00" if t.strftime("%H:%M:%S") == "23:59:59" else f"{t:%H:%M}"
    row = f"| {hhmm} | {cells} |"
    log = [l for l in log if not l.startswith(f"| {hhmm} ")] + [row]
    head = "| 時間 | " + " | ".join(f"{g['id']} 局數 | {g['id']} 玩家" for g in d["games"]) + " |"
    sep = "|---" * (1 + 2 * len(d["games"])) + "|"
    body = markdown(d) + f"\n{LOG_HEAD}\n\n今天累計到該時刻的數字。\n\n{head}\n{sep}\n" + "\n".join(sorted(log)) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", help="folder for <date>.md")
    ap.add_argument("--yesterday", action="store_true", help="the previous Taiwan day, full 24 hours")
    a = ap.parse_args()
    data = collect(a.yesterday)
    if a.report:
        print(write_report(data, a.report))
    print(json.dumps(data, ensure_ascii=False, indent=1) if a.json else markdown(data))
