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
├── agent/                         # Version-controlled policy and deck
│   ├── main.py
│   └── deck.csv
├── docs/
│   ├── 0_coding_standards.md
│   ├── 1_competition_instructions.md
│   ├── 2_eda_and_environment.md
│   ├── 3_agent_strategy.md
│   ├── 4_evaluation_and_submissions.md
│   ├── 5_kaggle_runbook.md
│   └── 6_experiment_log.md
├── notebooks/
│   ├── 01_card_database_eda.ipynb
│   ├── 02_agent_baseline_and_local_evaluation.ipynb
│   ├── 03_submission_packaging_and_validation.ipynb
│   └── metadata/                  # Kaggle kernel metadata templates
├── scripts/
│   └── build_notebooks.py         # Rebuilds notebooks deterministically
└── requirements.txt
```

## Recommended Kaggle workflow

1. Create a Kaggle notebook attached to the competition data.
2. Import and run `01_card_database_eda.ipynb` to audit the card catalogue and
   deck constraints.
3. Import and run `02_agent_baseline_and_local_evaluation.ipynb` with Internet
   disabled. It copies the official SDK into `/kaggle/working`, loads the
   repository policy, and runs paired self-play smoke tests.
4. Run `03_submission_packaging_and_validation.ipynb`. Download its
   `submission.tar.gz`, then submit it on the competition page.
5. Record the validation state, ladder rating, uncertainty, episode count, and
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

## Current baseline

`agent/main.py` is a deterministic, legality-first baseline. It removes the
random sample agent's run-to-run noise, ranks main-phase action types, and uses
stable tie-breaking. It is a foundation for controlled experiments—not a
claim of competitive strength.

The next meaningful upgrade is state-aware scoring of attacks, energy
attachments, evolutions, and setup choices, evaluated against frozen opponents
with seat-swapped paired games.

The latest Kaggle screen rejects this baseline for ladder use: it scored
`5-0-35` against the official random control (`0.125`, bootstrap 95% interval
`[0.025, 0.225]`). Candidate telemetry shows 322 attack selections but only 64
attachments, versus 139 attacks and 228 attachments for the control. The next
policy change should prevent premature attacks and value board development.


## Kaggle validation

The complete workflow was run on Kaggle on 21 June 2026:

| Notebook | Status | Evidence |
| --- | --- | --- |
| [Card Database EDA](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-card-database-eda) | Complete | 1,267 cards plus bounded PDF-reference audit |
| [Agent Baseline and Evaluation](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-agent-baseline-and-evaluation) | Complete | 40 control games; baseline rejected at 0.125 score rate |
| [Submission Packaging](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-submission-packaging) | Complete | Staged runtime game and exact tar.gz source/archive hashes verified |

The agent source is mounted from a private Kaggle dataset and credentials remain
outside this repository.
