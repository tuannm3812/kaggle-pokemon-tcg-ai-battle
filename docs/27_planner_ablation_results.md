# Planner Ablation Results

## Scope

This step moved from setup-active experiments to planner ablations, as
recommended after the setup variants failed to produce a safe submission
candidate.

New candidates:

- `candidates/planner_main_only_v1/`
- `candidates/planner_no_retreat_v1/`

Production remains unchanged.

## Candidate designs

### `planner_main_only_v1`

Starts from `abomasnow_planner_v2` but removes planner scoring for non-main
`CARD` prompts.

It keeps only the planner's main-phase attack/attach/evolve/play scoring when a
public attack plan is confident. This directly tests whether planner v2's direct
weakness came from broad card-selection scoring.

### `planner_no_retreat_v1`

Starts from `abomasnow_planner_v2` but disables the positive retreat override.

This tested whether planner v2's direct weakness came from retreating into a
planned bench attacker too aggressively.

## Direct promoted-control gates

Commands:

```powershell
python scripts\evaluate_direct_gate.py --candidate planner_main_only_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062807
python scripts\evaluate_direct_gate.py --candidate planner_no_retreat_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062808
```

Results:

| Candidate | Games | W-L | Score rate | Approx. 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| planner_main_only_v1 | 80 | 47-33 | 0.588 | [0.510, 0.661] | Promote candidate |
| planner_no_retreat_v1 | 80 | 40-40 | 0.500 | [0.423, 0.577] | Reject |

`planner_main_only_v1` still has one weak controlled cell, but unlike earlier
candidates its aggregate interval clears parity.

| Candidate seat | Player zero first? | planner_main_only_v1 score |
| ---: | --- | ---: |
| 0 | false | 8/20 |
| 0 | true | 16/20 |
| 1 | false | 17/20 |
| 1 | true | 6/20 |

## Random regression

Command:

```powershell
python scripts\evaluate_direct_gate.py --candidate planner_main_only_v1 --control official_random --games-per-cell 10 --max-decisions 2500 --seed 2026062809
```

Result:

| Matchup | Games | W-L | Score rate | Approx. 95% interval | Failures |
| --- | ---: | ---: | ---: | --- | ---: |
| planner_main_only_v1 vs official random | 40 | 32-8 | 0.800 | [0.700, 0.873] | 0 |

## Author-suite screen

Command:

```powershell
python scripts\evaluate_author_opponent_suite.py --games-per-cell 3 --max-decisions 2500 --seed 2026062810
```

Selected results:

| Candidate | Aggregate | Abomasnow | Lucario | Dragapult | Iono | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| promoted | 23/48 = 0.479 | 0.417 | 0.333 | 0.667 | 0.500 | Baseline |
| planner v2 | 29/48 = 0.604 | 0.417 | 0.583 | 0.833 | 0.583 | Hold |
| planner_main_only_v1 | 32/48 = 0.667 | 0.500 | 0.583 | 0.917 | 0.667 | Best |
| planner_no_retreat_v1 | 28/48 = 0.583 | 0.500 | 0.500 | 1.000 | 0.333 | Reject |

`planner_main_only_v1` is the first candidate to clear:

- direct promoted-control gate;
- official random regression;
- author-style coverage screen;
- zero runtime failures.

## Decision

`planner_main_only_v1` is a legitimate promotion candidate.

Do not replace production or submit automatically without an explicit submission
step, but this is now the best candidate to package next.

## Next recommendation

Prepare a Kaggle submission package from `planner_main_only_v1`, validate it
locally, and submit only if packaging validation passes.

After submission, compare the leaderboard score against the current accepted
baseline score of `537.5`.
