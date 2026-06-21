# Agent Strategy

## Strategic objective

Optimize match win probability under partial observability and a finite
runtime budget. Because ladder updates ignore margin, the agent should prefer a
line with the higher probability of eventually winning over a line that wins
more dramatically when it succeeds.

## Development ladder

### Stage 0 — Legality and determinism

Guarantee valid return types, index bounds, uniqueness, and selection counts.
Use deterministic tie-breaking so identical observations yield identical
actions. This makes regressions reproducible and reduces validation risk.

### Stage 1 — Context-aware heuristics

Score choices by decision context:

- setup: active durability, attack readiness, and bench development;
- main phase: immediate knockout, safe evolution, energy acceleration,
  consistency cards, manual attachment, retreat, then turn end;
- search/discard: preserve scarce combo pieces and choose cards aligned with
  the current plan;
- attack: prize swing, knockout probability, expected damage, resource cost,
  and retaliation risk.

Every context scorer must fall back to a legal stable selection if required
fields are unavailable.

### Stage 2 — Board evaluation

Represent a state with public, causally relevant features:

- prize differential and remaining prize liabilities;
- active HP and incoming knockout risk;
- bench quality and evolution readiness;
- attached energy value and retreat mobility;
- hand/deck resources and once-per-turn actions;
- status conditions and revealed opponent information.

A first value function can be a transparent weighted sum. Tune weights with
paired self-play, not isolated anecdotes.

### Stage 3 — Shallow simulator search

The SDK exposes search functions. Apply search selectively to high-impact
choices, especially attacks, retreats, and multi-action main phases. Use a
strict node/time budget and deterministic rollout policy. Cache equivalent
public states where safe.

Hidden information means a single determinization can be brittle. Sample
plausible opponent hands/deck orders from revealed information and average
action values, while never using information absent from the observation.

### Stage 4 — Learned policy/value components

Once telemetry is reliable, train from self-play trajectories or distill
search decisions. Keep a rule-based legality shield around learned outputs.
Validate calibration and generalization against frozen, diverse opponents.

## Deck and policy co-design

A policy cannot rescue an incoherent deck, and a strong deck can be squandered
by poor sequencing. Iterate in two tracks:

- freeze the policy while screening legal deck variants;
- freeze the deck while improving policy decisions.

Only combine gains after each component beats its control independently.

## Current promoted policy

The repository now uses development-first ordering: evolve, ability, attach,
play, attack, retreat, discard, then end. This is the only behavioral change
from the frozen attack-first baseline; setup and stable tie-breaking remain
unchanged.

## Near-term experiments

1. First-player attribution using the simulator's `firstPlayer` state, separated from player index.
2. Opponent-diverse evaluation against stronger frozen agents.
3. State-aware damage estimation including resistance, prevention, and active effects.
4. Selective one-ply search for attack/retreat decisions.
5. Alternative deck variants only after stronger-opponent evidence is available.

## Evidence from the first comparative screen

The deterministic baseline is contract-safe but lost `5-0-35` to the official
random policy over 40 seat-balanced games. Its score rate was `0.125` with a
bootstrap 95% interval of `[0.025, 0.225]`, so it must not be submitted.

Policy-attributed telemetry identifies premature aggression as the leading
hypothesis: the candidate selected attack 322 times and attach only 64 times,
while the control selected attack 139 times and attach 228 times. The next
single-change experiment should move attack behind safe board-development
actions, then add state-aware knockout and retaliation scoring. Preserve this
baseline as a reliability control, not a strength control.

## Development-first promotion evidence

The reproducible sequencing experiment completed 120 games without failures.
Development-first beat attack-first `37-0-3` with score rate `0.925` and a
bootstrap 95% interval of `[0.825, 1.000]`. It beat the official random policy
`32-0-8` (`0.800`, `[0.675, 0.925]`). An independent standard screen produced
`31-0-9` (`0.775`, `[0.650, 0.900]`).

State snapshots support the causal hypothesis: development-first attacked with
substantially more attached Energy and a larger Bench than attack-first. The
priority change is promoted.

## Printed-damage knockout follow-up

The follow-up preserved the deck and development-first fallback, changing only
one rule: attack immediately when a legal attack's printed base damage met or
exceeded the opposing Active Pokemon's current HP. It completed 40 games without
failures and scored `25-0-15` (`0.625`) against development-first, with a
bootstrap 95% interval of `[0.475, 0.775]`. The exception triggered 21 times and
displaced an available development action 11 times.

Because the interval overlaps parity, the result is **HOLD**. Do not modify
`agent/main.py`. Printed base damage omits resistance, temporary prevention or
reduction, and conditional damage; a future candidate must improve that state
model or gather a larger, opponent-diverse evidence set.

## Attack-readiness attachment follow-up

The attachment candidate preserved every non-ATTACH decision and changed only
the target of an attachment already selected by development-first. Across 40
Kaggle games it finished `20-0-20` (`0.500`) with a bootstrap 95% interval of
`[0.350, 0.650]`, zero failures, and 84 target changes.

The result is **HOLD**. Event inspection showed that minimizing distance to an
attack threshold can overvalue Snover's 30-damage attack and divert Energy from
Mega Abomasnow ex or Kyogre. The next scorer should optimize expected value per
attachment, including printed damage, Energy still required, evolution
potential, current Active relevance, and the cost of concentrating excess
Energy. The production agent remains unchanged.

## Projected attachment-value follow-up

The corrected value scorer projected Snover into Mega Abomasnow ex, divided
reliable printed damage by remaining Energy, applied a small Active multiplier,
and returned to baseline behavior when all targets were ready. This correction
removed the observed over-attachment defect: all 31 changed targets had fewer
than three Energy before attachment.

Across 40 Kaggle games it finished `20-0-20` (`0.500`) with a bootstrap 95%
interval of `[0.350, 0.650]` and zero failures. The result is **HOLD** and
`agent/main.py` remains unchanged. Since three isolated policy refinements have
not cleared parity, the next experiment should freeze policy and address the
starter deck's 45.86% no-Basic opening risk.


## Eight-Basic deck-consistency follow-up

The deck candidate replaced two of 35 Basic Water Energy cards with two Kyogre,
raising Basic Pokemon from six to eight while keeping all non-Energy copy counts
at four or fewer. Exact seven-card setup probability increased from `0.5414` to
`0.6536`, an 11.22 percentage-point gain.

With development-first frozen, the candidate finished `40-0-40` over 80 Kaggle
games (`0.500`, bootstrap 95% `[0.3875, 0.6125]`) with zero failures. It scored
`0.60` while occupying player 0 and `0.40` as player 1. The result is **HOLD**;
do not modify `agent/deck.csv`. The parity result and seat split shift the next
priority to actual `firstPlayer` attribution and opponent diversity rather than
another immediate deck edit.
