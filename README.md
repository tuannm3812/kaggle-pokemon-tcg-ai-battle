# Pokémon TCG AI Battle

A notebook-first research repository for the Kaggle **Pokémon TCG AI Battle**
simulation competition. The project turns the official simulator and card
catalogue into a reproducible workflow for card-pool analysis, legal-agent
development, paired self-play evaluation, and submission packaging.

> Competition data and Pokémon-related assets are governed by the competition
> rules. Do not redistribute the supplied PDFs, simulator binaries, or derived
> Pokémon assets through this repository.

## Competition snapshot

| Item | Detail |
| --- | --- |
| Task | Submit a 60-card deck and a Python decision agent |
| Evaluation | Repeated ladder games against similarly rated agents |
| Rating | Gaussian skill estimate, with uncertainty decreasing over games |
| Daily limit | Up to 5 submitted agents per team |
| Tracked agents | Latest 2 submissions |
| Deadline | 16 August 2026, 23:59 UTC |
| Official page | [pokemon-tcg-ai-battle](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle) |

The leaderboard rewards game outcomes only. Winning by a larger prize margin
does not produce a larger rating update. Our offline evaluation therefore uses
paired games, win/draw/loss counts, and uncertainty—not average damage.

## Repository map

```text
.
|- agent/                         # Version-controlled policy and deck
|  |- main.py
|  `- deck.csv
|- docs/                          # Rules, strategy, evidence, and runbook
|- notebooks/
|  |- 01_card_database_eda.ipynb
|  |- 02_agent_baseline_and_local_evaluation.ipynb
|  |- 03_submission_packaging_and_validation.ipynb
|  |- 04_action_sequence_experiment.ipynb
|  `- metadata/                  # Kaggle kernel metadata templates
|- scripts/
|  `- build_notebooks.py         # Rebuilds notebooks deterministically
`- requirements.txt
```

## Recommended Kaggle workflow

1. Create a Kaggle notebook attached to the competition data.
2. Import and run `01_card_database_eda.ipynb` to audit the card catalogue and
   deck constraints.
3. Run `02_agent_baseline_and_local_evaluation.ipynb` for contract checks and
   the standard random-control screen.
4. Run `04_action_sequence_experiment.ipynb` before promoting a sequencing
   change; it freezes both policies and records state-aware episode telemetry.
5. Run `03_submission_packaging_and_validation.ipynb`. Download its verified
   `submission.tar.gz`, then submit it on the competition page.
6. Record validation, uncertainty, episode count, and the promotion/submission
   decision in `docs/6_experiment_log.md`.

See [the full Kaggle runbook](docs/5_kaggle_runbook.md) for exact steps and
failure diagnostics.

## Local setup

The card EDA can run locally after placing `EN_Card_Data.csv` under
`data/raw/`. The official simulator requires `cg.dll` on Windows or
`libcg.so` on Linux; obtain it from the competition data and never commit it.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
jupyter lab
```

Credentials are intentionally absent from the repository. Prefer Kaggle's
attached competition data in notebooks. For local API use, keep the token
outside the repo and never print it in notebook output.

## Current agent

`agent/main.py` is the promoted deterministic development-first policy. Its
main-phase order is evolve, ability, attach, play, attack, retreat, discard,
then end. The legality shield and stable tie-breaking remain unchanged.

The single-change sequencing experiment completed 120 games with no failures.
Development-first beat attack-first `37-0-3` (`0.925`, bootstrap 95% interval
`[0.825, 1.000]`) and beat the random control `32-0-8` (`0.800`, interval
`[0.675, 0.925]`). The independent standard screen scored `31-0-9` (`0.775`,
interval `[0.650, 0.900]`).

This agent passes the random-control screen but is not yet ladder-proven. The
next controlled change should add an immediate-knockout exception or card-aware
attachment scoring, evaluated against stronger frozen opponents.

## Kaggle validation

The complete workflow was run on Kaggle on 21 June 2026:

| Notebook | Status | Evidence |
| --- | --- | --- |
| [Card Database EDA](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-card-database-eda) | Complete | 1,267 cards plus bounded PDF-reference audit |
| [Agent Evaluation](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-agent-baseline-and-evaluation) | Complete | Promoted agent passed random screen at 0.775 |
| [Action Sequence Experiment](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-action-sequence-experiment) | Complete | 120 games; development-first promoted |
| [Submission Packaging](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-submission-packaging) | Complete | Promoted-agent tar.gz and hashes verified |

The agent source is mounted from a private Kaggle dataset and credentials remain
outside this repository.
