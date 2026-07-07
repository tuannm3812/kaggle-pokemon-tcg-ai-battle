# Strategy EDA for V18

Date: 2026-07-07

## Purpose

Run the new strategy-oriented EDA layer described in
`docs/2_eda_and_environment.md`. The goal is to decide what the next candidate
should change before writing another agent branch.

Input:

- Active-best submission: `54303967`
- Candidate reference: `kojimar_simple_baseline_v1`
- Weak archetypes: `metal_cinderace`, `alakazam_dunsparce`
- Source diagnosis:
  `scratch/loss_diagnostics/54303967_metal_cinderace-alakazam_dunsparce_losses.json`

Command:

```powershell
python scripts/strategy_eda_from_loss_diagnostics.py --input scratch\loss_diagnostics\54303967_metal_cinderace-alakazam_dunsparce_losses.json --start-turn 5 --end-turn 7
```

Outputs:

- `scratch/strategy_eda/54303967_metal_cinderace-alakazam_dunsparce_losses_strategy_eda.json`
- `scratch/strategy_eda/54303967_metal_cinderace-alakazam_dunsparce_losses_strategy_eda.md`

## Findings

| Archetype | Episodes | Went first | Median first attack | Midgame rows | Boss in hand rows | Low-HP Mega Lucario rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `alakazam_dunsparce` | 9 | 4 | 4 | 138 | 70 | 4 |
| `metal_cinderace` | 21 | 19 | 3 | 405 | 200 | 51 |

The strongest signal is not initial setup. By turns 5-7, the agent frequently
already has `Mega Lucario ex` active:

| Archetype | Most common active in turns 5-7 |
| --- | --- |
| `alakazam_dunsparce` | `Mega Lucario ex` 79 rows |
| `metal_cinderace` | `Mega Lucario ex` 281 rows |

The repeated problem space is midgame conversion:

- Metal/Cinderace repeatedly exposes `Duraludon`, `Archaludon ex`,
  `Relicanth`, and `Cinderace`.
- Alakazam/Dunsparce repeatedly exposes `Alakazam`, `Dunsparce`, `Kadabra`,
  `Abra`, and `Dudunsparce`.
- Boss's Orders is present in many turn 5-7 rows, so the next question is not
  merely whether Boss exists, but whether it is used at the right time.
- Metal/Cinderace has many low-HP `Mega Lucario ex` rows, which means late
  midgame pressure can be too slow or poorly converted after the opponent has
  built a large evolved threat.

## Candidate implication

Reject more broad opening/setup changes. V17 already showed that forcing a
Riolu active opening regressed protected matchups.

The next candidate should be a **v1-derived midgame conversion patch**:

- allowed: tiny attack/Boss/retreat scoring change in turns 5-7;
- allowed: only when a Metal/Cinderace or Alakazam/Dunsparce key target is
  visible and already KO-able or near-KO;
- disallowed: global first/second-player preference;
- disallowed: global setup-active preference;
- disallowed: broad Boss's Orders guard like v8.

## V18 brief

Build `kojimar_simple_baseline_v18_midgame_finish_pressure` from
`kojimar_simple_baseline_v1`.

Hypothesis:

> Preserve v1, but slightly raise the value of converting visible midgame
> threats when the active-best agent already has a clear payoff line. The rule
> should activate only after setup, only for the weak public families, and only
> when it does not encourage low-value non-KO bench gusting.

Promotion gate:

- Must not regress Lucario public sample v3.
- Must not regress library-out.
- Should improve or tie v5/v8-style pressure controls.
- If the gate returns `hold`, do not submit.
