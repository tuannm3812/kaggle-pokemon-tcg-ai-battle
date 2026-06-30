# Public sample submission candidate results

Date: 2026-07-01

## Purpose

Continue the experiment loop until we find a candidate that is strong enough to
submit.

The repo-owned Lucario candidates improved head-to-head against our promoted
agent, but they still failed the exact author-archetype suite. The next test was
to benchmark and package attributed public competition-author sample baselines.

## Candidates tested

### `iono_adapted_v1`

Repo-owned Iono-inspired implementation.

Compact archetype suite result:

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 0-4 | 0.000 |
| Dragapult | 1-3 | 0.250 |
| Iono | 0-4 | 0.000 |
| Lucario | 0-4 | 0.000 |

Decision: reject.

### `iono_public_sample_v1`

Attributed local adaptation of the public competition-author Iono sample.

Direct gate:

| Control | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| promoted | 19-1 | 0.950 | 0 |
| official_random | 20-0 | 1.000 | 0 |

Larger exact archetype suite:

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 6-6 | 0.500 | 0 |
| Dragapult | 5-7 | 0.417 | 0 |
| Iono | 6-6 | 0.500 | 0 |
| Lucario | 3-9 | 0.250 | 0 |

Decision: strong but not selected; Lucario weakness is too large.

### `lucario_public_sample_v1`

Attributed local adaptation of the public competition-author Mega Lucario ex
sample.

Direct gate:

| Control | Result | Score rate | Wilson CI | Failures |
| --- | ---: | ---: | --- | ---: |
| promoted | 17-3 | 0.850 | [0.7093, 0.9294] | 0 |
| official_random | 17-3 | 0.850 | [0.7093, 0.9294] | 0 |

Exact author-archetype suite:

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 5-7 | 0.417 | 0 |
| Dragapult | 7-5 | 0.583 | 0 |
| Iono | 11-1 | 0.917 | 0 |
| Lucario | 8-4 | 0.667 | 0 |

Aggregate exact-archetype score: `0.646`.

## Packaging

Packaged and smoke-validated with:

```bash
python scripts/package_submission.py --candidate lucario_public_sample_v1 --games 6 --max-decisions 2500
```

Package:

```text
scratch/submission_packages/lucario_public_sample_v1/submission.tar.gz
```

Smoke result:

- 6/6 games completed;
- no invalid actions;
- archive includes `main.py`, `deck.csv`, and `cg/`.

## Decision

`lucario_public_sample_v1` is the first candidate in this experiment sequence
that is ready to submit.

Rationale:

- it strongly beats the current promoted package;
- it passes random-control reliability;
- it has the best broad exact-archetype profile so far;
- it is packaged and locally smoke-validated.

Known risk:

- Abomasnow is slightly below parity (`0.417`) in the larger exact-archetype
  suite.

Recommendation: submit `lucario_public_sample_v1` as the next Kaggle candidate,
then monitor the public score before deciding whether to continue with a custom
v2 or a different archetype.
