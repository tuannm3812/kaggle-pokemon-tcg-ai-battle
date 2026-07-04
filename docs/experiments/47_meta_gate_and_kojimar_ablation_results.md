# Meta gate and Kojimar ablation results

## Goal

Continue the search for a stronger candidate than the active submitted
`kojimar_simple_baseline_v1`, without spending another Kaggle submission slot
on a weak local signal.

## New evaluation tools

Added two local gates:

- `scripts/evaluate_meta_gate.py` combines the most important promotion checks:
  active best, previous Lucario best, library-out/control, official random, and
  author archetype decks.
- `scripts/evaluate_unforced_direct_gate.py` runs live-style direct games
  without overriding each policy's `IS_FIRST` choice. This is needed for
  first/second-player strategy experiments because the standard direct gates
  intentionally force turn order.

## Candidates tested

### `kojimar_simple_baseline_v2`

Experiment: add explicit anti-library-out recognition and raise priority for
Great Tusk, Dwebble, Crustle, and Terrakion. It also used a stricter low-deck
threshold against library-out/control.

Initial compact meta gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 6-6 | 0.500 |
| vs `lucario_public_sample_v3` | 7-5 | 0.583 |
| vs `koushikrudra_libraryout_v1` | 6-6 | 0.500 |
| vs official random | 12-0 | 1.000 |

Deeper direct-control check:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 13-19 | 0.406 |
| vs `lucario_public_sample_v3` | 21-11 | 0.656 |
| vs `koushikrudra_libraryout_v1` | 13-19 | 0.406 |

Decision: reject. The deeper run showed the anti-library-out patch did not
reliably improve the control matchup and lost ground to the active best.

### `kojimar_simple_baseline_v3`

Experiment: narrower anti-library-out target-priority ablation. It keeps the
new target priorities but removes the stricter low-deck behavior and Boss's
Orders change.

Compact meta gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 5-7 | 0.417 |
| vs `lucario_public_sample_v3` | 6-6 | 0.500 |
| vs `koushikrudra_libraryout_v1` | 6-6 | 0.500 |
| vs official random | 11-1 | 0.917 |

Decision: reject. Target-priority alone did not beat the active best.

### `kojimar_simple_baseline_v4_second`

Experiment: same policy/deck as v1, but choose to go second in live-style
`IS_FIRST` decisions.

Forced-turn meta gates are not sufficient for this candidate because they
override first-player choice by design. The unforced live-style check is the
more relevant signal:

| Matchup | Result | Score |
| --- | ---: | ---: |
| v1 vs v1, unforced reference | 8-12 | 0.400 |
| v4_second vs v1, unforced | 9-11 | 0.450 |

Decision: reject for now. Choosing second is not clearly stronger and is not
worth a submission slot.

## Additional survivor screens

Older watchlist candidates were checked against the current active best:

| Candidate | Control | Result | Score | Decision |
| --- | --- | ---: | ---: | --- |
| `lucario_public_sample_v4` | `kojimar_simple_baseline_v1` | 3-9 | 0.250 | reject |
| `lucario_public_sample_v7` | `kojimar_simple_baseline_v1` | 4-8 | 0.333 | reject |
| `iono_public_sample_v1` | `kojimar_simple_baseline_v1` | 2-10 | 0.167 | reject |

## Current conclusion

No new candidate is stronger than `kojimar_simple_baseline_v1` yet. The active
best should remain unchanged.

The highest-value next experiment is not another broad Lucario heuristic. The
next candidate should target one of these narrower areas:

1. a control/library-out counter that does not reduce normal prize-race tempo;
2. a match-state-gated trainer policy, especially draw suppression and Boss's
   Orders timing;
3. richer episode telemetry from leaderboard replays before changing the agent
   again.

