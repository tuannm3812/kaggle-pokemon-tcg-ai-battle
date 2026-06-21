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

## Baseline policy in this repository

The baseline ranks main actions approximately as attack, evolve, ability,
attach, play, retreat, discard, and end. Non-main decisions use conservative,
stable selection. This removes randomness and provides a testable control, but
it does not yet understand card value, attack damage, or the board.

## Near-term experiments

1. State-aware attack ranking using immediate knockout and printed damage.
2. Setup scoring using HP, retreat cost, and attack energy requirements.
3. Attachment scoring based on turns-to-attack.
4. First-player choice tested with seat-swapped matches.
5. Selective one-ply search for attack/retreat decisions.
