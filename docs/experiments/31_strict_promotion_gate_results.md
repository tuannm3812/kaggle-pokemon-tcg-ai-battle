# Strict Promotion Gate Results

## Scope

This step upgraded the evaluator after `planner_main_only_v1` validated locally
but underperformed on the Kaggle ladder.

New evaluation assets:

- `controls/anti_planner_pressure_v1/`
- `scripts/evaluate_promotion_gate.py`

## Anti-planner pressure control

The first idea was to add a frozen attack-pressure opponent that punishes
over-planning and delayed attacks.

Results:

| Matchup | Games | W-L | Score rate | Decision |
| --- | ---: | ---: | ---: | --- |
| promoted vs anti-planner pressure v1 | 80 | 68-12 | 0.850 | Control too weak |
| planner_main_only_v1 vs anti-planner pressure v1 | 80 | 77-3 | 0.963 | Does not catch planner risk |

This control is useful as a smoke opponent, but it does not catch the known
ladder-risk pattern. Do not use it as a promotion gate.

## Strict promotion gate

The useful lesson was not a new opponent; it was a stricter decision rule.

`scripts/evaluate_promotion_gate.py` now checks saved evaluation artifacts and
requires:

- direct promoted-control interval lower bound above parity;
- no controlled seat/first-player cell below `0.40`;
- official-random score at least `0.65`;
- no author-style matchup below `0.45`.

## Backtest on failed ladder candidate

Command:

```powershell
python scripts\evaluate_promotion_gate.py --candidate planner_main_only_v1
```

Result:

| Field | Value |
| --- | --- |
| Candidate | `planner_main_only_v1` |
| Decision | `REJECT` |
| Direct score | `0.5875` |
| Direct interval low | `0.510` |
| Random score | `0.800` |
| Rejection reason | `seat_1_player_zero_first_true=0.300` |

The stricter gate would have blocked `planner_main_only_v1` even though its
aggregate direct score looked good. This now captures the known post-submission
failure mode better than the previous gate.

## Decision

Use the strict promotion gate for every future submission candidate.

No candidate should be packaged for Kaggle unless:

```powershell
python scripts\evaluate_promotion_gate.py --candidate <candidate_name>
```

returns `PROMOTE`.

## Next recommendation

The next agent experiment should specifically improve the weak
`seat_1_player_zero_first_true` split without damaging author-style matchups.
Until then, keep production unchanged and do not submit another candidate.
