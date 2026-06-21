# Experiment and Submission Log

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
| 2026-06-21 | `pokemon-tcg-action-sequence-experiment` | 4 | Complete | Attachment follow-up: 20-0-20, hold; 84 target changes |
| 2026-06-21 | `pokemon-tcg-submission-packaging` | 6 | Complete | Promoted-agent tar.gz, staged runtime, and hashes verified |

The private Kaggle dataset
[`tuannm3812/pokemon-tcg-ai-battle-agent-source`](https://www.kaggle.com/datasets/tuannm3812/pokemon-tcg-ai-battle-agent-source)
provides the reviewed `main.py` and `deck.csv` to the execution notebooks.
