# Missing `__file__` Submission Fix

## Root cause

Kaggle validation executed `main.py` without defining `__file__`. Both failed
submissions crashed before the validation episode started:

```text
NameError: name '__file__' is not defined
```

The crash happened inside `read_deck_csv()` while trying to resolve
`Path(__file__).resolve().with_name("deck.csv")`.

## Fix

`agent/main.py` now resolves the deck path without requiring `__file__`:

1. `/kaggle_simulations/agent/deck.csv`
2. `deck.csv`
3. `Path(__file__).resolve().with_name("deck.csv")`, only when `__file__`
   exists

This keeps normal local and Kaggle notebook execution working while matching
the Kaggle competition wrapper.

## Validation

Before resubmission, the fixed package passed:

- execution of `main.py` without `__file__`;
- initial observation deck requests with `select: null`;
- `agent(None)` fallback;
- 100 self-play games;
- 200 games against the official sample agent.

## Corrected submission

| Field | Value |
| --- | --- |
| Ref | `54100265` |
| Message | `fix deck loader missing __file__` |
| Timestamp | `2026-06-27 07:17:00.513000` |
| Status at last check | `SubmissionStatus.PENDING` |
| Local package | `scratch/local_resubmission_no_file/submission.tar.gz` |
| Archive SHA-256 | `8c190a608d9160a32626b7c2418be6b7f497243d6227d7539e0edabf8de1731f` |
| `main.py` SHA-256 | `d95738a6fff646d5dc2b150ea0dc64cd10096b0ecfcb0d045898cd30b8a8e72b` |
| `deck.csv` SHA-256 | `e92d5717fd04865b0b528307df7a9d9aecc2c7b917bfbd5042fe58e3d1f26997` |

Check final status with:

```powershell
python -m kaggle competitions submissions -c pokemon-tcg-ai-battle
```
