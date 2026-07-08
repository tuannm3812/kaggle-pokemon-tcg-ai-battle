# Opening Category Cross-Branch Insights

Date: 2026-07-08

## Purpose

Continue the experiment cycle with an insight-generation pass instead of
immediately building another candidate. The goal is to understand whether v8's
improvements and failures are driven by opening/setup posture or by later
policy behavior.

Compared branches:

- v1 / `54303967`
- v8 / `54391951`

Focused archetypes:

- Metal/Cinderace
- Dragapult
- Phantump/Trevenant control

Commands:

```powershell
python scripts/analyze_opening_categories.py --submission-id 54303967 --archetypes metal_cinderace dragapult phantump_trevenant_control
python scripts/analyze_opening_categories.py --submission-id 54391951 --archetypes metal_cinderace dragapult phantump_trevenant_control
```

## V1 opening buckets

| Opening bucket | Games | Record | Score | Went first | Median first attack |
| --- | ---: | ---: | ---: | ---: | ---: |
| `riolu_slow_path` | 2 | 0-2 | 0.0000 | 2 | 7 |
| `lunatone_active` | 1 | 0-1 | 0.0000 | 1 | 3 |
| `riolu_fast_path` | 6 | 2-4 | 0.3333 | 6 | 3 |
| `unknown_active` | 31 | 13-18 | 0.4194 | 24 | 3 |
| `solrock_active` | 6 | 4-2 | 0.6667 | 6 | 5 |
| `makuhita_active` | 2 | 2-0 | 1.0000 | 2 | 5 |

## V8 opening buckets

| Opening bucket | Games | Record | Score | Went first | Median first attack |
| --- | ---: | ---: | ---: | ---: | ---: |
| `riolu_fast_path` | 4 | 1-3 | 0.2500 | 4 | 3 |
| `unknown_active` | 14 | 5-9 | 0.3571 | 11 | 3 |
| `makuhita_active` | 3 | 2-1 | 0.6667 | 3 | 7 |
| `solrock_active` | 3 | 2-1 | 0.6667 | 3 | 5 |
| `lunatone_active` | 2 | 2-0 | 1.0000 | 2 | 5 |

## Insights

### 1. Setup-active rewrites are not the obvious answer

Riolu starts are not consistently strong in these key archetypes:

- v1 `riolu_fast_path`: `2-4`
- v8 `riolu_fast_path`: `1-3`

This supports the earlier v17 rejection. Forcing Riolu active looked plausible
from isolated losses, but broader opening diagnostics show that Riolu openings
are not reliably superior.

### 2. Slower-looking openings can be winning

Solrock, Makuhita, and Lunatone openings have good small-sample results in both
branches. This means the policy can win without rushing into Mega Lucario as
quickly as possible. The quality of the follow-up line matters more than the
initial active alone.

### 3. V8's Metal/Cinderace improvement is probably not from opening posture

V8 still has weak `riolu_fast_path` and `unknown_active` buckets, yet it performs
well into Metal/Cinderace overall. That points back to midgame tactical behavior
— especially Boss timing and not over-gusting — rather than setup-active choice.

### 4. V8's Dragapult/Phantump collapse is unlikely to be fixed by setup alone

Because the opening buckets do not identify a clean, high-confidence failure
mode, the v8 collapse into Dragapult and Phantump/Trevenant likely comes from
later matchup-specific behavior. The broad Boss guard may be too passive against
these decks, or it may delay needed pressure windows.

## Strategy implication

Do not build another setup-active candidate.

The next strong candidate should focus on one of two paths:

1. **Replay-delta path:** compare v1 and v8 decisions only in Dragapult and
   Phantump/Trevenant public losses to identify what v8 does differently.
2. **Router path:** keep v1 globally and apply a very narrow v8-style Boss guard
   only against exact Metal/Cinderace signatures that have repeated public wins,
   not just broad archetype detection.

The safer next experiment is the replay-delta path because it can explain the
v8 collapse before we borrow more v8 behavior.
