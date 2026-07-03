# Kojimar matchup-test insights and Lucario v7 Crustle guard

Date: 2026-07-03

## Reference

Kaggle notebook reviewed:

- https://www.kaggle.com/code/kojimar/simple-baseline-matchup-tests

Useful ideas from the reference:

- prefer targeted matchup patches over broad global heuristic changes;
- keep public/meta matchup tables, not only random smoke tests;
- track matchup-specific causes such as Crustle wall behavior;
- use conditional logic when a matchup signal is visible instead of changing the
  default policy everywhere.

The reference reported a Crustle-focused improvement from `0.47` to `0.77` in a
100-game confirmation by avoiding wasted Mega Lucario ex attacks into Crustle
and keeping the non-ex Hariyama route available.

## Candidate

`lucario_public_sample_v7`

Starts from active best `lucario_public_sample_v3` and adds conditional logic:

- detect visible Dwebble/Crustle wall line (`344`, `345`);
- avoid choosing Mega Lucario ex attacks into active Crustle when no valid plan
  exists;
- boost Makuhita/Hariyama search and energy only when the Crustle wall signal is
  visible;
- raise low-deck safety threshold from `6` to `8`;
- suppress Lunatone ability when low deck.

## Direct gate versus active v3

First run:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v7   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 5-0 | 1.000 |
| seat 1, player zero first false | 2-3 | 0.400 |
| seat 1, player zero first true | 3-2 | 0.600 |
| total | 13-7 | 0.650 |

Confirmation with a different seed:

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v7   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000   --seed 20260703
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 2-3 | 0.400 |
| seat 1, player zero first false | 2-3 | 0.400 |
| seat 1, player zero first true | 2-3 | 0.400 |
| total | 9-11 | 0.450 |

## Exact archetype suite

```bash
python scripts/evaluate_author_archetype_deck_suite.py   --candidates lucario_public_sample_v7   --games-per-cell 3   --max-decisions 5000
```

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 5-7 | 0.417 |
| Dragapult | 7-5 | 0.583 |
| Iono | 10-2 | 0.833 |
| Lucario | 10-2 | 0.833 |

Aggregate exact-archetype score: `0.6667`.

## Random-control reliability

```bash
python scripts/evaluate_direct_gate.py   --candidate lucario_public_sample_v7   --control official_random   --games-per-cell 3   --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 12-0 |
| Score rate | 1.000 |
| Wilson score CI | [0.862, 1.0] |
| Failures | 0 |

## Decision

`lucario_public_sample_v7` is a watchlist candidate, not a submission candidate.

Positive signs:

- first direct gate beat active v3 `13-7`;
- exact-archetype aggregate improved to `0.6667`;
- Iono and Lucario archetype checks are strong (`10-2` each);
- random-control reliability is clean (`12-0`);
- v7 avoids the v4-style `seat_0_player_zero_first_true` hard collapse in the
  first run.

Risks:

- confirmation direct gate lost to active v3 `9-11`;
- Abomasnow remains weak at `5-7`;
- the current local suite does not yet include a true Crustle-wall opponent, so
  the intended targeted patch is not directly validated.

Next step:

Add or reconstruct a Crustle-wall control/opponent suite before submitting any
Crustle-guard candidate. If Crustle is common on the public leaderboard, v7-style
logic may be valuable, but we need direct Crustle validation first.
