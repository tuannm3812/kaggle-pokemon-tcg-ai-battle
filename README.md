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
|- docs/
|  |- README.md                  # Documentation index and latest score snapshot
|  |- experiments/               # Detailed experiment evidence
|  `- submissions/               # Packaging and Kaggle submission history
|- notebooks/
|  |- README.md                  # Notebook index; filenames kept stable for Kaggle
|  |- 01_card_database_eda.ipynb
|  |- 02_agent_baseline_and_local_evaluation.ipynb
|  |- 03_submission_packaging_and_validation.ipynb
|  `- metadata/                  # Kaggle kernel metadata templates
|- scripts/                      # Notebook builders and local evaluation tools
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
5. Run `05_deck_consistency_experiment.ipynb` for an isolated deck change while
   keeping the promoted policy frozen.
6. Run `03_submission_packaging_and_validation.ipynb`. Download its verified
   `submission.tar.gz`, then submit it on the competition page.
7. Record validation, uncertainty, episode count, and the promotion/submission
   decision in `docs/6_experiment_log.md` or the relevant `docs/experiments/` report.

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

## Current agent and score snapshot

`agent/main.py` remains the stable promoted baseline source. Recent experiments
produced `planner_main_only_v1`, which validated and submitted successfully, but
its ladder score later drifted below the previous accepted baseline.

Latest Kaggle status check on 2026-06-29:

| Submission | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54126975` | `planner main only v1` | `COMPLETE` | `493.9` |
| `54100265` | `fix deck loader missing __file__` | `COMPLETE` | `484.0` |

Conclusion: keep treating `planner_main_only_v1` as a validated experiment, not
a confirmed ladder improvement. See [docs/README.md](docs/README.md) for the
organized evidence trail.

## Kaggle validation

The complete workflow was run on Kaggle on 21 June 2026:

| Notebook | Status | Evidence |
| --- | --- | --- |
| [Card Database EDA](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-card-database-eda) | Complete | 1,267 cards plus bounded PDF-reference audit |
| [Agent Evaluation](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-agent-baseline-and-evaluation) | Complete | Promoted agent passed random screen at 0.775 |
| [Action Sequence Experiment](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-action-sequence-experiment) | Complete | Development-first promoted; three isolated follow-ups held |
| [Deck Consistency Experiment](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-deck-consistency-experiment) | Complete | Eight-Basic variant held at 40-0-40 over 80 games |
| [Submission Packaging](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-submission-packaging) | Complete | Promoted-agent tar.gz and hashes verified |

The agent source is mounted from a private Kaggle dataset and credentials remain
outside this repository.
