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
| Status at 2026-07-02 check | `SubmissionStatus.COMPLETE` |
| Public score at 2026-07-02 check | `661.3` |

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

## 2026-07-02 score check

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `661.3` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `556.4` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

The Lucario public sample submission improved over the previous active
submission by `+104.9` public score points at this check.

## Episode insights

The local episode suite predicted the direction correctly:

- `lucario_public_sample_v1` strongly beat the previous promoted package
  head-to-head (`17-3`, score rate `0.850`);
- it remained reliable against official random (`17-3`, score rate `0.850`);
- it had the best broad exact-author-archetype profile among candidates tested
  so far, with aggregate score rate `0.646`;
- it was especially strong into Iono (`11-1`) and Lucario mirror (`8-4`);
- the main known weakness remains Abomasnow (`5-7`, score rate `0.417`).

Conclusion: the episode evidence suggests that switching to a stronger complete
archetype package mattered more than incremental planner tuning on the old
Abomasnow/Kyogre agent.

## 2026-07-03 score check

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `658.5` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `556.4` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

The Lucario submission remains the active best submission. Its public score has
drifted from `661.3` to `658.5`, still `+102.1` above the previous planner
submission at this check.

## 2026-07-03 later score check

Checked while continuing the candidate search:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `681.0` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `556.3` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

The active Lucario submission continues to drift upward and remains the best
submitted agent.

## 2026-07-03 v3 leaderboard probe

Submitted `lucario_public_sample_v3` after the confirmation direct gate against
the active v1 candidate.

| Field | Value |
| --- | --- |
| Submission ref | `54283898` |
| Candidate | `lucario_public_sample_v3` |
| Message | `lucario public sample v3` |
| Package | `scratch/submission_packages/lucario_public_sample_v3/submission.tar.gz` |
| Status | `SubmissionStatus.COMPLETE` |
| Public score | `600.0` |

Score table immediately after completion:

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54283898` | `lucario public sample v3` | `SubmissionStatus.COMPLETE` | `600.0` |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `673.1` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `560.3` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

Outcome: v3 validated successfully but did not improve the active v1 leaderboard
score. The late-game deck-safety brake appears too conservative or too narrow
for the public leaderboard mix, despite positive local head-to-head evidence.

## 2026-07-03 v3 score drift check

A later Kaggle score refresh showed that the v3 leaderboard probe drifted upward
and became the active best submission.

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54283898` | `lucario public sample v3` | `SubmissionStatus.COMPLETE` | `742.0` |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `663.8` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `560.3` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

Insight: the first completed v3 score snapshot (`600.0`) was not stable. The
later score (`742.0`) matches the local confirmation gate direction better:
`lucario_public_sample_v3` beat `lucario_public_sample_v1` head-to-head 14-6
with Wilson CI `[0.5457, 0.8193]`.

