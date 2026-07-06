# Kojimar v8 public Boss guard submission

## Submission

| Field | Value |
| --- | --- |
| Candidate | `kojimar_simple_baseline_v8_public_boss_guard` |
| Kaggle reference | `54391951` |
| Description | `kojimar v8 public boss guard` |
| Submitted at | 2026-07-06 10:50:55 UTC |
| Final status | `COMPLETE` |
| Public score | `600.0` |
| Archive | `scratch/submission_packages/kojimar_simple_baseline_v8_public_boss_guard/submission.tar.gz` |

## Baseline at submission time

| Candidate | Submission | Public score |
| --- | ---: | ---: |
| `kojimar_simple_baseline_v1` | `54303967` | `864.5` |
| `kojimar_simple_baseline_v5_metal_pressure` | `54348833` | `733.3` |
| `lucario_public_sample_v3` | `54283898` | `711.2` |

## Rationale

v8 is the first post-v5 candidate with a stronger deeper direct-control signal
against active v1 while avoiding another static target-score boost. It guards
speculative Boss's Orders only when the opponent visibly belongs to the public
weak families:

- Metal/Cinderace;
- Alakazam/Dunsparce.

Package smoke passed before submission.

## Follow-up

`54391951` completed with public score `600.0`, far below v1 at submission time (`864.5`).

Decision: reject v8 as a leaderboard candidate. The local direct signal did not transfer. Before another submission, inspect v8 episodes and improve the replay-derived validation gate.

