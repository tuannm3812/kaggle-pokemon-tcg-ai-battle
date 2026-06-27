# Submission Score Review and Improvement Strategy

## Current submission result

Checked on 2026-06-27.

| Field | Value |
| --- | --- |
| Accepted submission ref | `54100265` |
| Message | `fix deck loader missing __file__` |
| Status | `SubmissionStatus.COMPLETE` |
| Public score | `537.5` |
| Top public score at check time | `1404.2` |
| Top-200 cutoff observed from CLI page | approximately `985.5` |

The Kaggle CLI exposes submission status and public score, but it does not
expose per-ladder-game episode logs for completed submissions. Detailed episode
analysis therefore still needs UI replay/log exports when Kaggle provides them.

## What the score means

The competition uses a ladder rating. The rating changes from game outcomes:

- wins increase rating;
- losses decrease rating;
- draws move ratings together;
- win margin does not add extra reward.

Therefore the improvement target is higher win rate across ladder opponents,
not larger damage, faster wins, or larger prize margin in already-won games.

## What we learned before submission

The current submitted agent is a valid baseline, but it is strategically shallow:

- it uses a deterministic development-first main-phase order;
- it beat the official random control in local/Kaggle screens;
- planner v1/v2 did not beat the promoted control;
- switch v1/v2 did not beat the promoted control;
- the eight-Basic deck variant improved setup probability but did not improve
  outcomes against the starter deck.

The ladder score confirms the same story: the agent is valid and can win games,
but it is far below strong public agents.

## Strategy to improve score

### 1. Stop small generic sequencing tweaks

Recent narrow heuristics did not move the primary matchup:

- attack planner v2 vs promoted: `18-22`, score rate `0.450`;
- switch v1 vs promoted: `18-22`, score rate `0.450`;
- switch v2 vs promoted: `17-23`, score rate `0.425`.

These are not promising enough for more rule-by-rule tweaks without better
opponent modeling.

### 2. Build a stronger local opponent suite

The official random policy is too weak. The next evaluation suite should include
frozen author-style agents and our best held candidates:

- promoted baseline;
- planner v2;
- pressure control;
- at least two author reference deck policies;
- official random only as a regression smoke test.

Promotion should require beating promoted and not regressing against this
stronger suite.

### 3. Add tactical attack selection before retreat work

The current submitted policy often delays attacking because `ATTACK` is after
development actions. Local experiments showed development-first was better than
attack-first globally, but the next useful change is not global attack-first.

Instead, test a tactical override:

1. if an available attack can knock out the opponent active, attack immediately;
2. if no knockout is available, keep development-first ordering;
3. preserve legal fallback for unknown contexts.

This is narrower than the earlier broad planner and should be easier to
attribute.

### 4. Revisit deck composition only with outcome-backed tests

The eight-Basic experiment showed that better opening probability alone was not
enough. Deck experiments should now be tied to a measured tactical goal:

- fewer dead evolution hands;
- more reliable early Kyogre pressure;
- better Mega Abomasnow setup by turn window;
- lower mulligan or no-attacker losses.

Do not change deck and policy together in one experiment.

### 5. Use ladder submissions sparingly

The competition tracks only the latest two submissions. Keep:

1. one stable accepted baseline;
2. one candidate submission only after it clears local gates.

The next candidate should not be submitted until it beats the accepted baseline
in controlled tests.

## Recommended next experiment

Build `tactical_ko_v1`:

- freeze the current deck;
- start from the accepted baseline agent;
- add one override: choose an available attack when public state indicates an
  immediate knockout;
- evaluate against promoted, planner v2, pressure, random, and author-style
  controls;
- submit only if the promoted-control interval clears parity and no regression
  appears.

This is the best next use of effort because it directly targets win rate while
avoiding the broad planner changes that already failed their gates.
