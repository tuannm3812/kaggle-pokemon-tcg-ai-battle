# Notebook Index

The notebook filenames are intentionally stable because Kaggle metadata and
builder scripts reference them directly. Keep notebooks at the repository
`notebooks/` root unless the metadata and builders are updated together.

## Core workflow

| Notebook | Purpose |
| --- | --- |
| `01_card_database_eda.ipynb` | Card catalogue, deck constraints, and early EDA |
| `02_agent_baseline_and_local_evaluation.ipynb` | Baseline contract checks and random-control screen |
| `03_submission_packaging_and_validation.ipynb` | Kaggle-style packaging and validation |

## Historical experiments

| Notebook | Purpose |
| --- | --- |
| `04_action_sequence_experiment.ipynb` | Development-first vs attack-first sequencing |
| `05_deck_consistency_experiment.ipynb` | Deck composition consistency checks |
| `06_first_player_and_replay_observability.ipynb` | First-player and replay observability |
| `07_controlled_turn_order_experiment.ipynb` | Controlled seat/turn-order factorial |
| `08_abomasnow_attack_planner_experiment.ipynb` | Planner v1 experiment |
| `09_abomasnow_planner_resource_guard_experiment.ipynb` | Planner v2 resource guard experiment |
| `10_loss_taxonomy_and_pressure_opponent.ipynb` | Loss taxonomy and pressure control |
| `11_conservative_switch_experiment.ipynb` | Conservative switch v1 |
| `12_conservative_switch_v2_experiment.ipynb` | Conservative switch v2 |

Prefer adding new local evaluation scripts under `scripts/` when an experiment
does not need Kaggle notebook execution.
