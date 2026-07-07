# Midgame Decision Delta: V20 vs V1

Date: 2026-07-07

## Purpose

Fix the candidate-vs-reference decision-delta diagnostic and verify whether v20
actually changes active-best v1 decisions in public-loss midgame states.

## Tooling fix

`scripts/compare_midgame_decision_deltas.py` was updated to:

- use the compact loss-diagnostics file instead of scanning all leaderboard
  replay metadata;
- use raw replay `MAIN` context value `0`;
- evaluate only filtered public-loss turns.

## Command

```powershell
python scripts/compare_midgame_decision_deltas.py --candidate kojimar_simple_baseline_v20_midgame_attack_enable --reference kojimar_simple_baseline_v1 --submission-id 54303967 --max-states 50
```

## Result

| Archetype | States | Changed | Changed rate |
| --- | ---: | ---: | ---: |
| `alakazam_dunsparce` | 9 | 7 | 0.7778 |
| `metal_cinderace` | 41 | 10 | 0.2439 |
| **Total** | 50 | 17 | 0.3400 |

## Interpretation

V20 does affect the intended public-loss states. The failure to improve the
quick gate is not because the patch never fires.

The changed examples show that v20 often replaces extra `PLAY`, `EVOLVE`, or
`ATTACH` actions with an immediate `ATTACK`. Some of these look correct, such as
attacking a low-HP active Duraludon or Kadabra. Others are riskier, especially
attacking a full `Archaludon ex` while our active `Mega Lucario ex` is already
low HP. That can sacrifice follow-up sequencing for a non-KO hit.

## V21 brief

Build a narrower v21:

`kojimar_simple_baseline_v21_midgame_ko_attack_enable`

Only prioritize the immediate attack when the current plan's active attack is
an actual KO. Do not prioritize merely near-finish attacks into large evolved
targets.
