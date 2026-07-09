# V23/V24 Phantump Control Candidate Results

Date: 2026-07-09

## Purpose

Continue from the replay-delta finding in
`75_v8_dragapult_phantump_replay_delta.md`: Phantump/Trevenant control is a
real public-meta pain point, but v10's broad pressure patch regressed active
best badly. This pass tested two narrower v1-based variants.

## Candidates

### `kojimar_simple_baseline_v23_phantump_ko_boss_guard`

Hypothesis: avoid wasting `Boss's Orders` against Phantump/Trevenant control
when the planned bench target is not a knockout.

Implementation:

- copied `kojimar_simple_baseline_v1`;
- added a Phantump/Trevenant board detector;
- suppressed `Boss's Orders` only when:
  - opponent shows Hop's Phantump or Hop's Trevenant;
  - planned target is on the bench;
  - planned attack leaves the target alive.

### `kojimar_simple_baseline_v24_phantump_ko_target_bonus`

Hypothesis: preserve v1 globally, but add a small target-score bonus only after
the planner already sees a KO against Phantump/Trevenant control.

Implementation:

- copied `kojimar_simple_baseline_v1`;
- added Phantump/Trevenant board detection;
- added KO-only bonuses for:
  - Hop's Phantump;
  - Hop's Trevenant;
  - Hop's Cramorant;
  - Hop's Snorlax.

This is intentionally narrower than rejected v10, which boosted target values
more broadly.

## Commands

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v23_phantump_ko_boss_guard --direct-games-per-cell 2 --max-decisions 5000 --seed 20260709

$env:POKEMON_TCG_RUNTIME_ROOT = (Join-Path (Resolve-Path 'scratch').Path 'delta_runtime_v23_vs_v1_phantump')
python scripts/compare_midgame_decision_deltas.py --candidate kojimar_simple_baseline_v23_phantump_ko_boss_guard --reference kojimar_simple_baseline_v1 --submission-id 54391951 --loss-diagnostics scratch\loss_diagnostics\54391951_dragapult-phantump_trevenant_control_losses.json --archetypes phantump_trevenant_control --start-turn 1 --end-turn 9 --max-states 120

python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v24_phantump_ko_target_bonus --direct-games-per-cell 2 --max-decisions 5000 --seed 20260709
```

## Compact public-meta gate results

### V23

| Control | Candidate score | Same-seed v1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 active best | 0.625 | 0.375 | +0.250 |
| v8 public Boss guard | 0.625 | 0.750 | -0.125 |
| v5 metal pressure | 0.750 | 0.375 | +0.375 |
| Lucario public v3 | 0.875 | 0.500 | +0.375 |
| Library-out | 0.375 | 0.500 | -0.125 |
| Official random | 1.000 | 1.000 | +0.000 |

Gate recommendation: `hold`

Decision flags:

- `under_reference_on_kojimar_simple_baseline_v8_public_boss_guard`
- `under_reference_on_koushikrudra_libraryout_v1`

Decision-delta check on v8 Phantump/Trevenant public losses:

| States | Changed decisions | Changed rate |
| ---: | ---: | ---: |
| 107 | 0 | 0.0000 |

Interpretation: v23 is too narrow to affect the known Phantump/Trevenant loss
states. Its compact-gate movement is not enough evidence for a submission.

### V24

| Control | Candidate score | Same-seed v1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 active best | 0.375 | 0.500 | -0.125 |
| v8 public Boss guard | 0.625 | 0.625 | +0.000 |
| v5 metal pressure | 0.125 | 0.250 | -0.125 |
| Lucario public v3 | 0.500 | 0.500 | +0.000 |
| Library-out | 0.625 | 0.500 | +0.125 |
| Official random | 1.000 | 0.750 | +0.250 |

Gate recommendation: `hold`

Decision flags:

- `fails_active_best_direct_gate`
- `under_reference_on_kojimar_simple_baseline_v1`
- `under_reference_on_kojimar_simple_baseline_v5_metal_pressure`

Interpretation: KO-only target bonuses still create unacceptable active-best
and metal-pressure regression. This is not a submit candidate.

## Decision

Do not submit v23 or v24.

The Phantump/Trevenant issue is still real, but simple tactical target/Boss
edits are not producing a robust candidate. The next improvement path should
move away from hand-tuned Phantump scoring and toward a replay-state diagnostic
that finds exact missed lethal / missed survival choices before writing more
policy code.

## Next strategy

Build a diagnostic, not another immediate candidate:

1. For Phantump/Trevenant public losses, enumerate turns where:
   - a KO was available but the chosen action did not take it;
   - `Boss's Orders` was available and could convert a KO;
   - switching or retreating could preserve a high-value attacker;
   - support draw was skipped while the hand was energy-heavy or dead.
2. Compare those opportunities against v1's actual selected action.
3. Only build v25 if the diagnostic finds a repeated, concrete missed action
   pattern.
