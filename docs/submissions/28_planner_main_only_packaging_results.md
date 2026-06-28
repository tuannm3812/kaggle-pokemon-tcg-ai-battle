# Planner Main-Only Packaging Results

## Scope

This step packaged the current promotion candidate for Kaggle submission:

- `candidates/planner_main_only_v1/`

Production `agent/` remains unchanged.

## Packaging script

Added:

- `scripts/package_submission.py`

The script stages:

- candidate `main.py`;
- candidate `deck.csv`;
- official `cg/` runtime;
- root-level `submission.tar.gz`.

It also performs:

- Python compile validation;
- deck length validation;
- staged self-play smoke tests;
- archive member checks;
- bytecode/cache exclusion from the final archive.

## Package result

Command:

```powershell
python scripts\package_submission.py --candidate planner_main_only_v1 --games 10 --max-decisions 2500 --seed 2026062812
```

Output package:

```text
scratch/submission_packages/planner_main_only_v1/submission.tar.gz
```

Report:

```text
scratch/submission_packages/planner_main_only_v1/package_report.json
```

Static checks:

| Check | Result |
| --- | ---: |
| `main.py` bytes | 13,843 |
| deck cards | 60 |
| `cg/` files staged | 14 |
| archive members | 12 |
| archive size | 1,977,219 bytes |

Smoke test:

| Test | Result |
| --- | --- |
| staged self-play games | 10/10 completed |
| action contract validation | passed |
| decision limit | not reached |

## Prior failure guard

The candidate deck loader was hardened before packaging because planner-derived
candidates inherited a brittle `Path(__file__)` assumption.

The packaged `main.py` was explicitly executed in a registered module namespace
without `__file__`, and `read_deck_csv()` successfully loaded the staged
`deck.csv`.

This protects against the same Kaggle validation failure that affected the
earlier baseline submission attempt.

## Decision

The package is ready for Kaggle submission approval.

Do not submit automatically without the explicit submit step. If approved, use:

```powershell
python -m kaggle competitions submit -c pokemon-tcg-ai-battle -f scratch\submission_packages\planner_main_only_v1\submission.tar.gz -m "planner main only v1"
```
