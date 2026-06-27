# Submission Packaging Results

## Scope

Kaggle notebook
[pokemon-tcg-submission-packaging](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-submission-packaging)
version 8 completed successfully on 2026-06-27.

The package uses the current promoted production files:

- `agent/main.py`
- `agent/deck.csv`

Held candidates such as planner v1/v2 and switch v1/v2 were not promoted and
are not included.

## Archive

The notebook produced:

- `/kaggle/working/submission.tar.gz`
- `/kaggle/working/submission_manifest.json`

Downloaded local evidence is under ignored scratch storage:

- `scratch/pull_submission_packaging_v8/submission.tar.gz`
- `scratch/pull_submission_packaging_v8/submission_manifest.json`

## Manifest

| Field | Value |
| --- | --- |
| Archive bytes | `1,975,014` |
| Archive SHA-256 | `23cb0f5020857786a1df31da667c29c0a64f5cd8f96b1b742128f27ebd5353c4` |
| `main.py` SHA-256 | `907aafc14b62c1ee6d10096acbd6d67863862d2a4116ada2513c628b87394d69` |
| `deck.csv` SHA-256 | `e92d5717fd04865b0b528307df7a9d9aecc2c7b917bfbd5042fe58e3d1f26997` |

## Archive members

The archive root contains:

- `main.py`
- `deck.csv`
- `cg/__init__.py`
- `cg/api.py`
- `cg/cg.dll`
- `cg/game.py`
- `cg/libcg-arm64.so`
- `cg/libcg.dylib`
- `cg/libcg.so`
- `cg/sim.py`
- `cg/utils.py`

There is no accidental `submission_agent/` parent directory inside the tarball.

## Runtime smoke

The packaged agent completed the notebook smoke test:

| Field | Value |
| --- | ---: |
| Status | finished |
| Winner | 0 |
| Turn | 3 |
| Decisions | 17 |
| Seconds | 0.0092 |

## Decision

The current promoted agent is ready for a baseline competition submission.

Do not submit any held candidate package. If submitting now, use:

```powershell
python -m kaggle competitions submit -c pokemon-tcg-ai-battle -f scratch\pull_submission_packaging_v8\submission.tar.gz -m "promoted development-first baseline"
```
