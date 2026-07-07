# V16 Meta Target Guard Results

Date: 2026-07-07

## Purpose

Create a conservative challenger from the score-leading `kojimar_simple_baseline_v1` rather than from the lower-scoring v8/v15 branches. The public episode meta showed repeated weaknesses into:

- Metal / Cinderace / Archaludon pressure
- Alakazam / Dunsparce setup
- Phantump / Trevenant control

V16 therefore adds only local target-priority bonuses for those families. It intentionally avoids the broad v8 Boss's Orders guard and the v15 Lucario-tempo reshaping because those earlier changes risked damaging Dragapult/Lucario behavior.

## Candidate

`candidates/kojimar_simple_baseline_v16_meta_target_guard`

Changes versus v1:

- Added opponent family detection for Metal/Cinderace, Alakazam/Dunsparce, and Phantump/Trevenant.
- Added `_meta_target_bonus(...)` inside attack planning.
- Bonuses prefer KO-able setup pieces and important evolved threats.
- Non-KO bench targets receive a small penalty to avoid overusing Boss's Orders for low-immediate-value gusts.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v16_meta_target_guard --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V16 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.5000 | 0.0000 |
| v8 public boss guard | 0.5625 | 0.5000 | +0.0625 |
| v5 metal pressure | 0.5000 | 0.5000 | 0.0000 |
| lucario public sample v3 | 0.5000 | 0.5625 | -0.0625 |
| koushikrudra library-out | 0.5000 | 0.5000 | 0.0000 |
| official random | 0.8125 | 0.7500 | +0.0625 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v16 yet. The direct gate has many `max_decisions` rows, so the small positive and negative deltas are noisy. However, the result is not strong enough to justify replacing v1, whose public leaderboard score remains our best known score.

The target-only direction is still useful because it is much safer than broad energy/setup rewrites. The next candidate should keep this narrow style but needs stronger evidence from replay-derived exact decision comparisons before submission.

## Next step

1. Use public loss replay diagnostics to find exact states where v1 loses tempo against Metal/Cinderace and Alakazam/Dunsparce.
2. Prefer a micro-patch only when the same mistake appears repeatedly.
3. Preserve v1 behavior against Lucario, Dragapult, and Crustle/library-out unless a replay proves a specific local decision is wrong.
4. Submit only after the public-meta gate does not flag a Lucario/Dragapult/library-out regression.
