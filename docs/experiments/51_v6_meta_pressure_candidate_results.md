# v6 meta-pressure candidate results

## Goal

Use refreshed `kojimar_simple_baseline_v1` public episode insights to build a
new candidate that can improve the leaderboard score.

The refreshed v1 public episodes showed two repeat weaknesses:

- Metal/Cinderace: `13-20`, episode score `0.394`;
- Alakazam/Dunsparce: `5-9`, episode score `0.357`.

## Candidates tested

### `kojimar_simple_baseline_v6_meta_pressure`

Change:

- keep conditional Metal/Cinderace pressure from v5 but reduce Relicanth;
- add Alakazam/Dunsparce pressure:
  - Abra/Kadabra as early tempo targets;
  - Alakazam as stabilized threat;
  - Dunsparce/Dudunsparce as support targets.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 5-7 | 0.417 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 5-7 | 0.417 |
| vs `lucario_public_sample_v3` | 8-4 | 0.667 |
| vs `koushikrudra_libraryout_v1` | 6-6 | 0.500 |

Decision: reject. Combining both public-episode patches hurt the active-best
gate.

### `kojimar_simple_baseline_v6_metal_conditional`

Change:

- narrower Metal/Cinderace-only pressure;
- lower Relicanth bonus than v5.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 4-8 | 0.333 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 7-5 | 0.583 |
| vs `lucario_public_sample_v3` | 6-6 | 0.500 |
| vs `koushikrudra_libraryout_v1` | 8-4 | 0.667 |

Decision: reject. It improved over v5 locally but failed against active v1.

### `kojimar_simple_baseline_v6_alakazam_pressure`

Change:

- Alakazam/Dunsparce-only pressure;
- no Metal/Cinderace changes.

Compact gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 5-7 | 0.417 |
| vs `kojimar_simple_baseline_v5_metal_pressure` | 5-7 | 0.417 |
| vs `lucario_public_sample_v3` | 9-3 | 0.750 |
| vs `koushikrudra_libraryout_v1` | 3-9 | 0.250 |

Decision: reject. It did not beat v1 and made the control/library-out gate
worse.

## Conclusion

No v6 candidate is submit-worthy.

The episode insights are still useful, but static target-score pressure is too
brittle. The next strong candidate should not be another simple target boost.
Recommended next directions:

1. build a replay-derived public-archetype gate from downloaded deck signatures;
2. test Boss's Orders timing separately from target scoring;
3. add decision telemetry to confirm whether losses come from wrong targets,
   slow attacker setup, or draw/deck-out pressure;
4. only submit when a candidate beats v1 locally and targets one public episode
   weakness without harming library-out/control.

