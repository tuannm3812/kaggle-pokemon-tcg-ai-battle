# Lucario adapted v1 results

Date: 2026-06-30

## Purpose

Build the first repo-owned Lucario archetype candidate after the episode-based
strategy showed that our submitted Abomasnow/Kyogre package is weak against
real author archetype decks, especially Lucario.

## Candidate

`candidates/lucario_adapted_v1`

The candidate uses:

- the reconstructed Mega Lucario ex decklist;
- a compact deterministic policy written in the repository style;
- tactical scoring for evolution, energy attachment, active switching, and
  immediate knockout attacks.

This is not promoted. It is a scaffold and first measurement point.

## Evaluator fix

While evaluating this candidate, we found an important local-evaluation issue:
`load_local_policy()` staged candidate `main.py` files into the shared runtime
but did not stage candidate-specific `deck.csv` files.

Impact:

- older Abomasnow-family candidates were unaffected because they intentionally
  use `agent/deck.csv`;
- new deck-archetype candidates, such as `lucario_adapted_v1`, would otherwise
  be evaluated with the wrong deck.

Fix:

- candidate-specific `deck.csv` is now copied beside the staged candidate module
  when present;
- candidates without their own deck continue to fall back to `agent/deck.csv`.

## Results

Compact author-archetype deck suite:

```bash
python scripts/evaluate_author_archetype_deck_suite.py --candidates lucario_adapted_v1 --games-per-cell 2 --max-decisions 5000
```

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 1-7 | 0.125 | 0 |
| Dragapult | 2-6 | 0.250 | 0 |
| Iono | 3-5 | 0.375 | 0 |
| Lucario | 2-6 | 0.250 | 0 |

Direct gate versus current promoted package:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v1 --control promoted --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 6-14 |
| Score rate | 0.300 |
| Wilson score CI | [0.1807, 0.4543] |
| Failures | 0 |

Cell breakdown:

| Cell | Score rate |
| --- | ---: |
| seat_0_player_zero_first_false | 0.400 |
| seat_0_player_zero_first_true | 0.000 |
| seat_1_player_zero_first_false | 0.400 |
| seat_1_player_zero_first_true | 0.400 |

Random-control screen:

```bash
python scripts/evaluate_direct_gate.py --candidate lucario_adapted_v1 --control official_random --games-per-cell 5 --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 20-0 |
| Score rate | 1.000 |
| Wilson score CI | [0.9124, 1.0000] |
| Failures | 0 |

## Decision

Reject `lucario_adapted_v1` for promotion.

The candidate is legal and functional, but it does not beat the current promoted
package and is too weak across exact author archetype decks.

## Recommended v2 work

Build `lucario_adapted_v2` only after improving the policy around:

1. target selection beyond the opponent active Pokémon;
2. Boss's Orders and Switch sequencing;
3. Mega Brave timing and prize-risk handling;
4. card search/selection priorities for Riolu, Mega Lucario ex, and Fighting
   Energy;
5. first-player/seat robustness, especially the `seat_0_player_zero_first_true`
   direct-gate cell.
