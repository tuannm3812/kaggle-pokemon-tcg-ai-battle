# v15 Lucario-tempo experiment

## Goal

After v14, we confirmed that always choosing second is too blunt. The replay
loss diagnosis still showed real first-player tempo failures into Dragapult and
Phantump/Trevenant, so v15 tested a more controllable lever: once the opponent
reveals Dragapult or Phantump/Trevenant cards, route setup and energy toward the
Lucario line instead of feeding Makuhita/Hariyama.

## Candidate

`kojimar_simple_baseline_v15_lucario_tempo`

Built from `kojimar_simple_baseline_v8_public_boss_guard`.

Changes:

- added visible Dragapult / Phantump-Trevenant detector;
- increased setup-active preference for Riolu in those matchups;
- increased energy attachment score for Riolu and Mega Lucario ex in those
  matchups;
- penalized Makuhita/Hariyama energy routing in those matchups.

## Results

### Delta-aware public-meta gate

| Control | v15 score | Same-seed v1 reference | Delta |
| --- | ---: | ---: | ---: |
| v1 | 0.875 | 0.500 | +0.375 |
| v8 | 0.500 | 0.500 | 0.000 |
| v5 | 0.250 | 0.500 | -0.250 |
| Lucario v3 | 0.250 | 0.625 | -0.375 |
| Koushikrudra library-out | 0.375 | 0.375 | 0.000 |
| official random | 1.000 | 1.000 | 0.000 |

Recommendation: hold.

### Author-policy suite

| Author policy | v15 | v8 | v1 |
| --- | ---: | ---: | ---: |
| Abomasnow | 0.833 | 0.750 | 0.833 |
| Lucario | 0.833 | 0.750 | 0.667 |
| Dragapult | 0.833 | 1.000 | 1.000 |
| Iono | 0.917 | 1.000 | 1.000 |

## Decision

Do not submit v15.

The candidate improved one compact active-best cell, but it failed the promotion
logic because it regressed v5/Lucario controls and did not improve author
Dragapult relative to v8 or v1. The lesson is that broad Lucario-line energy
routing is still too coarse.

## Next strategy

The next useful diagnostic is not another static patch. Extend replay analysis
to compare opening/setup categories across wins and losses:

- first choice and visible first-player state;
- setup active Pokemon;
- first basic hand options;
- whether Riolu, energy, Mega Lucario ex, Hero Cape, or Dusk Ball were available;
- first attack turn and first attacker;
- whether early energy went to Riolu/Lucario, Makuhita/Hariyama, or Solrock.

A future candidate should target the exact opening category that separates wins
from losses, instead of applying one matchup-wide routing rule.