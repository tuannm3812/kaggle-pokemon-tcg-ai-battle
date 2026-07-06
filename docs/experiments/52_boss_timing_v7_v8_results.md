# Boss timing v7/v8 results

## Goal

Move beyond static target-score boosts and test whether safer Boss's Orders
timing can improve the active `kojimar_simple_baseline_v1` agent.

## Candidate: `kojimar_simple_baseline_v7_boss_ko_only`

Change:

- play Boss's Orders only when the planned benched target is KO-able;
- reject speculative non-KO gusts.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 6-6 | 0.500 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 8-3-1 | 0.708 |
| vs `lucario_public_sample_v3` | 7-5 | 0.583 |
| vs `koushikrudra_libraryout_v1` | 3-9 | 0.250 |

Decision: reject. The idea was plausible but too broad, and the library-out
gate was poor.

## Candidate: `kojimar_simple_baseline_v8_public_boss_guard`

Change:

- keep v1 behavior everywhere except public weak families;
- if the opponent board visibly contains Metal/Cinderace or
  Alakazam/Dunsparce cards, suppress Boss's Orders unless the planned benched
  target is KO-able.

This is a surgical replay-informed change:

- targets the two refreshed v1 public episode weaknesses;
- avoids adding more target-score boosts;
- preserves normal Boss behavior in other matchups.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 8-4 | 0.667 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 5-7 | 0.417 |
| vs `lucario_public_sample_v3` | 7-5 | 0.583 |
| vs `koushikrudra_libraryout_v1` | 5-7 | 0.417 |

Deeper same-seed direct-control gate:

| Candidate | Control | Result | Score |
| --- | --- | ---: | ---: |
| v8 | v1 | 21-11 | 0.656 |
| v1 reference | v1 | 13-18-1 | 0.422 |
| v8 | Lucario v3 | 20-11-1 | 0.641 |
| v1 reference | Lucario v3 | 19-13 | 0.594 |
| v8 | library-out | 8-24 | 0.250 |
| v1 reference | library-out | 9-23 | 0.281 |

Author mini-cells were mixed:

- v8 underperformed v1 against author Abomasnow in the tiny four-game cell;
- v8 improved author Lucario and Dragapult mini-cells;
- v8 remains weak into library-out, but v1 is also weak there.

## Packaging

`kojimar_simple_baseline_v8_public_boss_guard` package smoke passed:

- archive:
  `scratch/submission_packages/kojimar_simple_baseline_v8_public_boss_guard/submission.tar.gz`
- six local package smoke games completed;
- archive contains `main.py`, `deck.csv`, and `cg/`.

## Decision

Promote `kojimar_simple_baseline_v8_public_boss_guard` as the next cautious
leaderboard probe.

It is not risk-free, but it is stronger than the v6 target-score variants and
has a clearer tactical hypothesis: reduce bad speculative gusts in the two
public episode weak families.

