# Experiment and Submission Log

## Current summary

Current active best submitted agent: `kojimar_simple_baseline_v1`.

Latest tracked public score: `864.5` on 2026-07-08.

High-level progression:

| Phase | Key candidate | Outcome |
| --- | --- | --- |
| Starter/planner baseline | `planner_main_only_v1` | Valid but low public score; useful simulator learning phase |
| Public Lucario sample | `lucario_public_sample_v3` | Became first strong submitted agent; reached scores above `700` |
| Kojimar simple baseline | `kojimar_simple_baseline_v1` | Current active best; reached `864.5` |
| Public meta replay mining | v5 / v8 / v16-v22 | Found useful Metal/Cinderace and library-out signals, but no submit-ready candidate above v1 |

Recent high-value experiment reports:

- [experiments/75_v8_dragapult_phantump_replay_delta.md](experiments/75_v8_dragapult_phantump_replay_delta.md)
- [experiments/74_opening_category_cross_branch_insights.md](experiments/74_opening_category_cross_branch_insights.md)
- [experiments/73_cross_submission_meta_insights.md](experiments/73_cross_submission_meta_insights.md)
- [experiments/72_v22_midgame_metal_boss_guard_results.md](experiments/72_v22_midgame_metal_boss_guard_results.md)
- [experiments/45_kojimar_simple_baseline_candidate_results.md](experiments/45_kojimar_simple_baseline_candidate_results.md)
- [experiments/44_kojimar_insights_v7_crustle_guard.md](experiments/44_kojimar_insights_v7_crustle_guard.md)
- [experiments/43_lucario_v5_v6_upgrade_attempts.md](experiments/43_lucario_v5_v6_upgrade_attempts.md)
- [experiments/41_lucario_public_v3_candidate_results.md](experiments/41_lucario_public_v3_candidate_results.md)

Chronological submission score tracking lives in
[submissions/39_lucario_public_sample_submission.md](submissions/39_lucario_public_sample_submission.md).

This ledger is intentionally factual. Add one row for every candidate that
reaches a meaningful paired evaluation or Kaggle submission.

## Offline experiments

| Date (UTC) | Candidate | Control | Deck | Seeds x seats | W-D-L | Score rate | CI | Decision |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| 2026-06-21 | `baseline-deterministic-v1` | self-play | starter | 4 games | 2-0-2 by player 0 | n/a | n/a | Reliability pass; freeze as control |
| 2026-06-21 | `baseline-deterministic-v1` | official random policy | starter | 40 seat-balanced games | 5-0-35 | 0.125 | bootstrap 95%: [0.025, 0.225] | Reject for ladder; reliable but strategically weak |
| 2026-06-21 | `development-first-v2` | attack-first v1 | starter | 40 seat-balanced games | 37-0-3 | 0.925 | bootstrap 95%: [0.825, 1.000] | Promote sequencing change |
| 2026-06-21 | `development-first-v2` | official random policy | starter | 40 seat-balanced games | 32-0-8 | 0.800 | bootstrap 95%: [0.675, 0.925] | Pass control screen |
| 2026-06-21 | `development-first-v2` | official random policy, independent screen | starter | 40 seat-balanced games | 31-0-9 | 0.775 | bootstrap 95%: [0.650, 0.900] | Confirm promotion |
| 2026-06-21 | `printed-knockout-v3` | development-first v2 | starter | 40 seat-balanced games | 25-0-15 | 0.625 | bootstrap 95%: [0.475, 0.775] | Hold; interval overlaps parity |
| 2026-06-21 | `attachment-readiness-v4` | development-first v2 | starter | 40 seat-balanced games | 20-0-20 | 0.500 | bootstrap 95%: [0.350, 0.650] | Hold; readiness alone adds no value |
| 2026-06-21 | `attachment-value-v6` | development-first v2 | starter | 40 seat-balanced games | 20-0-20 | 0.500 | bootstrap 95%: [0.350, 0.650] | Hold; 31 target changes, zero failures |
| 2026-06-21 | `eight-basic-deck-v1` | starter deck | 4 Kyogre, 4 Snover, 33 Water Energy | 80 seat-balanced games | 40-0-40 | 0.500 | bootstrap 95%: [0.3875, 0.6125] | Hold; setup gain did not improve outcomes |

## Kaggle submissions

| Date (UTC) | Version | Code hash | Deck hash | Validation | `mu` | `sigma` | Episodes | Decision |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| ? | ? | ? | ? | ? | ? | ? | ? | ? |

## Experiment note template

```markdown
### YYYY-MM-DD - candidate-name

- Hypothesis:
- Single intended change:
- Frozen control and opponents:
- Seeds, seats, and game count:
- Result with uncertainty:
- Runtime/errors:
- Interpretation:
- Decision and next action:
```


## Kaggle notebook validation

| Date (UTC) | Notebook | Version | Status | Verified output |
| --- | --- | ---: | --- | --- |
| 2026-06-21 | `pokemon-tcg-card-database-eda` | 3 | Complete | 1,267 cards plus bounded 1,306-page PDF-reference audit |
| 2026-06-21 | `pokemon-tcg-agent-baseline-and-evaluation` | 5 | Complete | Promoted agent: 31-0-9, score rate 0.775 |
| 2026-06-21 | `pokemon-tcg-action-sequence-experiment` | 6 | Complete | Corrected attachment-value follow-up: 20-0-20, hold |
| 2026-06-21 | `pokemon-tcg-deck-consistency-experiment` | 1 | Complete | Eight-Basic candidate: 40-0-40 over 80 games, hold |
| 2026-06-21 | `pokemon-tcg-submission-packaging` | 6 | Complete | Promoted-agent tar.gz, staged runtime, and hashes verified |

The private Kaggle dataset
[`tuannm3812/pokemon-tcg-ai-battle-agent-source`](https://www.kaggle.com/datasets/tuannm3812/pokemon-tcg-ai-battle-agent-source)
provides the reviewed `main.py` and `deck.csv` to the execution notebooks.
