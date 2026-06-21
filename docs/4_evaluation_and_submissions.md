# Evaluation and Submission Decisions

## Offline score

For candidate-versus-control games, award 1 for a win, 0.5 for a draw, and 0
for a loss:

```text
score_rate = (wins + 0.5 * draws) / games
```

Report a Wilson confidence interval on decisive-score indicators as a readable
uncertainty summary. Because games are paired by seed and seat, also report
pair-level outcomes and seat-specific rates. Bootstrap paired results when the
sample is large enough.

## Evaluation tiers

| Tier | Purpose | Suggested volume |
| --- | --- | ---: |
| Contract test | API legality and termination | 2–10 games |
| Smoke comparison | Catch severe regressions | 20–50 paired games |
| Candidate screen | Directional evidence | 100–300 paired games |
| Promotion test | Submission decision | 500+ paired games across opponents |

Volumes are guidance, not magic thresholds. Increase them when effects are
small, variance is high, or a submission slot is especially valuable.

## Opponent suite

Do not optimize only against the current baseline. Maintain frozen opponents:

- official random sample;
- deterministic baseline;
- previous ladder champion;
- attack-heavy and setup-heavy heuristic variants;
- representative deck variants.

Promote a candidate only if its aggregate improvement does not hide a critical
matchup collapse or increased crash rate.

## Ladder interpretation

`mu` without `sigma` and episode count is incomplete. A new agent may move
quickly because its uncertainty is high. Compare agents after adequate games,
inspect episode logs, and avoid reacting to a short streak.

## Submission gate

A candidate is ready only when:

- the package passes local structure checks;
- self-play terminates without exceptions;
- returned actions pass legality assertions;
- paired evaluation beats the frozen control with acceptable uncertainty;
- runtime and package size remain within live competition limits;
- the exact deck and code hashes are recorded;
- the expected benefit justifies replacing one of the latest two tracked
  agents.

## Post-submission review

Record validation status immediately. Later record `mu`, `sigma`, episode
count, observed failures, and the keep/reject decision. Download logs for every
error rather than resubmitting blindly. Use
`docs/6_experiment_log.md` as the canonical ledger.
