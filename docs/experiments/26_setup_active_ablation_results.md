# Setup-Active Ablation Results

## Scope

This step split `setup_active_v1` into smaller ablations to isolate why it
cleared the direct promoted-control gate but remained risky in author-style
coverage.

New candidates:

- `candidates/setup_first_snover_v1/`
- `candidates/setup_second_kyogre_v1/`

Production remains unchanged.

## Candidate designs

### `setup_first_snover_v1`

Only applies the first half of `setup_active_v1`:

- during `SETUP_ACTIVE_POKEMON`, prefer Snover when our player is going first;
- otherwise fall back to promoted baseline ordering.

### `setup_second_kyogre_v1`

Only applies the second half:

- during `SETUP_ACTIVE_POKEMON`, prefer Kyogre when our player is not going
  first;
- otherwise fall back to promoted baseline ordering.

## Direct promoted-control gates

Commands:

```powershell
python scripts\evaluate_direct_gate.py --candidate setup_first_snover_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062804
python scripts\evaluate_direct_gate.py --candidate setup_second_kyogre_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062805
python scripts\evaluate_direct_gate.py --candidate hybrid_card_ko_v1 --control promoted --games-per-cell 20 --max-decisions 2500 --seed 2026062806
```

Results:

| Candidate | Games | W-L | Score rate | Approx. 95% interval | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| setup_first_snover_v1 | 80 | 38-42 | 0.475 | [0.399, 0.552] | Reject |
| setup_second_kyogre_v1 | 80 | 43-37 | 0.538 | [0.460, 0.613] | Reject |
| hybrid_card_ko_v1 | 80 | 39-41 | 0.488 | [0.411, 0.564] | Reject |

## Interpretation

Neither half of `setup_active_v1` independently explains the stronger direct
result. The full rule appears to be a coupled setup effect, but it still carries
author-suite risk and should not be submitted.

The extra `hybrid_card_ko_v1` direct recheck was included because the latest
author-style screen made it look stronger than before. It failed the direct
promoted-control gate, so it remains rejected.

## Decision

Do not submit a new agent.

Current production remains the accepted promoted baseline.

## Next recommendation

Move away from setup-active variants for now. The strongest unresolved signal is
that planner-style policies can improve author-suite coverage but do not yet
separate from promoted in direct play.

The next useful experiment should be a planner ablation, not another setup
ablation:

1. start from `planner_v2`;
2. remove or soften the cells that hurt direct play, especially the poor
   `candidate seat 1 / player zero first true` split seen in several failed
   candidates;
3. keep the author-suite strengths only if the direct gate clears parity.
