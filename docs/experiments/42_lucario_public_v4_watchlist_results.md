# Lucario public sample v4 watchlist results

Date: 2026-07-03

## Purpose

Test whether we can find the next candidate while `lucario_public_sample_v3` is
settling on the leaderboard. The active best submission at the latest check was
`lucario_public_sample_v3` with public score `742.0`.

## Candidate

`lucario_public_sample_v4`

Change from v3:

- starts from the rejected v2 Lucario-line pressure changes;
- restores the v3 late-game deck-safety brake when `deckCount <= 6`;
- keeps the same public Mega Lucario ex deck.

This makes v4 a hybrid: more aggressive Riolu/Mega Lucario setup and search,
with the low-deck protection that helped v3 become the active best submission.

## Challenger screen

Existing challenger checks against active best v3:

| Candidate | Result vs v3 | Score rate | Notes |
| --- | ---: | ---: | --- |
| `iono_public_sample_v1` | 3-17 | 0.150 | not competitive |
| `lucario_public_sample_v1` | 8-12 | 0.400 | confirms v3 remains better |
| `lucario_public_sample_v2` | 10-10 | 0.500 | useful signal, but previously weak into Abomasnow |
| `lucario_public_sample_v4` | 13-7 | 0.650 | first positive challenger signal |

First v4 direct gate versus v3:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v4   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 4-1 | 0.800 |
| seat 0, player zero first true | 3-2 | 0.600 |
| seat 1, player zero first false | 4-1 | 0.800 |
| seat 1, player zero first true | 2-3 | 0.400 |
| total | 13-7 | 0.650 |

Confirmation direct gate with a different seed:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v4   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000   --seed 20260703
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 0-5 | 0.000 |
| seat 1, player zero first false | 4-1 | 0.800 |
| seat 1, player zero first true | 4-1 | 0.800 |
| total | 11-9 | 0.550 |

The confirmation run stayed positive overall but exposed a serious weak cell:
`seat_0_player_zero_first_true`.

## Exact archetype suite

```bash
python scripts/evaluate_author_archetype_deck_suite.py   --candidates lucario_public_sample_v4   --games-per-cell 3   --max-decisions 5000
```

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 5-7 | 0.417 |
| Dragapult | 6-6 | 0.500 |
| Iono | 9-3 | 0.750 |
| Lucario | 9-3 | 0.750 |

Aggregate exact-archetype score: `0.6042`.

This is better than the v3 exact-archetype aggregate (`0.5625`) but has a worse
Abomasnow cell.

## Random-control reliability

The full `games-per-cell 5` random-control gate timed out locally, so a smaller
reliability check was run:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v4   --control official_random   --games-per-cell 3   --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 10-2 |
| Score rate | 0.8333 |
| Wilson score CI | [0.6415, 0.9332] |
| Failures | 0 |

## Decision

`lucario_public_sample_v4` is a watchlist candidate, not an immediate submission.

Reasons to continue testing:

- first direct gate beat active v3 `13-7`;
- confirmation direct gate stayed positive at `11-9`;
- exact-archetype aggregate improved over v3;
- random-control reliability passed with no failures.

Reasons not to submit yet:

- confirmation direct-gate CI is not strong;
- one confirmation cell collapsed to `0-5`;
- Abomasnow exact-archetype result is weaker than desired;
- v3 is currently scoring strongly on the public leaderboard (`742.0`).

Next step: run a larger direct gate against v3 or build a v5 that keeps v4's
Lucario-line pressure only when the candidate is not in the weak first-player
cell.
