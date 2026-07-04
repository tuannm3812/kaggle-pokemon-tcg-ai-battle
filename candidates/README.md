# Candidate Agent Index

Each candidate folder is a self-contained local agent package with:

- `main.py`: Kaggle agent entrypoint;
- `deck.csv`: 60-card deck used by local gates and packaging.

The folder names are intentionally stable because `scripts/evaluate_author_opponent_suite.py`
registers candidates by path. Do not move or rename candidate folders without
updating the evaluator registry and experiment notes in the same commit.

## Current active best

| Candidate | Status | Notes |
| --- | --- | --- |
| `kojimar_simple_baseline_v1` | Active best submitted | Public score reached `861.4`; strongest local and leaderboard evidence so far |

## Important submitted candidates

| Candidate | Status | Notes |
| --- | --- | --- |
| `lucario_public_sample_v3` | Previous active best | Reached strong public scores after drift; superseded by Kojimar v1 |
| `lucario_public_sample_v1` | Submitted baseline | First successful public Lucario sample probe |
| `planner_main_only_v1` | Submitted historical | Older Abomasnow/planner branch, now superseded |

## Watchlist / rejected Lucario variants

| Candidate | Status | Main lesson |
| --- | --- | --- |
| `lucario_public_sample_v7` | Watchlist only | Conditional Crustle guard is conceptually useful but needs direct Crustle validation |
| `lucario_public_sample_v6` | Rejected | Search-only Lucario pressure did not beat v3 |
| `lucario_public_sample_v5` | Rejected | Mild Lucario pressure split 10-10 vs v3 |
| `lucario_public_sample_v4` | Watchlist only | Strong upside but unstable first-player cell |
| `lucario_public_sample_v2` | Rejected | Broad Lucario-line bias hurt earlier Abomasnow gate |

## Historical development candidates

Older folders such as `abomasnow_planner_*`, `setup_*`, `conservative_switch_*`,
and `lucario_adapted_*` are retained as reproducibility artifacts for the
experiment notes. Prefer creating a new candidate folder for new ideas instead
of mutating an old candidate in place.
