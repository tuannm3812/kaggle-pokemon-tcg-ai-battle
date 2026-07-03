# Lucario public sample v3 candidate results

Date: 2026-07-03

## Purpose

Continue monitoring the active leaderboard score and search for the next
candidate that can improve over `lucario_public_sample_v1`.

## Live score before experiment

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `681.0` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `556.3` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

The active Lucario submission remains the best submitted agent.

## Candidate

`lucario_public_sample_v3`

Change from v1:

- adds a late-game deck-safety brake for likely draw/search cards when
  `deckCount <= 6`;
- keeps the public Lucario deck and core policy structure intact;
- avoids the broad attacker-priority change that made `lucario_public_sample_v2`
  worse.

## Results

Focused Abomasnow comparison:

```bash
python scripts/evaluate_author_archetype_deck_suite.py \
  --candidates lucario_public_sample_v1 lucario_public_sample_v3 \
  --archetypes abomasnow \
  --games-per-cell 3 \
  --max-decisions 5000
```

| Candidate | Result vs Abomasnow | Score rate | Failures |
| --- | ---: | ---: | ---: |
| `lucario_public_sample_v1` | 4-8 | 0.333 | 0 |
| `lucario_public_sample_v3` | 4-8 | 0.333 | 0 |

Direct gate versus active v1:

```bash
python scripts/evaluate_direct_gate.py \
  --candidate lucario_public_sample_v3 \
  --control lucario_public_sample_v1 \
  --games-per-cell 5 \
  --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 13-7 |
| Score rate | 0.650 |
| Wilson score CI | [0.4951, 0.7787] |
| Failures | 0 |

Confirmation direct gate versus active v1:

```bash
python scripts/evaluate_direct_gate.py \
  --candidate lucario_public_sample_v3 \
  --control lucario_public_sample_v1 \
  --games-per-cell 5 \
  --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 14-6 |
| Score rate | 0.700 |
| Wilson score CI | [0.5457, 0.8193] |
| Failures | 0 |

The confirmation run improved the direct-gate evidence and moved the Wilson CI
lower bound above 0.50.

Exact archetype suite:

```bash
python scripts/evaluate_author_archetype_deck_suite.py \
  --candidates lucario_public_sample_v3 \
  --games-per-cell 3 \
  --max-decisions 5000
```

| Opponent archetype | Result | Score rate | Failures |
| --- | ---: | ---: | ---: |
| Abomasnow | 7-5 | 0.583 | 0 |
| Dragapult | 6-6 | 0.500 | 0 |
| Iono | 7-5 | 0.583 | 0 |
| Lucario | 7-5 | 0.583 | 0 |

Aggregate exact-archetype score: `0.5625`.

Random-control gate:

```bash
python scripts/evaluate_direct_gate.py \
  --candidate lucario_public_sample_v3 \
  --control official_random \
  --games-per-cell 5 \
  --max-decisions 5000
```

| Metric | Value |
| --- | ---: |
| Result | 18-2 |
| Score rate | 0.900 |
| Wilson score CI | [0.7695, 0.9604] |
| Failures | 0 |

Packaging:

```bash
python scripts/package_submission.py --candidate lucario_public_sample_v3 --games 6 --max-decisions 2500
```

Package:

```text
scratch/submission_packages/lucario_public_sample_v3/submission.tar.gz
```

Smoke result:

- 6/6 games completed;
- no invalid actions;
- archive includes `main.py`, `deck.csv`, and `cg/`.

## Decision

`lucario_public_sample_v3` is promoted from plausible candidate to next
submission candidate after the confirmation direct gate.

Reasons to submit:

- beats active v1 head-to-head locally (`13-7`);
- passes random-control reliability;
- has no exact-archetype collapse;
- packaged and smoke-validated.

Risks:

- focused Abomasnow comparison tied v1 rather than clearly improving it;
- exact-archetype aggregate (`0.5625`) is lower than the original v1 candidate
  aggregate observed before submission (`0.646`);
- the first direct-gate CI was borderline before the confirmation run strengthened it.

Recommendation: submit `lucario_public_sample_v3` as the next leaderboard probe
if we want to test a small, targeted improvement over the current public Lucario
submission. The main risk remains that the exact-archetype aggregate is lower
than the original v1 pre-submit aggregate, so this should be treated as a
controlled probe rather than a guaranteed improvement.
