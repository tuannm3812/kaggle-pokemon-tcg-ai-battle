# Current meta and v9 strict Boss guard

## Score snapshot

Checked on 2026-07-06:

| Submission | Candidate | Public score |
| ---: | --- | ---: |
| `54303967` | `kojimar_simple_baseline_v1` | `864.5` |
| `54391951` | `kojimar_simple_baseline_v8_public_boss_guard` | `767.8` |
| `54348833` | `kojimar_simple_baseline_v5_metal_pressure` | `728.8` |
| `54283898` | `lucario_public_sample_v3` | `711.2` |

v1 remains the active best.

## Refined public meta read

The classifier now separates several decks that were previously hidden in the
`other` bucket:

- Dragapult: `119/120/121`;
- Marnie Grimmsnarl: `646/647/648`;
- Hop Phantump/Trevenant: `878/879`;
- Rocket Honchkrow/Porygon: `463/891/473/474/475`.

### v1 public episodes

| Archetype | Result | Score |
| --- | ---: | ---: |
| Metal/Cinderace | 13-21 | 0.382 |
| Alakazam/Dunsparce | 5-9 | 0.357 |
| Phantump/Trevenant control | 1-3 | 0.250 |
| Dragapult | 7-3 | 0.700 |
| Grimmsnarl | 11-3 | 0.786 |
| Lucario | 23-15 | 0.605 |
| Crustle/library-out | 3-2 | 0.600 |

### v8 public episodes

| Archetype | Result | Score |
| --- | ---: | ---: |
| Dragapult | 0-4 | 0.000 |
| Phantump/Trevenant control | 0-2 | 0.000 |
| Alakazam/Dunsparce | 2-4 | 0.333 |
| Grimmsnarl | 1-2 | 0.333 |
| Metal/Cinderace | 3-1 | 0.750 |
| Lucario | 11-4 | 0.733 |
| Crustle/library-out | 7-1 | 0.875 |

Interpretation: v8's Boss guard helped some visible public weak families, but
it appears to harm or fail against Dragapult and Phantump/Trevenant-style decks.

## Candidate: `kojimar_simple_baseline_v9_strict_boss_guard`

Rationale:

- v8 likely triggered too broadly because Dunsparce/Dudunsparce appears in many
  non-Alakazam decks.
- v9 therefore guards speculative Boss's Orders only when true Metal/Cinderace
  or true Alakazam-line cards are visible:
  - Duraludon / Archaludon ex / Cinderace;
  - Abra / Kadabra / Alakazam.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 4-8 | 0.333 |
| vs `kojimar_simple_baseline_v8_public_boss_guard` | 5-7 | 0.417 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 8-4 | 0.667 |
| vs `lucario_public_sample_v3` | 7-5 | 0.583 |
| vs `koushikrudra_libraryout_v1` | 6-6 | 0.500 |

Decision: reject. v9 improves some side gates but fails the active-best
head-to-head, so it is not a submission candidate.

## Strategy implication

The leaderboard meta is now multi-polar:

1. v1 is weak into Metal/Cinderace and Alakazam/Dunsparce;
2. v8 helped Metal/Cinderace, Lucario, and Crustle/library-out but collapsed
   into Dragapult and Phantump/Trevenant samples;
3. v9's stricter guard did not preserve the useful v8 signal locally.

The next candidate should not be another Boss guard variant by itself. The next
useful step is a replay-derived public-archetype gate that includes Dragapult,
Phantump/Trevenant, Alakazam, and Metal/Cinderace opponents as separate controls.

