# V18 Midgame Finish Pressure Results

Date: 2026-07-07

## Purpose

Build the next candidate from the strategy EDA brief in
`docs/experiments/63_strategy_eda_for_v18.md`.

The strategy EDA showed that weak public losses against Metal/Cinderace and
Alakazam/Dunsparce were not primarily opening problems. In turns 5-7, the
active-best agent often already had `Mega Lucario ex` active and frequently had
Boss's Orders in hand. Therefore v18 tested a narrow midgame conversion patch.

## Candidate

`candidates/kojimar_simple_baseline_v18_midgame_finish_pressure`

Base:

- `kojimar_simple_baseline_v1`

Changes:

- Added visible-family detection for:
  - Metal/Cinderace/Archaludon
  - Alakazam/Dunsparce
- Added `_midgame_finish_bonus(...)` inside attack planning.
- The bonus activates only during turns 5-7.
- The bonus only helps key targets when they are KO-able or, for the active
  target, near-KO.
- Non-KO bench targets receive a small penalty.

Unchanged:

- setup-active scoring;
- first/second-player choice;
- energy routing;
- generic Boss's Orders timing;
- deck list.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v18_midgame_finish_pressure --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V18 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.6250 | -0.1250 |
| v8 public boss guard | 0.5000 | 0.5000 | 0.0000 |
| v5 metal pressure | 0.5000 | 0.5000 | 0.0000 |
| lucario public sample v3 | 0.5625 | 0.5625 | 0.0000 |
| koushikrudra library-out | 0.5625 | 0.5000 | +0.0625 |
| official random | 0.6250 | 0.7500 | -0.1250 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v18 yet.

The patch is safer than v17 because it does not regress Lucario in this quick
gate and it slightly improved the library-out control. However, it did not
improve the pressure controls that motivated the patch, and the quick gate
flagged under-reference results in the mirror and official-random cells.

Because the direct gate has many `max_decisions` rows, the exact deltas are
noisy. Still, the result is not strong enough to risk replacing active-best v1
on the leaderboard.

## Next step

Use v18 as a diagnostic branch, not a submission branch. The next improvement
should inspect exact decision deltas where v18 changes a v1 decision in weak
public-family states. If v18 rarely changes the target/attack decision, the
bonus is too weak or not placed at the right decision point. If it changes
decisions in random/protected matchups, the family detector is too broad.
