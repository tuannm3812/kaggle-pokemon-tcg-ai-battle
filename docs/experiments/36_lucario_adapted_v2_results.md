# Lucario adapted v2 results

Date: 2026-06-30

## Purpose

Improve `lucario_adapted_v1` by addressing the first clear failures:

- weak first-player direct-gate cell;
- missing Boss's Orders target planning;
- weak Switch/retreat sequencing;
- shallow setup and search priorities.

## Candidate

`candidates/lucario_adapted_v2`

Changes from v1:

- explicit target planning across opponent active and bench when Boss's Orders
  is playable;
- explicit switch planning for bench attackers;
- stronger setup preference for Solrock when going second and Riolu as the main
  evolution base;
- higher search value for Mega Lucario ex, Riolu, Fighting Energy, Boss's
  Orders, and Switch when the current plan needs them;
- safer play scoring for draw/search cards versus immediate knockout lines.

## Results

Author archetype deck suite:

```bash
python scripts/evaluate_author_archetype_deck_suite.py --candidates lucario_adapted_v2 --games-per-cell 2 --max-decisions 5000
```

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 1-7 | 0.125 | 0 |
| Dragapult | 0-8 | 0.000 | 0 |
| Iono | 2-6 | 0.250 | 0 |
| Lucario | 3-5 | 0.375 | 0 |

Direct gate versus current promoted package:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v2 --control promoted --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 13-7 |
| Score rate | 0.650 |
| Wilson score CI | [0.4951, 0.7787] |
| Failures | 0 |

Cell breakdown:

| Cell | Score rate |
| --- | ---: |
| seat_0_player_zero_first_false | 0.800 |
| seat_0_player_zero_first_true | 0.600 |
| seat_1_player_zero_first_false | 0.600 |
| seat_1_player_zero_first_true | 0.600 |

Random-control screen:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v2 --control official_random --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 18-2 |
| Score rate | 0.900 |
| Wilson score CI | [0.7695, 0.9604] |
| Failures | 0 |

## Decision

Hold `lucario_adapted_v2`; do not submit yet.

Compared with v1, v2 is much better head-to-head against the promoted package
and fixes the weakest direct-gate cell. However, it is still too weak against
exact author archetype decks, especially Dragapult and Abomasnow.

## Recommended v3 work

The next Lucario iteration should target archetype-suite weakness, not
head-to-head versus our current promoted Abomasnow package.

Priority:

1. improve Dragapult matchup first, because v2 scored `0-8`;
2. reduce overuse of Boss/Switch lines when the board is not ready;
3. make search cards prefer complete attacker lines instead of isolated strong
   cards;
4. add episode tracing for v2 losses to identify whether the main failure is
   setup, attachment, attack selection, or target selection.
