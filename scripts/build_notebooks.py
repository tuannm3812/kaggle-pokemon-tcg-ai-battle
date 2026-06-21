"""Generate the cleared, Kaggle-ready project notebooks."""

from pathlib import Path
import textwrap

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"


def md(value):
    return nbf.v4.new_markdown_cell(textwrap.dedent(value).strip())


def code(value):
    return nbf.v4.new_code_cell(textwrap.dedent(value).strip())


def save(name, cells):
    notebook = nbf.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
    )
    nbf.write(notebook, OUT / name)
    print(f"Wrote {name}: {len(cells)} cells")


EDA = [
    md("""
    # Card Database and Starter-Deck EDA

    **Purpose.** Audit the official English card catalogue and starter deck
    before changing either policy or deck construction.

    **Decision question.** Which card-pool and deck properties constrain our
    first agent experiments?

    This is a simulation competition: EDA means catalogue, deck, state-space,
    and episode analysisâ€”not train/test target exploration. Run with the
    `pokemon-tcg-ai-battle` competition data attached. A local `data/raw`
    fallback is supported.
    """),
    md("""
    ## 1. Configuration

    The input resolver avoids account-specific paths. We keep plots consistent
    and separate card identity from move-level records because one card can
    occupy several catalogue rows.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import re

    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    DATA_FILENAME = "EN_Card_Data.csv"
    sns.set_theme(style="whitegrid", palette="viridis")
    pd.set_option("display.max_columns", 50)

    def find_file(filename: str) -> Path:
        root = Path("/kaggle/input")
        matches = sorted(root.rglob(filename)) if root.exists() else []
        if matches:
            return matches[0]
        local = Path("../data/raw") / filename
        if local.exists():
            return local
        raise FileNotFoundError(
            f"Attach competition data or place {filename} in data/raw/."
        )

    card_path = find_file(DATA_FILENAME)
    print(f"Catalogue: {card_path}")
    """),
    md("""
    ## 2. Schema and representation audit

    We distinguish catalogue rows, unique card IDs, and cardâ€“move records.
    Structural missingness is expected: Energy and Trainer cards do not have
    PokÃ©mon HP or evolution fields.
    """),
    code("""
    raw = pd.read_csv(card_path)
    cards = raw.rename(columns=lambda x: re.sub(
        r"[^a-z0-9]+", "_", x.strip().lower()
    ).strip("_"))

    summary = pd.Series({
        "catalogue_rows": len(cards),
        "columns": cards.shape[1],
        "unique_card_ids": cards.card_id.nunique(),
        "exact_duplicate_rows": cards.duplicated().sum(),
    })
    display(summary.to_frame("value"))
    display(cards.head())

    quality = pd.DataFrame({
        "dtype": cards.dtypes.astype(str),
        "missing": cards.isna().sum(),
        "missing_pct": cards.isna().mean().mul(100).round(2),
        "unique": cards.nunique(dropna=True),
    }).sort_values("missing_pct", ascending=False)
    display(quality)
    """),
    md("""
    **Interpretation.** Do not globally impute the catalogue. Parse and analyze
    fields within relevant card categories, and use `Card ID` as the stable
    identity key. Names and move rows are not unique enough for policy logic.
    """),
    md("""
    ## 3. Card-pool composition

    Collapse identity fields to one record per card for composition plots.
    Attacks remain a separate one-to-many table for later action scoring.
    """),
    code("""
    category_col = "stage_pok_mon_type_energy_and_trainer"
    identity = [
        "card_id", "card_name", "expansion", category_col, "rule", "category",
        "previous_stage", "hp", "type", "weakness", "resistance_type", "retreat",
    ]
    identity = [column for column in identity if column in cards]
    unique_cards = cards[identity].groupby("card_id", as_index=False).first()

    counts = unique_cards[category_col].fillna("Missing").value_counts().head(15)
    ax = counts.sort_values().plot.barh(
        figsize=(10, 6), color=sns.color_palette("viridis", len(counts))
    )
    ax.set(title="Largest card categories", xlabel="Unique cards", ylabel="Category")
    plt.tight_layout()
    plt.show()

    unique_cards["hp_numeric"] = pd.to_numeric(unique_cards.hp, errors="coerce")
    unique_cards["retreat_numeric"] = pd.to_numeric(unique_cards.retreat, errors="coerce")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    sns.histplot(unique_cards.hp_numeric.dropna(), bins=30, ax=axes[0])
    axes[0].set_title("Printed HP distribution")
    sns.countplot(x=unique_cards.retreat_numeric, ax=axes[1], color="#2a788e")
    axes[1].set_title("Retreat-cost distribution")
    plt.tight_layout()
    plt.show()
    """),
    md("""
    **Interpretation.** Catalogue frequency is descriptive, not a deck recipe.
    Deck strength depends on legal counts, evolution support, energy curve,
    interactions, and whether the policy can sequence them correctly.
    """),
    md("""
    ## 4. Starter-deck audit

    Basic Energy can exceed the ordinary four-copy heuristic. We flag other
    large counts for review rather than claiming that a simplified check is the
    official legality test. The simulator start result remains authoritative.
    """),
    code("""
    def find_deck() -> Path:
        candidates = [Path("../agent/deck.csv"), Path("agent/deck.csv")]
        candidates += sorted(Path("/kaggle/input").rglob("sample_submission/deck.csv"))
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError("Could not find a repository or official starter deck.")

    deck_path = find_deck()
    deck = [int(x) for x in deck_path.read_text().splitlines() if x.strip()]
    deck_counts = pd.Series(Counter(deck), name="copies").rename_axis("card_id").reset_index()
    columns = ["card_id", "card_name", category_col, "hp", "retreat"]
    deck_view = deck_counts.merge(unique_cards[columns], on="card_id", how="left")
    deck_view = deck_view.sort_values(["copies", "card_id"], ascending=[False, True])

    print(f"Deck: {deck_path}")
    print(f"Cards: {len(deck)}; unique IDs: {len(deck_counts)}")
    display(deck_view)
    assert len(deck) == 60, "Submission decks require exactly 60 cards."
    assert deck_view.card_name.notna().all(), "All deck IDs must exist in the catalogue."

    basic_energy = deck_view[category_col].fillna("").str.contains(
        "Basic Energy", case=False, regex=False
    )
    print("Non-Basic-Energy entries above four copies (manual review):")
    display(deck_view[(deck_view.copies > 4) & ~basic_energy])
    """),
    md("""
    ## 5. Findings and next experiment

    - Preserve card ID as the stable join key.
    - Separate card identity from attacks before creating value tables.
    - Interpret missingness by category.
    - Use simulator initialization as the final executable deck check.
    - Next, run the deterministic baseline and capture context telemetry.

    **Limitation.** Printed card data does not reveal strategic synergy or
    opponent prevalence. Those require controlled episode evidence.
    """),
]


