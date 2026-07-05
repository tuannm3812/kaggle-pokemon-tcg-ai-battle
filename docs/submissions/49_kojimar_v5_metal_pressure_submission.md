# Kojimar v5 metal-pressure submission

## Submission

| Field | Value |
| --- | --- |
| Candidate | `kojimar_simple_baseline_v5_metal_pressure` |
| Kaggle reference | `54348833` |
| Description | `kojimar v5 metal pressure` |
| Submitted at | 2026-07-05 03:15:40 UTC |
| Final status | `COMPLETE` |
| Public score | `600.0` |
| Archive | `scratch/submission_packages/kojimar_simple_baseline_v5_metal_pressure/submission.tar.gz` |

## Baseline at submission time

| Candidate | Submission | Public score |
| --- | ---: | ---: |
| `kojimar_simple_baseline_v1` | `54303967` | `879.9` |
| `lucario_public_sample_v3` | `54283898` | `711.2` |

## Rationale

`kojimar_simple_baseline_v1` improved only modestly from the previous check
(`874.5` to `879.9`). Since `kojimar_simple_baseline_v5_metal_pressure` was
already package-smoke tested and targets a real leaderboard episode weakness
around Archaludon/Cinderace/Relicanth decks, it was submitted as the next public
leaderboard probe.

## Follow-up

`54348833` completed with public score `600.0`, far below the active v1 score `879.9`.

Decision: reject v5 as a leaderboard candidate. The target-only Metal/Cinderace pressure looked plausible locally but did not transfer to the public leaderboard. Next work should inspect v5 episodes before making another target-priority patch.

