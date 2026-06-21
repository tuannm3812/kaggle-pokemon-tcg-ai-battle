# EDA and Environment Analysis

## What “EDA” means here

This is not a supervised train/test CSV competition. Useful exploration has
three layers:

1. **Card-pool EDA** — card types, stages, HP, energy costs, attack damage,
   rules, missingness, and duplicate representations.
2. **Deck EDA** — legality, card counts, evolution lines, energy balance, setup
   consistency, and searchable targets.
3. **Episode EDA** — decision contexts, legal-option counts, action frequency,
   game length, terminal reasons, seat effects, and matchup outcomes.

## Official files

The English and Japanese card catalogues are CSV files. The official sample
submission provides `main.py`, `deck.csv`, the `cg` Python API, and Windows and
Linux simulator binaries. Two large card-ID PDFs are reference material and
should not be committed.

The English catalogue includes identifiers, names, expansion and collection
number, stage/type, rule/category, previous stage, HP, Pokémon/energy type,
weakness, resistance, retreat cost, move name, cost, damage, and effect text.
A card can occupy multiple rows when it has multiple moves, so row count is
not card count. Aggregate by `Card ID` before making deck-level conclusions.

## Required audits

### Catalogue quality

- Normalize column names and explicit `n/a` values.
- Check uniqueness at `(Card ID, Move Name)` rather than raw rows alone.
- Count unique cards separately from move rows.
- Parse HP, retreat, and printed damage conservatively; effect-dependent
  damage strings are not always plain integers.
- Compare English and Japanese ID coverage without assuming translated text is
  row-aligned.

### Deck legality

- Exactly 60 card IDs.
- Every ID exists in the official catalogue.
- Card-copy, basic-energy, ACE SPEC, and other construction rules must be
  checked against both catalogue metadata and current game rules.
- At least one Basic Pokémon must be available for setup.
- Evolution cards should have supported lower stages.

The starter deck contains many repeated Basic Water Energy cards. That is
expected because basic energy is exempt from the ordinary four-copy limit; a
naive duplicate-count check would falsely reject it.

### Episode telemetry

For every game, retain:

| Field | Why it matters |
| --- | --- |
| seed and seat | Reproducibility and first/second-player bias |
| candidate version | Traceability |
| result and terminal reason | Actual optimization target and failures |
| turns and decisions | Runtime and game-length profile |
| `SelectContext` frequency | Where the policy spends decisions |
| legal-option count | Branching-factor estimate |
| action-type frequency | Detects dead or overused strategic branches |

## Analysis-to-strategy bridge

- High setup failure or mulligan rates point to deck construction, not search.
- Large seat effects require paired evaluation and may justify different
  first-player choices.
- A few high-branching contexts suggest where shallow lookahead has the best
  computational return.
- Repeated losses after legal execution call for board-value and hidden-state
  improvements; validation crashes call for contract hardening first.

Run `notebooks/01_card_database_eda.ipynb` for the executable catalogue and
starter-deck audit.

## Card-reference PDF policy

The English Card ID PDF is a 1,306-page visual reference that maps simulator IDs
to card names, expansions, collection numbers, and images. Use the CSV for
programmatic analysis and join logic. Render only selected PDF pages when a card
image, printed layout, or special-rule presentation must be checked manually.
The Japanese PDF has identical content in another language and does not need a
separate analytical pass unless translation consistency becomes relevant.

Do not OCR or redistribute the full card-image corpus. Record sampled page
numbers and findings so visual checks remain reproducible and competition-only.
