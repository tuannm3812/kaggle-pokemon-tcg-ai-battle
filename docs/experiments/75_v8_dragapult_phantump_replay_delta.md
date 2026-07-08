# V8 Dragapult / Phantump Replay Delta

Date: 2026-07-08

## Purpose

The previous opening-category analysis showed that setup-active rewrites are not
the obvious next improvement. This experiment checks whether v8's weak public
results into Dragapult and Phantump/Trevenant are caused by actual policy
differences from v1, or by replay sampling / opponent signature mix.

Compared submissions:

- v1 / `54303967` / active public best, score `864.5`
- v8 / `54391951` / public Boss guard, score `808.6`
- v5 / `54348833` / metal pressure branch, score `724.6`

Focused archetypes:

- Dragapult
- Phantump/Trevenant control

## Commands

```powershell
python scripts/diagnose_public_loss_replays.py --submission-id 54391951 --archetypes dragapult phantump_trevenant_control --max-turn 9 --losses-only

$env:POKEMON_TCG_RUNTIME_ROOT = (Join-Path (Resolve-Path 'scratch').Path 'delta_runtime_v8_vs_v1_dragapult_phantump')
python scripts/compare_midgame_decision_deltas.py --candidate kojimar_simple_baseline_v8_public_boss_guard --reference kojimar_simple_baseline_v1 --submission-id 54391951 --loss-diagnostics scratch\loss_diagnostics\54391951_dragapult-phantump_trevenant_control_losses.json --archetypes dragapult phantump_trevenant_control --start-turn 1 --end-turn 9 --max-states 80

python scripts/compare_signature_outcomes.py --submission-ids 54303967 54391951 54348833 --archetypes dragapult phantump_trevenant_control --output-stem v1-v8-v5_dragapult_phantump
```

Artifacts:

- `scratch/loss_diagnostics/54391951_dragapult-phantump_trevenant_control_losses.json`
- `scratch/loss_diagnostics/54391951_dragapult-phantump_trevenant_control_losses.md`
- `scratch/midgame_decision_deltas/kojimar_simple_baseline_v8_public_boss_guard_vs_kojimar_simple_baseline_v1_54391951_t1_9.json`
- `scratch/signature_outcomes/v1-v8-v5_dragapult_phantump.json`
- `scratch/signature_outcomes/v1-v8-v5_dragapult_phantump.md`

## Loss replay diagnosis

V8 public losses:

| Archetype | Losses | Went first | First attack turns | Median first attack |
| --- | ---: | ---: | --- | ---: |
| Dragapult | 5 | 5/5 | 5, 5, 13, 3, 3 | 5 |
| Phantump/Trevenant control | 4 | 4/4 | 3, 3, 7, 3 | 3 |

The losses are not simply caused by going second or never attacking. In these
sampled losses we usually went first and attacked by turn 3-5, with one slow
Dragapult loss at turn 13 and one slower Phantump/Trevenant loss at turn 7.

## V8 vs v1 decision delta

The focused decision-delta check produced:

| Archetype | States checked | Changed decisions | Changed rate |
| --- | ---: | ---: | ---: |
| Dragapult | 40 | 0 | 0.0000 |
| Phantump/Trevenant control | 40 | 0 | 0.0000 |
| Total | 80 | 0 | 0.0000 |

This is the most important result in this pass: v8 and v1 make identical
decisions on the sampled early/midgame states from v8's Dragapult and
Phantump/Trevenant public losses.

## Exact signature outcomes

### Dragapult

The most repeated Dragapult signature appears in all three branches:

`Basic {P} Energy x4, Basic {R} Energy x4, Drakloak x4, Dreepy x4, Dragapult ex x3, Budew x2, Fezandipiti ex x1, Latias ex x1`

| Submission | Record | Score | Went first |
| --- | ---: | ---: | ---: |
| v1 / `54303967` | 3-3 | 0.5000 | 6/6 |
| v5 / `54348833` | 3-0 | 1.0000 | 2/3 |
| v8 / `54391951` | 0-3 | 0.0000 | 3/3 |

This does not prove that v8 is bad into this exact Dragapult list. The decision
delta says v8 and v1 behave identically in sampled loss states, and all v8 games
in this signature are only three games. The safer interpretation is that this
Dragapult cluster is high variance and dangerous, but not yet a clean policy
delta target.

### Phantump/Trevenant control

The most repeated Phantump/Trevenant signature is:

`Hop's Phantump x4, Hop's Trevenant x4, Mist Energy x4, Telepath Psychic Energy x4, Hop’s Cramorant x3, Hop’s Snorlax x2`

| Submission | Record | Score | Went first |
| --- | ---: | ---: | ---: |
| v1 / `54303967` | 1-1 | 0.5000 | 2/2 |
| v5 / `54348833` | 0-2 | 0.0000 | 2/2 |
| v8 / `54391951` | 0-3 | 0.0000 | 3/3 |

The second repeated Phantump/Trevenant signature is also poor:

`Dunsparce x4, Hop's Phantump x4, Mist Energy x4, Telepath Psychic Energy x4, Dudunsparce x3, Hop's Trevenant x2, Hop’s Snorlax x2, Legacy Energy x1`

| Submission | Record | Score | Went first |
| --- | ---: | ---: | ---: |
| v1 / `54303967` | 0-2 | 0.0000 | 1/2 |
| v5 / `54348833` | 0-2 | 0.0000 | 1/2 |

This looks more actionable than Dragapult. Phantump/Trevenant is not just a v8
collapse; it is a recurring control matchup problem across branches.

## Insights

### 1. Do not build another broad v8-style candidate yet

V8 still has attractive public strengths into Metal/Cinderace, Lucario, and
library-out, but the Dragapult/Phantump replay delta did not reveal a behavioral
change we can surgically copy or revert. Broadly promoting more v8 behavior
risks trading away v1's current leaderboard stability.

### 2. Dragapult should be treated as protected, not optimized from this sample

V8's Dragapult result is scary, but the shared exact signature has:

- v1: `3-3`
- v5: `3-0`
- v8: `0-3`

With identical sampled decisions between v1 and v8, this is not enough evidence
to justify a Dragapult-specific rewrite. The next candidate should avoid making
Dragapult worse, but should not be centered on Dragapult from this evidence
alone.

### 3. Phantump/Trevenant is the stronger candidate target

Phantump/Trevenant control repeatedly beats multiple branches even when we go
first and attack early. The core problem is likely not opening speed alone; it
is probably pressure allocation against Hop's Phantump / Hop's Trevenant /
Hop's Cramorant / Hop's Snorlax boards.

### 4. The next useful candidate should be narrow

The next candidate should start from v1 and add a narrow control-matchup rule,
not a broad archetype router. The safest shape is:

1. Detect exact or near-exact Phantump/Trevenant signatures.
2. Preserve v1 decisions everywhere else.
3. In the control matchup, prefer pressure on evolving Phantump/Trevenant lines
   when a knockout or meaningful damage race is available.
4. Gate against v1, v8, v5, Lucario v3, library-out, and random so we catch
   regressions before submission.

## Decision

No new submission yet.

The replay-delta path produced an insight, not a submit-ready candidate. The
next experiment should be a v1-based Phantump/Trevenant pressure candidate with
strict regression gates.
