# Episode-based score strategy

Date: 2026-06-30

## Live score check

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `495.2` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `478.4` |

The current submitted agent remains valid and slightly ahead of the previous
accepted baseline, but the score is still low and volatile.

## What episode data is available

The Kaggle CLI exposes submission status and public score, but not detailed
ladder episode histories for completed submissions. The actionable episode data
we can inspect locally comes from:

- validation/error replays from failed submissions;
- local paired simulator episodes;
- author-policy episodes;
- reconstructed author-archetype deck episodes.

For strategy, the reconstructed author-archetype deck suite is currently the
most useful because it tests complete deck + policy packages instead of only
policy behavior on our deck.

## Current episode evidence

Latest local archetype-deck suite result from
`scratch/author_archetype_deck_suite_results.json`:

| Candidate | Opponent archetype | Games | Wins | Losses | Score rate |
| --- | --- | ---: | ---: | ---: | ---: |
| promoted | Abomasnow | 8 | 2 | 6 | 0.250 |
| promoted | Dragapult | 8 | 1 | 7 | 0.125 |
| promoted | Iono | 8 | 2 | 6 | 0.250 |
| promoted | Lucario | 8 | 0 | 8 | 0.000 |

Cell-level result for promoted vs Lucario:

| Candidate seat | Player zero first? | Games | Score rate |
| ---: | --- | ---: | ---: |
| 0 | false | 2 | 0.000 |
| 0 | true | 2 | 0.000 |
| 1 | false | 2 | 0.000 |
| 1 | true | 2 | 0.000 |

This is a deck/archetype failure, not a packaging or legality failure.

The policy-only author-opponent suite tells a different story because every
policy uses our deck:

| Candidate | Opponent policy | Games | Score rate |
| --- | --- | ---: | ---: |
| planner_main_only_v1 | author Dragapult policy | 12 | 0.917 |
| planner_main_only_v1 | author Iono policy | 12 | 0.667 |
| planner_main_only_v1 | author Lucario policy | 12 | 0.583 |
| planner_main_only_v1 | author Abomasnow policy | 12 | 0.500 |

Interpretation: planner logic can select legal/useful actions, but our submitted
deck + policy package is not strong against real archetype decks.

## Strategy decision

Do not submit another planner-only candidate.

The next score-improvement work should be a full archetype candidate:

1. Build `candidates/lucario_adapted_v1`.
2. Use the reconstructed Lucario deck as the first deck baseline.
3. Implement a clean repo-owned Lucario policy rather than copying author code.
4. Run the archetype deck suite with at least 3 games per cell:

   ```bash
   python scripts/evaluate_author_archetype_deck_suite.py --candidates lucario_adapted_v1 --games-per-cell 3
   ```

5. If it improves the archetype suite, run the strict promotion gate:

   ```bash
   python scripts/evaluate_promotion_gate.py --candidate lucario_adapted_v1
   ```

6. Submit only if the strict promotion gate returns `PROMOTE`.

## Why Lucario first

Lucario is the clearest episode-based target:

- promoted scored `0/8` against exact Lucario archetype episodes;
- Lucario ranked among the best reconstructed author baselines in the archetype
  ranking pass;
- improving against Lucario should address the most visible matchup hole rather
  than tuning an already-accepted but low-scoring submission.

Secondary path: if Lucario adaptation is slow or unstable, build
`iono_adapted_v1` next because Iono tied Lucario in the small archetype ranking
pass and exposes a different game plan.
