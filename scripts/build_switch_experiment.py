"""Generate the Kaggle experiment notebook for conservative switch v1."""

from pathlib import Path
import textwrap

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "11_conservative_switch_experiment.ipynb"
CANDIDATE_SOURCE = (ROOT / "candidates" / "conservative_switch_v1" / "main.py").read_text(encoding="utf-8")
PROMOTED_SOURCE = (ROOT / "agent" / "main.py").read_text(encoding="utf-8")
PLANNER_V2_SOURCE = (ROOT / "candidates" / "abomasnow_planner_v2" / "main.py").read_text(encoding="utf-8")
DECK_SOURCE = (ROOT / "agent" / "deck.csv").read_text(encoding="utf-8")


PRESSURE_SOURCE = r'''"""Frozen attack-priority pressure control for evaluation only."""

from __future__ import annotations

from pathlib import Path

from cg.api import OptionType, SelectContext, SelectType, to_observation_class

MAIN_ACTION_PRIORITY = {
    OptionType.ATTACK: 0,
    OptionType.EVOLVE: 1,
    OptionType.ATTACH: 2,
    OptionType.ABILITY: 3,
    OptionType.PLAY: 4,
    OptionType.RETREAT: 5,
    OptionType.DISCARD: 6,
    OptionType.END: 7,
}


def read_deck_csv() -> list[int]:
    candidates = (
        Path(__file__).resolve().with_name("deck.csv"),
        Path("deck.csv"),
        Path("/kaggle_simulations/agent/deck.csv"),
    )
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        raise FileNotFoundError("Could not locate deck.csv.")
    deck = [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards in {path}, found {len(deck)}.")
    return deck


def _stable_key(option: object, index: int) -> tuple[int, ...]:
    fields = ("number", "playerIndex", "area", "index", "inPlayArea", "inPlayIndex", "attackId", "cardId", "serial")
    values = []
    for field in fields:
        value = getattr(option, field, None)
        try:
            values.append(int(value) if value is not None else 1_000_000)
        except (TypeError, ValueError):
            values.append(1_000_000)
    return (*values, index)


def _choose_indices(obs: object) -> list[int]:
    select = obs.select
    indexed = list(enumerate(select.option))
    if not indexed:
        return []
    if select.context == SelectContext.MULLIGAN:
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            indexed = no_choices
    elif select.context == SelectContext.IS_FIRST:
        yes_choices = [pair for pair in indexed if pair[1].type == OptionType.YES]
        if yes_choices:
            indexed = yes_choices
    elif select.type == SelectType.MAIN:
        indexed.sort(key=lambda pair: (MAIN_ACTION_PRIORITY.get(pair[1].type, 99), _stable_key(pair[1], pair[0])))
    else:
        indexed.sort(key=lambda pair: _stable_key(pair[1], pair[0]))
    required = max(0, int(select.minCount))
    requested = required if required > 0 else min(1, int(select.maxCount))
    count = min(requested, int(select.maxCount), len(indexed))
    chosen = [index for index, _ in indexed[:count]]
    if not (select.minCount <= len(chosen) <= select.maxCount):
        raise ValueError("Policy produced an invalid selection count.")
    if len(chosen) != len(set(chosen)):
        raise ValueError("Policy produced duplicate option indices.")
    return chosen


def agent(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
'''


def md(value: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(value).strip())


def code(value: str):
    return nbf.v4.new_code_cell(textwrap.dedent(value).strip())


