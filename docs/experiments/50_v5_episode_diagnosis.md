# v5 episode diagnosis

## Goal

Diagnose why `kojimar_simple_baseline_v5_metal_pressure` did not improve the
leaderboard score despite being built from a real v1 public-episode weakness.

## Current score snapshot

Checked on 2026-07-06:

| Submission | Candidate | Public score |
| ---: | --- | ---: |
| `54303967` | `kojimar_simple_baseline_v1` | `878.7` |
| `54348833` | `kojimar_simple_baseline_v5_metal_pressure` | `729.9` |
| `54283898` | `lucario_public_sample_v3` | `711.2` |

Decision: v1 remains the active best.

## Episode sample

Downloaded and analyzed public episodes:

| Candidate | Submission | Episodes | Wins | Episode score |
| --- | ---: | ---: | ---: | ---: |
| v1 | `54303967` | 92 | 52 | 0.565 |
| v5 | `54348833` | 68 | 37 | 0.544 |

The episode score gap is much smaller than the public-score gap, which means
v5 is not catastrophically illegal or nonfunctional. It is simply not strong
enough in the current matchmaking pool.

## Archetype comparison

| Opponent family | v1 episode score | v5 episode score | Interpretation |
| --- | ---: | ---: | --- |
| Metal/Cinderace | 0.400 | 0.643 | v5 improved the intended target family |
| Lucario | 0.594 | 0.611 | roughly stable |
| Other | 0.640 | 0.591 | slight decline/noisy sample |
| Alakazam/Dunsparce | 0.429 | 0.286 | still weak, possibly worse |
| Crustle/library-out | 0.750 | 0.200 | major caution, likely matchup/sample issue |
| Iono/Cynthia-style small sample | 1.000 | 0.500 | too small to over-interpret |

## What v5 taught us

The target-only Metal/Cinderace patch transferred in the intended slice:

- v1: `8-12` against Metal/Cinderace public episodes;
- v5: `9-5` against Metal/Cinderace public episodes.

However, improving one visible slice did not improve the overall leaderboard.
The next candidate should not simply add more static target-score boosts.

## Main failure areas after v5

The largest useful warnings:

1. **Alakazam/Dunsparce remains a real weakness.** Fighting damage is resisted
   by the Abra/Kadabra/Alakazam line, and the Dunsparce shell makes the matchup
   awkward.
2. **Crustle/library-out remains dangerous.** Prior local v2/v3 attempts did
   not solve it, and v5 public episodes had poor results in that slice.
3. **Static target boosts can be too brittle.** v5 was intentionally narrow,
   yet public score stayed far below v1. Any v6 should be conditional and
   validated against leaderboard-derived archetype samples.

## Recommended v6 direction

Do not submit another candidate immediately.

Build v6 only after adding a local replay-derived opponent suite or focused
public-archetype gate. The most promising v6 ideas:

1. Keep Metal/Cinderace pressure, but make it conditional on seeing the full
   `Duraludon + Archaludon ex + Cinderace` family.
2. Add early pressure against Abra/Kadabra before Alakazam stabilizes, instead
   of boosting every Psychic target equally.
3. Revisit Boss's Orders timing rather than only changing `target_score`.
4. Treat Crustle/library-out separately; previous target-only and low-deck
   patches were not enough.

