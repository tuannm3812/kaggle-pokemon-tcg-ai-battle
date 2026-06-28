# Conservative Switch v2 Experiment

## Hypothesis

Switch v1 was too narrow: it never chose `RETREAT` because the observed ready
bench condition did not appear in the tournament telemetry. Switch v2 tests a
broader but still conservative retreat trigger.

## Candidate

`conservative_switch_v2` keeps the promoted development-first ordering except
when a legal retreat can move a clearly poor active Pokémon to a better bench
option.

It prioritizes `RETREAT` when:

- the active Pokémon has no attached Energy and the bench has either attached
  Energy or at least 30 more HP; or
- the active Pokémon has 80 HP or less and the bench has at least 50 more HP.

When choosing the new active Pokémon, it prefers higher HP, then attached
Energy, then Mega Abomasnow ex or Kyogre.

Production remains unchanged until the candidate clears the controlled gates.

## Evaluation

Notebook `12_conservative_switch_v2_experiment.ipynb` evaluates switch v2
against:

- promoted development-first policy;
- held planner v2;
- official random policy;
- frozen pressure control.

The tournament uses controlled seat and first-player cells. Promotion requires
zero failures and bootstrap intervals above parity for every required matchup.
