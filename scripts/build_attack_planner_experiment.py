"""Generate the controlled Kaggle experiment for Abomasnow planner v1."""

from pathlib import Path
import textwrap

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "08_abomasnow_attack_planner_experiment.ipynb"
CANDIDATE_SOURCE = (ROOT / "candidates" / "abomasnow_planner_v1" / "main.py").read_text()


def md(value: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(value).strip())


def code(value: str):
    return nbf.v4.new_code_cell(textwrap.dedent(value).strip())


CELLS = [
    md("""
    # Mega Abomasnow/Kyogre Attack Planner Experiment

    **Purpose.** Test whether a compact, stateless attack plan improves on the
    promoted development-first ordering.

    **Single intended policy change.** Reconstruct an attacker plan from each
    observation and coordinate evolution, attachment, switching, attack choice,
    setup, search, and discard decisions around it. The 60-card deck is frozen.

    **Primary gate.** Planner versus promoted control. Planner versus official
    random is a regression screen, not proof of ladder strength.
    """),
    md("""
    ## 1. Configuration and frozen candidate source

    The candidate source is embedded by the deterministic local builder. This
    avoids changing the private production-agent dataset before promotion. Each
    matchup uses a balanced 2x2 candidate-seat by forced-turn-order design.
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

    BASE_SEED = 20260622
    GAMES_PER_CELL = 10
    MAX_DECISIONS = 5_000
    BOOTSTRAP_SAMPLES = 10_000
    REPLAYS_PER_CELL = 1
    WORK_DIR = Path("/kaggle/working/attack_planner_runtime")
    REPLAY_DIR = Path("/kaggle/working/planner_replays")
    CANDIDATE_SOURCE = {CANDIDATE_SOURCE!r}

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
    sources = [
        path.parent for path in sorted(Path("/kaggle/input").rglob("main.py"))
        if "sample_submission" not in path.parts and "cg" not in path.parts
    ]
    production_dir = next(
        (path for path in sources if (path / "main.py").exists() and (path / "deck.csv").exists()),
        None,
    )
    if production_dir is None:
        raise FileNotFoundError("Attach the private production agent-source dataset.")
    print(f"Promoted control: {{production_dir / 'main.py'}}")
    print(f"Official random: {{sample_dir / 'main.py'}}")
    """),
    md("""
    ## 2. Isolated simulator and policies

    Copy the official runtime, stage the frozen production source, and write the
    embedded candidate to working storage. Hash-equivalent deck lists are
    required before any game runs.
    """),
    code("""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    shutil.copytree(sample_dir, WORK_DIR)
    shutil.copy2(production_dir / "main.py", WORK_DIR / "baseline_main.py")
    shutil.copy2(production_dir / "deck.csv", WORK_DIR / "deck.csv")
    (WORK_DIR / "candidate_main.py").write_text(CANDIDATE_SOURCE, encoding="utf-8")
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(WORK_DIR))
    from cg.api import OptionType, SelectContext, SelectType, to_observation_class
    from cg.game import battle_finish, battle_select, battle_start, visualize_data

    candidate = load_module("abomasnow_planner_v1", WORK_DIR / "candidate_main.py")
    baseline = load_module("promoted_development_first", WORK_DIR / "baseline_main.py")
    random_control = load_module("official_random_control", sample_dir / "main.py")
    deck = candidate.read_deck_csv()
    assert deck == baseline.read_deck_csv() and len(deck) == 60
    print("PASS: candidate and controls share the frozen 60-card deck")
    """),
    md("""
    ## 3. Controlled first-player choice and telemetry

    The wrapper intercepts only `IS_FIRST`; all later choices go to the named
    frozen policy. Every action is contract-checked. At candidate main decisions
    we record the reconstructed attacker, readiness, expected damage, immediate
    knockout flag, chosen action, and available action types.
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

    replay_counts = Counter()
    replay_paths = []
    """),
    code("""
    def play_game(policies: dict, game_id: int, candidate_player: int, matchup: str):
        random.seed(BASE_SEED + game_id)
        started = time.perf_counter()
        decisions, first_player = 0, None
        candidate_actions = Counter()
        snapshots = []
        obs_log, action_log = [""], [None]
        try:
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                return ({
                    "status": "start_error", "matchup": matchup, "game": game_id,
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
                    key = (matchup, candidate_player, first_player == candidate_player)
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
                        "status": "finished", "matchup": matchup, "game": game_id,
                        "candidate_player": candidate_player, "first_player": first_player,
                        "candidate_went_first": first_player == candidate_player,
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
                        plan = candidate._build_plan(obs)
                        snapshots.append({
                            "matchup": matchup, "game": game_id,
                            "candidate_player": candidate_player,
                            "candidate_went_first": first_player == candidate_player,
                            "turn": int(obs.current.turn),
                            "chosen_action": chosen_names[0] if chosen_names else "SKIP",
                            "available_actions": ",".join(sorted({
                                enum_name(OptionType, option.type) for option in obs.select.option
                            })),
                            "plan_confident": bool(plan.confident),
                            "attacker_id": int(plan.attacker_id),
                            "attacker_area": str(plan.attacker_area),
                            "attack_id": int(plan.attack_id),
                            "expected_damage": float(plan.expected_damage),
                            "target_hp": int(plan.target_hp),
                            "energy_needed": int(plan.energy_needed),
                            "ready": bool(plan.ready),
                            "immediate_ko": bool(plan.immediate_ko),
                        })
                obs_log.append(replay_observation(obs_dict))
                action_log.append(list(action))
                obs_dict = battle_select(action)
                decisions += 1

            return ({
                "status": "decision_limit", "matchup": matchup, "game": game_id,
                "candidate_player": candidate_player, "first_player": first_player,
                "decisions": decisions,
            }, snapshots)
        except Exception as error:
            return ({
                "status": "exception", "matchup": matchup, "game": game_id,
                "candidate_player": candidate_player, "first_player": first_player,
                "error": f"{type(error).__name__}: {error}", "decisions": decisions,
            }, snapshots)
        finally:
            try:
                battle_finish()
            except Exception:
                pass
    """),
    md("""
    ## 4. Balanced two-matchup tournament

    For each opponent, run ten games in each seat/turn-order cell. Post-run
    assertions verify the forced order and exact cell balance before results are
    interpreted.
    """),
    code("""
    matchups = [
        ("planner_vs_promoted", baseline),
        ("planner_vs_random", random_control),
    ]
    results, snapshots = [], []
    game_id = 80_000
    for matchup, opponent in matchups:
        for candidate_player in (0, 1):
            for candidate_should_go_first in (False, True):
                for repetition in range(GAMES_PER_CELL):
                    player_zero_first = (
                        candidate_should_go_first if candidate_player == 0
                        else not candidate_should_go_first
                    )
                    if candidate_player == 0:
                        policies = {0: ForcedFirstChoice(candidate, player_zero_first), 1: opponent}
                    else:
                        policies = {0: ForcedFirstChoice(opponent, player_zero_first), 1: candidate}
                    result, game_snapshots = play_game(
                        policies, game_id, candidate_player, matchup
                    )
                    result["forced_candidate_went_first"] = candidate_should_go_first
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
    ## 5. Outcome uncertainty and promotion gate

    Bootstrap each matchup independently. Planner promotion requires zero
    failures, a primary interval above parity against the promoted control, and
    no regression against random. Otherwise hold or reject without modifying
    `agent/main.py`.
    """),
    code("""
    rng = np.random.default_rng(BASE_SEED)
    summaries = []
    for matchup, group in finished.groupby("matchup"):
        scores = group.candidate_score.to_numpy(dtype=float)
        boot = rng.choice(scores, size=(BOOTSTRAP_SAMPLES, len(scores)), replace=True).mean(axis=1)
        summaries.append({
            "matchup": matchup, "games": len(scores),
            "wins": int((scores == 1.0).sum()),
            "draws": int((scores == 0.5).sum()),
            "losses": int((scores == 0.0).sum()),
            "score_rate": float(scores.mean()),
            "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)),
        })
    summary_df = pd.DataFrame(summaries).set_index("matchup")
    display(summary_df)

    primary = summary_df.loc["planner_vs_promoted"]
    regression = summary_df.loc["planner_vs_random"]
    if len(failures):
        decision = "REJECT: runtime failures"
    elif primary.ci_low > 0.5 and regression.ci_low > 0.5:
        decision = "PROMOTE: planner clears primary and regression gates"
    elif primary.ci_high < 0.5:
        decision = "REJECT: planner is worse than promoted control"
    else:
        decision = "HOLD: primary interval overlaps parity"
    print(f"Decision: {decision}")
    """),
    md("""
    ## 6. Seat, turn-order, and mechanism checks

    Stratified results test whether an apparent gain is confined to one seat or
    turn order. Planner telemetry checks the intended mechanism: confident plans,
    attacker mix, readiness, immediate knockouts, and coordinated action choice.
    """),
    code("""
    attribution = finished.groupby(
        ["matchup", "candidate_player", "candidate_went_first"]
    ).candidate_score.agg(games="size", score_rate="mean")
    display(attribution)

    plan_summary = snapshots_df.groupby("matchup").agg(
        main_decisions=("game", "size"),
        confident_rate=("plan_confident", "mean"),
        ready_rate=("ready", "mean"),
        immediate_ko_rate=("immediate_ko", "mean"),
        mean_expected_damage=("expected_damage", "mean"),
        mean_energy_needed=("energy_needed", "mean"),
    )
    display(plan_summary)
    display(pd.crosstab(snapshots_df.attacker_id, snapshots_df.chosen_action))

    action_rows = []
    for result in results:
        for action, count in result.get("candidate_actions", {}).items():
            action_rows.append({"matchup": result["matchup"], "action": action, "count": count})
    action_df = pd.DataFrame(action_rows).groupby(["matchup", "action"], as_index=False).sum()
    display(action_df.pivot(index="action", columns="matchup", values="count").fillna(0))
    """),
    md("""
    ## 7. Evidence export

    Save aggregate results, every game, planner snapshots, and the bounded replay
    manifest. Replay files remain diagnostic and must not be committed.
    """),
    code("""
    payload = {
        "candidate": "abomasnow_planner_v1",
        "single_change": "stateless attack-plan coordination on frozen deck",
        "configuration": {
            "base_seed": BASE_SEED, "games_per_cell": GAMES_PER_CELL,
            "replays_per_cell": REPLAYS_PER_CELL,
            "simulator_seed_exposed": False,
        },
        "decision": decision,
        "summaries": summary_df.reset_index().to_dict("records"),
        "attribution": attribution.reset_index().to_dict("records"),
        "plan_summary": plan_summary.reset_index().to_dict("records"),
        "results": results,
        "snapshots": snapshots,
        "replays": replay_paths,
    }
    evidence_path = Path("/kaggle/working/abomasnow_planner_experiment.json")
    evidence_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Saved evidence to {evidence_path}")
    """),
    md("""
    ## 8. Interpretation

    Promote only the planner policy if the stated gate clears and replay review
    supports the mechanism. A hold leaves production unchanged and should use
    the changed-action and replay evidence to refine one planner component. The
    next strength gate after promotion is a frozen author-style opponent.
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
