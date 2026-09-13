# skills

Claude Code skills, distilled from real projects rather than written from
first principles. Each one exists because a specific way of working kept
paying off, or a specific way of failing kept recurring.

## Installing

Copy a skill's directory into `~/.claude/skills/`:

```bash
git clone https://github.com/csiesheep/skills.git
cp -r skills/agent-team-delivery ~/.claude/skills/
```

Claude Code picks it up on the next session. Invoke it by name, or let it
trigger on the phrases listed in its frontmatter.

## What's here

| Skill | What it's for |
|---|---|
| [`agent-team-delivery`](agent-team-delivery/SKILL.md) | Running several Claude sessions as a team: one orchestrator that prioritises, files issues, dispatches, verifies independently, and only then lands; peers that implement in their own worktrees. |
| [`initialize_a_game`](initialize_a_game/SKILL.md) | Turning a board game's name into a project ready to build for the games hub: rulebook digest, name and licensing call, plan note, phone mockups, repo scaffold, then stop and wait for the owner. |

### agent-team-delivery

Written in Traditional Chinese. Roughly half of it is a **failure
catalogue** — the ways a verification instrument lies to you while you are
working carefully:

- a cached build feeding you the old bytes while you measure the new ones
- a check that derives its expected value from the thing it is checking, so
  breaking the rule breaks the expectation too and the test stays green
- validating an instrument in the range where it works, which says nothing
  about the range where it doesn't
- a true statement carrying a scope wider than the evidence supports
- a test name promising more than its assertions check
- an absence-claim that passes because the population was empty
- a dispatch that reports success without ever being delivered
- sampling a curve at the points where two rival explanations agree
- asking a peer to report back over a channel that has no return path
- a watcher that fires on activity rather than on completion
- a correct diagnosis that outlives the condition it diagnosed
- measuring someone else's server, because yours never bound to the port
- a peer blocked on a confirmation you never knew it was waiting for
- an index still holding the old tree after a rejected push, staged to revert
- averaging across a transient and comparing it against an instantaneous reading
- a drain-style API whose return value carries the measurement you discarded
- the guard you keep citing as authoritative, which no one ever made go red
- an absence-check whose observer is watching nothing, reporting a confident zero
- naming a bug as a class, writing it up, and never sweeping for the second copy
- publishing your own inference under the principal's name, in durable content
- proving you have a permission, when the fix is to need no permission
- relaying a peer's true-when-written measurement as the tree's current state
- specifying a dimension because it is easy to assert, when reachability is the property
- a viewport that "fits" because the overflow was silently discarded

Every entry happened. The governing idea:

> The value of verification is not "I looked at it." It is "I made it go red
> once."

## Licence

MIT.

### initialize_a_game

One command, `/initialize_a_game <board game name>`, produces a decision
package rather than code: a rulebook digest in the owner's own words with
every table and the unclear points listed, a name-and-licensing proposal
(rules are not copyrightable, the title is a trademark, so pick an own name
*before* the repo exists), an implementation plan on the M0–M5 shape the
sibling games share, a canvas of phone mockups in both languages, and a
scaffolded repo copied from the newest sibling. Then it stops. The
`references/` folder carries the platform, repo, vault and deploy
conventions the hub expects, and the plan template.
