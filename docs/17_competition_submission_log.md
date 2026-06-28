# Competition Submission Log

## 2026-06-28 - planner main only v1

`planner_main_only_v1` was submitted after clearing local promoted-control,
official-random, author-suite, packaging, staged self-play, and missing
`__file__` deck-loader guards.

| Field | Value |
| --- | --- |
| Competition | `pokemon-tcg-ai-battle` |
| Submission ref | `54126975` |
| File | `submission.tar.gz` |
| Local package | `scratch/submission_packages/planner_main_only_v1/submission.tar.gz` |
| Message | `planner main only v1` |
| Kaggle timestamp | `2026-06-28 03:38:02.607000` |
| Status at last check | `SubmissionStatus.COMPLETE` |
| Public score at last check | `600.0` |

This is now the latest accepted submission. At the same CLI check, the previous
accepted baseline submission `54100265` showed public score `493.8`.

## 2026-06-27 - promoted development-first baseline

The current promoted production agent was submitted to the Kaggle competition
after packaging notebook version 8 completed successfully.

| Field | Value |
| --- | --- |
| Competition | `pokemon-tcg-ai-battle` |
| Submission ref | `54099181` |
| File | `submission.tar.gz` |
| Local package | `scratch/pull_submission_packaging_v8/submission.tar.gz` |
| Message | `promoted development-first baseline` |
| Kaggle timestamp | `2026-06-27 06:30:30.570000` |
| Status at last check | `SubmissionStatus.ERROR` |

The submitted package corresponds to the promoted `agent/main.py` and
`agent/deck.csv`. Held candidates such as planner v1/v2 and switch v1/v2 were
not submitted.

Check the final leaderboard/evaluation status with:

```powershell
python -m kaggle competitions submissions -c pokemon-tcg-ai-battle
```
