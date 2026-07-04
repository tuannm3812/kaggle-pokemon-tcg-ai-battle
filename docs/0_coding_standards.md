# Coding and Research Standards

## Scope

This repository supports both Kaggle notebooks and local script-driven
iteration. Stable Kaggle notebooks live under `notebooks/`; fast evaluator,
packaging, and tracing workflows live under `scripts/`. Candidate agents live in
`candidates/` as self-contained `main.py` plus `deck.csv` packages.

## Python

- Follow PEP 8 and use four-space indentation.
- Add type hints and concise docstrings to reusable functions.
- Keep the policy deterministic unless an experiment explicitly studies
  stochastic search.
- Never depend on option ordering without documenting the assumption.
- Validate every returned action: indices must be unique, in range, and the
  count must fall between `minCount` and `maxCount`.
- Treat new enum values and new observation fields as expected SDK evolution.
  Prefer safe fallbacks over exhaustive `match` statements that can crash.

## Notebooks

Every committed notebook must contain:

1. purpose and decision question;
2. assumptions and Kaggle execution notes;
3. one configuration cell near the top;
4. small, named functions instead of long procedural cells;
5. interpretation markdown after important outputs;
6. a conclusion with findings, limitations, and the next experiment;
7. cleared outputs and no embedded credentials.

Notebook code must resolve inputs in this order: attached Kaggle competition
data, then the documented local fallback. Paths must not depend on a particular
Kaggle username.

## Evaluation discipline

- Compare a candidate against a frozen baseline.
- Swap player positions for every seed.
- Report wins, draws, losses, score rate, and a confidence interval.
- Preserve failures as losses in the report; do not silently discard them.
- Use enough games for the decision being made. A smoke test proves execution,
  not strength.
- Change one strategic idea per candidate whenever practical.

## Documentation

- Lead with the implication, then provide evidence.
- Separate confirmed competition facts from hypotheses.
- Timestamp mutable facts such as deadlines and submission limits.
- Link to official Kaggle pages and repository-relative artifacts.
- Do not copy the full competition rules into the repo; summarize them and
  direct readers to the authoritative page.

## Git and security

Do not commit Kaggle credentials, competition binaries, card PDFs, generated
archives, logs, or raw downloads. Before committing, run:

```powershell
git status --short
git diff --check
```


## Change-based commit and push workflow

Commits must describe a coherent behavior or documentation change, not merely
the files that happened to change. Use this sequence:

1. Inspect `git status --short` and review every staged path.
2. Rebuild generated notebooks whenever `scripts/build_notebooks.py` changes.
3. Run checks proportional to the change:
   - function or policy changes: compile source, validate action contracts, and
     run at least one complete simulator game;
   - notebook changes: validate notebook JSON, compile every code cell, and run
     the affected notebook on Kaggle when mounted inputs or runtime matter;
   - documentation-only changes: verify relative links and factual dates.
4. Stage only the coherent change. Never stage credentials, raw competition
   data, downloaded binaries, executed notebooks, or submissions.
5. Use an imperative Conventional Commit subject, for example:
   `feat(agent): rank legal main-phase actions deterministically`.
6. Record material validation and known limitations in the commit body. Never
   claim a Kaggle run passed until its status and output have been checked.
7. Run `git diff --cached --check` and `git diff --cached --stat` before commit.
8. Push without force and confirm the commit exists on the expected branch.

Prefer one commit per coherent function-level change. Closely coupled generated
notebooks and their builder belong together; unrelated experiments do not.
Amend or force-push only with explicit approval when shared history exists.
