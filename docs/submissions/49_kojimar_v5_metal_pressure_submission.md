# Kojimar v5 metal-pressure submission

## Submission

| Field | Value |
| --- | --- |
| Candidate | `kojimar_simple_baseline_v5_metal_pressure` |
| Kaggle reference | `54348833` |
| Description | `kojimar v5 metal pressure` |
| Submitted at | 2026-07-05 03:15:40 UTC |
| Final status | `COMPLETE` |
| Latest checked public score | `729.9` |
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

`54348833` initially completed with a low public score, then drifted up to `729.9` by the 2026-07-06 check. It remains far below active v1 (`878.7`).

Episode diagnosis shows v5 did improve the intended Metal/Cinderace slice, but it did not improve the overall leaderboard enough and remains weak into Alakazam/Dunsparce and Crustle/library-out samples.

Decision: reject v5 as the active candidate, but keep it as an informative ablation. See `docs/experiments/50_v5_episode_diagnosis.md` before designing v6.