EVALUATION = [
    md("""
    # Deterministic Baseline and Local Evaluation

    **Purpose.** Install the official simulator into Kaggle working storage,
    load the version-controlled policy, and run legality-first self-play.

    **Decision question.** Does this candidate execute reliably enough to
    become a frozen control? Attach the competition data and a private dataset
    containing this repository's `agent/` directory. Internet is unnecessary.
    """),
    md("""
    ## 1. Configuration

    A small smoke test catches API and packaging faults; it does not estimate
    ladder strength. Increase volume only after all games terminate cleanly.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import importlib.util
    import json
    import shutil
    import sys
    import time

    import pandas as pd

    N_GAMES = 4
    MAX_DECISIONS = 10_000
    WORK_DIR = Path("/kaggle/working/agent_eval")
    """),
    code("""
    def first_match(pattern: str) -> Path:
        matches = sorted(Path("/kaggle/input").rglob(pattern))
        if not matches:
            raise FileNotFoundError(f"No Kaggle input matched {pattern}")
        return matches[0]

    sample_dir = first_match("sample_submission/main.py").parent
    candidates = [Path("../agent"), Path("agent")]
    candidates += [x.parent for x in sorted(Path("/kaggle/input").rglob("main.py")) if "sample_submission" not in x.parts and "cg" not in x.parts]
    repo_agent = next(
        (x for x in candidates if (x / "main.py").exists() and (x / "deck.csv").exists()),
        None,
    )
    print(f"Official sample: {sample_dir}")
    print(f"Repository agent: {repo_agent or 'not mounted; using official sample'}")
    """),
    md("""
    ## 2. Build an isolated environment

    Copy the complete `cg` directory: its Python wrapper loads a platform
    shared library. The disposable working directory is never the source of
    truth for policy code.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    if repo_agent:
        shutil.copy2(repo_agent / "main.py", WORK_DIR / "main.py")
        shutil.copy2(repo_agent / "deck.csv", WORK_DIR / "deck.csv")

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import to_observation_class
    from cg.game import battle_finish, battle_select, battle_start

    spec = importlib.util.spec_from_file_location("candidate", WORK_DIR / "main.py")
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    deck = candidate.read_deck_csv()
    assert len(deck) == 60
    """),
    md("""
    ## 3. Legality shield and game runner

    Validate each action before it reaches the simulator. Failures remain in
    the reportâ€”discarding them would produce a falsely optimistic estimate.
    """),
    code("""
    def validate_action(obs_dict: dict, action: list[int]) -> None:
        obs = to_observation_class(obs_dict)
        if obs.select is None:
            assert len(action) == 60
            return
        assert isinstance(action, list)
        assert all(isinstance(index, int) for index in action)
        assert len(action) == len(set(action))
        assert obs.select.minCount <= len(action) <= obs.select.maxCount
        assert all(0 <= index < len(obs.select.option) for index in action)

    def play_game() -> dict:
        started, decisions, contexts = time.perf_counter(), 0, Counter()
        try:
            obs_dict, start = battle_start(deck, deck)
            if obs_dict is None:
                return {"status": "start_error", "error_player": start.errorPlayer,
                        "error_type": start.errorType}
            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                if obs.current is not None and obs.current.result != -1:
                    return {"status": "finished", "winner": obs.current.result,
                            "turn": obs.current.turn, "decisions": decisions,
                            "seconds": time.perf_counter() - started,
                            "contexts": dict(contexts)}
                contexts[str(getattr(obs.select, "context", "none"))] += 1
                action = candidate.agent(obs_dict)
                validate_action(obs_dict, action)
                obs_dict = battle_select(action)
                decisions += 1
            return {"status": "decision_limit", "decisions": decisions}
        except Exception as error:
            return {"status": "exception", "error": f"{type(error).__name__}: {error}",
                    "decisions": decisions}
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    The current wrapper does not expose a random seed. Repeated self-play tests
    execution, but exact seed pairing should be added if a future SDK exposes a
    supported hook. For candidate comparisons, alternate policies by
    `obs.current.yourIndex` and swap seats.
    """),
    code("""
    results = []
    for game in range(N_GAMES):
        result = play_game()
        result["game"] = game
        results.append(result)
        print(result)

    results_df = pd.DataFrame(results)
    display(results_df)
    display(results_df.status.value_counts().rename("games").to_frame())
    failures = results_df[results_df.status != "finished"]
    print("PASS: contract smoke test" if failures.empty else "NOT READY: inspect failures")
    display(failures)
    Path("/kaggle/working/baseline_smoke_results.json").write_text(
        json.dumps(results, indent=2, default=str)
    )
    """),
    md("""
    ## 4. Interpretation and next experiment

    Self-play balance is not a strength estimate. A frozen baseline requires
    zero start errors, illegal actions, exceptions, and stalls. The first
    competitive candidate should change one ideaâ€”attack ranking by knockout
    and damageâ€”then face frozen opponents across both seats. Report wins,
    draws, losses, failure rate, and uncertainty before using a ladder slot.
    """),
]


