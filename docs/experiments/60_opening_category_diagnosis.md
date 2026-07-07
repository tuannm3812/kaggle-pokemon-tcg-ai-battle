# Opening-category diagnosis after v15

## Goal

The v15 Lucario-tempo candidate did not clear gates, so this step checked whether
there is a cleaner opening/setup category that separates public wins from losses.
The target was to avoid building another broad matchup patch without evidence.

## New tool

Added `scripts/analyze_opening_categories.py`.

The script reads cached public replays and summarizes:

- setup active Pokemon;
- whether the agent went first;
- first visible turn-1 hand features;
- first attack turn and attacker;
- early energy attachment targets;
- win/loss rates by opening bucket and setup active.

## Current score snapshot

Checked on 2026-07-07 with the Kaggle API:

| Submission | Candidate | Public score |
| ---: | --- | ---: |
| `54303967` | `kojimar_simple_baseline_v1` | 864.5 |
| `54391951` | `kojimar_simple_baseline_v8_public_boss_guard` | 788.3 |
| `54348833` | `kojimar_simple_baseline_v5_metal_pressure` | 720.7 |
| `54283898` | `lucario_public_sample_v3` | 711.2 |

v1 remains the active best. v8 is still far below v1 despite slight score drift.

## v8 all-archetype opening read

For all available v8 public episodes:

| Opening bucket | Result | Score | Read |
| --- | ---: | ---: | --- |
| `riolu_slow_path` | 0-2 | 0.000 | weak but tiny sample |
| `unknown_active` | 20-18 | 0.526 | mixed; replay encoding often hides setup-active action |
| `riolu_fast_path` | 6-2 | 0.750 | good signal |
| `makuhita_active` | 3-1 | 0.750 | not inherently bad |
| `solrock_active` | 3-1 | 0.750 | not inherently bad |
| `lunatone_active` | 4-1 | 0.800 | not inherently bad |

This weakens the idea that a simple setup-active rule will fix the score.

## v8 Dragapult / Phantump slice

For v8 Dragapult + Phantump/Trevenant public episodes:

| Opening bucket | Result | First attack turns |
| --- | ---: | --- |
| `unknown_active` | 0-4 | 3, 3, 5, 3 |
| `riolu_fast_path` | 0-2 | 5, 3 |
| `makuhita_active` | 0-1 | 7 |
| `solrock_active` | 0-1 | 13 |

Every category loses in this slice, including nominally good Riolu-fast starts.
That means the failure is not explained by one setup-active category alone.

## v1 comparison on same broad archetypes

For active-best v1 Dragapult + Phantump/Trevenant public episodes:

| Opening bucket | Result | Score |
| --- | ---: | ---: |
| `unknown_active` | 4-6 | 0.400 |
| `solrock_active` | 2-0 | 1.000 |
| `makuhita_active` | 1-0 | 1.000 |
| `riolu_fast_path` | 1-0 | 1.000 |

v1 can win with Solrock, Makuhita, and Riolu starts in these broad archetypes.
This suggests the v8 critical-loss pattern is partly public opponent sample/meta
drift, not a deterministic local policy bug we can fix with one opening rule.

## Decision

Do not submit a new candidate from v11-v15.

Also do not build another broad static patch immediately. The last candidates
changed target scoring, Boss timing, first-player choice, and energy routing;
none showed enough transfer quality.

## Next strategy

The next promising work should be one of these, in order:

1. improve public replay refresh/download reliability so all listed episodes are
   available for v1/v8/v5 before deriving meta conclusions;
2. compare v1 and v8 public opponents by exact opponent submission/team and deck
   signature, to separate policy weakness from opponent-sample drift;
3. only build a candidate if a repeated exact signature shows a replay-level
   decision pattern that differs from wins.

For now, active v1 remains the safest leaderboard candidate.