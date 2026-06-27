# Tactical KO v1 Results

## Scope

`tactical_ko_v1` tested one narrow policy change after the first accepted
leaderboard submission scored `537.5`.

Production remains unchanged. The candidate is stored under
`candidates/tactical_ko_v1/`.

## Candidate

The candidate starts from the accepted development-first baseline and adds one
main-phase override:

- if an available attack is estimated to immediately knock out the opponent's
  active Pokémon, attack now;
- otherwise keep the accepted development-first ordering.

The override uses only high-confidence public damage:

| Attack ID | Attack | Damage model |
| ---: | --- | --- |
| `1042` | Kyogre Riptide | `20 * visible Basic Water Energy in discard` |
| `1043` | Kyogre Swirling Waves | `130` |
| `1044` | Snover Beat | `10` |
| `1045` | Snover Icy Snow | `30` |
| `1047` | Mega Abomasnow ex Frost Barrier | `200` |

Mega Abomasnow ex `Hammer-lanche` is intentionally excluded from knockout
prediction because its damage depends on random top-deck discard.

## Local controlled screen

The screen used ten games in each candidate-seat by forced-turn-order cell.

| Matchup | Games | W-L | Score rate | Bootstrap 95% interval | Override count | Decision |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| tactical KO v1 vs accepted baseline | 40 | 22-18 | 0.550 | [0.400, 0.700] | 10 | Hold |
| tactical KO v1 vs planner v2 | 40 | 15-25 | 0.375 | [0.225, 0.525] | 6 | Reject |
| tactical KO v1 vs official random | 40 | 34-6 | 0.850 | [0.725, 0.950] | 18 | Regression pass |

All games completed without failures.

## Interpretation

The override fires and is legal, but it is not a promotion candidate:

- the primary baseline matchup interval overlaps parity;
- the planner v2 matchup is poor at `15-25`;
- the candidate would risk occupying one of the two tracked submission slots
  without evidence of a robust ladder gain.

Do not submit `tactical_ko_v1`.

## Next recommendation

Move from tactical overrides to opponent/deck coverage:

1. build a stronger local opponent suite from author-reference agents;
2. evaluate the accepted baseline and held candidates against those frozen
   opponents;
3. choose the next change based on the dominant loss mode against stronger
   opponents, not against random or self-play only.

The most promising next implementation path is an author-style opponent suite
not another small sequencing heuristic.
