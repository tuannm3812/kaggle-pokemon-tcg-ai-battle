# Agent Strategy

## Current strategic state

Current active best submitted agent: `kojimar_simple_baseline_v1`.

Latest tracked public score: `861.4` on 2026-07-04.

The project strategy has evolved through three phases:

1. **Starter Abomasnow/planner phase** - useful for learning the simulator,
   action contracts, first-player attribution, and packaging failure modes.
2. **Public Lucario sample phase** - a stronger complete deck/policy package;
   `lucario_public_sample_v3` became the first high-performing submitted agent.
3. **Kojimar simple baseline phase** - extracted from a public reference
   notebook, validated locally, submitted, and now active best.

The practical lesson is clear: complete archetype package quality and matchup
coverage mattered more than isolated micro-tuning of an older weak baseline.

## Current active best: Kojimar simple baseline

`kojimar_simple_baseline_v1` is the current anchor for future work.

Why it is active best:

| Evidence | Result |
| --- | ---: |
| Direct gate vs `lucario_public_sample_v3` | `14-6` |
| Confirmation direct gate vs `lucario_public_sample_v3` | `14-6` |
| Exact author-archetype aggregate | `0.7708` |
| Official random gate | `20-0` |
| Public leaderboard score check | `861.4` |

Exact archetype detail:

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | `10-2` | `0.833` |
| Dragapult | `8-4` | `0.667` |
| Iono | `11-1` | `0.917` |
| Lucario | `8-4` | `0.667` |

The biggest strategic improvement over `lucario_public_sample_v3` is broader
matchup coverage, especially the recurring Abomasnow weakness.

## Promotion baseline

New candidates should be compared against `kojimar_simple_baseline_v1`, not the
older planner or Lucario v3 baselines, unless the experiment explicitly studies
regression against those older agents.

A strong future candidate should satisfy all of the following before submission:

- beat `kojimar_simple_baseline_v1` in a direct gate or target a clearly defined
  matchup where Kojimar is weak;
- preserve random-control reliability;
- avoid a severe seat/first-player cell collapse;
- improve or preserve exact author-archetype aggregate;
- package and smoke-test cleanly.

## Candidate design principles learned

### Prefer complete package upgrades over tiny global heuristics

The jump from planner variants to Lucario, then from Lucario v3 to Kojimar,
showed that deck/policy package quality dominated most local micro-tuning.
Tiny global heuristic changes often created unstable cells without improving the
leaderboard.

### Use conditional matchup patches

The Kojimar reference showed that targeted visible-matchup logic is safer than
changing the default behavior everywhere. Example: Crustle-wall logic should
activate only when Dwebble/Crustle is visible.

### Treat score drift carefully

Both `lucario_public_sample_v3` and `kojimar_simple_baseline_v1` initially had
low public snapshots around `600.0`, then drifted much higher after additional
matches. Do not overreact to the first completed score; track later refreshes
and compare to local evidence.

### Keep weak-cell diagnostics

Seat/first-player cells exposed why v4 was risky even when aggregate results
looked promising. Every direct gate should keep the four-cell breakdown:

- candidate seat 0, player zero not first;
- candidate seat 0, player zero first;
- candidate seat 1, player zero not first;
- candidate seat 1, player zero first.

## Near-term roadmap

1. Track `kojimar_simple_baseline_v1` score drift for stability.
2. Build a true Crustle-wall control suite before submitting Crustle-specific
   patches.
3. Search for public/meta reference agents that expose Kojimar weaknesses.
4. Promote only candidates that beat Kojimar or improve a validated weak matchup
   without aggregate collapse.
5. Keep documentation append-only: record rejected candidates because they
   explain why future ideas are constrained.

## Historical notes

Older Abomasnow/planner strategy and starter-deck analysis are retained in the
experiment reports for reproducibility. They are no longer the strategic anchor.
Use them as lessons about simulator mechanics, not as the baseline to beat.
