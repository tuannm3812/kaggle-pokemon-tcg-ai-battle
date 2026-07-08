# Cross-Submission Meta Insights

Date: 2026-07-08

## Purpose

Compare refreshed public replay performance across the main submitted branches:

- `v1`: `54303967`, active-best leaderboard score `864.5`
- `v8`: `54391951`, public Boss guard, leaderboard score `808.6`
- `v5`: `54348833`, metal pressure, leaderboard score `724.6`

This note turns the refreshed episode summaries into strategy guidance for the
next candidate cycle.

## Overall public replay sample

| Branch | Games | Record | Replay score rate | Leaderboard public score |
| --- | ---: | ---: | ---: | ---: |
| v1 | 135 | 73-62 | 0.5407 | 864.5 |
| v8 | 76 | 46-30 | 0.6053 | 808.6 |
| v5 | 103 | 54-49 | 0.5243 | 724.6 |

The replay score rate alone is not enough to choose a submission. v8 has a
better observed replay score rate than v1, but v1 remains much stronger on the
leaderboard. This means branch quality depends heavily on which archetypes the
matchmaker exposes and how expensive specific losses are.

## Archetype comparison

| Archetype | v1 n | v1 score | v8 n | v8 score | v5 n | v5 score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alakazam/Dunsparce | 14 | 0.3571 | 8 | 0.3750 | 13 | 0.3846 |
| Crustle/library-out | 5 | 0.6000 | 9 | 0.8889 | 5 | 0.2000 |
| Dragapult | 10 | 0.7000 | 5 | 0.0000 | 9 | 0.6667 |
| Grimmsnarl | 14 | 0.7857 | 6 | 0.5000 | 9 | 0.5556 |
| Lucario | 38 | 0.6053 | 20 | 0.7500 | 21 | 0.6190 |
| Metal/Cinderace | 34 | 0.3824 | 17 | 0.7059 | 19 | 0.5263 |
| Phantump/Trevenant control | 4 | 0.2500 | 4 | 0.0000 | 4 | 0.0000 |

## Key insights

### 1. V8's useful signal is real but unsafe

V8 is clearly better than v1 in:

- Metal/Cinderace: `0.7059` vs `0.3824`
- Crustle/library-out: `0.8889` vs `0.6000`
- Lucario: `0.7500` vs `0.6053`

But it is catastrophic in:

- Dragapult: `0.0000` vs v1 `0.7000`
- Phantump/Trevenant: `0.0000` vs v1 `0.2500`

This explains why v8 can look good in refreshed local public replays but remain
below v1 on the leaderboard. The failure mode is narrow but severe.

### 2. V5 is not the missing bridge

V5 improves Metal/Cinderace relative to v1, but not enough:

- Metal/Cinderace: v5 `0.5263`, v8 `0.7059`

It also fails badly into Crustle/library-out and Phantump/Trevenant. V5 should
remain a diagnostic branch, not a promotion base.

### 3. Alakazam/Dunsparce remains unsolved

All three branches are weak:

- v1: `0.3571`
- v8: `0.3750`
- v5: `0.3846`

No current branch provides a convincing Alakazam answer. A future Alakazam
candidate needs a separate diagnosis rather than borrowing from v5/v8.

### 4. Dragapult is the protected matchup

The single most important guardrail is Dragapult. V1 handles it well, while v8
collapses. Any candidate that imports v8 behavior must prove it does not break
Dragapult before submission.

## Strategy conclusion

The next strong candidate should not be a simple v1/v8 blend. We already tried
several local patches that borrowed pieces of v8, and none cleared the gate.

The right next experiment is a **Dragapult-safe Metal/Cinderace adapter**:

- start from v1;
- activate only when the opponent shows Metal/Cinderace;
- explicitly deactivate if Dragapult or Phantump/Trevenant cards are visible;
- avoid changing setup, Lucario, and library-out behavior;
- measure with public-meta gate plus exact public replay deltas.

## Submit status

No new branch is submit-ready.

Active-best remains:

`kojimar_simple_baseline_v1`

Public score: `864.5`
