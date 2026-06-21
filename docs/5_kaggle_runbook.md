# Kaggle Notebook and Submission Runbook

## One-time setup

1. Open the competition and accept its rules with the submitting account.
2. Create a private Kaggle notebook and attach the competition data.
3. Keep Internet disabled for the final reproducibility run.
4. Import this repository's notebooks or push them with the Kaggle API.

No credential is required inside a Kaggle notebook. The competition dataset is
mounted under `/kaggle/input`; notebooks discover the exact subdirectory rather
than hard-coding an account-specific path.

## Notebook order

### 1. Card database EDA

Run `01_card_database_eda.ipynb`. Confirm that it finds
`EN_Card_Data.csv`, prints the catalogue schema, and validates the starter
deck. Review warnings before changing deck composition.

### 2. Baseline and local evaluation

Run `02_agent_baseline_and_local_evaluation.ipynb`. It locates the official
`sample_submission`, copies the SDK to `/kaggle/working/agent_eval`, installs
the repository `main.py` and `deck.csv`, then performs deterministic self-play.

A successful smoke test proves packaging and API compatibility only. It does
not prove ladder strength.

### 3. Action-sequencing experiment

Run `04_action_sequence_experiment.ipynb` when testing main-phase ordering. It
freezes attack-first and development-first maps independently of the current
agent source, runs three seat-balanced matchups, and writes state snapshots plus
a promotion decision.

### 4. Package and validate

Run `03_submission_packaging_and_validation.ipynb`. It creates a clean staging
directory, copies the official `cg` runtime plus the version-controlled policy
and deck, runs static checks, and writes `/kaggle/working/submission.tar.gz`.

Inspect the tarball member list. `main.py` and `deck.csv` must be at the archive
root, with the SDK under `cg/`; an accidental extra parent directory can make
an otherwise correct agent fail validation.

## Pushing notebooks from a local machine

Copy the appropriate template from `notebooks/metadata/` to
`kernel-metadata.json`, replace `YOUR_DATASET_SLUG` with a dataset containing
the repository's `agent/` directory if needed, and run:

```powershell
python -m kaggle kernels push -p notebooks
python -m kaggle kernels status tuannm3812/pokemon-tcg-card-database-eda
```

Keep API credentials outside this repository. The metadata templates are
private by default and disable Internet.

## Failure diagnosis

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Competition input not found | Data not attached | Add competition data in notebook settings |
| `libcg.so` load error | SDK copied incompletely | Copy the entire official `cg` directory |
| Validation `IndexError` | Illegal option index/count | Log context and run legality assertions |
| Deck rejected | Construction rule violation | Re-run deck audit and inspect start error codes |
| Timeout | Search budget too high or loop stalled | Add hard decision/game limits and profile contexts |
| Works locally, fails on Kaggle | path/platform assumption | Use resolver functions and Linux runtime from SDK |

## Credential safety

Never upload `kaggle.json` as notebook data, commit it, display it, or print
environment variables. If a token is ever exposed in output or Git history,
revoke it immediately in Kaggle account settings.
