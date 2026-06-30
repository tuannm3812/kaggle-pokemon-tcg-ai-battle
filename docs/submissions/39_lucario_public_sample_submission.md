# Lucario Public Sample Submission

## Submission

Submitted on 2026-07-01 Australia/Sydney time.

| Field | Value |
| --- | --- |
| Competition | `pokemon-tcg-ai-battle` |
| Submission ref | `54213861` |
| Candidate | `lucario_public_sample_v1` |
| Message | `lucario public sample v1` |
| Package | `scratch/submission_packages/lucario_public_sample_v1/submission.tar.gz` |
| Package smoke test | 6/6 games completed |
| Status at first post-submit check | `SubmissionStatus.PENDING` |

## Score before submission

Checked immediately before submitting:

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `543.9` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

## Local promotion evidence

`lucario_public_sample_v1` was selected because it was the first candidate in
the current experiment loop to clear the practical submission bar.

| Gate | Result | Score rate |
| --- | ---: | ---: |
| vs promoted | 17-3 | 0.850 |
| vs official random | 17-3 | 0.850 |
| exact archetype aggregate | 31-17 | 0.646 |

Exact archetype detail:

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 5-7 | 0.417 |
| Dragapult | 7-5 | 0.583 |
| Iono | 11-1 | 0.917 |
| Lucario | 8-4 | 0.667 |

## Follow-up

Poll the submission until it reaches `COMPLETE` or `ERROR`:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

If complete, compare the new public score against the previous active score
`543.9`.
