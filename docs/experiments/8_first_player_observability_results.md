# First-Player Observability Results

## Outcome

Two private Kaggle notebooks completed the observability step:

- [First Player Replays](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-first-player-replays), version 1;
- [Controlled Turn Order](https://www.kaggle.com/code/tuannm3812/pokemon-tcg-controlled-turn-order), version 2.

The production agent and deck were not changed.

## Observational screen

The promoted policy played 40 seat-balanced games against the official random
policy and finished `29-0-11`, score rate `0.725`, bootstrap 95% interval
`[0.575, 0.850]`, with zero failures.

| Candidate condition | Games | Score rate |
| --- | ---: | ---: |
| Player 0 | 20 | 0.750 |
| Player 1 | 20 | 0.700 |
| Went first | 31 | 0.710 |
| Went second | 9 | 0.778 |

This run revealed that first-player status is not passively balanced. When the
candidate occupied player 0, it chose to go first in all 20 games. The nine
second-player games all occurred while the candidate occupied player 1.
Consequently, the observational split remained confounded and could not estimate
a causal turn-order effect.

Four candidate losses were saved as replay JSON. An inspected replay contained
43 visualization steps, all with observation and action fields. Replay sizes
ranged from approximately 312 KB to 579 KB.

## Controlled 2x2 screen

The follow-up changed only player 0's `IS_FIRST` response, then delegated every
later choice to the frozen policy. It crossed candidate seat with forced
candidate turn order, using ten games per cell.

| Candidate seat | Turn order | Games | W-L | Score rate |
| ---: | --- | ---: | ---: | ---: |
| 0 | Second | 10 | 8-2 | 0.800 |
| 0 | First | 10 | 10-0 | 1.000 |
| 1 | Second | 10 | 6-4 | 0.600 |
| 1 | First | 10 | 8-2 | 0.800 |

Overall, the candidate finished `32-0-8`, score rate `0.800`, bootstrap 95%
interval `[0.675, 0.925]`, with zero failures. The design assertion confirmed
ten games in each intended seat/turn-order cell.

Going first improved score rate from `0.700` to `0.900`. The observed
`+0.200` direction was identical within both seats. Player 0 also exceeded
player 1 by `+0.200`, so both dimensions remain strategically relevant.

## Interpretation

The controlled direction is consistent and practically large, but each cell
contains only ten games. Treat it as screening evidence rather than proof of a
stable 20-point advantage. The current result supports making setup and attack
planning aware of `state.firstPlayer`; it does not justify changing the
production policy solely to force first-player selection.

The replay quota retained three losses rather than four because the
seat-0/first cell had no losses. This is expected and confirms that replay
retention is outcome- and cell-aware.

## Next experiment

Build the compact Mega Abomasnow/Kyogre attack planner described in the author
reference review. Include `state.firstPlayer` in its setup plan, preserve the
promoted legality fallback, and evaluate the candidate in the same controlled
2x2 design against both the promoted control and a stronger frozen opponent.
