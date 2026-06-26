"""Generate the Kaggle loss-taxonomy and pressure-opponent experiment notebook."""

from pathlib import Path
import textwrap

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "10_loss_taxonomy_and_pressure_opponent.ipynb"
PROMOTED_SOURCE = (ROOT / "agent" / "main.py").read_text(encoding="utf-8")
PLANNER_V2_SOURCE = (ROOT / "candidates" / "abomasnow_planner_v2" / "main.py").read_text(encoding="utf-8")
DECK_SOURCE = (ROOT / "agent" / "deck.csv").read_text(encoding="utf-8")


PRESSURE_SOURCE = r'''"""Frozen pressure-style control policy for evaluator notebooks.

This is not a submission candidate. It is a deterministic opponent designed to
stress attack timing by prioritizing legal attacks earlier than the promoted
development-first baseline.
"""

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
    fields = (
        "number", "playerIndex", "area", "index", "inPlayArea",
        "inPlayIndex", "attackId", "cardId", "serial",
    )
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
    options = list(select.option)
    if not options:
        return []

    indexed = list(enumerate(options))
    if select.context == SelectContext.MULLIGAN:
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            indexed = no_choices
    elif select.context == SelectContext.IS_FIRST:
        yes_choices = [pair for pair in indexed if pair[1].type == OptionType.YES]
        if yes_choices:
            indexed = yes_choices
    elif select.type == SelectType.MAIN:
        indexed.sort(
            key=lambda pair: (
                MAIN_ACTION_PRIORITY.get(pair[1].type, 99),
                _stable_key(pair[1], pair[0]),
            )
        )
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
    # Loss Taxonomy and Pressure-Opponent Experiment

    **Purpose.** Improve the evaluation environment before adding more
    heuristic rules. This notebook compares the promoted policy and held
    planner v2 against frozen controls, then labels losses by likely failure
    mode.

    **Why this comes next.** Planner v2 fixed a visible Kyogre resource bug but
    did not beat the promoted policy. Before changing the agent again, we need
    better evidence about whether losses are caused by setup, attacker
    development, switch timing, attachment choices, attack timing, or opponent
    pressure.

    **Production safety.** This notebook does not edit `agent/main.py` or
    `agent/deck.csv`. It only writes diagnostic JSON and bounded replay files
    under `/kaggle/working`.
    """),
    md("""
    ## 1. Configuration and frozen sources

    The promoted policy, planner v2, frozen deck, and pressure-style control are
    embedded by the local builder. The official random policy and simulator are
    still loaded from the competition input.
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
    GAMES_PER_CELL = 5
    MAX_DECISIONS = 5_000
    BOOTSTRAP_SAMPLES = 5_000
    REPLAYS_PER_CELL = 1
    WORK_DIR = Path("/kaggle/working/loss_taxonomy_runtime")
    REPLAY_DIR = Path("/kaggle/working/loss_taxonomy_replays")

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

    Copy the official simulator, then stage each frozen policy in the same
    runtime directory. All policies must read the exact same 60-card deck before
    games are allowed to run.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    (WORK_DIR / "deck.csv").write_text(DECK_SOURCE, encoding="utf-8")
    (WORK_DIR / "promoted_main.py").write_text(PROMOTED_SOURCE, encoding="utf-8")
    (WORK_DIR / "planner_v2_main.py").write_text(PLANNER_V2_SOURCE, encoding="utf-8")
    (WORK_DIR / "pressure_main.py").write_text(PRESSURE_SOURCE, encoding="utf-8")

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start, visualize_data

    promoted = load_module("promoted_frozen", WORK_DIR / "promoted_main.py")
    planner_v2 = load_module("planner_v2_frozen", WORK_DIR / "planner_v2_main.py")
    pressure = load_module("pressure_control_frozen", WORK_DIR / "pressure_main.py")
    random_control = load_module("official_random_control", sample_dir / "main.py")

    deck = promoted.read_deck_csv()
    assert deck == planner_v2.read_deck_csv() == pressure.read_deck_csv()
    assert len(deck) == 60
    print("PASS: all frozen policies share the same 60-card deck")
    """),
    md("""
    ## 3. Controlled play, telemetry, and replay capture

    The wrapper controls only the first-player choice. Every later action is
    delegated to the tested policy. For candidate turns we record compact board
    and action features that can support loss labels without relying on private
    hidden state.
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

    def pokemon_summary(pokemon) -> dict:
        if pokemon is None:
            return {"id": -1, "hp": 0, "energy": 0}
        energies = getattr(pokemon, "energies", None)
        if energies is None:
            energies = getattr(pokemon, "energyCards", [])
        return {
            "id": int(getattr(pokemon, "id", -1)),
            "hp": int(getattr(pokemon, "hp", 0)),
            "energy": len(energies),
        }

    def board_features(obs, candidate_player: int) -> dict:
        player_state = obs.current.players[candidate_player]
        opponent_state = obs.current.players[1 - candidate_player]
        active = player_state.active[0] if player_state.active else None
        opponent_active = opponent_state.active[0] if opponent_state.active else None
        bench = [card for card in player_state.bench if card is not None]
        active_summary = pokemon_summary(active)
        bench_summaries = [pokemon_summary(card) for card in bench]
        ready_attackers = int(active_summary["energy"] >= 1)
        ready_bench = sum(summary["energy"] >= 1 for summary in bench_summaries)
        return {
            "active_id": active_summary["id"],
            "active_hp": active_summary["hp"],
            "active_energy": active_summary["energy"],
            "bench_count": len(bench_summaries),
            "bench_energy_max": max([0] + [summary["energy"] for summary in bench_summaries]),
            "ready_attackers": ready_attackers + ready_bench,
            "ready_bench": ready_bench,
            "hand_size": len(player_state.hand),
            "discard_size": len(player_state.discard),
            "deck_count": int(player_state.deckCount),
            "opponent_active_id": pokemon_summary(opponent_active)["id"],
            "opponent_active_hp": pokemon_summary(opponent_active)["hp"],
            "turn": int(obs.current.turn),
        }

    replay_counts = Counter()
    replay_paths = []
    """),
    code("""
    def play_game(candidate_policy, opponent_policy, candidate_name: str, opponent_name: str,
                  game_id: int, candidate_player: int, candidate_should_go_first: bool):
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions, first_player = 0, None
        candidate_actions = Counter()
        snapshots = []
        obs_log, action_log = [""], [None]
        player_zero_first = (
            candidate_should_go_first if candidate_player == 0
            else not candidate_should_go_first
        )
        policies = (
            {0: ForcedFirstChoice(candidate_policy, player_zero_first), 1: opponent_policy}
            if candidate_player == 0
            else {0: ForcedFirstChoice(opponent_policy, player_zero_first), 1: candidate_policy}
        )
        matchup = f"{candidate_name}_vs_{opponent_name}"
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return ({
                    "status": "start_error", "candidate": candidate_name,
                    "opponent": opponent_name, "matchup": matchup, "game": game_id,
                    "candidate_player": candidate_player,
                    "error_player": start_data.errorPlayer, "error_type": start_data.errorType,
                }, snapshots)

            while decisions < MAX_DECISIONS:
                obs = to_observation_class(obs_dict)
                observed_first = getattr(obs.current, "firstPlayer", None)
                if observed_first in (0, 1):
                    first_player = int(observed_first)
                if obs.current.result != -1:
                    winner = int(obs.current.result)
                    score = 1.0 if winner == candidate_player else 0.0 if winner in (0, 1) else 0.5
                    key = (matchup, candidate_player, first_player == candidate_player, score)
                    replay_path = None
                    if score == 0.0 and replay_counts[key] < REPLAYS_PER_CELL:
                        replay_path = REPLAY_DIR / (
                            f"{matchup}_game_{game_id}_seat_{candidate_player}_"
                            f"first_{first_player}.json"
                        )
                        write_replay(obs_log, action_log, replay_path)
                        replay_counts[key] += 1
                        replay_paths.append(str(replay_path))
                    return ({
                        "status": "finished", "candidate": candidate_name,
                        "opponent": opponent_name, "matchup": matchup, "game": game_id,
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
                chosen_names = [
                    enum_name(OptionType, obs.select.option[index].type) for index in action
                ]
                if player == candidate_player:
                    candidate_actions.update(chosen_names)
                    if obs.select.type == SelectType.MAIN:
                        features = board_features(obs, candidate_player)
                        features.update({
                            "candidate": candidate_name,
                            "opponent": opponent_name,
                            "matchup": matchup,
                            "game": game_id,
                            "candidate_player": candidate_player,
                            "candidate_went_first": first_player == candidate_player,
                            "chosen_action": chosen_names[0] if chosen_names else "SKIP",
                            "available_actions": ",".join(sorted({
                                enum_name(OptionType, option.type) for option in obs.select.option
                            })),
                        })
                        if hasattr(candidate_policy, "_build_plan"):
                            plan = candidate_policy._build_plan(obs)
                            features.update({
                                "plan_confident": bool(plan.confident),
                                "plan_ready": bool(plan.ready),
                                "plan_immediate_ko": bool(plan.immediate_ko),
                                "plan_expected_damage": float(plan.expected_damage),
                                "plan_energy_needed": int(plan.energy_needed),
                                "plan_attacker_id": int(plan.attacker_id),
                            })
                        else:
                            features.update({
                                "plan_confident": False,
                                "plan_ready": False,
                                "plan_immediate_ko": False,
                                "plan_expected_damage": 0.0,
                                "plan_energy_needed": 0,
                                "plan_attacker_id": -1,
                            })
                        snapshots.append(features)
                obs_log.append(replay_observation(obs_dict))
                action_log.append(list(action))
                obs_dict = battle_select(action)
                decisions += 1

            return ({
                "status": "decision_limit", "candidate": candidate_name,
                "opponent": opponent_name, "matchup": matchup, "game": game_id,
                "candidate_player": candidate_player, "first_player": first_player,
                "forced_candidate_went_first": candidate_should_go_first,
                "decisions": decisions,
            }, snapshots)
        except Exception as error:
            return ({
                "status": "exception", "candidate": candidate_name,
                "opponent": opponent_name, "matchup": matchup, "game": game_id,
                "candidate_player": candidate_player, "first_player": first_player,
                "forced_candidate_went_first": candidate_should_go_first,
                "error": f"{type(error).__name__}: {error}", "decisions": decisions,
            }, snapshots)
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    ## 4. Balanced diagnostic tournament

    Run the promoted policy and planner v2 against two controls:

    1. official random, to keep a weak-regression anchor;
    2. frozen pressure-style control, to stress attack timing and early tempo.

    Each matchup uses both candidate seats and both forced turn orders.
    """),
    code("""
    candidates = [("promoted", promoted), ("planner_v2", planner_v2)]
    opponents = [("random", random_control), ("pressure", pressure)]

    results, snapshots = [], []
    game_id = 100_000
    for candidate_name, candidate_policy in candidates:
        for opponent_name, opponent_policy in opponents:
            for candidate_player in (0, 1):
                for candidate_should_go_first in (False, True):
                    for repetition in range(GAMES_PER_CELL):
                        result, game_snapshots = play_game(
                            candidate_policy, opponent_policy,
                            candidate_name, opponent_name,
                            game_id, candidate_player, candidate_should_go_first,
                        )
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
    ## 5. Scores and controlled-cell attribution

    These scores are diagnostic, not promotion gates. The main value is to show
    where the policies lose and which controlled cells need replay review.
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

    attribution = finished.groupby(
        ["matchup", "candidate_player", "candidate_went_first"]
    ).candidate_score.agg(games="size", score_rate="mean")
    display(attribution)
    """),
    md("""
    ## 6. Loss taxonomy

    The labels below are heuristics. They are meant to triage replay review, not
    replace it. A label is useful when it repeatedly appears across controlled
    cells and aligns with replay evidence.
    """),
    code("""
    def label_loss(game_row, game_snapshots: pd.DataFrame) -> str:
        if game_row.candidate_score != 0.0:
            return "not_loss"
        if game_snapshots.empty:
            return "no_candidate_main_decisions"

        first_half = game_snapshots.head(max(1, len(game_snapshots) // 2))
        actions = Counter(game_snapshots.chosen_action)
        available_attack = game_snapshots.available_actions.str.contains("ATTACK", regex=False).any()
        available_retreat = game_snapshots.available_actions.str.contains("RETREAT", regex=False).any()
        immediate_ko_missed = (
            (game_snapshots.plan_immediate_ko == True)
            & (game_snapshots.chosen_action != "ATTACK")
        ).any()
        ready_bench_pressure = (
            (game_snapshots.ready_bench > 0)
            & (game_snapshots.active_energy == 0)
            & game_snapshots.available_actions.str.contains("RETREAT", regex=False)
        ).any()
        early_no_board = (first_half.bench_count.max() == 0 and first_half.ready_attackers.max() == 0)
        low_development = game_snapshots.ready_attackers.max() == 0
        low_attachment = actions.get("ATTACH", 0) == 0 and game_snapshots.active_energy.max() == 0
        late_game_pressure = int(game_row.turn) <= 8

        if early_no_board:
            return "setup"
        if low_development:
            return "attacker_development"
        if low_attachment:
            return "attachment"
        if ready_bench_pressure or (available_retreat and actions.get("RETREAT", 0) == 0):
            return "switch"
        if immediate_ko_missed or (available_attack and actions.get("ATTACK", 0) == 0):
            return "attack_timing"
        if late_game_pressure:
            return "opponent_pressure"
        return "unclear_review_replay"

    loss_rows = []
    for _, row in finished.iterrows():
        game_snapshots = snapshots_df[snapshots_df.game == row.game].copy()
        label = label_loss(row, game_snapshots)
        loss_rows.append({
            "game": int(row.game),
            "candidate": row.candidate,
            "opponent": row.opponent,
            "matchup": row.matchup,
            "candidate_player": int(row.candidate_player),
            "candidate_went_first": bool(row.candidate_went_first),
            "candidate_score": float(row.candidate_score),
            "turn": int(row.turn),
            "label": label,
            "replay_path": row.replay_path,
        })

    loss_df = pd.DataFrame(loss_rows)
    display(loss_df[loss_df.candidate_score == 0.0].sort_values(["matchup", "label", "game"]))
    taxonomy = (
        loss_df[loss_df.candidate_score == 0.0]
        .groupby(["matchup", "label"])
        .size()
        .rename("losses")
        .reset_index()
        .sort_values(["matchup", "losses"], ascending=[True, False])
    )
    display(taxonomy)
    """),
    md("""
    ## 7. Mechanism tables

    These tables connect labels back to observed decisions: action counts,
    readiness, immediate knockout opportunities, and planner confidence.
    """),
    code("""
    action_rows = []
    for result in results:
        for action, count in result.get("candidate_actions", {}).items():
            action_rows.append({
                "matchup": result["matchup"],
                "action": action,
                "count": count,
            })
    action_df = pd.DataFrame(action_rows)
    display(action_df.groupby(["matchup", "action"]).sum().reset_index())

    mechanism = snapshots_df.groupby("matchup").agg(
        main_decisions=("game", "size"),
        ready_rate=("ready_attackers", lambda s: float((s > 0).mean())),
        attack_available_rate=("available_actions", lambda s: float(s.str.contains("ATTACK", regex=False).mean())),
        attack_chosen_rate=("chosen_action", lambda s: float((s == "ATTACK").mean())),
        retreat_available_rate=("available_actions", lambda s: float(s.str.contains("RETREAT", regex=False).mean())),
        retreat_chosen_rate=("chosen_action", lambda s: float((s == "RETREAT").mean())),
        planner_confident_rate=("plan_confident", "mean"),
        planner_immediate_ko_rate=("plan_immediate_ko", "mean"),
        planner_expected_damage=("plan_expected_damage", "mean"),
    )
    display(mechanism)
    """),
    md("""
    ## 8. Evidence export and next action

    Export one JSON file containing the tournament, taxonomy, mechanism tables,
    and replay manifest. Use the dominant loss labels to choose exactly one
    next implementation change.
    """),
    code("""
    payload = {
        "experiment": "loss_taxonomy_and_pressure_opponent",
        "configuration": {
            "base_seed": BASE_SEED,
            "games_per_cell": GAMES_PER_CELL,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "replays_per_cell": REPLAYS_PER_CELL,
        },
        "summaries": summary_df.reset_index().to_dict("records"),
        "attribution": attribution.reset_index().to_dict("records"),
        "taxonomy": taxonomy.to_dict("records"),
        "losses": loss_df.to_dict("records"),
        "mechanism": mechanism.reset_index().to_dict("records"),
        "results": results,
        "snapshots": snapshots,
        "replays": replay_paths,
        "interpretation_rule": (
            "Do not promote from this notebook directly. Pick one next change "
            "only after dominant loss labels and replay review agree."
        ),
    }
    evidence_path = Path("/kaggle/working/loss_taxonomy_experiment.json")
    evidence_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Saved evidence to {evidence_path}")
    print("Next: review one replay per dominant label before changing policy.")
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
