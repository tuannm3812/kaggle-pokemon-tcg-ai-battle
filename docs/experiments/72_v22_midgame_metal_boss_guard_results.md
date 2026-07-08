# V22 Midgame Metal Boss Guard Results

Date: 2026-07-08

## Purpose

Build a candidate from the refreshed public-meta insight:

- v8 improved Metal/Cinderace and library-out slices;
- v8 remains too risky into Dragapult and Phantump/Trevenant;
- v11 already tried a broader metal-only Boss guard and failed.

V22 therefore tests a stricter version of the useful v8 idea: preserve v1
everywhere, and block speculative non-KO Boss's Orders only in midgame
Metal/Cinderace states where the opponent active is already a meaningful metal
threat.

## Candidate

`candidates/kojimar_simple_baseline_v22_midgame_metal_boss_guard`

Base:

- `kojimar_simple_baseline_v1`

Changes:

- Added Metal/Cinderace family IDs.
- Added `_should_guard_midgame_metal_boss()`.
- Blocks Boss's Orders only when all are true:
  - opponent shows Metal/Cinderace family;
  - turn is 5-9;
  - opponent active is `Duraludon`, `Archaludon ex`, or `Cinderace`;
  - current plan wants a bench target;
  - planned bench target is not an immediate KO.

Unchanged:

- Alakazam/Dunsparce behavior;
- Dragapult behavior;
- Phantump/Trevenant behavior;
- Lucario behavior;
- setup, energy routing, attack scoring, and deck list.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v22_midgame_metal_boss_guard --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260708
```

Result:

| Matchup | V22 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.5625 | -0.0625 |
| v8 public boss guard | 0.5000 | 0.5000 | 0.0000 |
| v5 metal pressure | 0.5000 | 0.4375 | +0.0625 |
| lucario public sample v3 | 0.4375 | 0.5000 | -0.0625 |
| koushikrudra library-out | 0.6250 | 0.5000 | +0.1250 |
| official random | 0.6250 | 0.7500 | -0.1250 |

Gate recommendation: **hold**.

## Interpretation

Do not submit v22.

V22 moved in the desired direction for v5 metal pressure and library-out, but it
still failed the promotion standard due to active-best, Lucario, and random
under-reference cells. Some of these deltas may be noisy because the patch
should not activate in non-metal matchups, but the candidate is not strong enough
to risk replacing public-best v1.

## Submit-ready status

No new candidate is submit-ready from the v16-v22 branch.

The only submit-ready/leaderboard-proven agent remains:

`kojimar_simple_baseline_v1`

Public score: `864.5`
