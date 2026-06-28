# Conservative Switch v1 Experiment

## Hypothesis

The loss-taxonomy notebook found repeated switch-related losses and showed that
the promoted policy never chose `RETREAT` in the diagnostic run. A narrow
retreat rule may improve tempo without disrupting the stable development-first
baseline.

## Candidate

`conservative_switch_v1` keeps the promoted development-first ordering except
for one condition:

1. the current selection is a main-phase selection;
2. `RETREAT` is legal;
3. the active Pokémon has no attached Energy;
4. at least one benched Pokémon has at least one attached Energy.

Only then does the candidate prioritize `RETREAT`. If the simulator asks which
Pokémon should become active, the candidate chooses a ready benched Pokémon,
preferring more attached Energy and then Mega Abomasnow ex or Kyogre.

The production files `agent/main.py` and `agent/deck.csv` remain unchanged.

## Evaluation plan

Notebook `11_conservative_switch_experiment.ipynb` evaluates the candidate
against four frozen controls:

- promoted development-first policy;
- held planner v2;
- official random policy;
- frozen pressure control.

Each matchup uses controlled seat and first-player cells. Promotion requires
zero failures and bootstrap intervals above parity for all required matchups.

## Interpretation

Promote only if the switch rule beats the promoted control and does not regress
against planner v2, random, or pressure. If it holds but does not clear the
gate, inspect the exported replays and switch telemetry before changing the
rule.