PACKAGING = [
    md("""
    # Submission Packaging and Validation

    **Purpose.** Create a clean agent archive from the official runtime and the
    reviewed repository policy/deck.

    **Decision question.** Is this exact artifact structurally safe and
    traceable? This notebook deliberately does not submit automatically; a
    human decides whether the evidence deserves one of the latest two slots.
    """),
    md("""
    ## 1. Discover clean sources

    `main.py` and `deck.csv` must sit at the ZIP root, with the complete SDK in
    `cg/`. Never package a stale evaluation directory.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import ast
    import hashlib
    import json
    import shutil
    import zipfile

    PACKAGE_DIR = Path("/kaggle/working/submission_agent")
    ARCHIVE = Path("/kaggle/working/submission.zip")

    sample = sorted(Path("/kaggle/input").rglob("sample_submission/main.py"))[0].parent
    candidates = [Path("../agent"), Path("agent")]
    candidates += [x.parent for x in sorted(Path("/kaggle/input").rglob("main.py")) if "sample_submission" not in x.parts and "cg" not in x.parts]
    repo_agent = next(
        (x for x in candidates if (x / "main.py").exists() and (x / "deck.csv").exists()),
        None,
    )
    if repo_agent is None:
        raise FileNotFoundError("Attach a private dataset containing this repo's agent/ directory.")
    print(f"Official runtime: {sample}")
    print(f"Reviewed agent: {repo_agent}")
    """),
    md("""
    ## 2. Assemble and statically validate

    Start empty so experiment residue cannot leak into the archive. The live
    Kaggle validation episode remains authoritative, but syntax, structure,
    deck length, and corrupt-ZIP errors are cheaper to catch here.
    """),
    code("""
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)
    shutil.copytree(sample / "cg", PACKAGE_DIR / "cg")
    shutil.copy2(repo_agent / "main.py", PACKAGE_DIR / "main.py")
    shutil.copy2(repo_agent / "deck.csv", PACKAGE_DIR / "deck.csv")

    source = (PACKAGE_DIR / "main.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "agent" in names, "main.py must define agent(obs_dict)."

    deck = [int(x) for x in (PACKAGE_DIR / "deck.csv").read_text().splitlines() if x.strip()]
    assert len(deck) == 60, f"Expected 60 cards, found {len(deck)}."
    display(Counter(deck).most_common())

    required = ["main.py", "deck.csv", "cg/__init__.py", "cg/api.py", "cg/game.py", "cg/sim.py"]
    missing = [x for x in required if not (PACKAGE_DIR / x).exists()]
    assert not missing, f"Missing files: {missing}"
    """),
    md("""
    ## 3. Hash and package the exact artifact

    Hashes link ladder results to immutable code and deck content. Archive paths
    are relative to staging so no accidental parent folder is introduced.
    """),
    code("""
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()

    manifest = {
        "main_sha256": sha256(PACKAGE_DIR / "main.py"),
        "deck_sha256": sha256(PACKAGE_DIR / "deck.csv"),
        "files": sorted(str(x.relative_to(PACKAGE_DIR)).replace("\\\\", "/")
                        for x in PACKAGE_DIR.rglob("*") if x.is_file()),
    }
    Path("/kaggle/working/submission_manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )
    display(manifest)

    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE_DIR))
    with zipfile.ZipFile(ARCHIVE) as archive:
        members, bad = archive.namelist(), archive.testzip()
    assert bad is None
    assert "main.py" in members and "deck.csv" in members
    assert any(x.startswith("cg/") for x in members)
    assert not any(x.startswith("submission_agent/") for x in members)
    print(f"Archive: {ARCHIVE} ({ARCHIVE.stat().st_size / 1e6:.2f} MB)")
    print("\\n".join(members))
    """),
    md("""
    ## 4. Submission gate

    Upload only after the evaluation notebook passes, paired evidence beats the
    frozen control, hashes are copied to the experiment ledger, current rules
    are rechecked, and replacing one of the latest two tracked agents is
    intentional. After upload, wait for validation. On failure, download the
    agent log and diagnose this exact hash rather than making an unrecorded edit.
    """),
]


OUT.mkdir(parents=True, exist_ok=True)
save("01_card_database_eda.ipynb", EDA)
save("02_agent_baseline_and_local_evaluation.ipynb", EVALUATION)
save("03_submission_packaging_and_validation.ipynb", PACKAGING)
