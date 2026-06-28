# Conservative Switch v2 Results

## Scope

The private Kaggle notebook
[pokemon-tcg-conservative-switch-v2-experiment](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-conservative-switch-v2-experiment)
version 2 evaluated `conservative_switch_v2` on 2026-06-26.

Production remains unchanged. `agent/main.py` and `agent/deck.csv` were not
modified.

## Candidate

Switch v2 broadened switch v1's trigger. It prioritizes legal `RETREAT` when:

- the active Pokémon has no attached Energy and the bench has either attached
  Energy or at least 30 more HP; or
- the active Pokémon has 80 HP or less and the bench has at least 50 more HP.

When choosing the new active Pokémon, it prefers higher HP, then attached
Energy, then Mega Abomasnow ex or Kyogre.

## Matchup results

| Matchup | Games | W-L | Score rate | Bootstrap 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| switch v2 vs planner v2 | 40 | 18-22 | 0.450 | [0.300, 0.600] | Hold |
| switch v2 vs pressure | 40 | 30-10 | 0.750 | [0.600, 0.875] | Regression pass |
| switch v2 vs promoted | 40 | 17-23 | 0.425 | [0.275, 0.575] | Hold |
| switch v2 vs random | 40 | 34-6 | 0.850 | [0.725, 0.950] | Regression pass |

The notebook decision was **HOLD** because at least one required interval
overlapped parity. The primary promoted-control point estimate was below
parity, so switch v2 should not be promoted or submitted.

## Mechanism check

| Matchup | Main decisions | Retreat available | Retreat chosen | Ready bench | Unready active |
| --- | ---: | ---: | ---: | ---: | ---: |
| switch v2 vs planner v2 | 607 | 0.341 | 0.0049 | 0.000 | 0.117 |
| switch v2 vs pressure | 1200 | 0.593 | 0.0125 | 0.091 | 0.053 |
| switch v2 vs promoted | 684 | 0.468 | 0.0015 | 0.000 | 0.099 |
| switch v2 vs random | 584 | 0.250 | 0.0103 | 0.027 | 0.116 |

Switch v2 did exercise `RETREAT`, unlike v1, but the frequency was very low and
did not improve the primary matchup. This suggests retreat rules alone are not
the right next production change unless they are tied to more precise tactical
state.

## Decision

Do not promote or submit switch v2.

The current promoted production agent remains the best submission candidate in
the repository. It is valid to submit as a baseline or smoke submission, but not
because switch v2 improved it.

## Next recommendation

Stop expanding retreat heuristics for now. The next useful step is a submission
readiness pass on the promoted agent:

1. rerun the packaging notebook;
2. verify the tarball contains only `main.py`, `deck.csv`, and `cg/`;
3. submit the current promoted agent if the goal is to establish a competition
   baseline;
4. only resume policy changes after leaderboard feedback or stronger local
   opponent evidence identifies a larger gap.
