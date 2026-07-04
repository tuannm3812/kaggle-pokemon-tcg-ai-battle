# Koushikrudra library-out candidate results

Date: 2026-07-04

## Purpose

Check whether the Koushikrudra Great Tusk / Crustle library-out reference
notebook can become a new submission candidate or at least a useful local control
opponent.

Reference notebook:

- https://www.kaggle.com/code/koushikrudra/i-have-one-rear-card

## Candidate

`koushikrudra_libraryout_v1`

Local adaptation:

- extracted notebook `main.py` and `deck.csv` into `candidates/koushikrudra_libraryout_v1/`;
- adjusted deck-path loading for local/Kaggle runtime compatibility;
- registered the candidate in `scripts/evaluate_author_opponent_suite.py`.

The deck is a Great Tusk / Dwebble / Crustle / Terrakion library-out control
package. It is strategically different from the active best
`kojimar_simple_baseline_v1`.

## Current leaderboard context

Latest score check before this challenger screen:

| Submission ref | Message | Public score |
| --- | --- | ---: |
| `54303967` | `kojimar simple baseline v1` | `867.9` |
| `54283898` | `lucario public sample v3` | `722.5` |
| `54213861` | `lucario public sample v1` | `662.0` |

Decision baseline: new candidates must beat or clearly target a weakness in
`kojimar_simple_baseline_v1`.

## Direct gate versus active best

```bash
python scripts/evaluate_direct_gate.py   --candidate koushikrudra_libraryout_v1   --control kojimar_simple_baseline_v1   --games-per-cell 3   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 0-3 | 0.000 |
| seat 0, player zero first true | 2-1 | 0.667 |
| seat 1, player zero first false | 1-2 | 0.333 |
| seat 1, player zero first true | 3-0 | 1.000 |
| total | 6-6 | 0.500 |

The aggregate is parity, but the seat/first-player profile is highly unstable.

## Random-control reliability

```bash
python scripts/evaluate_direct_gate.py   --candidate koushikrudra_libraryout_v1   --control official_random   --games-per-cell 3   --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 10-2 |
| Score rate | 0.8333 |
| Wilson score CI | [0.6415, 0.9332] |
| Failures | 0 |

## Compact exact archetype suite

```bash
python scripts/evaluate_author_archetype_deck_suite.py   --candidates koushikrudra_libraryout_v1   --games-per-cell 2   --max-decisions 5000
```

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 3-5 | 0.375 |
| Dragapult | 1-7 | 0.125 |
| Iono | 0-8 | 0.000 |
| Lucario | 8-0 | 1.000 |

## Decision

`koushikrudra_libraryout_v1` is not a submission candidate right now.

Reasons:

- split active best Kojimar v1 at `6-6` rather than beating it;
- severe weak cell: `seat_0_player_zero_first_false` was `0-3`;
- compact archetype suite collapsed into Iono and Dragapult;
- current public best Kojimar v1 is still improving and much stronger on the
  leaderboard.

Useful insight:

- the library-out/control deck can dominate Lucario-style author sample (`8-0`),
  so it is valuable as a future local control opponent or as a targeted anti-
  Lucario idea;
- it should not replace Kojimar v1 unless we can fix the Iono/Dragapult collapse
  and seat instability.

Next step: keep it registered as a control/challenger. Future work can create a
hybrid or matchup-specific detector, but do not submit this version.
