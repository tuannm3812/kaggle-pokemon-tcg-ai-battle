# Loss Taxonomy and Pressure-Opponent Evaluation

## Purpose

The attack-planner experiments showed that aggregate win rate is not enough to
choose the next change. Planner v2 fixed the zero-damage Kyogre mechanism, but
it did not beat the promoted policy. The next step is therefore diagnostic:
measure why games are lost before adding another heuristic.

Notebook `10_loss_taxonomy_and_pressure_opponent.ipynb` compares two frozen
candidate policies:

- `promoted`: the current production `agent/main.py`;
- `planner_v2`: the held Abomasnow resource-guard planner.

It tests both against:

- `random`: the official sample random policy;
- `pressure`: a frozen deterministic pressure policy that prioritizes attacks
  earlier than the promoted development-first control.

The pressure control is not intended as a submission candidate. It is an
evaluation opponent that stresses tempo and attack timing.

## Outputs

The notebook writes:

- `/kaggle/working/loss_taxonomy_experiment.json`
- bounded loss replays under `/kaggle/working/loss_taxonomy_replays/`

The JSON contains:

- matchup summaries with bootstrap intervals;
- controlled seat and first-player attribution;
- per-game loss labels;
- mechanism tables for action choice, readiness, retreat availability, planner
  confidence, immediate knockouts, and expected damage;
- replay paths for sampled losses.

## Loss labels

Labels are triage heuristics, not final truth:

| Label | Meaning |
| --- | --- |
| `setup` | The candidate failed to build an early board or ready attacker. |
| `attacker_development` | No ready attacker appeared across candidate main decisions. |
| `attachment` | Attachment did not appear to convert into active readiness. |
| `switch` | A ready benched attacker or retreat opportunity was not converted. |
| `attack_timing` | Attack was available, or an immediate-KO plan existed, but attack was not chosen. |
| `opponent_pressure` | The loss happened quickly enough that tempo pressure may dominate. |
| `unclear_review_replay` | The replay should be reviewed manually before assigning blame. |

Use a label only when it repeats across controlled cells and agrees with replay
inspection.

## Decision rule

Do not promote directly from this notebook. Use it to choose the next single
implementation change:

1. run the notebook on Kaggle;
2. download `loss_taxonomy_experiment.json`;
3. inspect at least one replay per dominant loss label;
4. choose one focused change only if labels and replay evidence agree.

If the dominant label is `attack_timing` or `switch`, selective Search API work
becomes worth revisiting. If it is `setup` or `attacker_development`, improve
deterministic sequencing or deck consistency first.
