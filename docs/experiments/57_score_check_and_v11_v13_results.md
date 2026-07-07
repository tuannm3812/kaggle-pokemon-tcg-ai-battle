# Current score check and v11-v13 candidate results

## Score snapshot

Checked on 2026-07-07 with the Kaggle API:

| Submission | Candidate | Public score | Status |
| ---: | --- | ---: | --- |
| `54303967` | `kojimar_simple_baseline_v1` | 864.5 | active best |
| `54391951` | `kojimar_simple_baseline_v8_public_boss_guard` | 786.0 | rejected / watch only |
| `54348833` | `kojimar_simple_baseline_v5_metal_pressure` | 722.0 | rejected |
| `54283898` | `lucario_public_sample_v3` | 711.2 | superseded |

v1 remains the best leaderboard candidate. v8 recovered from its initial low
score but remains meaningfully below v1.

## Refreshed episode insight

Kaggle now lists 61 public episodes for v8. After refreshing available replays,
the v8 public episode analysis is:

| Archetype | Result | Score | Read |
| --- | ---: | ---: | --- |
| Dragapult | 0-4 | 0.000 | critical weakness |
| Phantump/Trevenant control | 0-4 | 0.000 | critical weakness |
| Alakazam/Dunsparce | 3-4 | 0.429 | still weak |
| Grimmsnarl | 3-3 | 0.500 | neutral |
| Metal/Cinderace | 6-4 | 0.600 | improved but not dominant |
| Lucario | 11-4 | 0.733 | strong |
| Other | 5-1 | 0.833 | strong |
| Crustle/library-out | 8-1 | 0.889 | strong |

The meta lesson is not “submit more v8.” v8 has useful upside into
library-out/Lucario/Metal, but its Dragapult and Phantump/Trevenant collapses
are too expensive.

## Evaluator fix

During this round we found a local-evaluation issue: imported candidate modules
keep globals such as `pre_turn`, `ability_used`, and `plan` across batched local
games. Kaggle episodes are effectively fresh runs, so the local evaluator should
reset these globals before each game.

`scripts/evaluate_author_opponent_suite.py` now resets common policy globals at
the start of every `run_game` call. This makes future gates less sensitive to
cross-game residue.

## Candidate results

### v11: `kojimar_simple_baseline_v11_metal_boss_guard`

Hypothesis: keep v1 behavior, but block speculative Boss's Orders only against
visible Metal/Cinderace boards.

Delta-aware public-meta gate result:

- held by active-best, Lucario, and library-out reference regressions;
- not a submission candidate.

### v12: `kojimar_simple_baseline_v12_dragapult_pressure`

Hypothesis: start from v1 and raise target priority on Dreepy, Drakloak,
Dragapult ex, and Budew when the opponent shows the Dragapult line.

After evaluator reset:

| Control | Candidate score | Delta vs v1 reference |
| --- | ---: | ---: |
| v1 | 0.625 | 0.000 |
| v8 | 0.500 | 0.000 |
| v5 | 0.250 | -0.375 |
| Lucario v3 | 0.500 | -0.125 |
| Koushikrudra library-out | 0.500 | +0.250 |
| official random | 1.000 | 0.000 |

Author-policy suite showed a target-matchup benefit, but not enough overall:

| Author policy | v12 | v1 |
| --- | ---: | ---: |
| Abomasnow | 0.750 | 0.833 |
| Lucario | 0.833 | 0.917 |
| Dragapult | 1.000 | 0.917 |
| Iono | 0.917 | 1.000 |

Decision: reject v12.

### v13: `kojimar_simple_baseline_v13_v8_dragapult_pressure`

Hypothesis: preserve v8's public upside and add Dragapult pressure.

Delta-aware public-meta gate result:

| Control | Candidate score | Delta vs v1 reference |
| --- | ---: | ---: |
| v1 | 0.625 | -0.063 |
| v8 | 0.375 | -0.125 |
| v5 | 0.500 | 0.000 |
| Lucario v3 | 0.375 | -0.188 |
| Koushikrudra library-out | 0.500 | 0.000 |
| official random | 1.000 | 0.000 |

Author-policy suite:

| Author policy | v13 | v8 | v1 |
| --- | ---: | ---: | ---: |
| Abomasnow | 0.750 | 0.583 | 0.750 |
| Lucario | 0.750 | 0.750 | 1.000 |
| Dragapult | 1.000 | 0.917 | 1.000 |
| Iono | 0.917 | 0.833 | 1.000 |

Decision: reject v13 as a submission candidate. It improves v8 in some author
policy cells, but it still does not beat v1 broadly enough.

## Next strategy

Do not submit v11, v12, or v13.

The next strong candidate likely needs a structural change rather than another
small static target-score patch. Recommended directions:

1. build a replay-specific Dragapult/Phantump diagnosis notebook or script that
   traces the losing public episodes turn-by-turn;
2. identify whether losses come from setup choice, energy attachment, Boss
   timing, retreat/switch timing, or prize-target selection;
3. only then create a candidate that changes one of those mechanisms with a
   clear local replay rationale.