# Failed Baseline Submission and Defensive Resubmission

## Failed submission

The first baseline submission failed Kaggle validation.

| Field | Value |
| --- | --- |
| Ref | `54099181` |
| Message | `promoted development-first baseline` |
| Status | `SubmissionStatus.ERROR` |
| Reported UI error | `Validation Episode failed` |

Local reproduction from the exact submitted package completed 200 self-play
games and 400 games against the official sample agent, so the failure was not
reproduced in normal battle loops.

## Defensive fix

`agent/main.py` was hardened at the public `agent()` entrypoint:

- malformed or partial observations now return the deck instead of raising;
- deck-request edge cases such as `None`, `{}`, and `{"select": None}` are
  handled safely;
- if deterministic action selection raises due to a hidden runner/context edge
  case, the agent falls back to the first legal option indices.

This keeps the promoted development-first strategy intact for normal
observations and only changes error handling.

## Rebuilt package

A fresh tarball was built locally from the current repository source and the
official sample-submission `cg/` runtime rather than relying on the Kaggle
agent-source dataset.

| Field | Value |
| --- | --- |
| Local package | `scratch/local_resubmission_defensive/submission.tar.gz` |
| Archive SHA-256 | `93e84db79d62ede01ea9726faf4a0c1a6e08c52e6d56bf31deee425ca068b6aa` |
| `main.py` SHA-256 | `2415493d95cadbbe672bd55a291ece8d70eec6f56db8cb7f59a2d1e27676d1a7` |
| `deck.csv` SHA-256 | `e92d5717fd04865b0b528307df7a9d9aecc2c7b917bfbd5042fe58e3d1f26997` |

Validation before resubmission:

- edge deck-request calls passed;
- 100 self-play games completed;
- 200 games against the official sample agent completed;
- archive root contains `main.py`, `deck.csv`, and `cg/` without a parent
  `submission_agent/` directory.

## Defensive resubmission

| Field | Value |
| --- | --- |
| Ref | `54099849` |
| Message | `defensive promoted baseline resubmission` |
| Timestamp | `2026-06-27 06:57:35.890000` |
| Status at last check | `SubmissionStatus.ERROR` |

Check status with:

```powershell
python -m kaggle competitions submissions -c pokemon-tcg-ai-battle
```

The defensive resubmission also failed Kaggle validation. Local validation did not reproduce the failure, so the next required evidence is the Kaggle UI `Agent 0 Logs`, `Agent 1 Logs`, or replay error from submission ref `54099849`.
