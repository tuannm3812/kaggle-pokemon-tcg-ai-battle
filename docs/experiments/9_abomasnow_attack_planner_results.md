# Abomasnow Attack-Planner Results

## Scope

Two private Kaggle experiments evaluated a stateless Mega Abomasnow/Kyogre attack planner while freezing the production deck and promoted policy:

- [Planner v1](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-abomasnow-attack-planner), version 1.
- [Planner v2 resource guards](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-abomasnow-resource-guards), version 1.

Neither candidate is promoted. `agent/main.py` and `agent/deck.csv` remain unchanged.

## Planner v1

V1 reconstructs a plan from each observation and coordinates its intended Kyogre or Mega Abomasnow ex attacker, expected damage, attachment target, evolution, switching, setup, search, discard, and immediate knockouts. It uses the promoted development-first legality fallback whenever confidence is low.

| Matchup | Games | W-L | Score rate | Bootstrap 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| v1 vs promoted | 40 | 25-15 | 0.625 | [0.475, 0.775] | Hold |
| v1 vs random | 40 | 30-10 | 0.750 | [0.625, 0.875] | Regression pass |

All 80 games completed without failures. The primary interval overlapped parity, so the predefined decision was **HOLD**.

### V1 mechanism finding

Against promoted, the planner reported a confident plan in 288 of 395 main decisions. Kyogre accounted for 218 of those planned states, but its estimated damage averaged only `0.92`. Mega Abomasnow ex accounted for 70 states and averaged approximately `413` expected damage.

The defect was structural:

1. a ready Kyogre received a readiness bonus even with no Water Energy in the discard pile and therefore zero estimated Riptide damage;
2. planned-attacker attachment bonus still applied after that attacker had met its Energy requirement.

This could prioritize repeated attachment to a ready, near-zero-damage Kyogre.

## Planner v2 resource guards

V2 changed only the resource-completion logic:

- zero-damage Kyogre is excluded from confident attack plans;
- planned-attacker attachment bonus applies only while the plan needs Energy.

The follow-up added a direct v2-versus-v1 matchup and retained ten games in each candidate-seat by forced-turn-order cell.

| Matchup | Games | W-L | Score rate | Bootstrap 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| v2 vs v1 | 40 | 24-16 | 0.600 | [0.450, 0.750] | Hold |
| v2 vs promoted | 40 | 18-22 | 0.450 | [0.300, 0.600] | Hold |
| v2 vs random | 40 | 36-4 | 0.900 | [0.800, 0.975] | Regression pass |

All 120 games completed without failures. At least one required interval overlapped parity, so the predefined decision was **HOLD**.

The guards changed the mechanism as intended. Against promoted, confident-plan rate fell from `0.729` in v1 to `0.303` in v2 because invalid Kyogre plans no longer qualified. Immediate-knockout rate rose from `0.106` to `0.134`, and mean expected damage across main decisions rose from about `73.8` to `128.1`.

## Controlled-cell attribution

| Matchup | Seat | Candidate turn order | Score rate |
| --- | ---: | --- | ---: |
| v2 vs promoted | 0 | Second | 0.100 |
| v2 vs promoted | 0 | First | 0.500 |
| v2 vs promoted | 1 | Second | 0.600 |
| v2 vs promoted | 1 | First | 0.600 |
| v2 vs v1 | 0 | Second | 0.400 |
| v2 vs v1 | 0 | First | 0.900 |
| v2 vs v1 | 1 | Second | 0.500 |
| v2 vs v1 | 1 | First | 0.600 |

Ten games per cell are too few for stable cell estimates, but the spread shows why aggregate point estimates alone are unsafe.

## Decision and next step

Do not promote or submit either planner. V1's `0.625` primary point estimate was promising but uncertain and accompanied by a clear resource bug. V2 fixed the bug and beat v1 at `0.600`, yet fell below promoted at `0.450`. The results are compatible with noise, matchup-specific behavior, or both.

Improve the evaluation environment before adding another planner rule:

1. add at least one stronger frozen author-style opponent;
2. review matched loss replays from every controlled cell;
3. label failures as setup, attacker development, switch, attachment, attack timing, or opponent pressure;
4. choose one change only after measuring the dominant failure class.

Selective Search API work remains deferred until the failure taxonomy shows that tactical attack or retreat ambiguity is frequent.
