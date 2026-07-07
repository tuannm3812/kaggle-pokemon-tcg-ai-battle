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
| 9. Public meta snapshot | Which opponent archetypes currently matter most? | Matchup-priority backlog |
| 10. Loss timing EDA | Where do active-best losses lose tempo? | Candidate patch location |
| 11. Decision-signature EDA | Which repeated local decisions differ from stronger branches? | Minimal policy hypothesis |
| 12. Candidate brief | What exact change should be tested next? | Controlled experiment plan |

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

## Live public-meta EDA layer

After the first successful leaderboard submissions, EDA should no longer stop at
card catalogue and local simulator structure. The useful question becomes:
**which live public matchup slices are large enough, weak enough, and local
enough to justify a new candidate?**

As of the 2026-07-07 score check, the active-best submission remains
`kojimar_simple_baseline_v1` with public score `864.5`. Public episode analysis
shows the field is concentrated around several recurring families:

| Archetype family | Current signal | Strategy implication |
| --- | --- | --- |
| Lucario variants | Frequent; v1 handles them well | Preserve v1 behavior; regression here is disqualifying |
| Metal/Cinderace/Archaludon | Frequent and weak for v1 (`13-21` in cached public episodes) | Highest-value improvement target |
| Alakazam/Dunsparce | Persistent weakness across v1/v8/v5 | Improve only if the patch does not damage Lucario/Dragapult |
| Dragapult | Dangerous; v1 was strong while v8 collapsed | Do not import broad v8/v15 behavior blindly |
| Crustle/library-out | Important control slice; v8 was strong, v5 weak | Avoid overdraw and low-value wall attacks |
| Phantump/Trevenant | Small sample but dangerous | Watchlist until repeated local mistakes are isolated |

This makes `kojimar_simple_baseline_v1` the reference policy, not merely a
historical baseline. New candidates must show either stronger public-meta replay
evidence or no regression against the protected matchups: Lucario, Dragapult,
and library-out/control.

## Replay-derived loss timing EDA

The latest replay diagnosis for active-best submission `54303967` focused on
Metal/Cinderace and Alakazam/Dunsparce losses:

| Weak archetype | Loss episodes analyzed | Went first | Median first attack turn | Main read |
| --- | ---: | ---: | ---: | --- |
| Metal/Cinderace | 21 | 19/21 | 3 | Going first is strongly associated with losses, but simple opening rewrites are unsafe |
| Alakazam/Dunsparce | 9 | 4/9 | 4 | Losses are more mixed; likely midgame finish/target timing rather than only turn order |

Two candidate probes refined the interpretation:

| Candidate | Hypothesis | Result | Lesson |
| --- | --- | --- | --- |
| v16 meta target guard | Add narrow target bonuses for weak public families | Hold; slight gains but Lucario regression flag | Target-only patch is plausible but not proven |
| v17 setup Riolu pressure | Prefer Riolu active against visible Metal/Alakazam families | Rejected; regressed v5, Lucario, and library-out gates | Opening preference is too blunt |

The strategy EDA script then inspected turns 5-7 from the same public losses:

```powershell
python scripts/strategy_eda_from_loss_diagnostics.py --input scratch\loss_diagnostics\54303967_metal_cinderace-alakazam_dunsparce_losses.json --start-turn 5 --end-turn 7
```

| Archetype | Midgame rows | Boss in hand rows | Most common active | Key target signal |
| --- | ---: | ---: | --- | --- |
| Alakazam/Dunsparce | 138 | 70 | Mega Lucario ex | Alakazam, Dunsparce, Kadabra, Abra |
| Metal/Cinderace | 405 | 200 | Mega Lucario ex | Duraludon, Archaludon ex, Relicanth, Cinderace |

Therefore the next candidate should inspect **midgame conversion signatures**,
especially turns 5-7 after the opponent evolves into Archaludon ex, Kadabra, or
Alakazam. The current evidence does not support another broad setup-active,
turn-order, or energy-routing rewrite.

## Candidate strategy brief for v18

EDA should produce a candidate brief before any code change. The current brief is:

| Item | Decision |
| --- | --- |
| Base policy | Start from `kojimar_simple_baseline_v1` |
| Protected behavior | Lucario, Dragapult, Crustle/library-out |
| Primary target | Metal/Cinderace midgame turns 5-7 |
| Secondary target | Alakazam/Dunsparce midgame turns 5-7 |
| Allowed patch shape | Local attack/Boss/retreat scoring after evolved threats are visible |
| Disallowed patch shape | Global setup-active changes, global go-second changes, broad Boss guard |
| Promotion requirement | Public-meta gate must not flag Lucario/library-out regression |

A suitable v18 hypothesis would be:

> Preserve v1, but add a tiny midgame finish-pressure rule only when a visible
> Metal/Cinderace or Alakazam/Dunsparce target is already KO-able or near-KO, and
> only if the rule changes a repeated losing decision from public replay
> diagnostics.

This turns EDA into a testable strategy pipeline: **meta frequency -> weak
archetype -> replay timing -> repeated local decision -> smallest candidate
patch -> promotion gate**.

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
early development, not blind aggression, was the missing behavior.

The remaining episode-EDA gap is now more specific than generic opponent
diversity. For the next candidate cycle, prioritize:

- exact midgame board snapshots in losing public replays;
- whether Boss's Orders was available, used, or held;
- whether Mega Brave was legal but not selected;
- active and benched opponent HP after our attacks;
- whether low-HP Kadabra/Alakazam, Duraludon, or Archaludon survived one turn too long;
- whether a candidate changes only those repeated decisions while preserving protected matchups.

Future evidence can still include frozen stronger opponents, prize trajectories,
knockout timing, deck-out frequency, and revealed-card beliefs, but candidate
work should start with the repeated public-loss signatures above.

## Card-reference PDF policy

The 1,306-page English Card ID PDF maps simulator IDs to names, expansions,
collection numbers, and images. Use the CSV for programmatic joins. Render only
selected pages when card art, printed layout, or special-rule presentation must
be checked manually. The repository audit sampled pages 1, 2, 654, 1,305, and
1,306 from the 137.65 MB file.

Do not bulk-OCR or redistribute the card-image corpus. Record sampled pages and
findings so visual checks remain bounded and reproducible.
