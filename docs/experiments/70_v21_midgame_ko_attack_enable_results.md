# V21 Midgame KO Attack Enable Results

Date: 2026-07-07

## Purpose

V20 confirmed that the attack-enable patch changed public-loss midgame decisions,
but it sometimes attacked into large evolved threats without taking a KO. V21
tests a stricter version: prioritize immediate attack only when the planned
active Mega Lucario attack is an actual KO.

## Candidate

`candidates/kojimar_simple_baseline_v21_midgame_ko_attack_enable`

Base:

- `kojimar_simple_baseline_v1`

Changes:

- Same weak-family detection as v20.
- Activates only during turns 5-9.
- Requires active `Mega Lucario ex`.
- Requires opponent active to be a Metal/Cinderace or Alakazam/Dunsparce key
  threat.
- Requires the current attack plan to use active Mega Lucario against the
  opponent active.
- Requires `plan.remain_hp <= 0`, so the attack should take a KO.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v21_midgame_ko_attack_enable --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V21 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.5000 | 0.0000 |
| v8 public boss guard | 0.5000 | 0.5625 | -0.0625 |
| v5 metal pressure | 0.5000 | 0.5000 | 0.0000 |
| lucario public sample v3 | 0.5000 | 0.5625 | -0.0625 |
| koushikrudra library-out | 0.5000 | 0.5625 | -0.0625 |
| official random | 0.8125 | 0.7500 | +0.0625 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v21.

The stricter KO-only rule reduced the conceptual risk from v20, but the gate
still did not show a pressure-control improvement and flagged protected
matchup under-reference cells. Active-best remains v1.

## Diagnostic note

The fixed decision-delta comparator succeeded for v20 on 50 filtered states, but
the v21 50-state run hit a native/runtime timeout in the current Windows/Drive
workspace. Treat that tool as useful but flaky until runtime staging is made
more robust.

## Next strategy

The v18-v21 branch has tested:

- target-score pressure;
- active-threat finish pressure;
- attack-action priority;
- KO-only attack-action priority.

None produced a submit-worthy gate result. Stop iterating on the same local
policy scoring idea for now. The next high-value step is either:

1. refresh public episode/meta analysis after more leaderboard games, or
2. clean up and commit the experiment trail so the repository has a stable
   research checkpoint.
