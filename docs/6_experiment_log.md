# Experiment and Submission Log

This ledger is intentionally factual. Add one row for every candidate that
reaches a meaningful paired evaluation or Kaggle submission.

## Offline experiments

| Date (UTC) | Candidate | Control | Deck | Seeds ? seats | W-D-L | Score rate | CI | Decision |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| 2026-06-21 | `baseline-deterministic-v1` | self-play | starter | 4 games | 2-0-2 by player 0 | n/a | n/a | Reliability pass; freeze as control |
| 2026-06-21 | `baseline-deterministic-v1` | official random policy | starter | 40 seat-balanced games | 5-0-35 | 0.125 | bootstrap 95%: [0.025, 0.225] | Reject for ladder; reliable but strategically weak |

## Kaggle submissions

| Date (UTC) | Version | Code hash | Deck hash | Validation | `mu` | `sigma` | Episodes | Decision |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| ? | ? | ? | ? | ? | ? | ? | ? | ? |

## Experiment note template

```markdown
### YYYY-MM-DD ? candidate-name

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
| 2026-06-21 | `pokemon-tcg-agent-baseline-and-evaluation` | 4 | Complete | 4/4 contract games and 40 control games; explicit reject decision |
| 2026-06-21 | `pokemon-tcg-submission-packaging` | 5 | Complete | Official tar.gz layout, staged runtime, and exact hashes verified |

The private Kaggle dataset
[`tuannm3812/pokemon-tcg-ai-battle-agent-source`](https://www.kaggle.com/datasets/tuannm3812/pokemon-tcg-ai-battle-agent-source)
provides the reviewed `main.py` and `deck.csv` to the execution notebooks.
