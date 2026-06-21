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
    and episode analysis?not train/test target exploration. Run with the
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

    We distinguish catalogue rows, unique card IDs, and card?move records.
    Structural missingness is expected: Energy and Trainer cards do not have
    Pok?mon HP or evolution fields.
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
    ## 5. Move structure and deck readiness

    The first Kaggle run confirmed a 60-card starter deck with only nine unique
    IDs. That concentration makes aggregate catalogue plots insufficient: we
    need to inspect the attacks, energy requirements, evolution support, and
    retreat burden of cards the baseline can actually draw.
    """),
    code("""
    move_columns = [
        "card_id", "card_name", "move_name", "cost", "damage",
        "effect_explanation",
    ]
    moves = cards[[column for column in move_columns if column in cards]].copy()
    moves = moves[moves.move_name.notna()].copy()
    moves["printed_damage"] = pd.to_numeric(moves.damage, errors="coerce")
    moves["damage_floor"] = pd.to_numeric(
        moves.damage.astype(str).str.extract(r"(\d+)")[0], errors="coerce"
    )
    moves["energy_symbols"] = moves.cost.fillna("").str.count(r"\{[^}]+\}")
    moves["variable_damage"] = moves.damage.notna() & moves.printed_damage.isna()

    deck_moves = moves[moves.card_id.isin(deck_counts.card_id)].merge(
        deck_counts, on="card_id", how="left"
    ).sort_values(["copies", "card_id", "move_name"], ascending=[False, True, True])
    display(deck_moves[
        ["card_id", "card_name", "copies", "move_name", "cost", "damage",
         "energy_symbols", "variable_damage"]
    ])

    deck_detail = deck_view.copy()
    deck_detail["weighted_retreat"] = (
        pd.to_numeric(deck_detail.retreat, errors="coerce").fillna(0)
        * deck_detail.copies
    )
    deck_summary = pd.Series({
        "cards": len(deck),
        "unique_ids": len(deck_counts),
        "basic_energy_cards": int(deck_view.loc[basic_energy, "copies"].sum()),
        "non_energy_cards": int(deck_view.loc[~basic_energy, "copies"].sum()),
        "deck_moves": len(deck_moves),
        "variable_damage_moves": int(deck_moves.variable_damage.sum()),
        "weighted_retreat_cost": float(deck_detail.weighted_retreat.sum()),
    })
    display(deck_summary.to_frame("value"))
    """),
    code("""
    import json

    output = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path(".")
    eda_summary = {
        "catalogue_rows": int(len(cards)),
        "unique_card_ids": int(cards.card_id.nunique()),
        "deck": {key: float(value) for key, value in deck_summary.items()},
        "deck_card_ids": {str(int(row.card_id)): int(row.copies)
                          for row in deck_counts.itertuples()},
    }
    (output / "card_eda_summary.json").write_text(
        json.dumps(eda_summary, indent=2)
    )
    print(f"Saved summary to {output / 'card_eda_summary.json'}")
    """),
    md("""
    ## 6. Card-reference PDF audit

    The official English PDF is a visual lookup from simulator card ID to card
    name, expansion, collection number, and card image. The CSV remains the
    computational source of truth; bulk OCR would be slower, noisier, and would
    unnecessarily reproduce protected card content.

    A repository audit of the 137.7 MB English document found 1,306 pages and
    rendered pages 1, 2, 654, 1,305, and 1,306 for structural sampling. Set
    `RUN_PDF_RENDER = True` only when a human needs to resolve a visual ambiguity.
    """),
    code("""
    RUN_PDF_RENDER = False
    PDF_SAMPLE_PAGES = (1, 2, 654, 1305, 1306)
    pdf_candidates = sorted(Path("/kaggle/input").rglob("*List_EN.pdf"))
    if not pdf_candidates:
        pdf_candidates = sorted(Path("../tmp/pdfs").glob("*.pdf"))
    pdf_path = pdf_candidates[0] if pdf_candidates else None

    pdf_audit = {
        "role": "visual card-ID reference; CSV is the analysis source",
        "observed_pages": 1306,
        "sampled_pages": list(PDF_SAMPLE_PAGES),
        "file_found": pdf_path is not None,
        "size_mb": round(pdf_path.stat().st_size / 1_000_000, 2) if pdf_path else None,
    }
    display(pd.Series(pdf_audit).to_frame("value"))

    if RUN_PDF_RENDER:
        import fitz
        from IPython.display import display as display_image
        from PIL import Image

        if pdf_path is None:
            raise FileNotFoundError("Attach the English Card ID PDF before rendering.")
        document = fitz.open(pdf_path)
        assert document.page_count == pdf_audit["observed_pages"]
        for page_number in PDF_SAMPLE_PAGES:
            page = document[page_number - 1]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.75, 0.75), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            print(f"Reference page {page_number}")
            display_image(image)
    else:
        print("PDF rendering skipped by default; enable only for targeted visual review.")

    eda_summary["pdf_reference"] = pdf_audit
    (output / "card_eda_summary.json").write_text(json.dumps(eda_summary, indent=2))
    """),
    md("""
    ## 7. Findings and next experiment

    - Preserve card ID as the stable join key.
    - Separate card identity from attacks before creating value tables.
    - Interpret missingness by category.
    - Use simulator initialization as the final executable deck check.
    - Use deck-specific move summaries to design action scorers.
    - Next, run comparative evaluation and capture named context telemetry.

    **Limitation.** Printed card data does not reveal strategic synergy or
    opponent prevalence. Those require controlled episode evidence.
    """),
]


EVALUATION = [
    md("""
    # Baseline Reliability and Comparative Evaluation

    **Purpose.** Validate the repository policy against the official simulator,
    then compare it with Kaggle's random sample policy across both player seats.

    **Decision question.** Is the deterministic policy reliable, and does it
    provide measurable improvement over the official control? This is an
    offline screening result, not a ladder-rating estimate.
    """),
    md("""
    ## 1. Configuration and reproducibility limits

    The previous run completed four self-play games but exposed only numeric
    context IDs and no control comparison. This revision records named decision
    contexts and action types, retains every failure, and balances candidate
    games across both seats.

    Python's random policy is seeded. The current simulator wrapper does not
    expose its internal card-draw or coin-toss seed, so seat-balanced games are
    independent repetitions rather than exact paired seeds.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import importlib.util
    import json
    import random
    import shutil
    import sys
    import time

    import numpy as np
    import pandas as pd

    CONTRACT_GAMES = 4
    GAMES_PER_SEAT = 20
    MAX_DECISIONS = 10_000
    BASE_SEED = 42
    BOOTSTRAP_SAMPLES = 10_000
    WORK_DIR = Path("/kaggle/working/agent_eval")
    """),
    code("""
    def first_match(pattern: str) -> Path:
        matches = sorted(Path("/kaggle/input").rglob(pattern))
        if not matches:
            raise FileNotFoundError(f"No Kaggle input matched {pattern}")
        return matches[0]

    def load_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sample_dir = first_match("sample_submission/main.py").parent
    candidates = [Path("../agent"), Path("agent")]
    candidates += [
        path.parent for path in sorted(Path("/kaggle/input").rglob("main.py"))
        if "sample_submission" not in path.parts and "cg" not in path.parts
    ]
    repo_agent = next(
        (path for path in candidates
         if (path / "main.py").exists() and (path / "deck.csv").exists()),
        None,
    )
    if repo_agent is None:
        raise FileNotFoundError("Attach the private agent-source dataset.")
    print(f"Official control: {sample_dir / 'main.py'}")
    print(f"Candidate: {repo_agent / 'main.py'}")
    """),
    md("""
    ## 2. Isolated simulator and policies

    The complete official `cg` directory is copied into working storage. The
    candidate and control are loaded as separate modules, while both use the
    same reviewed 60-card deck so this experiment isolates policy behavior.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    shutil.copy2(repo_agent / "main.py", WORK_DIR / "candidate_main.py")
    shutil.copy2(repo_agent / "deck.csv", WORK_DIR / "deck.csv")

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import OptionType, SelectContext, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start

    candidate = load_module("candidate_policy", WORK_DIR / "candidate_main.py")
    control = load_module("official_random_policy", sample_dir / "main.py")
    deck = candidate.read_deck_csv()
    assert len(deck) == 60
    """),
    md("""
    ## 3. Instrumented game runner

    Every action is checked before the simulator receives it. Telemetry uses
    enum names rather than opaque integers, making high-frequency decision
    bottlenecks immediately visible. Exceptions and decision-limit stalls are
    preserved as failed games.
    """),
    code("""
    def enum_name(enum_class, value) -> str:
        try:
            return enum_class(value).name
        except (ValueError, TypeError):
            return f"UNKNOWN_{value}"

    def validate_action(obs, action: list[int]) -> None:
        select = obs.select
        assert isinstance(action, list)
        assert all(isinstance(index, int) for index in action)
        assert len(action) == len(set(action))
        assert select.minCount <= len(action) <= select.maxCount
        assert all(0 <= index < len(select.option) for index in action)

    def play_game(
        policies: dict[int, object],
        game_id: int,
        candidate_player: int | None,
        experiment: str,
    ) -> dict:
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions = 0
        contexts, actions = Counter(), Counter()
        role_contexts, role_actions = Counter(), Counter()
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return {
                    "status": "start_error", "experiment": experiment,
                    "game": game_id, "candidate_player": candidate_player,
                    "error_player": start_data.errorPlayer,
                    "error_type": start_data.errorType,
                }
            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                if obs.current is not None and obs.current.result != -1:
                    winner = int(obs.current.result)
                    if candidate_player is None:
                        candidate_score = None
                    elif winner == candidate_player:
                        candidate_score = 1.0
                    elif winner in (0, 1):
                        candidate_score = 0.0
                    else:
                        candidate_score = 0.5
                    return {
                        "status": "finished", "experiment": experiment,
                        "game": game_id, "candidate_player": candidate_player,
                        "winner": winner, "candidate_score": candidate_score,
                        "turn": int(obs.current.turn), "decisions": decisions,
                        "seconds": time.perf_counter() - started,
                        "contexts": dict(contexts), "actions": dict(actions),
                        "role_contexts": dict(role_contexts),
                        "role_actions": dict(role_actions),
                    }
                player = int(obs.current.yourIndex)
                role = (
                    "candidate"
                    if candidate_player is None or player == candidate_player
                    else "control"
                )
                context_name = enum_name(SelectContext, obs.select.context)
                contexts[context_name] += 1
                role_contexts[f"{role}:{context_name}"] += 1
                action = policies[player].agent(obs_dict)
                validate_action(obs, action)
                for index in action:
                    action_name = enum_name(OptionType, obs.select.option[index].type)
                    actions[action_name] += 1
                    role_actions[f"{role}:{action_name}"] += 1
                obs_dict = battle_select(action)
                decisions += 1
            return {
                "status": "decision_limit", "experiment": experiment,
                "game": game_id, "candidate_player": candidate_player,
                "decisions": decisions,
            }
        except Exception as error:
            return {
                "status": "exception", "experiment": experiment,
                "game": game_id, "candidate_player": candidate_player,
                "error": f"{type(error).__name__}: {error}",
                "decisions": decisions,
            }
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    ## 4. Contract smoke test

    Candidate-versus-candidate games test deck initialization, action legality,
    termination, and runtime. They do not measure strength.
    """),
    code("""
    contract_results = [
        play_game({0: candidate, 1: candidate}, game, None, "contract_self_play")
        for game in range(CONTRACT_GAMES)
    ]
    contract_df = pd.DataFrame(contract_results)
    display(contract_df.drop(
        columns=["contexts", "actions", "role_contexts", "role_actions"],
        errors="ignore",
    ))
    contract_failures = contract_df[contract_df.status != "finished"]
    assert contract_failures.empty, contract_failures.to_dict("records")
    print(f"PASS: {len(contract_df)}/{len(contract_df)} contract games finished")
    """),
    md("""
    ## 5. Candidate versus official random control

    The candidate plays an equal number of games as player 0 and player 1.
    A bootstrap interval summarizes game-level uncertainty. Because simulator
    seeds are unavailable, treat this as a screening estimate rather than a
    paired causal measurement.
    """),
    code("""
    matchup_results = []
    game_id = 10_000
    for candidate_player in (0, 1):
        for repetition in range(GAMES_PER_SEAT):
            policies = {
                candidate_player: candidate,
                1 - candidate_player: control,
            }
            matchup_results.append(play_game(
                policies, game_id, candidate_player, "candidate_vs_random"
            ))
            game_id += 1

    matchup_df = pd.DataFrame(matchup_results)
    display(matchup_df.drop(
        columns=["contexts", "actions", "role_contexts", "role_actions"],
        errors="ignore",
    ))
    failures = matchup_df[matchup_df.status != "finished"]
    finished = matchup_df[matchup_df.status == "finished"].copy()
    assert failures.empty, failures.to_dict("records")

    scores = finished.candidate_score.to_numpy(dtype=float)
    rng = np.random.default_rng(BASE_SEED)
    bootstrap_means = rng.choice(
        scores, size=(BOOTSTRAP_SAMPLES, len(scores)), replace=True
    ).mean(axis=1)
    ci_low, ci_high = np.quantile(bootstrap_means, [0.025, 0.975])
    wins = int((scores == 1.0).sum())
    draws = int((scores == 0.5).sum())
    losses = int((scores == 0.0).sum())
    summary = {
        "games": len(finished), "wins": wins, "draws": draws, "losses": losses,
        "score_rate": float(scores.mean()),
        "bootstrap_95_low": float(ci_low), "bootstrap_95_high": float(ci_high),
        "failures": len(failures),
    }
    if len(failures):
        decision = "REJECT: runtime failures observed"
    elif ci_high < 0.5:
        decision = "REJECT: candidate is worse than random control"
    elif ci_low > 0.5:
        decision = "PASS SCREEN: evaluate against stronger frozen controls"
    else:
        decision = "HOLD: interval overlaps parity"
    summary["decision"] = decision
    display(pd.Series(summary).to_frame("value"))
    print(f"Promotion decision: {decision}")
    display(finished.groupby("candidate_player").candidate_score.agg(
        games="size", score_rate="mean"
    ))
    """),
    md("""
    ## 6. Decision-context and action telemetry

    The first run spent most decisions in context `0`, which was unreadable.
    Named aggregation below shows where future heuristics or search can affect
    the largest share of decisions and which actions the policy actually uses.
    """),
    code("""
    context_counts, action_counts = Counter(), Counter()
    role_context_counts, role_action_counts = Counter(), Counter()
    for row in contract_results + matchup_results:
        context_counts.update(row.get("contexts", {}))
        action_counts.update(row.get("actions", {}))
        role_context_counts.update(row.get("role_contexts", {}))
        role_action_counts.update(row.get("role_actions", {}))

    context_df = pd.Series(context_counts, name="decisions").sort_values(ascending=False).to_frame()
    action_df = pd.Series(action_counts, name="selections").sort_values(ascending=False).to_frame()
    display(context_df)
    display(action_df)

    role_action_rows = [
        {"role": key.split(":", 1)[0], "action": key.split(":", 1)[1],
         "selections": value}
        for key, value in role_action_counts.items()
    ]
    role_context_rows = [
        {"role": key.split(":", 1)[0], "context": key.split(":", 1)[1],
         "decisions": value}
        for key, value in role_context_counts.items()
    ]
    role_action_df = pd.DataFrame(role_action_rows).pivot_table(
        index="action", columns="role", values="selections", fill_value=0
    ).sort_values("candidate", ascending=False)
    role_context_df = pd.DataFrame(role_context_rows).pivot_table(
        index="context", columns="role", values="decisions", fill_value=0
    ).sort_values("candidate", ascending=False)
    display(role_action_df)
    display(role_context_df)
    display(finished[["turn", "decisions", "seconds"]].describe().T)

    output = Path("/kaggle/working")
    payload = {
        "configuration": {
            "contract_games": CONTRACT_GAMES,
            "games_per_seat": GAMES_PER_SEAT,
            "simulator_seed_exposed": False,
        },
        "summary": summary,
        "context_counts": dict(context_counts),
        "action_counts": dict(action_counts),
        "role_context_counts": dict(role_context_counts),
        "role_action_counts": dict(role_action_counts),
        "contract_results": contract_results,
        "matchup_results": matchup_results,
    }
    (output / "agent_evaluation_results.json").write_text(
        json.dumps(payload, indent=2, default=str)
    )
    print(f"Saved evaluation evidence to {output / 'agent_evaluation_results.json'}")
    """),
    md("""
    ## 7. Promotion decision

    Reliability is mandatory. Strength promotion additionally requires a score
    rate above 0.5 with an uncertainty interval that is useful for the decision,
    no material seat collapse, and zero runtime failures. This random-policy
    comparison is only the first control; the next notebook version should add
    frozen historical and strategy-diverse opponents before a ladder submission.
    """),
]


PACKAGING = [
    md("""
    # Submission Packaging and Runtime Validation

    **Purpose.** Build a clean agent archive, execute the staged package with
    the official simulator, and emit a traceable manifest.

    **Decision question.** Does the exact tar.gz candidate import, locate its deck,
    select legal actions, finish a game, and preserve the required root layout?

    The previous packaging run verified structure but did not execute staged
    `main.py`; that gap allowed a working-directory deck-path defect to escape.
    This revision makes runtime smoke validation part of packaging itself.
    """),
    md("""
    ## 1. Discover immutable inputs

    Simulator files come only from the attached competition data. Reviewed
    policy and deck files come from the private agent-source dataset. The
    staging directory is recreated from scratch on every run.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import ast
    import hashlib
    import importlib.util
    import json
    import shutil
    import sys
    import time
    import tarfile

    import pandas as pd

    PACKAGE_DIR = Path("/kaggle/working/submission_agent")
    ARCHIVE = Path("/kaggle/working/submission.tar.gz")
    MANIFEST_PATH = Path("/kaggle/working/submission_manifest.json")
    MAX_DECISIONS = 10_000

    sample = sorted(Path("/kaggle/input").rglob("sample_submission/main.py"))[0].parent
    candidates = [Path("../agent"), Path("agent")]
    candidates += [
        path.parent for path in sorted(Path("/kaggle/input").rglob("main.py"))
        if "sample_submission" not in path.parts and "cg" not in path.parts
    ]
    repo_agent = next(
        (path for path in candidates
         if (path / "main.py").exists() and (path / "deck.csv").exists()),
        None,
    )
    if repo_agent is None:
        raise FileNotFoundError("Attach the private agent-source dataset.")
    print(f"Official runtime: {sample}")
    print(f"Reviewed agent: {repo_agent}")
    """),
    md("""
    ## 2. Assemble and statically validate

    Static checks reject syntax errors, missing entrypoints, malformed deck
    length, incomplete SDK copies, and unexpected source locations before the
    more expensive simulator test.
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

    deck = [
        int(value) for value in (PACKAGE_DIR / "deck.csv").read_text().splitlines()
        if value.strip()
    ]
    assert len(deck) == 60, f"Expected 60 cards, found {len(deck)}."
    display(pd.Series(Counter(deck), name="copies").rename_axis("card_id").to_frame())

    required = {
        "main.py", "deck.csv", "cg/__init__.py", "cg/api.py", "cg/game.py",
        "cg/sim.py", "cg/utils.py", "cg/cg.dll", "cg/libcg.so",
    }
    staged = {
        str(path.relative_to(PACKAGE_DIR)).replace("\\\\", "/")
        for path in PACKAGE_DIR.rglob("*") if path.is_file()
    }
    assert required <= staged, f"Missing required files: {sorted(required - staged)}"
    """),
    md("""
    ## 3. Execute the staged package

    Import `main.py` from staging, not from the source dataset, and run one full
    legality-checked self-play game. This specifically verifies module-relative
    deck discovery and the Linux shared library used by Kaggle.
    """),
    code("""
    sys.path.insert(0, str(PACKAGE_DIR))
    spec = importlib.util.spec_from_file_location("staged_agent", PACKAGE_DIR / "main.py")
    staged_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(staged_agent)

    from cg.api import to_observation_class
    from cg.game import battle_finish, battle_select, battle_start

    staged_deck = staged_agent.read_deck_csv()
    assert staged_deck == deck
    started = time.perf_counter()
    decisions = 0
    try:
        obs_dict, start_data = battle_start(staged_deck, staged_deck)
        assert obs_dict is not None, {
            "error_player": start_data.errorPlayer,
            "error_type": start_data.errorType,
        }
        while decisions < MAX_DECISIONS:
            obs = to_observation_class(obs_dict)
            if obs.current is not None and obs.current.result != -1:
                runtime_smoke = {
                    "status": "finished", "winner": int(obs.current.result),
                    "turn": int(obs.current.turn), "decisions": decisions,
                    "seconds": time.perf_counter() - started,
                }
                break
            action = staged_agent.agent(obs_dict)
            select = obs.select
            assert isinstance(action, list)
            assert len(action) == len(set(action))
            assert select.minCount <= len(action) <= select.maxCount
            assert all(isinstance(index, int) for index in action)
            assert all(0 <= index < len(select.option) for index in action)
            obs_dict = battle_select(action)
            decisions += 1
        else:
            raise RuntimeError("Staged package reached the decision limit.")
    finally:
        battle_finish()
    display(runtime_smoke)

    for cache in PACKAGE_DIR.rglob("__pycache__"):
        shutil.rmtree(cache)
    for compiled in PACKAGE_DIR.rglob("*.pyc"):
        compiled.unlink()
    """),
    md("""
    ## 4. Hash, archive, and inspect

    Source hashes link the ladder artifact to reviewed repository files. The
    archive hash identifies the exact uploaded bytes. Tar members are relative
    to staging so `main.py` cannot be hidden under an accidental parent folder.
    """),
    code("""
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()

    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with tarfile.open(ARCHIVE, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                archive.add(
                    path,
                    arcname=path.relative_to(PACKAGE_DIR).as_posix(),
                    recursive=False,
                )

    with tarfile.open(ARCHIVE, "r:gz") as archive:
        file_members = [member for member in archive.getmembers() if member.isfile()]
        members = [member.name for member in file_members]
        for member in file_members:
            stream = archive.extractfile(member)
            assert stream is not None
            while stream.read(1 << 20):
                pass
    assert set(members) == required, {
        "missing": sorted(required - set(members)),
        "unexpected": sorted(set(members) - required),
    }
    assert not any(member.startswith("submission_agent/") for member in members)

    manifest = {
        "format": "tar.gz",
        "main_sha256": sha256(PACKAGE_DIR / "main.py"),
        "deck_sha256": sha256(PACKAGE_DIR / "deck.csv"),
        "archive_sha256": sha256(ARCHIVE),
        "archive_bytes": ARCHIVE.stat().st_size,
        "members": members,
        "runtime_smoke": runtime_smoke,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    display(manifest)
    print(f"Archive: {ARCHIVE} ({ARCHIVE.stat().st_size / 1e6:.2f} MB)")
    """),
    md("""
    ## 5. Submission gate

    A complete packaging run now proves static structure and one staged runtime
    path. Submission still requires comparative evidence, recorded hashes,
    review of live rules, and an intentional decision about the latest two
    tracked ladder slots. Kaggle's validation episode remains the final runtime
    authority.
    """),
]


SEQUENCING = [
    md("""
    # Action-Sequencing Experiment: Development Before Attack

    **Purpose.** Test one causal hypothesis from the baseline telemetry: the
    attack-first policy attacks before developing its board and therefore loses
    even to the random control.

    **Single intended change.** Reorder legal main-phase actions from
    `attack ? evolve ? ability ? attach ? play` to
    `evolve ? ability ? attach ? play ? attack`. Deck, tie-breaking, setup
    choices, and all non-main selections remain unchanged.

    **Promotion question.** Does development-first beat the frozen baseline and
    materially improve performance against the official random policy without
    introducing contract failures?
    """),
    md("""
    ## 1. Configuration

    Each matchup is balanced across player seats. Python randomness is seeded,
    but the simulator does not expose its card-draw or coin-toss seed; these are
    independent seat-balanced games rather than exact paired simulations.
    """),
    code("""
    from collections import Counter
    from pathlib import Path
    import importlib.util
    import json
    import random
    import shutil
    import sys
    import time

    import numpy as np
    import pandas as pd

    GAMES_PER_SEAT = 20
    MAX_DECISIONS = 10_000
    BASE_SEED = 20260621
    BOOTSTRAP_SAMPLES = 10_000
    WORK_DIR = Path("/kaggle/working/action_sequence_experiment")
    BASELINE_RANDOM_BENCHMARK = 0.125
    """),
    code("""
    def first_match(pattern: str) -> Path:
        matches = sorted(Path("/kaggle/input").rglob(pattern))
        if not matches:
            raise FileNotFoundError(f"No Kaggle input matched {pattern}")
        return matches[0]

    def load_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sample_dir = first_match("sample_submission/main.py").parent
    agent_candidates = [
        path.parent for path in sorted(Path("/kaggle/input").rglob("main.py"))
        if "sample_submission" not in path.parts and "cg" not in path.parts
    ]
    agent_dir = next(
        (path for path in agent_candidates
         if (path / "main.py").exists() and (path / "deck.csv").exists()),
        None,
    )
    if agent_dir is None:
        raise FileNotFoundError("Attach the private agent-source dataset.")
    print(f"Frozen source: {agent_dir / 'main.py'}")
    print(f"Official random control: {sample_dir / 'main.py'}")
    """),
    md("""
    ## 2. Freeze baseline and create the one-change candidate

    Both deterministic modules are loaded from the same reviewed source. Only
    the candidate's `MAIN_ACTION_PRIORITY` dictionary changes in memory. This
    prevents accidental deck, setup, or tie-break differences.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    shutil.copy2(agent_dir / "main.py", WORK_DIR / "main.py")
    shutil.copy2(agent_dir / "deck.csv", WORK_DIR / "deck.csv")
    sys.path.insert(0, str(WORK_DIR))

    from cg.api import OptionType, SelectContext, SelectType, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start

    baseline = load_module("attack_first_baseline", WORK_DIR / "main.py")
    candidate = load_module("development_first_candidate", WORK_DIR / "main.py")
    random_control = load_module("official_random_control", sample_dir / "main.py")

    attack_priority = {
        OptionType.ATTACK: 0,
        OptionType.EVOLVE: 1,
        OptionType.ABILITY: 2,
        OptionType.ATTACH: 3,
        OptionType.PLAY: 4,
        OptionType.RETREAT: 5,
        OptionType.DISCARD: 6,
        OptionType.END: 7,
    }
    development_priority = {
        OptionType.EVOLVE: 0,
        OptionType.ABILITY: 1,
        OptionType.ATTACH: 2,
        OptionType.PLAY: 3,
        OptionType.ATTACK: 4,
        OptionType.RETREAT: 5,
        OptionType.DISCARD: 6,
        OptionType.END: 7,
    }
    baseline.MAIN_ACTION_PRIORITY = attack_priority
    candidate.MAIN_ACTION_PRIORITY = development_priority
    assert baseline.MAIN_ACTION_PRIORITY[OptionType.ATTACK] == 0
    assert candidate.MAIN_ACTION_PRIORITY[OptionType.ATTACK] == 4
    deck = baseline.read_deck_csv()
    assert deck == candidate.read_deck_csv() and len(deck) == 60
    display(pd.DataFrame({
        "attack_first": {key.name: value for key, value in baseline.MAIN_ACTION_PRIORITY.items()},
        "development_first": {key.name: value for key, value in candidate.MAIN_ACTION_PRIORITY.items()},
    }).sort_values("development_first"))
    """),
    md("""
    ## 3. State-aware instrumentation

    For the focal policy, record the public board immediately before each main
    decision: HP, Energy, Bench, Hand, Prize count, available actions, and chosen
    action. These snapshots explain *how* the ordering changes play rather than
    reporting only final wins.
    """),
    code("""
    def enum_name(enum_class, value) -> str:
        try:
            return enum_class(value).name
        except (ValueError, TypeError):
            return f"UNKNOWN_{value}"

    def active_features(player_state) -> tuple[int, int]:
        if not player_state.active or player_state.active[0] is None:
            return 0, 0
        active = player_state.active[0]
        return int(active.hp), len(active.energies)

    def state_snapshot(obs, player: int, chosen_action: str, matchup: str, game: int) -> dict:
        yours = obs.current.players[player]
        opponent = obs.current.players[1 - player]
        your_hp, your_energy = active_features(yours)
        opp_hp, opp_energy = active_features(opponent)
        available = sorted({enum_name(OptionType, option.type) for option in obs.select.option})
        return {
            "matchup": matchup, "game": game, "player": player,
            "turn": int(obs.current.turn), "turn_action": int(obs.current.turnActionCount),
            "chosen_action": chosen_action, "available_actions": ",".join(available),
            "your_active_hp": your_hp, "your_active_energy": your_energy,
            "your_bench": len(yours.bench), "your_hand": int(yours.handCount),
            "your_prizes": len(yours.prize), "your_deck": int(yours.deckCount),
            "opp_active_hp": opp_hp, "opp_active_energy": opp_energy,
            "opp_bench": len(opponent.bench), "opp_hand": int(opponent.handCount),
            "opp_prizes": len(opponent.prize), "opp_deck": int(opponent.deckCount),
        }

    def validate_action(obs, action: list[int]) -> None:
        select = obs.select
        assert isinstance(action, list)
        assert all(isinstance(index, int) for index in action)
        assert len(action) == len(set(action))
        assert select.minCount <= len(action) <= select.maxCount
        assert all(0 <= index < len(select.option) for index in action)
    """),
    code("""
    def play_game(
        policies: dict[int, object],
        focal_player: int,
        game_id: int,
        matchup: str,
    ) -> tuple[dict, list[dict]]:
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions = 0
        focal_actions = Counter()
        snapshots = []
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return ({
                    "status": "start_error", "matchup": matchup, "game": game_id,
                    "focal_player": focal_player, "error_player": start_data.errorPlayer,
                    "error_type": start_data.errorType,
                }, snapshots)
            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                if obs.current is not None and obs.current.result != -1:
                    winner = int(obs.current.result)
                    score = 1.0 if winner == focal_player else (0.0 if winner in (0, 1) else 0.5)
                    return ({
                        "status": "finished", "matchup": matchup, "game": game_id,
                        "focal_player": focal_player, "winner": winner,
                        "focal_score": score, "turn": int(obs.current.turn),
                        "decisions": decisions, "seconds": time.perf_counter() - started,
                        "focal_actions": dict(focal_actions),
                    }, snapshots)

                player = int(obs.current.yourIndex)
                action = policies[player].agent(obs_dict)
                validate_action(obs, action)
                chosen_names = [
                    enum_name(OptionType, obs.select.option[index].type) for index in action
                ]
                if player == focal_player:
                    focal_actions.update(chosen_names)
                    if obs.select.type == SelectType.MAIN and chosen_names:
                        snapshots.append(state_snapshot(
                            obs, player, chosen_names[0], matchup, game_id
                        ))
                obs_dict = battle_select(action)
                decisions += 1
            return ({
                "status": "decision_limit", "matchup": matchup, "game": game_id,
                "focal_player": focal_player, "decisions": decisions,
            }, snapshots)
        except Exception as error:
            return ({
                "status": "exception", "matchup": matchup, "game": game_id,
                "focal_player": focal_player,
                "error": f"{type(error).__name__}: {error}", "decisions": decisions,
            }, snapshots)
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    ## 4. Seat-balanced tournament

    Three matchups separate improvement from mere opponent weakness:

    1. development-first versus attack-first;
    2. development-first versus official random;
    3. frozen attack-first versus official random as a benchmark refresh.
    """),
    code("""
    experiments = [
        ("development_vs_attack", candidate, baseline),
        ("development_vs_random", candidate, random_control),
        ("attack_vs_random", baseline, random_control),
    ]
    results, snapshots = [], []
    game_id = 0
    for matchup, focal_policy, opponent_policy in experiments:
        for focal_player in (0, 1):
            for repetition in range(GAMES_PER_SEAT):
                policies = {focal_player: focal_policy, 1 - focal_player: opponent_policy}
                result, game_snapshots = play_game(
                    policies, focal_player, game_id, matchup
                )
                results.append(result)
                snapshots.extend(game_snapshots)
                game_id += 1

    results_df = pd.DataFrame(results)
    snapshots_df = pd.DataFrame(snapshots)
    failures = results_df[results_df.status != "finished"]
    assert failures.empty, failures.to_dict("records")
    display(results_df.drop(columns=["focal_actions"], errors="ignore"))
    print(f"Completed {len(results_df)} games with {len(failures)} failures.")
    """),
    md("""
    ## 5. Outcome uncertainty and promotion gate

    Bootstrap intervals describe game-level uncertainty. Promotion requires
    development-first to beat attack-first and to improve convincingly over the
    frozen baseline's `0.125` random-control benchmark. Reliability alone is
    insufficient.
    """),
    code("""
    rng = np.random.default_rng(BASE_SEED)
    summaries = []
    for matchup, group in results_df.groupby("matchup"):
        scores = group.focal_score.to_numpy(dtype=float)
        boot = rng.choice(
            scores, size=(BOOTSTRAP_SAMPLES, len(scores)), replace=True
        ).mean(axis=1)
        low, high = np.quantile(boot, [0.025, 0.975])
        summaries.append({
            "matchup": matchup, "games": len(scores),
            "wins": int((scores == 1).sum()), "draws": int((scores == 0.5).sum()),
            "losses": int((scores == 0).sum()), "score_rate": float(scores.mean()),
            "ci_low": float(low), "ci_high": float(high),
        })
    summary_df = pd.DataFrame(summaries).set_index("matchup")
    display(summary_df)

    head_to_head = summary_df.loc["development_vs_attack"]
    versus_random = summary_df.loc["development_vs_random"]
    if len(failures):
        decision = "REJECT: runtime failure"
    elif head_to_head.ci_low <= 0.5:
        decision = "HOLD: development-first did not clearly beat attack-first"
    elif versus_random.ci_low <= BASELINE_RANDOM_BENCHMARK:
        decision = "HOLD: improvement over random benchmark is uncertain"
    else:
        decision = "PROMOTE: development-first passes sequencing gate"
    print(f"Promotion decision: {decision}")
    """),
    md("""
    ## 6. Episode/action-sequencing EDA

    Compare action mix and the board state at attacks. A healthier candidate
    should attach and develop before attacking, attack with more Energy or a
    stronger board, and avoid simply extending games without improving results.
    """),
    code("""
    action_rows = []
    for result in results:
        for action, count in result.get("focal_actions", {}).items():
            action_rows.append({
                "matchup": result["matchup"], "action": action, "count": count
            })
    action_df = pd.DataFrame(action_rows).groupby(
        ["matchup", "action"], as_index=False
    ).sum()
    display(action_df.pivot(index="action", columns="matchup", values="count").fillna(0))

    attack_states = snapshots_df[snapshots_df.chosen_action == "ATTACK"]
    attack_summary = attack_states.groupby("matchup").agg(
        attacks=("chosen_action", "size"),
        median_turn=("turn", "median"),
        mean_active_energy=("your_active_energy", "mean"),
        mean_bench=("your_bench", "mean"),
        mean_active_hp=("your_active_hp", "mean"),
        mean_opponent_hp=("opp_active_hp", "mean"),
    )
    display(attack_summary)
    display(snapshots_df.groupby(["matchup", "chosen_action"]).size().rename("count").to_frame())
    """),
    code("""
    output = Path("/kaggle/working")
    payload = {
        "configuration": {
            "games_per_seat": GAMES_PER_SEAT,
            "single_change": "development actions before attack",
            "simulator_seed_exposed": False,
        },
        "summary": summary_df.reset_index().to_dict("records"),
        "decision": decision,
        "attack_state_summary": attack_summary.reset_index().to_dict("records"),
        "results": results,
        "snapshots": snapshots,
    }
    (output / "action_sequence_experiment.json").write_text(
        json.dumps(payload, indent=2, default=str)
    )
    print(f"Saved evidence to {output / 'action_sequence_experiment.json'}")
    """),
    md("""
    ## 7. Interpretation

    Promote only the tested priority dictionary; do not mix in attack scoring,
    deck changes, or setup heuristics in the same commit. If held or rejected,
    use the state snapshots to choose the next single change?most likely an
    immediate-knockout exception or card-aware attachment scoring.
    """),
]


OUT.mkdir(parents=True, exist_ok=True)
save("01_card_database_eda.ipynb", EDA)
save("02_agent_baseline_and_local_evaluation.ipynb", EVALUATION)
save("03_submission_packaging_and_validation.ipynb", PACKAGING)
save("04_action_sequence_experiment.ipynb", SEQUENCING)
