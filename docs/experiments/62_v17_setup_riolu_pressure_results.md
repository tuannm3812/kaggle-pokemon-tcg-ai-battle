# V17 Setup Riolu Pressure Results

Date: 2026-07-07

## Purpose

Replay diagnosis for active-best submission `54303967` showed that the largest weak public slice, Metal/Cinderace, was strongly associated with going first and delayed pressure:

- Metal/Cinderace losses: 21 episodes, 19 went first.
- Median first attack turn: 3, but several losses first attacked on turn 5 or 7.
- Many early snapshots showed passive starts with Solrock, Lunatone, or Makuhita active instead of a fast Riolu/Mega Lucario opening.

V17 tested a very narrow hypothesis: if Metal/Cinderace or Alakazam/Dunsparce cards are visible during setup-active selection, prefer Riolu as active to speed up Mega Lucario pressure.

## Candidate

`candidates/kojimar_simple_baseline_v17_setup_riolu_pressure`

Changes versus v1:

- Added opponent-family detection for Metal/Cinderace and Alakazam/Dunsparce.
- Changed only `_score_setup_active(...)` for those visible families:
  - Riolu: high priority
  - Makuhita: secondary
  - Solrock/Lunatone: reduced priority
- No target, Boss's Orders, energy-routing, or attack-plan changes.

## Quick public-meta gate

Command:

```powershell
python scripts/evaluate_public_meta_gate.py --candidate kojimar_simple_baseline_v17_setup_riolu_pressure --reference-candidate kojimar_simple_baseline_v1 --direct-games-per-cell 2 --max-decisions 80 --seed 20260707
```

Result:

| Matchup | V17 score | V1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 mirror | 0.5000 | 0.5000 | 0.0000 |
| v8 public boss guard | 0.5625 | 0.5625 | 0.0000 |
| v5 metal pressure | 0.5000 | 0.5625 | -0.0625 |
| lucario public sample v3 | 0.3750 | 0.5000 | -0.1250 |
| koushikrudra library-out | 0.5000 | 0.5625 | -0.0625 |
| official random | 0.8125 | 0.7500 | +0.0625 |

Gate recommendation: **hold**.

## Interpretation

Reject v17 for submission. The opening hypothesis was plausible from replay diagnosis, but forcing Riolu active in visible pressure matchups introduced broader local-control regressions, especially Lucario public sample v3 and library-out.

This is a useful negative result: the public losses are not solved by a simple setup-active preference. We need a more state-specific decision patch, likely around midgame attack/retreat/Boss timing after the opponent evolves into Archaludon or Alakazam, not at initial setup.

## Next step

Focus on exact repeated midgame states from public losses:

1. Metal/Cinderace: turns 5-7 where Mega Lucario ex has 1-2 energy and Archaludon ex is active with 300-400 HP.
2. Alakazam/Dunsparce: turns 5-7 where Alakazam/Kadabra survives at low HP or Dunsparce/Dudunsparce enables setup.
3. Compare v1 decisions with v8/v5 only in those states, then patch the smallest scoring term that changes a repeated bad choice.
