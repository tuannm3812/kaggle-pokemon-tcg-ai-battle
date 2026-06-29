# Notebook Organization Plan

## Current decision

Keep the physical notebook directory flat.

Reason: Kaggle metadata files under `notebooks/metadata/` reference exact
notebook filenames through `code_file`, and builder scripts also emit notebooks
into the `notebooks/` root. Moving notebooks into subfolders would create a
higher risk of broken Kaggle pushes than the benefit of a cleaner tree.

## Implemented organization

Instead of moving notebooks, the repo now uses logical organization:

- `notebooks/README.md` separates active workflow notebooks from historical
  experiment notebooks;
- `notebooks/metadata/README.md` maps metadata files to notebook filenames;
- detailed experiment conclusions live under `docs/experiments/`;
- submission/package records live under `docs/submissions/`.

## Active notebooks

Use these for fresh work:

1. `01_card_database_eda.ipynb`
2. `02_agent_baseline_and_local_evaluation.ipynb`
3. `03_submission_packaging_and_validation.ipynb`

## Historical notebooks

Keep `04` through `12` as reproducible experiment history. Prefer local scripts
for new fast iteration unless a Kaggle runtime is required.

## Future cleanup rule

If we eventually move notebooks physically, do it in one dedicated commit that:

1. moves the notebook;
2. updates `notebooks/metadata/*.json` `code_file` values;
3. updates all builder output paths;
4. updates README/docs links;
5. validates notebook JSON and at least one Kaggle metadata push target.