CELLS = [
    md("""
    # Conservative Switch v1 Experiment

    **Purpose.** Test one focused response to the loss-taxonomy result: retreat
    only when the active Pokémon is not ready and a benched Pokémon is ready.

    **Single intended change.** Keep the promoted development-first ordering,
    except prioritize a legal `RETREAT` in that specific ready-bench situation
    and choose the best ready benched target afterward.

    **Promotion gate.** The candidate must clear promoted, planner v2, random,
    and pressure controls without runtime failures. Production remains frozen
    unless the gate clears.
    """),
    md("""
    ## 1. Configuration and frozen sources

    The candidate and all non-random controls are embedded by the deterministic
    local builder. The official random policy and simulator are loaded from the
    Kaggle competition input.
    """),
    code(f"""
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

    BASE_SEED = 20260626
    GAMES_PER_CELL = 10
    MAX_DECISIONS = 5_000
    BOOTSTRAP_SAMPLES = 10_000
    WORK_DIR = Path("/kaggle/working/switch_v1_runtime")
    REPLAY_DIR = Path("/kaggle/working/switch_v1_replays")

    CANDIDATE_SOURCE = {CANDIDATE_SOURCE!r}
    PROMOTED_SOURCE = {PROMOTED_SOURCE!r}
    PLANNER_V2_SOURCE = {PLANNER_V2_SOURCE!r}
    PRESSURE_SOURCE = {PRESSURE_SOURCE!r}
    DECK_SOURCE = {DECK_SOURCE!r}

    def first_match(pattern: str) -> Path:
        matches = sorted(Path("/kaggle/input").rglob(pattern))
        if not matches:
            raise FileNotFoundError(f"No Kaggle input matched {{pattern}}")
        return matches[0]

    def load_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    sample_dir = first_match("sample_submission/main.py").parent
    print(f"Official random source: {{sample_dir / 'main.py'}}")
    """),
    md("""
    ## 2. Runtime staging

    Stage each policy in one official simulator copy. All policies must share
    the same frozen 60-card deck before the tournament starts.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    (WORK_DIR / "deck.csv").write_text(DECK_SOURCE, encoding="utf-8")
    (WORK_DIR / "candidate_main.py").write_text(CANDIDATE_SOURCE, encoding="utf-8")
    (WORK_DIR / "promoted_main.py").write_text(PROMOTED_SOURCE, encoding="utf-8")
    (WORK_DIR / "planner_v2_main.py").write_text(PLANNER_V2_SOURCE, encoding="utf-8")
    (WORK_DIR / "pressure_main.py").write_text(PRESSURE_SOURCE, encoding="utf-8")

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import OptionType, SelectContext, SelectType, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start, visualize_data

    candidate = load_module("conservative_switch_v1", WORK_DIR / "candidate_main.py")
    promoted = load_module("promoted_frozen", WORK_DIR / "promoted_main.py")
    planner_v2 = load_module("planner_v2_frozen", WORK_DIR / "planner_v2_main.py")
    pressure = load_module("pressure_control_frozen", WORK_DIR / "pressure_main.py")
    random_control = load_module("official_random_control", sample_dir / "main.py")

    deck = candidate.read_deck_csv()
    assert deck == promoted.read_deck_csv() == planner_v2.read_deck_csv() == pressure.read_deck_csv()
    assert len(deck) == 60
    print("PASS: candidate and controls share the frozen 60-card deck")
    """),
    md("""
    ## 3. Controlled play and switch telemetry

    The wrapper controls only first-player choice. Candidate main decisions log
    whether retreat was available and whether it was chosen.
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

    class ForcedFirstChoice:
        def __init__(self, base_policy, player_zero_goes_first: bool):
            self.base_policy = base_policy
            self.player_zero_goes_first = player_zero_goes_first

        def agent(self, obs_dict: dict) -> list[int]:
            obs = to_observation_class(obs_dict)
            if obs.select is not None and obs.select.context == SelectContext.IS_FIRST:
                desired = OptionType.YES if self.player_zero_goes_first else OptionType.NO
                matches = [i for i, option in enumerate(obs.select.option) if option.type == desired]
                if not matches:
                    raise ValueError(f"IS_FIRST does not expose {desired.name}")
                return [matches[0]]
            return self.base_policy.agent(obs_dict)

    def energy_count(pokemon) -> int:
        if pokemon is None:
            return 0
        energies = getattr(pokemon, "energies", None)
        if energies is None:
            energies = getattr(pokemon, "energyCards", [])
        return len(energies)

    def switch_features(obs, chosen_names: list[str]) -> dict:
        player = int(obs.current.yourIndex)
        player_state = obs.current.players[player]
        active = player_state.active[0] if player_state.active else None
        bench = [card for card in player_state.bench if card is not None]
        available = {enum_name(OptionType, option.type) for option in obs.select.option}
        return {
            "active_energy": energy_count(active),
            "ready_bench": sum(energy_count(card) >= 1 for card in bench),
            "retreat_available": "RETREAT" in available,
            "attack_available": "ATTACK" in available,
            "chosen_action": chosen_names[0] if chosen_names else "SKIP",
        }

    replay_counts = Counter()
    replay_paths = []

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
    """),
    code("""
    def play_game(opponent_policy, opponent_name: str, game_id: int, candidate_player: int, candidate_should_go_first: bool):
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions, first_player = 0, None
        candidate_actions = Counter()
        snapshots = []
        obs_log, action_log = [""], [None]
        player_zero_first = candidate_should_go_first if candidate_player == 0 else not candidate_should_go_first
        policies = (
            {0: ForcedFirstChoice(candidate, player_zero_first), 1: opponent_policy}
            if candidate_player == 0
            else {0: ForcedFirstChoice(opponent_policy, player_zero_first), 1: candidate}
        )
        matchup = f"switch_v1_vs_{opponent_name}"
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return ({"status": "start_error", "matchup": matchup, "game": game_id, "candidate_player": candidate_player, "error_player": start_data.errorPlayer, "error_type": start_data.errorType}, snapshots)

            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                observed_first = getattr(obs.current, "firstPlayer", None)
                if observed_first in (0, 1):
                    first_player = int(observed_first)
                if obs.current.result != -1:
                    winner = int(obs.current.result)
                    score = 1.0 if winner == candidate_player else 0.0 if winner in (0, 1) else 0.5
                    replay_path = None
                    key = (matchup, candidate_player, first_player == candidate_player, score)
                    if score == 0.0 and replay_counts[key] < 1:
                        replay_path = REPLAY_DIR / f"{matchup}_game_{game_id}_seat_{candidate_player}_first_{first_player}.json"
                        write_replay(obs_log, action_log, replay_path)
                        replay_counts[key] += 1
                        replay_paths.append(str(replay_path))
                    return ({
                        "status": "finished", "matchup": matchup, "game": game_id,
                        "candidate_player": candidate_player, "first_player": first_player,
                        "candidate_went_first": first_player == candidate_player,
                        "forced_candidate_went_first": candidate_should_go_first,
                        "winner": winner, "candidate_score": score,
                        "turn": int(obs.current.turn), "decisions": decisions,
                        "seconds": time.perf_counter() - started,
                        "candidate_actions": dict(candidate_actions),
                        "replay_path": str(replay_path) if replay_path else None,
                    }, snapshots)

                player = int(obs.current.yourIndex)
                action = policies[player].agent(obs_dict)
                validate_action(obs, action)
                chosen_names = [enum_name(OptionType, obs.select.option[index].type) for index in action]
                if player == candidate_player:
                    candidate_actions.update(chosen_names)
                    if obs.select.type == SelectType.MAIN:
                        features = switch_features(obs, chosen_names)
                        features.update({
                            "matchup": matchup,
                            "game": game_id,
                            "candidate_player": candidate_player,
                            "candidate_went_first": first_player == candidate_player,
                            "turn": int(obs.current.turn),
                        })
                        snapshots.append(features)
                obs_log.append(replay_observation(obs_dict))
                action_log.append(list(action))
                obs_dict = battle_select(action)
                decisions += 1

            return ({"status": "decision_limit", "matchup": matchup, "game": game_id, "candidate_player": candidate_player, "first_player": first_player, "decisions": decisions}, snapshots)
        except Exception as error:
            return ({"status": "exception", "matchup": matchup, "game": game_id, "candidate_player": candidate_player, "first_player": first_player, "error": f"{type(error).__name__}: {error}", "decisions": decisions}, snapshots)
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    ## 4. Balanced four-opponent tournament

    Each opponent uses ten games in every candidate-seat by forced-turn-order
    cell.
    """),
    code("""
    opponents = [
        ("promoted", promoted),
        ("planner_v2", planner_v2),
        ("random", random_control),
        ("pressure", pressure),
    ]
    results, snapshots = [], []
    game_id = 120_000
    for opponent_name, opponent_policy in opponents:
        for candidate_player in (0, 1):
            for candidate_should_go_first in (False, True):
                for repetition in range(GAMES_PER_CELL):
                    result, game_snapshots = play_game(opponent_policy, opponent_name, game_id, candidate_player, candidate_should_go_first)
                    results.append(result)
                    snapshots.extend(game_snapshots)
                    game_id += 1

    results_df = pd.DataFrame(results)
    snapshots_df = pd.DataFrame(snapshots)
    failures = results_df[results_df.status != "finished"]
    finished = results_df[results_df.status == "finished"].copy()
    assert failures.empty, failures.to_dict("records")
    assert (finished.candidate_went_first == finished.forced_candidate_went_first).all()
    cells = finished.groupby(["matchup", "candidate_player", "candidate_went_first"]).size()
    assert (cells == GAMES_PER_CELL).all(), cells.to_dict()
    display(finished.drop(columns=["candidate_actions"], errors="ignore"))
    print(f"Completed {len(finished)} games with {len(failures)} failures.")
    """),
    md("""
    ## 5. Outcome uncertainty and decision

    Promote only if the primary promoted-control interval and regression
    intervals are all above parity with zero failures.
    """),
    code("""
    rng = np.random.default_rng(BASE_SEED)
    summaries = []
    for matchup, group in finished.groupby("matchup"):
        scores = group.candidate_score.to_numpy(dtype=float)
        boot = rng.choice(scores, size=(BOOTSTRAP_SAMPLES, len(scores)), replace=True).mean(axis=1)
        summaries.append({
            "matchup": matchup,
            "games": len(scores),
            "wins": int((scores == 1.0).sum()),
            "draws": int((scores == 0.5).sum()),
            "losses": int((scores == 0.0).sum()),
            "score_rate": float(scores.mean()),
            "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)),
        })
    summary_df = pd.DataFrame(summaries).set_index("matchup")
    display(summary_df)

    required = ["switch_v1_vs_promoted", "switch_v1_vs_planner_v2", "switch_v1_vs_random", "switch_v1_vs_pressure"]
    if len(failures):
        decision = "REJECT: runtime failures"
    elif all(summary_df.loc[name].ci_low > 0.5 for name in required):
        decision = "PROMOTE: switch v1 clears all controlled gates"
    elif summary_df.loc["switch_v1_vs_promoted"].ci_high < 0.5:
        decision = "REJECT: switch v1 is clearly worse than promoted"
    else:
        decision = "HOLD: at least one required interval overlaps parity"
    print(f"Decision: {decision}")
    """),
    md("""
    ## 6. Switch mechanism checks

    Confirm that the candidate actually uses retreat and whether that correlates
    with controlled-cell score differences.
    """),
    code("""
    attribution = finished.groupby(["matchup", "candidate_player", "candidate_went_first"]).candidate_score.agg(games="size", score_rate="mean")
    display(attribution)

    mechanism = snapshots_df.groupby("matchup").agg(
        main_decisions=("game", "size"),
        retreat_available_rate=("retreat_available", "mean"),
        retreat_chosen_rate=("chosen_action", lambda s: float((s == "RETREAT").mean())),
        ready_bench_rate=("ready_bench", lambda s: float((s > 0).mean())),
        unready_active_rate=("active_energy", lambda s: float((s == 0).mean())),
        attack_available_rate=("attack_available", "mean"),
        attack_chosen_rate=("chosen_action", lambda s: float((s == "ATTACK").mean())),
    )
    display(mechanism)

    action_rows = []
    for result in results:
        for action, count in result.get("candidate_actions", {}).items():
            action_rows.append({"matchup": result["matchup"], "action": action, "count": count})
    action_df = pd.DataFrame(action_rows).groupby(["matchup", "action"], as_index=False).sum()
    display(action_df.pivot(index="action", columns="matchup", values="count").fillna(0))
    """),
    md("""
    ## 7. Evidence export

    Save aggregate results, per-game records, switch telemetry, and replay
    paths. Do not commit replay JSON files.
    """),
    code("""
    payload = {
        "candidate": "conservative_switch_v1",
        "single_change": "retreat when active is unready and a benched attacker is ready",
        "configuration": {
            "base_seed": BASE_SEED,
            "games_per_cell": GAMES_PER_CELL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
        },
        "decision": decision,
        "summaries": summary_df.reset_index().to_dict("records"),
        "attribution": attribution.reset_index().to_dict("records"),
        "mechanism": mechanism.reset_index().to_dict("records"),
        "results": results,
        "snapshots": snapshots,
        "replays": replay_paths,
    }
    evidence_path = Path("/kaggle/working/conservative_switch_experiment.json")
    evidence_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Saved evidence to {evidence_path}")
    """),
]


for index, cell in enumerate(CELLS):
    cell["id"] = f"cell-{index:02d}"

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
