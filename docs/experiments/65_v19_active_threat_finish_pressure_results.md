# V19 Active Threat Finish Pressure Results

Date: 2026-07-07

## Purpose

Follow up on v18 with an even narrower candidate. V18 used midgame target
bonuses but still allowed bench-target effects. V19 tests a safer idea:
active-threat-only finish pressure.

## Candidate

`candidates/kojimar_simple_baseline_v19_active_threat_finish_pressure`

Base:

- `kojimar_simple_baseline_v1`

Changes:

- Added visible-family detection for:
  - Metal/Cinderace/Archaludon
  - Alakazam/Dunsparce
- Added `_active_threat_finish_bonus(...)` inside attack planning.
- The bonus activates only:
  - on turns 5-9;
  - against weak public families;
  - for the opponent active Pokemon only;
  - when that active target is KO-able or near-finish.

Unchanged:

- setup-active scoring;
- first/second-player choice;
- energy routing;
- generic Boss's Orders timing;
- bench target selection;
- deck list.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v19_active_threat_finish_pressure --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V19 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.5625 | -0.0625 |
| v8 public boss guard | 0.5000 | 0.5000 | 0.0000 |
| v5 metal pressure | 0.5000 | 0.5000 | 0.0000 |
| lucario public sample v3 | 0.5000 | 0.5000 | 0.0000 |
| koushikrudra library-out | 0.5000 | 0.5000 | 0.0000 |
| official random | 0.7500 | 0.8750 | -0.1250 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v19.

The mirror and official-random deltas are likely gate noise because v19's weak
family detector should not activate there. The more important result is that
v19 did not improve v5/v8 pressure controls. This suggests the patch either:

- does not fire in the pressure-control states that matter;
- fires but is too late or too weak;
- is aimed at attack target scoring while the actual failure is another
  decision point, such as supporter use, evolution sequencing, retreat, or
  attack availability.

## Diagnostic blocker

I added `scripts/compare_midgame_decision_deltas.py` to compare candidate versus
reference decisions only on filtered public-loss midgame states. The existing
full replay comparator and the new focused comparator both hit native runtime
loading/time limits in this Windows/Drive workspace. The script is retained
because it is the right diagnostic shape, but it needs runtime-staging cleanup
before it can drive v20.

## Next step

Before building v20, fix or simplify the midgame decision-delta comparator so it
can answer:

1. Does v18/v19 ever choose a different action than v1 in Metal/Cinderace and
   Alakazam/Dunsparce turns 5-9?
2. If yes, which option type changes?
3. If no, the scoring hook is misplaced and the next patch should inspect
   supporter/retreat/evolution sequencing instead of attack target score.
