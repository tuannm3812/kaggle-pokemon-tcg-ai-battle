# Lucario v5/v6 upgrade attempts

Date: 2026-07-03

## Purpose

Prepare safer upgraded candidates while `lucario_public_sample_v3` remains the
active best submitted agent. The goal was to borrow only the useful parts of
`lucario_public_sample_v4` without inheriting its unstable cell collapse.

## Current active submission

Latest checked submission before these upgrade attempts:

| Submission ref | Candidate | Public score |
| --- | --- | ---: |
| `54283898` | `lucario_public_sample_v3` | `718.6` |

## Candidate v5

`lucario_public_sample_v5` starts from v3 and adds mild Lucario-line pressure:

- keeps v3 setup-active logic unchanged;
- keeps v3 late-game deck-safety brake;
- mildly increases energy priority for Riolu/Mega Lucario;
- mildly increases `TO_HAND` search priority for Riolu/Mega Lucario;
- mildly increases `PLAY` score for Riolu.

Direct gate:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v5   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 3-2 | 0.600 |
| seat 1, player zero first false | 2-3 | 0.400 |
| seat 1, player zero first true | 2-3 | 0.400 |
| total | 10-10 | 0.500 |

Decision: reject v5 for submission. It is safer than v4 but does not improve
against current best v3.

## Candidate v6

`lucario_public_sample_v6` starts from v3 and narrows the experiment further:

- keeps v3 setup-active logic unchanged;
- keeps v3 energy scoring unchanged;
- keeps v3 Pok?mon play scoring unchanged;
- only changes `TO_HAND` search priority toward Riolu/Mega Lucario.

Direct gate:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v6   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 3-2 | 0.600 |
| seat 1, player zero first false | 1-4 | 0.200 |
| seat 1, player zero first true | 2-3 | 0.400 |
| total | 9-11 | 0.450 |

Decision: reject v6 for submission. Search-only Lucario pressure is not enough
and appears to weaken the already sensitive seat-1 cells.

## Insight

The v4 improvement was not reproduced by safer partial changes. This suggests
v4's gains likely come from a coupled package of Lucario-line setup, play,
search, and energy pressure. Unfortunately, that same coupled package produced a
`0-5` collapse in `seat_0_player_zero_first_true` during confirmation.

Current recommendation:

1. Keep `lucario_public_sample_v3` as the active submitted agent.
2. Do not submit v4, v5, or v6.
3. If we continue, build a v7 around a conditional strategy: use v4-style
   Lucario pressure only when board state confirms the line is already stable,
   otherwise fall back to v3.
