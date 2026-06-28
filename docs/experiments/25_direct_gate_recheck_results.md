# Direct Gate Recheck Results

## Scope

This step converted the one-off direct candidate-vs-promoted check into a
repeatable script and reran the promotion gates with explicit Python and NumPy
RNG seeding.

New script:

- `scripts/evaluate_direct_gate.py`

Updated shared runner:

- `scripts/evaluate_author_opponent_suite.py` now seeds both Python `random`
  and NumPy before each game.

This matters because repeated gates with the same Python seed were not stable
until NumPy was also seeded.

## Direct promoted-control gates

### `setup_active_v1`

Command:

```powershell
python scripts\evaluate_direct_gate.py --candidate setup_active_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 20260628
```

Result:

| Matchup | Games | W-L | Score rate | Approx. 95% interval | Failures |
| --- | ---: | ---: | ---: | --- | ---: |
| setup_active_v1 vs promoted | 80 | 51-29 | 0.638 | [0.561, 0.708] | 0 |

Cell split:

| Candidate seat | Player zero first? | Score |
| ---: | --- | ---: |
| 0 | false | 9/20 |
| 0 | true | 14/20 |
| 1 | false | 16/20 |
| 1 | true | 12/20 |

### `planner_v2`

Command:

```powershell
python scripts\evaluate_direct_gate.py --candidate planner_v2 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062803
```

Result:

| Matchup | Games | W-L | Score rate | Approx. 95% interval | Failures |
| --- | ---: | ---: | ---: | --- | ---: |
| planner_v2 vs promoted | 80 | 43-37 | 0.538 | [0.460, 0.613] | 0 |

Planner v2 still does not clear the direct promoted-control gate.

## Random regression

Command:

```powershell
python scripts\evaluate_direct_gate.py --candidate setup_active_v1 --control official_random --games-per-cell 10 --max-decisions 2500 --seed 2026062802
```

Result:

| Matchup | Games | W-L | Score rate | Approx. 95% interval | Failures |
| --- | ---: | ---: | ---: | --- | ---: |
| setup_active_v1 vs official random | 40 | 30-10 | 0.750 | [0.645, 0.832] | 0 |

## Reproducible author-suite recheck

Command:

```powershell
python scripts\evaluate_author_opponent_suite.py --games-per-cell 3 --max-decisions 2500 --seed 20260627
```

Selected aggregate results:

| Candidate | Aggregate | Abomasnow | Lucario | Dragapult | Iono | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| promoted | 28/48 = 0.583 | 0.500 | 0.583 | 0.667 | 0.583 | Baseline |
| setup_active_v1 | 24/48 = 0.500 | 0.500 | 0.667 | 0.500 | 0.333 | Reject for author regression |
| planner_v2 | 32/48 = 0.667 | 0.500 | 0.667 | 1.000 | 0.500 | Hold, direct gate weak |
| card_selection_v1 | 29/48 = 0.604 | 0.583 | 0.333 | 0.833 | 0.667 | Reject for Lucario regression |

## Decision

Do not submit yet.

`setup_active_v1` clears the promoted-control gate and random regression, but
the reproducible author suite exposes a serious Iono-style regression. That is
too risky for the ladder.

`planner_v2` looks strongest in the author suite, but still fails to separate
from promoted in the 80-game direct gate.

## Next recommendation

Use the reproducible gates going forward and stop relying on any pre-seeding
results.

The next candidate should target the tradeoff directly:

1. start from promoted or planner v2;
2. preserve the Iono-safe behavior from `card_selection_v1`;
3. avoid the Lucario regression from broad card-selection scoring;
4. pass both gates:
   - direct promoted-control interval above parity;
   - no author-policy matchup below `0.45`.

Until that happens, keep production unchanged.
