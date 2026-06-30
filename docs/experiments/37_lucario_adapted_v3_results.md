# Lucario adapted v3 results

Date: 2026-06-30

## Purpose

Improve `lucario_adapted_v2` using loss traces against the exact Dragapult
author archetype deck.

The trace showed that v2 sometimes over-built around Solrock and even switched
away from Mega Lucario. V3 therefore makes the policy less clever and more
focused:

- prioritize Riolu into Mega Lucario ex;
- demote Solrock from attacker to setup/support;
- avoid switching away from active Mega Lucario unless a better Mega Lucario
  attack line is ready;
- increase value for Mega Lucario ex, Riolu, and Fighting Energy search;
- keep Boss/Switch planning, but require Mega Lucario to be the payoff attacker.

## Candidate

`candidates/lucario_adapted_v3`

## Results

Author archetype deck suite:

```bash
python scripts/evaluate_author_archetype_deck_suite.py --candidates lucario_adapted_v3 --games-per-cell 2 --max-decisions 5000
```

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 1-7 | 0.125 | 0 |
| Dragapult | 2-6 | 0.250 | 0 |
| Iono | 2-6 | 0.250 | 0 |
| Lucario | 4-4 | 0.500 | 0 |

Direct gate versus current promoted package:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v3 --control promoted --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 14-6 |
| Score rate | 0.700 |
| Wilson score CI | [0.5457, 0.8193] |
| Failures | 0 |

Cell breakdown:

| Cell | Score rate |
| --- | ---: |
| seat_0_player_zero_first_false | 0.600 |
| seat_0_player_zero_first_true | 0.800 |
| seat_1_player_zero_first_false | 0.800 |
| seat_1_player_zero_first_true | 0.600 |

Random-control screen:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v3 --control official_random --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 18-2 |
| Score rate | 0.900 |
| Wilson score CI | [0.7695, 0.9604] |
| Failures | 0 |

## Comparison

| Candidate | vs promoted | vs random | Abomasnow | Dragapult | Iono | Lucario |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| lucario_adapted_v1 | 0.300 | 1.000 | 0.125 | 0.250 | 0.375 | 0.250 |
| lucario_adapted_v2 | 0.650 | 0.900 | 0.125 | 0.000 | 0.250 | 0.375 |
| lucario_adapted_v3 | 0.700 | 0.900 | 0.125 | 0.250 | 0.250 | 0.500 |

## Decision

Hold `lucario_adapted_v3`; do not submit yet.

V3 is the best Lucario candidate so far and beats the current promoted package
head-to-head, but it is still too weak against exact author archetype decks.
The strict submission bar remains unmet because Abomasnow, Dragapult, and Iono
matchups are below parity.

## Recommended next step

Stop improving Lucario only by direct gate. The next useful work is matchup
diagnosis against Abomasnow and Iono exact decks, or a separate Iono adapted
candidate. Current evidence suggests Lucario can beat our existing promoted
package but is not yet broad enough for the live ladder.
