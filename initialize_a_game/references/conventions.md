# Conventions for games on games.csiesheep.com

Learned across dice_war, zombie_in_the_pocket, jiangshi_in_the_pocket,
elevator_inc, betrayal_sound_board and tiandihui. Follow unless the owner
says otherwise.

## Platform

- **One Cloudflare Worker per game**, attached to the shared hostname by
  two path-scoped Routes (`games.csiesheep.com/<slug>` and `/<slug>/*`,
  zone `csiesheep.com`). The hub Worker `games` owns the hostname as a
  Custom Domain and serves `/`, `robots.txt`, `ads.txt`, `sitemap.xml`.
- `src/index.js` is a **path-prefix router**: `PREFIX = "/<slug>"`;
  bare prefix 301s to the trailing-slash form; `/<slug>/ws` upgrades to
  the room Durable Object; `/<slug>/sitemap.xml` is prefix-scoped; other
  paths strip the prefix and go to `env.ASSETS` with `run_worker_first`.
  Same-origin redirects from the asset handler must get the prefix put
  back (see tiandihui `src/index.js`).
- **Static assets** in `public/`; `src/` is bundled. Query-string routes
  (`?play`, `?room=ABCD`, `?lang=`) so one build works at any prefix.
- **Rooms** are one Durable Object per room, named by a 4-letter code
  (alphabet without 0/O/1/I), WebSocket Hibernation API, one alarm for all
  timers, per-seat `view(state, seat)` is the only data that leaves the
  object. Bots fill empty seats and take over disconnected humans after a
  grace period; the tab's token in sessionStorage reclaims a seat.
- **Shared engine**: `public/shared/engine.js` is pure and runs in both
  the browser (solo) and the DO. Seeded RNG in the state
  (mulberry32) so games replay from seed + actions. `clone` is a JSON
  clone, not `structuredClone` (V8 crash on this machine).
- **Bots** in `public/shared/bots.js`, table talk templates in
  `public/shared/talk.js`; every decision carries a `why` for talk.
- **i18n**: all player-visible strings in `public/i18n/en.js` and
  `public/i18n/zh-Hant.js`; `app.js` carries no prose. Chinese numerals
  helper (`nums`) where the design calls for 一二三.
- Fonts from Google Fonts only; the hub loads only faces a tile uses.

## Repo

- `csiesheep/<slug>`, public, `main`. Git identity per repo:
  `git config user.name csiesheep`, `user.email csiegoat@gmail.com`,
  `core.autocrlf false`.
- `package.json` scripts: `dev` (`wrangler dev`), `deploy`, `test`
  (`node --test`, not `node --test tests/` on Windows), `sim`.
- Tests: `tests/engine.test.js`, `tests/bots.test.js`, `tests/room.test.js`
  (fake DO context), `tests/sim.js` bot-vs-bot harness with `--cell` child
  processes and retries.
- README: what it is, fan-made line, how it works, milestones, develop.
- Commit messages: a sentence, then why, then the session's trailer.

## Deploy and verify

- `npx wrangler deploy` from the repo on the local machine; the dashboard
  is not connected, pushes do not deploy.
- After deploy, byte-compare live files to the repo with sha1 and
  cache-busting retries (`?v=$RANDOM`); the edge briefly serves stale
  files. `/<slug>/index.html` redirects — compare `/<slug>/` instead.
- Local: `npx wrangler dev --port 8788` in the background; stop with
  PowerShell `Get-NetTCPConnection -LocalPort 8788` → `Stop-Process`, and
  kill leftover `workerd`. `workerd` sometimes dies with 0xC0000005 on
  this machine; retry, or serve `public/` with `python -m http.server`
  for pure-static checks.
- Node 24 on this Windows box crashes randomly (access violation) on long
  runs: the harness runs cells as child processes with retries. Treat as
  environmental; re-run a failed test once before believing it.
- Browser pane: `file://` is refused; use a server. Coordinates are
  unreliable — click by `ref` or drive with `javascript_tool`. Hidden
  overlays keep their DOM (`#btnPeek` exists while hidden).

## Vault

- `C:\Users\sheep\code\obsidian\Projects\<slug>\<slug> plan.md` and
  `<slug> - rulebook.md`. Commit and push the vault after every plan
  change. Keep a Decisions list with absolute dates and a Next steps
  checklist with dates on the ticked items.

## Ship (M5) checklist

- Drop `noindex` on both pages; OG + Twitter cards; `VideoGame` JSON-LD;
  1200×630 social image (Pillow with local fonts works: `kaiu.ttf`,
  `NotoSerifTC-VF.ttf`); a crawlable paragraph on the landing.
- Hub (`C:\Users\sheep\code\games`): a tile in `index.html` painted from
  the game's own stylesheet in `css/style.css`, a `SITEMAP_URLS` line with
  lastmod, a `robots.txt` Sitemap pointer to the game's own sitemap if it
  has inner pages, the tile's fonts in the hub font link. Never list a
  page in the sitemap while it is still `noindex`.
- Search Console submission is the owner's manual step. AdSense is a
  separate decision.

## Licensing position (not legal advice)

Rules are not copyrightable; the trademark is the risk. Own name, own
setting, own faction words, own art and prose; credit the original once
in the footer as the design that inspired the play. Decide the name
before creating the repo — every rename so far cost a new repo, Worker
and URL.
