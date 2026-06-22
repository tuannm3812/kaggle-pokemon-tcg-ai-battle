# Competition Author Reference Review

## Scope

This review covers six notebooks published by competition author `kiyotah`:

1. [Local battle JSON and replay viewer](https://www.kaggle.com/code/kiyotah/how-to-output-local-battle-as-json-and-view)
2. [Reinforcement learning and MCTS sample](https://www.kaggle.com/code/kiyotah/reinforcement-learning-and-mcts-sample-code)
3. [Rule agent: Iono's deck](https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-iono-s-deck)
4. [Rule agent: Mega Lucario ex](https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck)
5. [Rule agent: Dragapult ex](https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-dragapult-ex-deck)
6. [Rule agent: Mega Abomasnow ex](https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-mega-abomasnow-ex-deck)

These are examples, not validated drop-in solutions. Their main value is the
decision architecture: how they convert legal choices into a coherent turn
plan under partial observability.

## Executive conclusion

The next useful abstraction for this repository is an **attack plan**, not
another isolated priority exception. The strongest author agents first choose
an intended attacker, target, attack, and required setup. They then score
attachments, switches, searches, supporters, evolutions, and attacks by how
well each action advances that same plan.

This explains why our isolated knockout and attachment rules did not clear
their promotion gates. They improved one local decision without coordinating
the rest of the turn. The references support this order of work:

1. add first-player attribution and replay artifacts to evaluation;
2. build a compact Mega Abomasnow-specific attack planner;
3. evaluate it against the promoted policy and stronger frozen opponents;
4. use the Search API only for narrow, high-impact decisions;
5. defer full reinforcement learning until telemetry and opponents mature.

## Reference comparison

| Reference | Main technique | Most transferable idea | Main limitation |
| --- | --- | --- | --- |
| Battle JSON viewer | Records observations and both players' actions in replay JSON | Inspect complete failed episodes instead of relying only on counters | The optional web viewer sends replay JSON to an external service |
| RL and MCTS | Sparse policy/value network with PUCT-like simulator search | Search can answer exact tactical questions that printed card text cannot | Tiny search, crude hidden-state completion, and a 64-action cap |
| Iono | Resource-engine state and role-specific action scores | Energy value depends on Pokemon role and the existing board engine | Highly coupled to the example deck |
| Mega Lucario ex | Persistent per-turn `AttackPlan` | Choose attacker and target first, then make each action execute the plan | Card-specific branches and mutable global state |
| Dragapult ex | Attack planning, prize valuation, logs, and visible-card tracking | Prize-aware targeting and multi-target damage allocation | The 800+ line policy is too specialized to copy wholesale |
| Mega Abomasnow ex | Deck-specific scoring for an Abomasnow/Kyogre core | Closest strategic reference for our deck and best adaptation starting point | Its trainer package differs materially from ours |

## Detailed findings

### Replay JSON and visual debugging

The replay notebook demonstrates two paths:

- run a `cabt` Kaggle Environment episode and save its visualization payload;
- call `battle_start`, repeatedly call `battle_select`, capture observations
  and both players' action indices, then merge them into `visualize_data()`.

The direct simulator path removes `search_begin_input` before serializing an
observation. The field is not required for replay and can make artifacts large.

Replay capture should be optional and bounded. Save failed games, unexpected
draws, and a small sample of wins; keep them out of Git. The author's HTML
viewer posts JSON to `ptcgvis.heroz.jp`, so do not use it with secrets or data
that should remain local.

### RL and MCTS sample

The model encodes public state, relevant card zones, active and benched Pokemon,
status, turn, and whether the agent is first player. It separately encodes each
legal action and predicts a scalar value and action policy. A PUCT-like search
uses these outputs through the simulator Search API.

Training alternates between evaluation, self-play collection, and Huber-loss
optimization. The value label blends the final result with search values, and
the policy label comes from search visits. It is an end-to-end example, but:

- `SEARCH_COUNT` is only 10;
- action combinations are capped at 64;
- unknown opponent cards are filled with placeholders;
- evaluation uses only a random opponent;
- training runs for five iterations with 100 self-play games each.

The immediate lesson is not to launch a large RL project. First use Search as a
tactical oracle where printed damage and rule text are insufficient.

### Iono's deck

This policy tracks total Energy, ready attackers, evolution lines, deck-out
risk, stadium state, and specific hand value. Attachment thresholds differ by
Pokemon and by whether a ready attacker already exists. Search, discard,
supporter, evolution, and retreat scores all depend on this shared state.

The transferable principle is that Energy has no universal value. Its value is
conditional on attacker role, attack threshold, redundancy, and turn plan.

### Mega Lucario ex

This is the clearest plan-first controller. At the main choice, it enumerates
attackers, attacks, attachment needs, opponent targets, weakness/resistance,
knockout prizes, and game-winning lines. It stores a plan for the turn. Later
selections prefer the attachment target, switch target, opponent target, and
attack named by that plan.

Its setup policy also changes with `state.firstPlayer`. This directly confirms
that first-player status should be logged separately from player index.

### Dragapult ex

The Dragapult agent extends plan-first control with prize-aware target value,
multi-target damage allocation, immunity checks, previous-turn logs, visible
card counts, prize-card inference, safe optional choices, and an explicit
first/second-player preference.

Its scores encode sequencing: evolution is high because it should happen
early, while attack is low because it normally ends the turn. A score is a
sequencing instruction, not an absolute estimate of card strength.

### Mega Abomasnow ex

This is closest to our Pokemon core. It coordinates Mega Abomasnow ex and
Kyogre using attacker readiness, Water Energy in the discard pile, expected
damage, useful switch targets, evolution pieces, and duplicate cards. It
preserves useful held evolutions when judging draw supporters and avoids
overattaching to an already-ready attacker.

Its deck is not identical to ours. The reference uses Ultra Ball, Precious
Trolley, Carmine, Lillie's Determination, and Surfing Beach. We should transfer
the state model and planning structure, then write logic for our own 60 cards.

## Implications for our experiments

Our promoted policy globally orders action types but has no shared tactical
plan. The held follow-ups fit the author evidence:

- printed-knockout used base damage and current HP only;
- attack-readiness attachment overvalued Snover's low-damage attack;
- projected attachment value improved a local estimate but did not coordinate
  attachment with switching, evolution, search, or the intended attack;
- the eight-Basic deck improved setup probability but not outcomes, and its
  seat split could not distinguish seat from first-player effects.

The references do not prove that an attack planner will win. They provide a
stronger causal hypothesis and a coherent design that can be tested.

## Recommended implementation sequence

### Phase 1: observability

Add these fields to every episode summary:

- agent seat and actual first player;
- winner, termination reason, turns, and runtime;
- actions selected by context and option type;
- optional replay path for selected episodes.

Report outcomes by both seat and first-player status. This resolves the most
important ambiguity in our current evidence.

### Phase 2: compact Abomasnow attack planner

Preserve the current legality shield and stable fallback. At the first main
choice of a turn, compute a small plan containing:

- intended attacker and required switch;
- intended attack and reliable damage estimate;
- attachment target and remaining Energy requirement;
- immediate knockout and prize value;
- evolution or search prerequisite;
- discard-Energy value for Kyogre;
- confidence flag when state is incomplete.

Override choices only when the plan is confident; otherwise use the promoted
development-first order. Avoid mutable state that can leak between games. Key
any cache by episode and turn, or reconstruct the plan from the observation.

### Phase 3: evaluation gate

Evaluate against the promoted control, the random policy as a regression check,
and at least one frozen stronger opponent. Balance seats and first-player
status, record failures/runtime, and inspect replays for changed decisions.

### Phase 4: selective Search API

After the planner is stable, use bounded search when two tactical choices are
close or printed damage is unreliable. Good first targets are attack selection,
retreat versus attack, and a switch that creates an immediate knockout. Record
search calls, nodes, elapsed time, selection, and timeout fallback.

## Decision

Do not copy an author agent or start full RL/MCTS now. Adopt replay and
first-player instrumentation first, then build one compact deck-specific attack
planner. This is the smallest next step that addresses our experimental failure
mode and the common design pattern in the official references.
