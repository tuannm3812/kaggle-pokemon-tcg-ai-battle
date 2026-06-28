# Hybrid Card-Selection Candidate Results

## Scope

This experiment followed the first author-opponent suite. The goal was to test
whether we could combine useful pieces from planner v2 and tactical KO v1
without accepting their broad regressions.

Two policy-only candidates were created with the promoted deck unchanged:

- `candidates/hybrid_card_ko_v1/`
- `candidates/card_selection_v1/`

Production remains unchanged.

## Candidate designs

### `hybrid_card_ko_v1`

This candidate kept the promoted development-first main action priority and
added:

1. high-confidence immediate knockout attack selection;
2. planner-style scoring for non-main `CARD` selections.

### `card_selection_v1`

This was the ablation after the hybrid smoke test showed an Iono-style
regression. It removed the immediate-knockout override and kept only
planner-style scoring for non-main `CARD` selections:

- setup active;
- switch/to-active;
- search/to-hand/to-bench;
- discard;
- attach-from prompts.

## Author-suite gate

Command:

```powershell
python scripts\evaluate_author_opponent_suite.py --games-per-cell 3 --max-decisions 2500
```

Each candidate played 12 games against each sanitized author policy.

| Candidate | Aggregate | Abomasnow | Lucario | Dragapult | Iono | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| promoted | 28/48 = 0.583 | 5-7 | 7-5 | 11-1 | 5-7 | Keep |
| hybrid card + KO v1 | 25/48 = 0.521 | 4-8 | 6-6 | 8-4 | 7-5 | Reject |
| card selection v1 | 24/48 = 0.500 | 5-7 | 4-8 | 6-6 | 9-3 | Reject |

All games completed without runtime failures.

## Interpretation

The card-selection heuristic is not globally safe.

It clearly improved the Iono-style policy matchup, but that came with a larger
cost against Lucario and Dragapult-style policies. The hybrid version softened
the Iono regression but still underperformed the promoted baseline overall.

This is another warning against blind heuristic stacking. We now have enough
evidence that policy changes need replay-level attribution before being merged
into a new submission candidate.

## Next recommendation

Do not submit either candidate.

The next step should be a replay telemetry pass over author-suite losses:

1. capture compact decision logs for promoted losses against author Abomasnow
   and author Iono;
2. compare the same seeds against `card_selection_v1`;
3. identify which exact selection contexts helped Iono and which harmed Lucario;
4. test a narrower candidate that only changes the beneficial context.

The most likely useful direction is not "all non-main CARD scoring"; it is a
single-context correction, probably setup active, search target, or discard
choice, validated one context at a time.
