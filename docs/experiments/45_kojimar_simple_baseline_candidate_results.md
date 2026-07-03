# Kojimar simple baseline candidate results

Date: 2026-07-03

## Purpose

Continue searching until we find a stronger candidate than the active submitted
`lucario_public_sample_v3` agent.

The reference notebook reviewed was:

- https://www.kaggle.com/code/kojimar/simple-baseline-matchup-tests

The notebook contains a full compact Mega Lucario ex baseline plus local matchup
results. We extracted it as a local candidate instead of only borrowing isolated
heuristics.

## Candidate

`kojimar_simple_baseline_v1`

Local adaptation:

- extracted the notebook `DECK` into `candidates/kojimar_simple_baseline_v1/deck.csv`;
- extracted the notebook `main.py` into the same candidate directory;
- adjusted deck-path loading for local/Kaggle runtime compatibility;
- added `read_deck_csv()` for our packaging smoke-test helper;
- registered the candidate in `scripts/evaluate_author_opponent_suite.py`.

## Direct gate versus active best v3

First run:

```bash
python scripts/evaluate_direct_gate.py   --candidate kojimar_simple_baseline_v1   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 3-2 | 0.600 |
| seat 0, player zero first true | 4-1 | 0.800 |
| seat 1, player zero first false | 4-1 | 0.800 |
| seat 1, player zero first true | 3-2 | 0.600 |
| total | 14-6 | 0.700 |

Confirmation with a different seed:

```bash
python scripts/evaluate_direct_gate.py   --candidate kojimar_simple_baseline_v1   --control lucario_public_sample_v3   --games-per-cell 5   --max-decisions 5000   --seed 20260703
```

| Cell | Result | Score rate |
| --- | ---: | ---: |
| seat 0, player zero first false | 4-1 | 0.800 |
| seat 0, player zero first true | 3-2 | 0.600 |
| seat 1, player zero first false | 5-0 | 1.000 |
| seat 1, player zero first true | 2-3 | 0.400 |
| total | 14-6 | 0.700 |

The direct-gate evidence is stronger than v4-v7 because both runs beat active v3
`14-6` and every first-run cell was positive.

## Exact archetype suite

```bash
python scripts/evaluate_author_archetype_deck_suite.py   --candidates kojimar_simple_baseline_v1   --games-per-cell 3   --max-decisions 5000
```

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 10-2 | 0.833 |
| Dragapult | 8-4 | 0.667 |
| Iono | 11-1 | 0.917 |
| Lucario | 8-4 | 0.667 |

Aggregate exact-archetype score: `0.7708`.

This is materially stronger than the v3 exact-archetype score (`0.5625`) and
v7 watchlist score (`0.6667`).

## Random-control reliability

```bash
python scripts/evaluate_direct_gate.py   --candidate kojimar_simple_baseline_v1   --control official_random   --games-per-cell 5   --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 20-0 |
| Score rate | 1.000 |
| Wilson score CI | [0.9124, 1.0] |
| Failures | 0 |

## Packaging

```bash
python scripts/package_submission.py   --candidate kojimar_simple_baseline_v1   --games 6   --max-decisions 2500
```

Package:

```text
scratch/submission_packages/kojimar_simple_baseline_v1/submission.tar.gz
```

Smoke result:

- 6/6 games completed;
- no packaging/runtime failures;
- archive includes `main.py`, `deck.csv`, and `cg/`.

## Decision

`kojimar_simple_baseline_v1` is the next strong submission candidate.

Reasons to submit:

- beat current active v3 in two direct gates (`14-6`, then `14-6`);
- exact-archetype aggregate is substantially stronger than v3;
- Abomasnow result improved to `10-2`, addressing a recurring weakness;
- random-control reliability is perfect in this gate (`20-0`);
- package smoke test passed.

Main risk:

- the candidate is extracted from a public notebook, so it may be common in the
  public leaderboard pool and could be mirrored by many competitors.

Recommendation: submit as the next controlled leaderboard probe unless we want
to first add a true Crustle-wall control suite.
