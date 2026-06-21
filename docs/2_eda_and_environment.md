# EDA and Environment Analysis

## Purpose

This is a simulation competition, not a supervised train/test prediction task.
EDA should reduce uncertainty about decisions the agent or deck designer can
actually change. It has three connected layers:

1. **Card-pool EDA** - representation, card roles, HP, retreat, attacks, costs,
   effects, missingness, and duplicate move rows.
2. **Deck EDA** - legality, functional roles, setup consistency, evolution
   support, energy balance, retreat burden, and attack readiness.
3. **Episode EDA** - legal choices, action sequences, board development, seat
   effects, terminal reasons, runtime, and matchup outcomes.

The refined notebook follows that order and ends with decisions rather than a
collection of disconnected charts.

## Recommended notebook flow

| Stage | Question answered | Output used downstream |
| --- | --- | --- |
| 1. Provenance and schema | Are inputs present and represented safely? | Stable paths and normalized columns |
| 2. Catalogue grain | Is a row a card or a card-move record? | One identity row per `Card ID` plus a separate move table |
| 3. Card-pool landscape | What roles and printed stat ranges exist? | Context for deck-level comparisons |
| 4. Deck audit | Is the 60-card list recognized and plausibly legal? | Executable validation gate |
| 5. Setup consistency | How often can the deck open a Basic Pokemon? | Deck-construction priority |
| 6. Evolution support | Are evolution cards structurally live? | Development-action rationale |
| 7. Attack efficiency | What printed damage and energy requirements are available? | Features for action scoring |
| 8. PDF audit | Is a targeted visual lookup necessary? | Bounded manual verification |
| 9. Decision summary | What changes next, and what stays fixed? | Controlled experiment plan |

Run [`notebooks/01_card_database_eda.ipynb`](../notebooks/01_card_database_eda.ipynb)
for the executable analysis.

## Official files and data grain

The English and Japanese card catalogues are CSV files. The sample submission
provides `main.py`, `deck.csv`, the `cg` Python API, and Windows and Linux
simulator binaries. The large card-ID PDFs are visual references and should not
be committed.

The English catalogue contains 2,022 rows but 1,267 unique card IDs. A card can
occupy multiple rows when it has multiple moves, so row count is not card count.
Use `Card ID` as the stable identity key, create one identity record per card,
and retain attacks as a one-to-many table. Missing HP or evolution fields on
Trainer and Energy cards are structural, not values to impute globally.

## Validated starter-deck findings

The refined notebook executed successfully against the local competition data.
Its starter deck contains 60 cards across nine unique IDs:

- 35 Basic Water Energy cards;
- 10 Pokemon cards: six Basic and four Stage 1;
- 15 Trainer/Tool/Item cards;
- six printed moves, including two variable-damage moves;
- weighted retreat cost of 34 across Pokemon copies.

The most important result is setup consistency. With six Basic Pokemon in a
60-card deck, the exact hypergeometric probability that a seven-card opening
hand contains at least one Basic is:

```text
P(setup) = 1 - C(54, 7) / C(60, 7) = 0.5414
P(no Basic / mulligan)                 = 0.4586
```

This 45.86% no-Basic risk is more actionable than another broad catalogue plot.
The Stage 1 evolution line is structurally supported at 100% by copy count, so
the main deck-level concern is opening consistency rather than a dead evolution
line. Simulator initialization remains the authoritative legality check.

## Analysis-to-strategy bridge

| Evidence | Interpretation | Action |
| --- | --- | --- |
| Only 54.14% opening setup probability | Policy cannot repair a no-Basic opening | Later test Basic-Pokemon count as an isolated deck intervention |
| Evolution support rate is 100% | Development actions can unlock live Stage 1 cards | Preserve evolution and early board-development opportunities |
| Two variable-damage moves | Printed damage is an incomplete action-value estimate | Use state-aware simulator telemetry, not damage alone |
| Development-first beat attack-first `37-0-3` | Premature aggression was a causal weakness | Keep development-first as the control policy |
| Development-first beat random `32-0-8` | The promoted ordering is a meaningful baseline | Test only one policy exception at a time |

The printed-damage knockout and both attachment follow-ups were held. The
separate deck-consistency experiment then replaced two Basic Water Energy with
two Kyogre, raising exact setup probability from 54.14% to 65.36%. Across 80
seat-balanced games the variant finished `40-0-40` (`0.500`, bootstrap 95%
`[0.3875, 0.6125]`) with zero failures. The setup gain did not produce a strength
gain, so `agent/deck.csv` remains unchanged. The `0.60` versus `0.40` score split
by occupied player index makes first-player attribution and stronger opponents
the next evidence priorities.

## Episode telemetry

Every controlled game should retain:

| Field | Why it matters |
| --- | --- |
| seed and seat | Reproducibility and first/second-player bias |
| candidate version | Traceability |
| result and terminal reason | Objective outcome and failure diagnosis |
| turns and decisions | Runtime and game-length profile |
| `SelectContext` frequency | Where the policy spends decisions |
| legal-option count | Branching-factor estimate |
| action-type frequency | Dead or overused strategic branches |
| board state at attacks | Whether aggression follows adequate development |

Across 120 completed sequencing games, development-first beat attack-first
`37-0-3` and random `32-0-8`, with no simulator failures. At attack decisions it
had more attached Energy and a larger Bench, supporting the interpretation that
early development?not blind aggression?was the missing behavior.

The remaining episode-EDA gap is opponent diversity and terminal-reason detail.
Future evidence should include frozen stronger opponents or ladder replays,
prize trajectories, knockout timing, deck-out frequency, and revealed-card
beliefs.

## Card-reference PDF policy

The 1,306-page English Card ID PDF maps simulator IDs to names, expansions,
collection numbers, and images. Use the CSV for programmatic joins. Render only
selected pages when card art, printed layout, or special-rule presentation must
be checked manually. The repository audit sampled pages 1, 2, 654, 1,305, and
1,306 from the 137.65 MB file.

Do not bulk-OCR or redistribute the card-image corpus. Record sampled pages and
findings so visual checks remain bounded and reproducible.
