# Post-Submission Ladder Risk Plan

## Current status

Latest Kaggle check on 2026-06-28:

| Submission | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `466.3` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `493.8` |

`planner_main_only_v1` validated and initially looked promising locally, but its
ladder score has drifted below the previous accepted baseline. Do not submit
another policy until the offline gate better matches ladder risk.

## Interpretation

The current local direct gate over-rewards candidates that beat our own promoted
baseline. The ladder appears to punish behaviors that our local baseline and
small author suite do not represent well enough.

## Next experiment direction

Before creating another submission candidate, improve the evaluator:

1. keep the promoted baseline as the production reference;
2. add a stronger anti-planner control that punishes delayed attacks and poor
   first-player/seat splits;
3. require any candidate to beat promoted directly and avoid weak cells below
   `0.40`;
4. require no author-style matchup below `0.45`;
5. only package after the evaluator catches the known `planner_main_only_v1`
   ladder-risk pattern.

The next implementation should therefore be an evaluation upgrade, not a new
agent heuristic.
