# Public loss replay diagnosis and v14 first-choice test

## Goal

Continue from the v8 public episode finding: v8 is strong into library-out,
Lucario, and some Metal/Cinderace samples, but collapses into Dragapult and
Phantump/Trevenant control. Instead of another target-score tweak, this round
looked at replay-level failure mechanics.

## New tool

Added `scripts/diagnose_public_loss_replays.py`.

The script reads cached replay JSONs and `analysis_summary.json`, then writes:

- a JSON diagnostic under `scratch/loss_diagnostics/`;
- a Markdown diagnostic under `scratch/loss_diagnostics/`;
- per-archetype first-attack timing;
- early board snapshots;
- setup choices;
- passive early `MAIN` decisions.

This is not a counterfactual simulator. It is a replay diagnosis tool for
finding candidate hypotheses.

## v8 Dragapult / Phantump diagnosis

Ran:

```bash
python scripts/diagnose_public_loss_replays.py --submission-id 54391951 --archetypes dragapult phantump_trevenant_control --max-turn 6
```

Key output:

| Archetype | Losing episodes | Went first | First attack turns | Read |
| --- | ---: | ---: | --- | --- |
| Dragapult | 4 | 4/4 | 5, 5, 13, 3 | one severe tempo failure, generally slow pressure |
| Phantump/Trevenant | 4 | 4/4 | 3, 3, 7, 3 | usually attacks, but still loses control race |

Representative replay observations:

- Dragapult episode `84372805`: forced Solrock active because opening hand had
  only Solrock as a basic; first attack did not happen until turn 13.
- Dragapult episodes often showed Budew or Latias early while our side spent
  turns assembling Mega Lucario rather than converting first-player tempo into
  prizes.
- Phantump/Trevenant losses often attacked earlier, but into Hop's Snorlax,
  Cramorant, or Trevenant boards where target-score changes alone did not solve
  the control race.

The common public-loss pattern is not simply “wrong target.” The stronger signal
is first-player tempo: all 8 critical v8 losses went first.

## Evaluator cleanup

Patched `scripts/evaluate_unforced_direct_gate.py` to reset candidate/opponent
module globals before each local game, matching the fix already added to the
forced evaluator. This avoids cross-game residue in live-style first-choice
experiments.

## Candidate v14

Candidate: `kojimar_simple_baseline_v14_v8_prefer_second`

Hypothesis: if all critical Dragapult/Phantump v8 losses went first, maybe v8
should choose second in live play.

Implementation:

- copied `kojimar_simple_baseline_v8_public_boss_guard`;
- changed `SelectContext.IS_FIRST` scoring so `NO` is preferred over `YES`;
- registered the candidate in `scripts/evaluate_author_opponent_suite.py`.

Unforced direct gate results, 5 games per seat:

| Control | Result | Score | Decision |
| --- | ---: | ---: | --- |
| v1 | 4-6 | 0.400 | fail |
| v8 | 5-5 | 0.500 | neutral |
| v5 | 2-8 | 0.200 | fail |
| Lucario v3 | 4-6 | 0.400 | fail |
| Koushikrudra library-out | 4-6 | 0.400 | fail |

Decision: reject v14. The went-first diagnosis is useful, but always choosing
second is too blunt.

## Next strategy

Do not submit v14.

The next candidate should test a conditional first-choice policy rather than an
always-second policy. Possible forms:

1. choose second only for v8-style candidate when the opening hand has no Riolu
   and no fast Lucario path;
2. choose first when Riolu + energy / Hero Cape / Mega Lucario path is available;
3. choose second when the only basic is Solrock or Makuhita, because those hands
   created the worst Dragapult/Phantump tempo losses.

Before implementing that, the replay diagnostic should be extended to summarize
opening hand categories across all v8 wins/losses, not only the critical losses.