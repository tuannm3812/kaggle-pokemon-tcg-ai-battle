# v10 Phantump/Trevenant pressure results

## Goal

Public episode analysis showed a small but painful weakness into
Phantump/Trevenant control-style opponents. This candidate tested a narrow
target-priority patch on top of `kojimar_simple_baseline_v1`:

- raise pressure on Dunsparce and Dudunsparce when the opponent shows the
  Phantump/Trevenant line;
- prefer removing Phantump before it evolves or stabilizes;
- avoid over-targeting low-value Hop's Cramorant in that matchup.

## Candidate

`kojimar_simple_baseline_v10_phantump_pressure`

Implementation scope was intentionally small:

- copied the current active-best Kojimar v1 baseline;
- added a Phantump/Trevenant opponent detector;
- routed attack target scoring through a matchup-aware target score function;
- registered the candidate in `scripts/evaluate_author_opponent_suite.py`.

## Validation results

### Compact public-meta challenger gate

The initial compact screen looked encouraging:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 5-3 | 0.625 |
| vs `kojimar_simple_baseline_v8_public_boss_guard` | 5-3 | 0.625 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 4-4 | 0.500 |
| vs `lucario_public_sample_v3` | 5-3 | 0.625 |
| vs `koushikrudra_libraryout_v1` | 4-4 | 0.500 |
| vs official random | 8-0 | 1.000 |

The compact result was enough for deeper validation, not enough for submission.

### Deeper meta gate

The deeper direct-control screen rejected the candidate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 5-15 | 0.250 |
| vs `kojimar_simple_baseline_v8_public_boss_guard` | 7-13 | 0.350 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 9-11 | 0.450 |
| vs `lucario_public_sample_v3` | 12-8 | 0.600 |
| vs `koushikrudra_libraryout_v1` | 9-11 | 0.450 |
| vs author Abomasnow policy | 6-2 | 0.750 |
| vs author Lucario policy | 6-2 | 0.750 |
| vs author Dragapult policy | 6-2 | 0.750 |
| vs author Iono policy | 7-1 | 0.875 |

## Decision

Do not submit v10.

The candidate may be directionally useful against some author-reference decks,
but the active-best regression is too large. This also confirms that the compact
public-meta gate is noisy and should be treated only as a first filter.

## Next strategy

Before creating another submission candidate, improve the gate itself:

1. run a same-seed active-best reference beside every challenger;
2. compare deltas against v1 rather than relying only on absolute small-sample
   scores;
3. require any Phantump/Trevenant or Dragapult patch to preserve library-out and
   active-best direct controls.

The next candidate should be promoted only if it beats the same-seed reference
on public-meta weaknesses without a meaningful active-best regression.