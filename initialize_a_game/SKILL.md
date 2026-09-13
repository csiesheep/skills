---
name: initialize_a_game
description: |
  Kick off a new browser board game for games.csiesheep.com/<game>/ from a board game's name: find the rulebook, settle the name and licensing, write the implementation plan, mock up the pages, create the Obsidian plan note and the GitHub repo — then STOP and wait for the owner's confirmation before implementing anything.
  Trigger on "/initialize_a_game <name>", "initialize a game", "start a new game project", "kick off <board game> web version". Not for games that already have a repo.
---

# Initialize a game

One command turns a board game's name into a project ready to build:
rulebook → name/licensing → plan → mockups → vault note → repo → **wait**.

The output of this skill is a decision package, not code. Everything after
the owner says "go" belongs to the plan's milestones, not to this skill.

## Inputs

`/initialize_a_game <board game name> [slug]`

- **board game name**: the published game to base the web version on
  (e.g. "The Resistance", "Coup", "Love Letter").
- **slug** (optional): the URL and repo name, `snake_case`, ASCII. If
  omitted, propose one and confirm it in the first message. The slug
  becomes `games.csiesheep.com/<slug>/`, repo `csiesheep/<slug>`, Worker
  name `<slug>`, and the vault folder `Projects/<slug>/`.

Defaults every project has had so far (say them, do not re-ask):
solo vs AI **and** online rooms with bots filling seats; English +
Traditional Chinese from v1; phone-first; fan-made and unofficial; deploy
as one Cloudflare Worker under the `games` hub. Ask only when the game
makes one of these wrong (a two-player game has no "bots fill seats").

## Steps

Read `references/conventions.md` first — it holds the platform, repo, vault
and deploy conventions the sibling games follow, and the lessons that cost
time before. Match them; the hub expects one shape.

### 1. Rulebook

- Search for the official rulebook (publisher PDF, BGG files, the
  designer's page). Fetch it; if a PDF will not render, extract text
  (`pypdf`, `PYTHONIOENCODING=utf-8`).
- Write `references`-grade notes in your own words into
  `Projects/<slug>/<slug> - rulebook.md` in the vault: components, setup
  by player count, turn structure, win conditions, every table (player
  counts, team sizes, special cases), official variants and expansions.
  Tables as markdown tables. Never paste rulebook prose.
- List what is unclear or contradictory across sources. Those are the
  unknowns the engine tests must pin down.

### 2. Name and licensing — decide this BEFORE the repo exists

Rules and mechanics are not copyrightable; **the product name is a
trademark**, and using it as the name of a similar product on a page with
ads is the real exposure. "Fan-made, unofficial" mitigates, it does not
defend. The Resistance → 天地會 and Zombie in My Pocket → Grave Errand were
both renamed after the fact; renaming later means a new repo, new Worker,
new routes and an orphaned URL.

So, in the first message to the owner:
- Explain the risk in two sentences.
- Propose 3–5 own names (bilingual) with an own setting and faction words
  that keep the play but drop the publisher's title, and recommend one.
- Ask whether to ship under the own name (recommended) or the original
  with a credit line.

The chosen name decides the slug, the repo and every string. Credit the
original exactly once, in the footer, as the design that inspired the
play. No official art, no lifted text, own rules page. Say "not legal
advice".

### 3. Plan

Write `Projects/<slug>/<slug> plan.md` from `references/plan-template.md`.
Fill every section with this game's specifics; keep the milestone shape
M0–M5 (scaffold → engine → bots → solo → rooms → ship), because the
sibling repos and the hub are built for it. Include:
- the rules in scope for v1 (base game exactly; expansions data-driven
  later),
- the bot approach (what the AI must reason about; for hidden-role games a
  posterior over role assignments, for area games a scored search),
- the balance harness (bot-vs-bot, N games per cell, child processes),
- open questions with your recommended answer for each.

Convert relative dates to absolute. Commit the vault with a short message
and push.

### 4. Pages and UI

Show, do not describe: publish a mockup the owner can look at.
- Prefer the `design` skill (a canvas of phone artboards, 390×844) when it
  is available; otherwise a single HTML artifact with the phone frames
  side by side.
- One artboard per page: landing, setup, lobby, reveal/setup-in-game, the
  main table (two or three states), game over, rules. Real copy in both
  languages, no lorem ipsum.
- Settle the aesthetic with the owner: sketch two or three directions
  first if the setting is open; if the owner already named a theme (a
  Qing-era brotherhood, a haunted mortuary), commit to it and show one.
- Record the chosen tokens (colours, type, semantics of each colour) in
  the plan's "Look" section once picked.

### 5. Repo

Only after the name is settled:
```bash
gh repo create csiesheep/<slug> --public --description "<one line>"
```
Scaffold from the newest sibling repo (`tiandihui` today) rather than from
scratch: copy `wrangler.jsonc`, `package.json`, `src/index.js` (prefix
router), `public/` skeleton, `tests/` layout; strip the old game's engine,
bots, strings and art. Set the git identity per conventions, commit the
scaffold, push. Do not deploy yet unless the owner asks for a placeholder
at the URL (M0 is a separate step).

### 6. Stop

End with one message containing: the recommended name, the rulebook note
link, the plan note link, the mockup link, the repo link, and the open
questions as a short numbered list with your recommendation for each.
Then wait. Implementation begins only when the owner confirms.

## Conventions the owner expects in replies

- Traditional Chinese unless the owner writes in English; lead with the
  outcome; short sentences; numbers in tables; no em dashes.
- Commit trailer as the session's system reminder specifies.
- After every change to the plan, commit the vault.
- Never claim something is deployed or verified without having checked the
  live bytes.
