"""Generate the Kaggle-ready first-player observability notebook."""

from pathlib import Path
import textwrap

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "06_first_player_and_replay_observability.ipynb"


def md(value: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(value).strip())


def code(value: str):
    return nbf.v4.new_code_cell(textwrap.dedent(value).strip())


CELLS = [
    md("""
    # First-Player Attribution and Replay Diagnostics

    **Purpose.** Resolve the seat-versus-first-player ambiguity in prior
    experiments and produce bounded replay artifacts for turn-level debugging.

    **Decision question.** Does the promoted policy's outcome vary with actual
    first-player status after accounting for player index?

    This notebook changes no policy or deck behavior. Run it with the
    competition data and private reviewed agent-source dataset attached.
    """),
    md("""
    ## 1. Configuration and reproducibility

    Seat balance does not guarantee first-player balance, so every result stores
    `state.firstPlayer` directly. Complete trajectories live only until their
    outcome is known, and only a bounded sample of non-wins is written.
    """),
    code("""
    from collections import Counter
    from copy import deepcopy
    from pathlib import Path
    import importlib.util
    import json
    import random
    import shutil
    import sys
    import time

    import numpy as np
    import pandas as pd

    BASE_SEED = 20260622
    GAMES_PER_SEAT = 20
    MAX_DECISIONS = 5_000
    BOOTSTRAP_SAMPLES = 10_000
    MAX_REPLAYS = 4
    WORK_DIR = Path("/kaggle/working/first_player_runtime")
    REPLAY_DIR = Path("/kaggle/working/replays")

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
    candidates = [
        path.parent for path in sorted(Path("/kaggle/input").rglob("main.py"))
        if "sample_submission" not in path.parts and "cg" not in path.parts
    ]
    agent_dir = next(
        (path for path in candidates
         if (path / "main.py").exists() and (path / "deck.csv").exists()),
        None,
    )
    if agent_dir is None:
        raise FileNotFoundError("Attach the private agent-source dataset.")
    print(f"Promoted agent: {agent_dir / 'main.py'}")
    print(f"Official control: {sample_dir / 'main.py'}")
    """),
    md("""
    ## 2. Isolated simulator and frozen policies

    Copy the complete official runtime to working storage and load both policies
    separately. Both players use the promoted deck, isolating policy behavior.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    shutil.copy2(agent_dir / "main.py", WORK_DIR / "candidate_main.py")
    shutil.copy2(agent_dir / "deck.csv", WORK_DIR / "deck.csv")
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import OptionType, SelectContext, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start, visualize_data

    candidate = load_module("promoted_candidate", WORK_DIR / "candidate_main.py")
    control = load_module("official_random_control", sample_dir / "main.py")
    deck = candidate.read_deck_csv()
    assert len(deck) == 60
    """),
    md("""
    ## 3. Contract checks, replay serialization, and runner

    Actions are validated before simulation. Replay observations are deep-copied
    so removing the Search API payload cannot mutate agent input. The replay
    structure follows the competition author's official example.
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

    def replay_observation(obs_dict: dict) -> dict:
        saved = deepcopy(obs_dict)
        saved.pop("search_begin_input", None)
        return saved

    def write_replay(obs_log: list, action_log: list, path: Path) -> None:
        visual = json.loads(visualize_data())
        for index, step in enumerate(visual):
            if index < len(obs_log):
                step["obs"] = obs_log[index]
            if index < len(action_log):
                step["action"] = [action_log[index], action_log[index]]
        path.write_text(json.dumps(visual), encoding="utf-8")

    replay_paths = []

    def play_game(policies: dict, game_id: int, candidate_player: int) -> dict:
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions, first_player = 0, None
        contexts, candidate_actions = Counter(), Counter()
        obs_log, action_log = [""], [None]
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return {
                    "status": "start_error", "game": game_id,
                    "candidate_player": candidate_player,
                    "error_player": start_data.errorPlayer,
                    "error_type": start_data.errorType,
                }

            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                observed_first = getattr(obs.current, "firstPlayer", None)
                if observed_first in (0, 1):
                    first_player = int(observed_first)

                if obs.current.result != -1:
                    winner = int(obs.current.result)
                    score = (1.0 if winner == candidate_player
                             else 0.0 if winner in (0, 1) else 0.5)
                    replay_path = None
                    if score < 1.0 and len(replay_paths) < MAX_REPLAYS:
                        replay_path = REPLAY_DIR / (
                            f"game_{game_id}_seat_{candidate_player}_"
                            f"first_{first_player}_score_{score:.1f}.json"
                        )
                        write_replay(obs_log, action_log, replay_path)
                        replay_paths.append(str(replay_path))
                    return {
                        "status": "finished", "game": game_id,
                        "candidate_player": candidate_player,
                        "first_player": first_player,
                        "candidate_went_first": first_player == candidate_player,
                        "winner": winner, "candidate_score": score,
                        "turn": int(obs.current.turn), "decisions": decisions,
                        "seconds": time.perf_counter() - started,
                        "contexts": dict(contexts),
                        "candidate_actions": dict(candidate_actions),
                        "replay_path": str(replay_path) if replay_path else None,
                    }

                player = int(obs.current.yourIndex)
                contexts[enum_name(SelectContext, obs.select.context)] += 1
                action = policies[player].agent(obs_dict)
                validate_action(obs, action)
                if player == candidate_player:
                    candidate_actions.update(
                        enum_name(OptionType, obs.select.option[index].type)
                        for index in action
                    )
                obs_log.append(replay_observation(obs_dict))
                action_log.append(list(action))
                obs_dict = battle_select(action)
                decisions += 1

            return {
                "status": "decision_limit", "game": game_id,
                "candidate_player": candidate_player,
                "first_player": first_player, "decisions": decisions,
            }
        except Exception as error:
            return {
                "status": "exception", "game": game_id,
                "candidate_player": candidate_player,
                "first_player": first_player,
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
    ## 4. Seat-balanced screen

    The promoted candidate plays equally often as player 0 and player 1 against
    the official random policy. Actual first-player assignment is observed.
    """),
    code("""
    results = []
    game_id = 60_000
    for candidate_player in (0, 1):
        for repetition in range(GAMES_PER_SEAT):
            policies = {candidate_player: candidate, 1 - candidate_player: control}
            results.append(play_game(policies, game_id, candidate_player))
            game_id += 1

    results_df = pd.DataFrame(results)
    failures = results_df[results_df.status != "finished"]
    finished = results_df[results_df.status == "finished"].copy()
    assert failures.empty, failures.to_dict("records")
    assert finished.first_player.isin([0, 1]).all(), "Missing first-player attribution"
    display(finished.drop(columns=["contexts", "candidate_actions"], errors="ignore"))
    print(f"Completed {len(finished)} games; saved {len(replay_paths)} replays.")
    """),
    md("""
    ## 5. Outcome uncertainty and attribution

    The overall bootstrap interval is the screen result. Stratified tables are
    diagnostic; small realized first-player cells must not be overinterpreted.
    """),
    code("""
    scores = finished.candidate_score.to_numpy(dtype=float)
    rng = np.random.default_rng(BASE_SEED)
    boot = rng.choice(scores, size=(BOOTSTRAP_SAMPLES, len(scores)), replace=True).mean(axis=1)
    summary = {
        "games": len(finished),
        "wins": int((scores == 1.0).sum()),
        "draws": int((scores == 0.5).sum()),
        "losses": int((scores == 0.0).sum()),
        "score_rate": float(scores.mean()),
        "bootstrap_95_low": float(np.quantile(boot, 0.025)),
        "bootstrap_95_high": float(np.quantile(boot, 0.975)),
        "failures": len(failures), "replays_saved": len(replay_paths),
    }
    display(pd.Series(summary).to_frame("value"))

    by_seat = finished.groupby("candidate_player").candidate_score.agg(
        games="size", score_rate="mean"
    )
    by_turn_order = finished.groupby("candidate_went_first").candidate_score.agg(
        games="size", score_rate="mean"
    ).rename(index={False: "went_second", True: "went_first"})
    joint = finished.pivot_table(
        index="candidate_player", columns="candidate_went_first",
        values="candidate_score", aggfunc=["size", "mean"], fill_value=0,
    )
    display(by_seat)
    display(by_turn_order)
    display(joint)
    """),
    md("""
    ## 6. Action telemetry and replay manifest

    Replay files are diagnostic samples, not independent evaluation evidence.
    The optional author viewer uploads JSON externally; inspect the artifact and
    competition rules before using that service.
    """),
    code("""
    action_counts, context_counts = Counter(), Counter()
    for result in results:
        action_counts.update(result.get("candidate_actions", {}))
        context_counts.update(result.get("contexts", {}))
    display(pd.Series(action_counts, name="candidate_selections").sort_values(ascending=False).to_frame())
    display(pd.Series(context_counts, name="decisions").sort_values(ascending=False).to_frame())
    replay_manifest = finished.loc[
        finished.replay_path.notna(),
        ["game", "candidate_player", "first_player", "candidate_score", "replay_path"],
    ]
    display(replay_manifest)
    """),
    code("""
    payload = {
        "experiment": "first-player attribution and bounded replay capture",
        "configuration": {
            "base_seed": BASE_SEED, "games_per_seat": GAMES_PER_SEAT,
            "max_replays": MAX_REPLAYS, "simulator_seed_exposed": False,
        },
        "summary": summary,
        "by_seat": by_seat.reset_index().to_dict("records"),
        "by_turn_order": by_turn_order.reset_index().to_dict("records"),
        "replays": replay_manifest.to_dict("records"),
        "results": results,
    }
    evidence_path = Path("/kaggle/working/first_player_observability.json")
    evidence_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Saved evidence to {evidence_path}")
    """),
    md("""
    ## 7. Interpretation gate

    This notebook does not promote a policy. Use it to determine whether the
    previous seat split was a turn-order effect and to select failed turns for
    the attack-planner design. Increase games if either turn-order cell is sparse.
    """),
]


notebook = nbf.v4.new_notebook(
    cells=CELLS,
    metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT)
print(f"Wrote {OUTPUT.name}: {len(CELLS)} cells")
