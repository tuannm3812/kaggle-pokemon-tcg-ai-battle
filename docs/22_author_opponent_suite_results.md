# Author Opponent Suite Results

## Scope

This step built a stronger local evaluation harness after the accepted
submission scored `537.5` and small heuristic candidates failed their promotion
gates.

The new script is:

- `scripts/evaluate_author_opponent_suite.py`

It loads extracted competition-author reference notebooks from
`scratch/author_references`, cuts off notebook packaging cells before
`import tarfile`, and evaluates our local policies against the sanitized author
`agent()` functions.

## Important limitation

This first suite runs every policy on our promoted `agent/deck.csv`.

That means it is an action-selection pressure test, not a full recreation of
the authors' exact deck submissions. This is intentional for v1 of the suite:
deck composition stays constant, so differences mostly come from policy logic.

## Run

Command:

```powershell
python scripts\evaluate_author_opponent_suite.py --games-per-cell 3 --max-decisions 2500
```

Design:

- 3 games in each candidate-seat by first-player cell;
- 12 games per matchup;
- promoted baseline, planner v2, and tactical KO v1 as candidates;
- four sanitized author policies as opponents;
- all candidates and opponents use the promoted 60-card deck;
- results saved to `scratch/author_opponent_suite_results.json`.

## Summary

| Candidate | Opponent policy | W-L | Score rate | Failures |
| --- | --- | ---: | ---: | ---: |
| promoted | author Abomasnow | 4-8 | 0.333 | 0 |
| promoted | author Lucario | 5-7 | 0.417 | 0 |
| promoted | author Dragapult | 6-6 | 0.500 | 0 |
| promoted | author Iono | 7-5 | 0.583 | 0 |
| planner v2 | author Abomasnow | 6-6 | 0.500 | 0 |
| planner v2 | author Lucario | 3-9 | 0.250 | 0 |
| planner v2 | author Dragapult | 12-0 | 1.000 | 0 |
| planner v2 | author Iono | 7-5 | 0.583 | 0 |
| tactical KO v1 | author Abomasnow | 6-6 | 0.500 | 0 |
| tactical KO v1 | author Lucario | 7-5 | 0.583 | 0 |
| tactical KO v1 | author Dragapult | 12-0 | 1.000 | 0 |
| tactical KO v1 | author Iono | 3-9 | 0.250 | 0 |

## Interpretation

The suite is now operational and catches meaningful opponent differences.

The promoted baseline is weakest against the author Abomasnow and Lucario-style
policies. Planner v2 improves the Abomasnow-policy matchup but collapses against
Lucario-style pressure. Tactical KO v1 improves Lucario-style results but
collapses against Iono-style policy. That explains why small one-off heuristics
are risky: they can improve one local pressure point while damaging another.

The Dragapult author policy is currently not a useful pressure opponent when
forced onto our Abomasnow deck. It may rely on deck-specific card IDs and
therefore becomes weak under this constant-deck setup.

## Next strategy

Do not submit a new candidate yet.

The next improvement should target a policy primitive shared by the stronger
author references rather than a narrow tactical override:

1. extract action telemetry from losses against author Abomasnow and author
   Lucario policies;
2. compare promoted vs planner v2 vs tactical KO v1 decisions in the same
   controlled cells;
3. design one candidate that combines the safer parts:
   - planner v2's improved Abomasnow-pressure behavior;
   - tactical KO v1's improved Lucario-pressure behavior;
   - without tactical KO v1's Iono regression;
4. rerun the author suite and only promote if it improves aggregate score while
   avoiding a severe loss in any author-policy matchup.

This creates a better local gate for leaderboard score improvement than
random-only or self-play evaluation.
