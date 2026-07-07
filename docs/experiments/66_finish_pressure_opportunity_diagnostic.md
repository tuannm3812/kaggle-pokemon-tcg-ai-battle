# Finish Pressure Opportunity Diagnostic

Date: 2026-07-07

## Purpose

The native replay decision comparators were too slow/unstable in the current
Windows + Drive workspace. To keep moving, we added a no-SDK diagnostic that
checks whether the v18/v19 finish-pressure rules have opportunities in the
public-loss midgame states.

Script:

```powershell
python scripts/analyze_finish_pressure_opportunities.py
```

Input:

`scratch/strategy_eda/54303967_metal_cinderace-alakazam_dunsparce_losses_strategy_eda.json`

Outputs:

- `scratch/strategy_eda/finish_pressure_opportunities.json`
- `scratch/strategy_eda/finish_pressure_opportunities.md`

## Results

| Archetype | Rows | Weak active rows | Near-HP active rows | Mega Lucario + Energy rows | v19-style opportunities | Opportunity rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `alakazam_dunsparce` | 138 | 113 | 113 | 65 | 65 | 0.4710 |
| `metal_cinderace` | 405 | 361 | 125 | 254 | 101 | 0.2494 |

## Interpretation

The opportunity signal is not rare:

- Alakazam/Dunsparce has v19-style opportunities in nearly half of sampled
  turn 5-7 rows.
- Metal/Cinderace has v19-style opportunities in about one quarter of sampled
  turn 5-7 rows.

Therefore v18/v19 likely failed the quick gate for one of these reasons:

1. Attack-target scoring is not the binding decision point.
2. The local v5/v8 pressure controls do not reproduce the exact public-loss
   states where the rule would matter.
3. The finish-pressure bonus changes planning but not enough downstream actions
   to alter outcomes.
4. The actual failure may be supporter sequencing, evolution timing, retreat,
   or attack availability rather than target preference.

## Strategy implication

Do not keep increasing target-score bonuses. The public-loss rows already show
many opportunities, but the gates did not improve.

The next candidate should move away from target score and inspect a different
decision point. The strongest next hypotheses are:

- midgame survival: keep low-HP `Mega Lucario ex` alive long enough to convert
  the active evolved threat;
- attack availability: make sure `Mega Brave` / the intended attack is enabled
  before spending lower-value actions;
- sequencing: prefer actions that immediately enable the active attack line over
  generic draw/development in turns 5-7.

## V20 brief

Build v20 only after choosing one of the above decision points. A reasonable
candidate name would be:

`kojimar_simple_baseline_v20_midgame_attack_enable`

The patch should still start from v1 and avoid setup-active, first-player,
global Boss, or deck-list changes.
