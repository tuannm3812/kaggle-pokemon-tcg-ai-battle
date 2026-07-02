# Lucario Abomasnow trace and v2 rejection

Date: 2026-07-03

## Live score check

Checked with:

```bash
python -m kaggle competitions submissions pokemon-tcg-ai-battle
```

| Submission ref | Message | Status | Public score |
| --- | --- | --- | ---: |
| `54213861` | `lucario public sample v1` | `SubmissionStatus.COMPLETE` | `658.5` |
| `54126975` | `planner main only v1` | `SubmissionStatus.COMPLETE` | `556.4` |
| `54100265` | `fix deck loader missing __file__` | `SubmissionStatus.COMPLETE` | `496.7` |

The active Lucario submission remains materially stronger than the previous
planner submission, though the public score has drifted from `661.3` to `658.5`.

## Trace target

The known local weakness for `lucario_public_sample_v1` was exact Abomasnow:

| Candidate | Opponent archetype | Prior score rate |
| --- | --- | ---: |
| `lucario_public_sample_v1` | author Abomasnow own deck | `0.417` |

We traced eight local games:

```text
scratch/lucario_public_v1_abomasnow_trace.json
```

Trace summary:

- result: 4 wins, 4 losses in this trace sample;
- losses often involved routing energy/search through Makuhita, Hariyama, or
  Lunatone instead of stabilizing the Riolu -> Mega Lucario line;
- `ATTACH_FROM` chose Makuhita (`673`) heavily;
- `TO_ACTIVE` choices in losses included Makuhita (`673`) and Mega Lucario ex
  (`678`), suggesting the issue is not simply "always choose Mega Lucario";
- Abomasnow remains a high-variance matchup, so direct tweaks need local gates.

## v2 tweak

Created `lucario_public_sample_v2` as a conservative local tweak:

- prioritize Riolu as setup active;
- demote Lunatone and secondary Makuhita/Hariyama setup;
- increase search value for Riolu and Mega Lucario ex;
- bias attachment scoring toward Riolu/Mega Lucario.

## Result

Focused Abomasnow gate:

```bash
python scripts/evaluate_author_archetype_deck_suite.py \
  --candidates lucario_public_sample_v1 lucario_public_sample_v2 \
  --archetypes abomasnow \
  --games-per-cell 3 \
  --max-decisions 5000
```

| Candidate | Result vs Abomasnow | Score rate | Failures |
| --- | ---: | ---: | ---: |
| `lucario_public_sample_v1` | 9-3 | 0.750 | 0 |
| `lucario_public_sample_v2` | 4-8 | 0.333 | 0 |

## Decision

Reject `lucario_public_sample_v2`.

The simple Riolu-focus tweak made the targeted Abomasnow matchup worse in the
local gate. Do not submit it.

## Insight

The Abomasnow matchup is not fixed by blindly suppressing the secondary
attacker package. The public Lucario policy appears to need its secondary lines
for some Abomasnow games. The next useful improvement should be trace-guided and
conditional, not a global demotion of Makuhita/Hariyama/Lunatone.

Recommended next step:

1. keep `lucario_public_sample_v1` as the active submitted candidate;
2. do not submit v2;
3. if continuing Lucario improvements, trace Abomasnow wins versus losses at the
   turn/board level and target a narrow condition rather than broad setup
   priorities.

## Iono v2 cleanup

An untracked `candidates/iono_adapted_v2` folder was found from an earlier
unfinished experiment. A compact exact-archetype screen rejected it:

| Opponent archetype | Result | Score rate |
| --- | ---: | ---: |
| Abomasnow | 0-4 | 0.000 |
| Dragapult | 0-4 | 0.000 |
| Iono | 1-3 | 0.250 |
| Lucario | 0-4 | 0.000 |

Decision: remove the untracked folder and do not continue Iono adapted v2.
