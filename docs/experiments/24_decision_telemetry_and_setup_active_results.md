# Decision Telemetry and Setup-Active Results

## Scope

This step followed the rejected broad card-selection candidates. Instead of
stacking more heuristics, we added decision telemetry to identify which narrow
selection context might be useful.

New diagnostic script:

- `scripts/trace_author_decisions.py`

New narrow candidates:

- `candidates/attach_from_v1/`
- `candidates/setup_active_v1/`

Production remains unchanged.

## Telemetry finding

The telemetry compared promoted versus `card_selection_v1` against author
Abomasnow, Lucario, and Iono-style policies.

Useful signal:

- `card_selection_v1` changed many contexts at once;
- the most interpretable differences were in `SETUP_ACTIVE_POKEMON` and
  `ATTACH_FROM`;
- broad non-main `CARD` scoring was too blunt, so we tested each as a narrow
  candidate.

## Narrow candidates

### `attach_from_v1`

Single intended change:

- in `ATTACH_FROM` card prompts, prefer under-energized Mega Abomasnow ex,
  then Snover, then Kyogre.

Result: rejected. It did not beat promoted in the broader author gate.

### `setup_active_v1`

Single intended change:

- in `SETUP_ACTIVE_POKEMON`, prefer Snover when going first;
- prefer Kyogre when not going first;
- otherwise keep the promoted production policy unchanged.

This is intentionally tiny: it changes only the initial active Pokémon choice.

## Author-suite gate

Command:

```powershell
python scripts\evaluate_author_opponent_suite.py --games-per-cell 3 --max-decisions 2500
```

Selected aggregate results:

| Candidate | Aggregate author-suite score | Decision |
| --- | ---: | --- |
| promoted | 27/48 = 0.563 | Baseline |
| attach_from_v1 | 26/48 = 0.542 | Reject |
| setup_active_v1 | 29/48 = 0.604 | Hold |

`setup_active_v1` was the best narrow candidate in this gate:

| Opponent policy | setup_active_v1 W-L | Score rate |
| --- | ---: | ---: |
| author Abomasnow | 7-5 | 0.583 |
| author Lucario | 7-5 | 0.583 |
| author Dragapult | 7-5 | 0.583 |
| author Iono | 8-4 | 0.667 |

All games completed without runtime failures.

## Primary promoted-control gate

Direct controlled test:

| Matchup | Games | W-L | Score rate | Failures |
| --- | ---: | ---: | ---: | ---: |
| setup_active_v1 vs promoted | 40 | 22-18 | 0.550 | 0 |

Controlled cells:

| Candidate seat | Player zero first? | Score |
| ---: | --- | ---: |
| 0 | false | 4/10 |
| 0 | true | 7/10 |
| 1 | false | 6/10 |
| 1 | true | 5/10 |

## Decision

Do not submit yet.

`setup_active_v1` is the first narrow candidate with a plausible author-suite
gain and a positive direct result against promoted, but `22-18` is not strong
enough to spend a Kaggle submission slot. Treat it as a hold candidate.

## Next recommendation

Run a larger direct gate for `setup_active_v1` before any submission:

1. 20 games per controlled seat/first-player cell;
2. promoted baseline, author suite, and official random regression;
3. promote only if the direct promoted-control interval moves clearly above
   parity and no author-policy collapse appears.

If it remains around `0.55`, keep production unchanged and use the same
telemetry workflow to test another single setup/search context.
