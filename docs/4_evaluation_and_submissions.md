# Evaluation and Submission Decisions

## Current promotion anchor

Current active best: `kojimar_simple_baseline_v1`.

Future promotion gates should normally compare against this agent. Older agents
such as `lucario_public_sample_v3`, `lucario_public_sample_v1`, and
`planner_main_only_v1` remain useful regression controls, but they are no longer
the main submission bar.

## Offline score

For candidate-versus-control games, award 1 for a win, 0.5 for a draw, and 0
for a loss:

```text
score_rate = (wins + 0.5 * draws) / games
```

Report:

- wins/draws/losses;
- score rate;
- Wilson confidence interval;
- failures counted explicitly;
- seat and first-player cell breakdown;
- opponent/archetype labels when available.

## Evaluation tiers

| Tier | Purpose | Typical command |
| --- | --- | --- |
| Contract/package smoke | API legality and termination | `python scripts/package_submission.py --candidate NAME --games 6` |
| Direct gate | Candidate vs active best | `python scripts/evaluate_direct_gate.py --candidate NAME --control kojimar_simple_baseline_v1 --games-per-cell 5` |
| Confirmation gate | Repeat direct gate with new seed | Add `--seed YYYYMMDD` |
| Reliability gate | Catch crashes and random-control weakness | `--control official_random` |
| Archetype suite | Check broad matchup coverage | `python scripts/evaluate_author_archetype_deck_suite.py --candidates NAME` |
| Targeted matchup suite | Validate a specific patch | Build/use a matching frozen control, e.g. Crustle wall |

Small local gates are directional. Submit only when the evidence is strong enough
for the available submission slot and the candidate package validates locally.

## Promotion decision rule

A candidate is ready for a leaderboard probe when it satisfies most of these:

- beats the active best in direct and confirmation gates;
- has no validation/runtime failures;
- does not collapse in any seat/first-player cell;
- preserves or improves exact-archetype aggregate;
- passes random-control reliability;
- has a documented hypothesis and single main change;
- package smoke test passes with `main.py`, `deck.csv`, and `cg/` at archive
  root.

A candidate should be held or rejected when:

- direct evidence is near parity;
- one cell collapses badly even if aggregate is positive;
- the candidate only improves an unvalidated theoretical matchup;
- public score is lower and local evidence was weak or contradictory.

## Ladder interpretation

Leaderboard scores are volatile because agents continue receiving matches.
Important lessons from this project:

- `lucario_public_sample_v3` initially completed around `600.0`, then drifted
  above `700`.
- `kojimar_simple_baseline_v1` initially completed at `600.0`, then drifted to
  `861.4`.

Therefore:

1. Record the first completed score.
2. Poll later before making a final keep/reject decision.
3. Compare score drift with local gate evidence.
4. Do not panic-submit a replacement after one low initial snapshot.

## Submission workflow

1. Package locally:

   ```powershell
   python scripts/package_submission.py --candidate NAME --games 6 --max-decisions 2500
   ```

2. Submit:

   ```powershell
   python -m kaggle competitions submit -c pokemon-tcg-ai-battle -f scratch/submission_packages/NAME/submission.tar.gz -m "message"
   ```

3. Poll status:

   ```powershell
   python -m kaggle competitions submissions pokemon-tcg-ai-battle
   ```

4. Record in `docs/submissions/39_lucario_public_sample_submission.md`:

   - ref;
   - message;
   - status;
   - initial public score;
   - later score drift;
   - comparison against active best;
   - keep/hold/reject decision.

## Current score source of truth

Use `docs/submissions/39_lucario_public_sample_submission.md` for chronological
score tracking. Use `docs/README.md` for the latest high-level snapshot.
