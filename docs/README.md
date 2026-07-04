# Documentation Index

## Current status

Latest tracked Kaggle score check: 2026-07-04.

| Submission | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54303967` | `kojimar simple baseline v1` | `COMPLETE` | `861.4` |
| `54283898` | `lucario public sample v3` | `COMPLETE` | `708.3` |
| `54213861` | `lucario public sample v1` | `COMPLETE` | `662.0` |
| `54126975` | `planner main only v1` | `COMPLETE` | `560.3` |
| `54100265` | `fix deck loader missing __file__` | `COMPLETE` | `496.7` |

Current active best: `kojimar_simple_baseline_v1`.

## Start here

| Need | File |
| --- | --- |
| Coding and commit standards | [0_coding_standards.md](0_coding_standards.md) |
| Competition rules and constraints | [1_competition_instructions.md](1_competition_instructions.md) |
| EDA and environment findings | [2_eda_and_environment.md](2_eda_and_environment.md) |
| Agent strategy | [3_agent_strategy.md](3_agent_strategy.md) |
| Evaluation/submission methodology | [4_evaluation_and_submissions.md](4_evaluation_and_submissions.md) |
| Kaggle workflow runbook | [5_kaggle_runbook.md](5_kaggle_runbook.md) |
| High-level experiment ledger | [6_experiment_log.md](6_experiment_log.md) |
| Competition-author reference notes | [7_competition_author_references.md](7_competition_author_references.md) |

## Current high-value evidence

| File | Why it matters |
| --- | --- |
| [experiments/45_kojimar_simple_baseline_candidate_results.md](experiments/45_kojimar_simple_baseline_candidate_results.md) | Strongest current local candidate evidence; led to active best submission |
| [submissions/39_lucario_public_sample_submission.md](submissions/39_lucario_public_sample_submission.md) | Chronological leaderboard/submission tracking, including v3 and Kojimar v1 drift |
| [experiments/44_kojimar_insights_v7_crustle_guard.md](experiments/44_kojimar_insights_v7_crustle_guard.md) | Kojimar-inspired Crustle-guard attempt and why it stayed watchlist only |
| [experiments/43_lucario_v5_v6_upgrade_attempts.md](experiments/43_lucario_v5_v6_upgrade_attempts.md) | Rejected safer Lucario-line pressure attempts |
| [experiments/42_lucario_public_v4_watchlist_results.md](experiments/42_lucario_public_v4_watchlist_results.md) | v4 watchlist evidence and unstable weak-cell diagnosis |
| [experiments/41_lucario_public_v3_candidate_results.md](experiments/41_lucario_public_v3_candidate_results.md) | Prior active-best v3 evidence and submission rationale |

## Folder map

| Folder | Purpose | Notes |
| --- | --- | --- |
| `agent/` | Legacy/promoted local agent package | Keep stable; current submissions are tracked under `candidates/` and `scratch/submission_packages/` |
| `candidates/` | Versioned candidate agents, each with `main.py` and `deck.csv` | See [../candidates/README.md](../candidates/README.md) |
| `controls/` | Local opponent/control agents for gates | Small, reusable pressure-test policies |
| `docs/experiments/` | Detailed experiment reports | Append-only evidence trail; do not delete old reports |
| `docs/submissions/` | Submission/package/score tracking | Source of truth for leaderboard history |
| `notebooks/` | Kaggle-runnable notebooks | Flat layout by design; see [../notebooks/README.md](../notebooks/README.md) |
| `scripts/` | Local builders, evaluators, tracing, packaging | See [../scripts/README.md](../scripts/README.md) |
| `scratch/` | Ignored runtime outputs, pulled references, packages, traces | Not committed; safe to regenerate selectively |
| `data/` | Ignored competition/downloaded data | Keep out of Git |
| `tmp/` | Ignored temporary local workspace | Keep out of Git |

## Maintenance rule

Prefer adding a concise experiment note under `docs/experiments/` and a score
note under `docs/submissions/` instead of editing old reports in place. Keep
candidate folders stable because evaluation scripts reference them by name.
