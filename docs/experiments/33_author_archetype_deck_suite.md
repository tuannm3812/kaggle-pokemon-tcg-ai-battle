# Author archetype deck suite

Date: 2026-06-29

## Purpose

Our public leaderboard score is still low, so the next useful question is no longer
"which tiny planner heuristic should we promote?" It is:

> Are we losing mostly because of the policy, the deck, or both?

The existing author-opponent evaluator runs author policies on our submitted
deck. That is useful for isolating action-selection behavior, but it does not
measure real archetype strength. This experiment reconstructs the four public
author sample decks from the locally extracted reference notebooks and runs each
author policy on its own deck.

## New script

`scripts/evaluate_author_archetype_deck_suite.py`

The suite:

- reconstructs exact 60-card decklists from `scratch/author_references/*/extracted_code.py`;
- stages each author policy with its own `deck.csv`;
- evaluates local candidates against author archetype policies;
- optionally evaluates reconstructed author archetypes as candidate baselines;
- writes results to `scratch/author_archetype_deck_suite_results.json`.

## Reconstructed archetypes

The first version covers all four public author sample archetypes:

- Abomasnow/Kyogre
- Mega Lucario ex
- Dragapult ex
- Iono/Bellibolt/Kilowattrel

These are used for local evaluation only. Generated runtime files remain under
`scratch/`.

## First-pass result

Command:

```bash
python scripts/evaluate_author_archetype_deck_suite.py --games-per-cell 3 --max-decisions 5000
```

Summary:

| Candidate | Opponent archetype | Score rate |
|---|---:|---:|
| promoted | Abomasnow | 0.3333 |
| promoted | Dragapult | 0.3333 |
| promoted | Iono | 0.5000 |
| promoted | Lucario | 0.2500 |
| planner_main_only_v1 | Abomasnow | 0.4167 |
| planner_main_only_v1 | Dragapult | 0.0000 |
| planner_main_only_v1 | Iono | 0.0000 |
| planner_main_only_v1 | Lucario | 0.0833 |

Interpretation:

- `planner_main_only_v1` should not be submitted; it collapses against several
  real archetype decks.
- The current promoted agent is only competitive against Iono in this small
  sample and is weak against Lucario, Dragapult, and Abomasnow.
- This points to a deck/archetype bottleneck, not just a final-action selector
  bottleneck.

## Archetype ranking pass

Command:

```bash
python scripts/evaluate_author_archetype_deck_suite.py --candidates promoted --author-candidate-archetypes abomasnow lucario dragapult iono --games-per-cell 2 --max-decisions 5000
```

Aggregate score across the four reconstructed author opponents:

| Candidate baseline | Games | Mean score |
|---|---:|---:|
| author_lucario_policy_own_deck | 32 | 0.4688 |
| author_iono_policy_own_deck | 32 | 0.4688 |
| author_abomasnow_policy_own_deck | 32 | 0.4062 |
| author_dragapult_policy_own_deck | 32 | 0.4062 |
| promoted | 32 | 0.1562 |

Interpretation:

- The public author archetype baselines are materially stronger locally than our
  promoted submission package.
- Lucario and Iono are the best first archetypes to adapt because they rank best
  in the small round-robin and expose different game plans.
- Lucario appears to be the hardest opponent for our current promoted agent.

## Recommended next step

Build a first adapted archetype candidate instead of continuing to tune the
current Abomasnow planner.

Priority order:

1. Create `candidates/lucario_adapted_v1` using the reconstructed Lucario deck
   and a clean, repo-owned policy implementation inspired by observed author
   priorities.
2. Run the author archetype deck suite against `lucario_adapted_v1`.
3. Run the strict promotion gate:

   ```bash
   python scripts/evaluate_promotion_gate.py --candidate lucario_adapted_v1
   ```

4. Promote only if the strict gate returns `PROMOTE`; otherwise keep iterating
   locally.

## Decision

Do not submit another planner-only variant yet. The next score-improvement work
should be a deck/archetype candidate, starting with Lucario or Iono.
