# Experiment and Submission Log

This ledger is intentionally factual. Add one row for every candidate that
reaches a meaningful paired evaluation or Kaggle submission.

## Offline experiments

| Date (UTC) | Candidate | Control | Deck | Seeds Ã— seats | W-D-L | Score rate | CI | Decision |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| 2026-06-21 | `baseline-deterministic-v1` | self-play | starter | 4 games | 2-0-2 by player 0 | n/a | n/a | Reliability pass; freeze as control |

## Kaggle submissions

| Date (UTC) | Version | Code hash | Deck hash | Validation | `mu` | `sigma` | Episodes | Decision |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” |

## Experiment note template

```markdown
### YYYY-MM-DD â€” candidate-name

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
| 2026-06-21 | `pokemon-tcg-card-database-eda` | 1 | Complete | Official catalogue and deck audit executed |
| 2026-06-21 | `pokemon-tcg-agent-baseline-and-evaluation` | 2 | Complete | 4/4 self-play games finished; 0 contract errors |
| 2026-06-21 | `pokemon-tcg-submission-packaging` | 2 | Complete | ZIP integrity, root layout, and repository hashes verified |

The private Kaggle dataset
[`tuannm3812/pokemon-tcg-ai-battle-agent-source`](https://www.kaggle.com/datasets/tuannm3812/pokemon-tcg-ai-battle-agent-source)
provides the reviewed `main.py` and `deck.csv` to the execution notebooks.
