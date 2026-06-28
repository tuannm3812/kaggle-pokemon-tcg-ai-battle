# Loss Taxonomy Results

## Scope

The private Kaggle notebook
[pokemon-tcg-loss-taxonomy-and-pressure-opponent](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-loss-taxonomy-and-pressure-opponent)
version 1 ran a diagnostic tournament on 2026-06-26.

This notebook is not a promotion gate. It compares frozen policies and labels
losses so the next implementation change can target the most repeated failure
mode.

## Matchups

| Candidate | Opponent | Games | W-L | Score rate | Bootstrap 95% interval |
| --- | --- | ---: | ---: | ---: | --- |
| planner v2 | pressure | 20 | 20-0 | 1.000 | [1.000, 1.000] |
| planner v2 | random | 20 | 17-3 | 0.850 | [0.650, 1.000] |
| promoted | pressure | 20 | 18-2 | 0.900 | [0.750, 1.000] |
| promoted | random | 20 | 16-4 | 0.800 | [0.600, 0.950] |

The pressure policy did not become a stronger benchmark in this run. It is
still useful as a tempo stress control because it prioritizes legal attacks
earlier than the promoted development-first policy, but it should not replace
the need for a stronger author-style opponent.

## Loss taxonomy

| Matchup | Label | Losses |
| --- | --- | ---: |
| planner v2 vs random | attack_timing | 1 |
| planner v2 vs random | opponent_pressure | 1 |
| planner v2 vs random | switch | 1 |
| promoted vs pressure | switch | 2 |
| promoted vs random | opponent_pressure | 2 |
| promoted vs random | switch | 1 |
| promoted vs random | unclear_review_replay | 1 |

The most repeated actionable label is `switch`. Across all promoted-policy
losses, switch-related labels account for three of six losses. Planner v2 also
has one switch-labeled loss and one attack-timing loss.

## Mechanism observations

| Matchup | Main decisions | Ready rate | Attack available | Attack chosen | Retreat available | Retreat chosen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| planner v2 vs pressure | 341 | 0.941 | 0.859 | 0.299 | 0.185 | 0.023 |
| planner v2 vs random | 257 | 0.903 | 0.770 | 0.335 | 0.101 | 0.004 |
| promoted vs pressure | 501 | 0.930 | 0.832 | 0.309 | 0.455 | 0.000 |
| promoted vs random | 185 | 0.870 | 0.686 | 0.249 | 0.070 | 0.000 |

The promoted policy never chose `RETREAT` in this run despite retreat being
available in many main decisions, especially against the pressure control. This
matches the repeated `switch` loss label and is a better next target than
another broad attack-planning rule.

## Replay evidence

The Kaggle run exported eight bounded loss replays:

- `promoted_vs_random_game_100008_seat_0_first_0.json`
- `promoted_vs_random_game_100010_seat_1_first_0.json`
- `promoted_vs_random_game_100018_seat_1_first_1.json`
- `promoted_vs_pressure_game_100030_seat_1_first_0.json`
- `promoted_vs_pressure_game_100037_seat_1_first_1.json`
- `planner_v2_vs_random_game_100043_seat_0_first_1.json`
- `planner_v2_vs_random_game_100046_seat_0_first_0.json`
- `planner_v2_vs_random_game_100050_seat_1_first_0.json`

These files are diagnostic artifacts downloaded under `scratch/` and should not
be committed.

## Decision

Do not submit a new agent yet. The next focused implementation experiment
should be a conservative switch/retreat rule:

1. if a benched attacker is ready and the active Pokémon is not ready, prefer a
   legal retreat or switch-like action;
2. preserve current development-first sequencing when no ready benched attacker
   exists;
3. evaluate against promoted, planner v2, random, and the pressure control with
   the same controlled seat/turn-order cells.

Selective Search API work remains deferred. The current evidence points first
to a deterministic switch policy gap, not deep tactical search.
