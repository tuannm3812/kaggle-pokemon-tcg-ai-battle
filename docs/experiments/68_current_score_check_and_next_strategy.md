# Current Score Check and Next Strategy

Date: 2026-07-07

## Current Kaggle submission scores

Checked with:

```powershell
python -m kaggle competitions submissions pokemon-tcg-ai-battle -v
```

| Submission | Description | Status | Public score |
| ---: | --- | --- | ---: |
| `54391951` | kojimar v8 public boss guard | COMPLETE | 805.1 |
| `54348833` | kojimar v5 metal pressure | COMPLETE | 727.0 |
| `54303967` | kojimar simple baseline v1 | COMPLETE | 864.5 |
| `54283898` | lucario public sample v3 | COMPLETE | 711.2 |
| `54213861` | lucario public sample v1 | COMPLETE | 662.0 |
| `54126975` | planner main only v1 | COMPLETE | 560.3 |
| `54100265` | fix deck loader missing `__file__` | COMPLETE | 496.7 |

## Decision

Do not submit v18, v19, or v20.

The active-best public score is still `kojimar_simple_baseline_v1` at `864.5`.
Although v8 drifted upward to `805.1`, it remains below v1 and previously showed
bad Dragapult/Phantump behavior. The recent local candidates v18-v20 did not
produce a convincing pressure-control improvement.

## Next strategy

The next step should be diagnostic tooling, not another submission:

1. Fix or simplify candidate-vs-reference decision-delta comparison.
2. Use it only on public-loss midgame states.
3. Identify the exact option type where v1 differs from a useful challenger.
4. Build v21 only if the delta points to a repeated decision point.

Active-best remains:

`kojimar_simple_baseline_v1`
