# Planner Main-Only Submission Result

## Submission

Submitted on 2026-06-28.

| Field | Value |
| --- | --- |
| Competition | `pokemon-tcg-ai-battle` |
| Submission ref | `54126975` |
| Candidate | `planner_main_only_v1` |
| Message | `planner main only v1` |
| Package | `scratch/submission_packages/planner_main_only_v1/submission.tar.gz` |
| Status | `SubmissionStatus.COMPLETE` |
| Public score at first completion check | `600.0` |
| Public score at latest check | `491.6` |

## Comparison

At the same status check, the previous accepted baseline submission showed:

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `464.8` |

The new planner-main-only submission is accepted and remains above the previous
accepted baseline at the latest check, but the score has been volatile. Treat it
as valid but not a durable ladder breakthrough.

## Next recommendation

Monitor the score because this is a ladder competition and public score can move
as games are played. Continue monitoring before treating `planner_main_only_v1` as definitively
stronger than the baseline.

## 2026-06-30 status check

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `491.6` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `464.8` |

Decision: do not submit another planner-only candidate yet. Use the author
archetype deck suite to build and gate a stronger adapted archetype candidate,
starting with Lucario or Iono.

