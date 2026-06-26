# Conservative Switch v1 Results

## Scope

The private Kaggle notebook
[pokemon-tcg-conservative-switch-experiment](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-conservative-switch-experiment)
version 1 evaluated `conservative_switch_v1` on 2026-06-26.

Production remains unchanged. `agent/main.py` and `agent/deck.csv` were not
modified.

## Candidate

`conservative_switch_v1` keeps the promoted development-first policy except for
one narrow trigger:

- `RETREAT` is legal;
- the active Pokémon has no attached Energy;
- at least one benched Pokémon has at least one attached Energy.

Only in that condition does the candidate prioritize retreat and then choose a
ready benched target.

## Matchup results

| Matchup | Games | W-L | Score rate | Bootstrap 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| switch v1 vs planner v2 | 40 | 19-21 | 0.475 | [0.325, 0.625] | Hold |
| switch v1 vs pressure | 40 | 35-5 | 0.875 | [0.775, 0.975] | Regression pass |
| switch v1 vs promoted | 40 | 18-22 | 0.450 | [0.300, 0.600] | Hold |
| switch v1 vs random | 40 | 29-11 | 0.725 | [0.575, 0.850] | Regression pass |

The notebook decision was **HOLD** because at least one required interval
overlapped parity. The primary matchup against promoted also had a below-parity
point estimate.

## Mechanism check

| Matchup | Main decisions | Retreat available | Retreat chosen | Ready bench | Unready active |
| --- | ---: | ---: | ---: | ---: | ---: |
| switch v1 vs planner v2 | 404 | 0.136 | 0.000 | 0.000 | 0.163 |
| switch v1 vs pressure | 895 | 0.571 | 0.000 | 0.000 | 0.056 |
| switch v1 vs promoted | 550 | 0.311 | 0.000 | 0.000 | 0.133 |
| switch v1 vs random | 574 | 0.193 | 0.000 | 0.000 | 0.091 |

The candidate never chose `RETREAT`. This means the implementation was legal
and stable, but the trigger was too narrow for observed games: retreat was often
available, yet a ready benched attacker was never observed under the telemetry.

## Interpretation

Do not promote or submit `conservative_switch_v1`.

The previous loss taxonomy correctly identified a switch/retreat blind spot, but
the first candidate translated that signal too literally. The broader issue is
not only "ready bench with unready active"; it is that the promoted policy has no
retreat model at all.

## Next candidate

The next switch experiment should stay conservative but use a broader trigger:

1. retreat when the active Pokémon is heavily damaged and a benched Pokémon can
   preserve board stability;
2. retreat when the active Pokémon has no useful attack while a benched Pokémon
   has attached Energy or higher HP;
3. avoid retreat if it discards scarce Energy or prevents an immediate attack.

This should be evaluated with the same controlled seat/turn-order design before
any production change.
