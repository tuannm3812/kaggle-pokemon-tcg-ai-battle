# Script Index

Local iteration should usually happen through scripts first, then be promoted to
Kaggle notebooks only when a workflow needs to run on Kaggle.

## Core evaluation and packaging

| Script | Purpose |
| --- | --- |
| `evaluate_direct_gate.py` | Head-to-head candidate vs control gate with seat/first-player cells |
| `evaluate_author_archetype_deck_suite.py` | Candidate vs reconstructed author archetype decks |
| `evaluate_author_opponent_suite.py` | Shared evaluator utilities and candidate registry |
| `evaluate_promotion_gate.py` | Older promotion-gate runner retained for reproducibility |
| `package_submission.py` | Build `submission.tar.gz` and run package smoke tests |
| `trace_author_decisions.py` | Decision tracing for matchup diagnosis |
| `analyze_submission_episodes.py` | Analyze downloaded public episode replays by archetype |
| `build_public_meta_fixtures.py` | Build replay-derived public meta fixture JSON from episode summaries |
| `evaluate_public_meta_gate.py` | Conservative challenger gate combining local controls with public-meta fixtures |

## Notebook builders and historical experiment scripts

`build_*`, `finalize_*`, and `validate_*` scripts generate or maintain the
Kaggle-runnable notebooks under `notebooks/`. Keep them because notebook metadata
and historical experiment reports depend on them.

## Maintenance notes

- Register new candidate folders in `evaluate_author_opponent_suite.py`.
- Keep generated outputs under `scratch/`; do not commit package artifacts or
  local trace files.
- Remove `__pycache__` directories before committing if local runs create them.
