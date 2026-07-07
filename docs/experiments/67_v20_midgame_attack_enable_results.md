# V20 Midgame Attack Enable Results

Date: 2026-07-07

## Purpose

Test the next hypothesis after v18/v19: target-score bonuses had opportunities
but did not improve pressure gates, so maybe the binding decision point is action
ordering. V20 tries to attack earlier in weak-family midgames when active Mega
Lucario already has a planned attack line.

## Candidate

`candidates/kojimar_simple_baseline_v20_midgame_attack_enable`

Base:

- `kojimar_simple_baseline_v1`

Changes:

- Added visible-family detection for:
  - Metal/Cinderace/Archaludon
  - Alakazam/Dunsparce
- Added `_should_prioritize_midgame_attack()`.
- During turns 5-9, if:
  - active Pokemon is `Mega Lucario ex`;
  - opponent active is a weak-family key threat;
  - the current attack plan uses active Mega Lucario;
  - active Mega Lucario has at least one energy;
  then the selected attack receives very high priority.

Unchanged:

- setup-active scoring;
- first/second-player choice;
- energy routing;
- deck list;
- target-score bonuses.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v20_midgame_attack_enable --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V20 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.4375 | 0.5000 | -0.0625 |
| v8 public boss guard | 0.5000 | 0.5625 | -0.0625 |
| v5 metal pressure | 0.5000 | 0.5000 | 0.0000 |
| lucario public sample v3 | 0.5000 | 0.5000 | 0.0000 |
| koushikrudra library-out | 0.5625 | 0.5000 | +0.0625 |
| official random | 0.8750 | 0.6875 | +0.1875 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v20.

V20 improved random and library-out in this quick gate, but it regressed the
active-best direct gate and v8 pressure-control reference. It also did not
improve the v5 metal-pressure control. The idea is therefore not strong enough
for leaderboard risk.

The result is useful because it tests a different decision point from v18/v19:
action ordering rather than target score. Since it still fails to move the
pressure controls, the next branch should not simply raise attack priority more.

## Next step

The remaining likely bottleneck is not a single attack-priority score. Inspect:

1. Whether local pressure controls are too weak/noisy to validate public-loss
   states.
2. Whether the public losses are caused by survival/resource sequencing before
   turn 5, not the turn 5-9 attack action.
3. Whether a deck-level or opponent-specific branch is needed instead of more
   local policy scoring.

For now, active-best remains `kojimar_simple_baseline_v1`.
