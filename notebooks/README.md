# Notebook Index

The notebook filenames are intentionally stable because Kaggle metadata and
builder scripts reference them directly. Do not move notebooks into subfolders
unless the corresponding `notebooks/metadata/*.json` files and builder scripts
are updated in the same commit.

## Active workflow notebooks

These are the notebooks to use for a fresh Kaggle workflow. The static card/deck
EDA remains notebook-first; live public-meta and replay-loss EDA should be run
through `scripts/analyze_submission_episodes.py`,
`scripts/diagnose_public_loss_replays.py`, and
`scripts/evaluate_public_meta_gate.py`, then summarized in `docs/experiments/`.
This keeps Kaggle notebooks stable while fast strategy iteration happens in
local scripts.

| Notebook | Status | Purpose |
| --- | --- | --- |
| `01_card_database_eda.ipynb` | Active | Card catalogue, deck constraints, and static starter-deck EDA |
| `02_agent_baseline_and_local_evaluation.ipynb` | Active | Baseline contract checks and random-control screen |
| `03_submission_packaging_and_validation.ipynb` | Active | Kaggle-style packaging and validation |

## Historical experiment notebooks

These notebooks preserve evidence and Kaggle-runnable experiment templates, but
new quick iteration should usually happen in `scripts/` first.

| Notebook | Status | Purpose |
| --- | --- | --- |
| `04_action_sequence_experiment.ipynb` | Historical | Development-first vs attack-first sequencing |
| `05_deck_consistency_experiment.ipynb` | Historical | Deck composition consistency checks |
| `06_first_player_and_replay_observability.ipynb` | Historical | First-player and replay observability |
| `07_controlled_turn_order_experiment.ipynb` | Historical | Controlled seat/turn-order factorial |
| `08_abomasnow_attack_planner_experiment.ipynb` | Historical | Planner v1 experiment |
| `09_abomasnow_planner_resource_guard_experiment.ipynb` | Historical | Planner v2 resource guard experiment |
| `10_loss_taxonomy_and_pressure_opponent.ipynb` | Historical | Loss taxonomy and pressure control |
| `11_conservative_switch_experiment.ipynb` | Historical | Conservative switch v1 |
| `12_conservative_switch_v2_experiment.ipynb` | Historical | Conservative switch v2 |

## Metadata

Kaggle kernel metadata lives in `notebooks/metadata/`. Each metadata file has a
`code_file` field that points to one notebook filename at this directory root.
That is why the physical notebook layout stays flat.

## Strategy EDA handoff

The current candidate workflow is:

1. Use `01_card_database_eda.ipynb` for static card/deck understanding.
2. Use public episode scripts for live meta frequency, weak archetypes, and loss timing.
3. Write candidate briefs in `docs/2_eda_and_environment.md` and `docs/experiments/` before coding a new agent.
4. Promote a candidate only after the public-meta gate avoids protected-matchup regressions.

## Maintenance rule

- Keep stable Kaggle notebooks at `notebooks/` root.
- Add new local evaluator work under `scripts/` unless Kaggle notebook execution
  is required.
- If a notebook is superseded, mark it as Historical here instead of moving it.
- If a notebook is renamed, update metadata, builders, README links, and docs in
  the same commit.
