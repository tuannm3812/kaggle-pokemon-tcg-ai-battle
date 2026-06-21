# Competition Instructions

Last verified against the official Kaggle pages: **21 June 2026**.

## Objective

Build an agent that plays the Pokémon Trading Card Game through the supplied
simulator. A submission contains a legal 60-card deck and a Python `agent`
function that selects valid option indices from each observation.

The core difficulty is sequential decision-making under hidden information.
The agent sees its own hand and public board state but not the opponent's hand.
Card draws and coin tosses introduce additional variance.

## Agent contract

On the first call, `obs.select` is `None`; return the 60 integer card IDs in the
deck. On subsequent calls, return a list of unique option indices satisfying:

```text
0 <= index < len(obs.select.option)
obs.select.minCount <= len(return_value) <= obs.select.maxCount
```

The official SDK may append enum members and dataclass attributes during the
competition. Code defensively and retain a legal fallback.

## Evaluation

- Each new agent first plays a validation episode against a copy of itself.
- Valid submissions enter a ladder and repeatedly play agents with similar
  ratings.
- Skill is represented by a Gaussian estimate `N(mu, sigma^2)`. Wins raise the
  estimate, losses lower it, and additional games reduce uncertainty.
- Draws move the two estimates toward their mean.
- Win margin does not affect rating updates.
- New agents receive games more frequently for faster initial feedback.
- The leaderboard displays the team's best scoring agent, while the
  submissions page tracks each active submission.

## Submission policy

Kaggle states that a team may submit up to five agents each day and only its
latest two submissions are tracked for final submissions. Treat those two
slots as scarce: keep one stable control and one candidate whenever possible.

After the submission deadline, new submissions are locked and games continue
for approximately two weeks before ratings become final.

## Important rule hygiene

- Join and accept the rules before using competition data or submitting.
- Use competition data and Pokémon elements only as permitted by the official
  rules. Restrictions extend to derived models and outputs outside the
  competition context.
- Do not redistribute supplied simulator binaries, card PDFs, or protected
  Pokémon assets in this public repository.
- Confirm team, external-data, licensing, winner-documentation, and eligibility
  clauses on the live rules page before relying on them; rules can change.

The authoritative sources are the Kaggle
[overview](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview),
[evaluation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/evaluation),
and [rules](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/rules)
pages.
