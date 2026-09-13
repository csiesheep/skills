# <Game name> — plan

Created <YYYY-MM-DD>. Repo `csiesheep/<slug>`, live at
`https://games.csiesheep.com/<slug>/` (not yet).

## Overview
One paragraph: what the game is, how many players, how long a game, what
the web version adds (solo vs bots, rooms with a 4-letter code, en +
zh-Hant, phone-first). Fan-made, unofficial; own name and setting.

## Why this shape
Which sibling repo it is modelled on and what is reused (router, rooms,
harness). What is new to this game.

## Licensing
Original title, designer, publisher. Rules not copyrightable; trademark
risk in the title. Own name chosen: `<name> / <中文>`. Credit line text.
*Not legal advice.*

## Source material
Links to the rulebook(s) used; the rulebook note `[[<slug> - rulebook]]`;
unclear points across sources and how v1 resolves each.

## Theme
| slot | original | now (zh) | now (en) |
|---|---|---|---|
| title | | | |
| sides / roles | | | |
| bot names | | | |
| favicon | | | |

### Look
Tokens once chosen: ground, ink, accents and what each colour means;
display and body faces; corner and rule style. Link to the design canvas.

## Rules in scope (v1 = base game, exactly)
Player counts, setup, turn structure, win conditions, every table.
Expansions and variants listed as data-driven later work.

## Architecture
- Worker + prefix router, static assets, one DO per room.
- `engine.js`: state shape, actions, `view(state, seat)`, RNG.
- `bots.js`: what the AI reasons about; level knobs; `why` for talk.
- `room.js`: phase clocks, grace period, bot fill, idle deletion.
- Solo driver in `app.js`.

## Pages and UI
| Route | View | What is on it |
|---|---|---|
| `/<slug>/` | Landing | |
| `?play` | Solo setup | |
| `?room=ABCD` | Lobby | |
| (in game) | Table | |
| (in game) | Game over | |
| `/<slug>/rules` | Rulebook | |

Mockup link. Phone-first.

## Bots and balance
Approach; levels; the harness (`node tests/sim.js <games> <n or 0> …`);
target win rates and what "feels human" means for this game.

## Milestones
- M0 Scaffold: router, placeholder, deploy, routes verified.
- M1 Engine + tests (incl. a fuzz test over legal moves).
- M2 Bots + harness, win-rate table.
- M3 Solo UI, bot talk, i18n, rules page.
- M4 Rooms: DO, clocks, chat, bot fill, reconnect, rematch.
- M5 Ship: noindex off, OG, JSON-LD, hub tile, sitemap.

## Open questions (decide before M0)
1. … — recommendation: …

## Decisions
- **<YYYY-MM-DD>** — …

## Next steps
- [ ] Owner confirms the plan and the open questions above.
- [ ] M0 …
