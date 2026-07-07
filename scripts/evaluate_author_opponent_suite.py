"""Evaluate local candidates against sanitized author-reference policies.

This script builds a stronger local screen than self-play/random-only tests.
It does not redistribute author notebook code in the repository; instead it
loads the extracted notebooks from ``scratch/author_references`` when present,
cuts off packaging cells, and runs the strategy code in an isolated runtime.

The first suite intentionally runs each author policy on our promoted deck.
That is not a perfect recreation of the author's submitted deck, but it is a
useful pressure test of action-selection logic while keeping deck composition
constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import importlib.util
import json
import os
import random
import shutil
import sys
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
AUTHOR_ROOT = SCRATCH / "author_references"
RUNTIME_ROOT = Path(os.environ.get("POKEMON_TCG_RUNTIME_ROOT", Path(tempfile.gettempdir()) / "pokemon_tcg_author_suite_runtime"))
RESULTS_PATH = SCRATCH / "author_opponent_suite_results.json"

SDK_CANDIDATES = (
    SCRATCH / "competition_files" / "extracted_sample" / "sample_submission" / "sample_submission",
    SCRATCH / "competition_files" / "sample_submission" / "sample_submission",
)

AGENT_PATHS = {
    "promoted": ROOT / "agent" / "main.py",
    "planner_v2": ROOT / "candidates" / "abomasnow_planner_v2" / "main.py",
    "tactical_ko_v1": ROOT / "candidates" / "tactical_ko_v1" / "main.py",
    "hybrid_card_ko_v1": ROOT / "candidates" / "hybrid_card_ko_v1" / "main.py",
    "card_selection_v1": ROOT / "candidates" / "card_selection_v1" / "main.py",
    "attach_from_v1": ROOT / "candidates" / "attach_from_v1" / "main.py",
    "setup_active_v1": ROOT / "candidates" / "setup_active_v1" / "main.py",
    "setup_first_snover_v1": ROOT / "candidates" / "setup_first_snover_v1" / "main.py",
    "setup_second_kyogre_v1": ROOT / "candidates" / "setup_second_kyogre_v1" / "main.py",
    "planner_main_only_v1": ROOT / "candidates" / "planner_main_only_v1" / "main.py",
    "planner_no_retreat_v1": ROOT / "candidates" / "planner_no_retreat_v1" / "main.py",
    "lucario_adapted_v1": ROOT / "candidates" / "lucario_adapted_v1" / "main.py",
    "lucario_adapted_v2": ROOT / "candidates" / "lucario_adapted_v2" / "main.py",
    "lucario_adapted_v3": ROOT / "candidates" / "lucario_adapted_v3" / "main.py",
    "iono_adapted_v1": ROOT / "candidates" / "iono_adapted_v1" / "main.py",
    "iono_public_sample_v1": ROOT / "candidates" / "iono_public_sample_v1" / "main.py",
    "lucario_public_sample_v1": ROOT / "candidates" / "lucario_public_sample_v1" / "main.py",
    "lucario_public_sample_v2": ROOT / "candidates" / "lucario_public_sample_v2" / "main.py",
    "lucario_public_sample_v3": ROOT / "candidates" / "lucario_public_sample_v3" / "main.py",
    "lucario_public_sample_v4": ROOT / "candidates" / "lucario_public_sample_v4" / "main.py",
    "lucario_public_sample_v5": ROOT / "candidates" / "lucario_public_sample_v5" / "main.py",
    "lucario_public_sample_v6": ROOT / "candidates" / "lucario_public_sample_v6" / "main.py",
    "lucario_public_sample_v7": ROOT / "candidates" / "lucario_public_sample_v7" / "main.py",
    "kojimar_simple_baseline_v1": ROOT / "candidates" / "kojimar_simple_baseline_v1" / "main.py",
    "koushikrudra_libraryout_v1": ROOT / "candidates" / "koushikrudra_libraryout_v1" / "main.py",
    "kojimar_simple_baseline_v2": ROOT / "candidates" / "kojimar_simple_baseline_v2" / "main.py",
    "kojimar_simple_baseline_v3": ROOT / "candidates" / "kojimar_simple_baseline_v3" / "main.py",
    "kojimar_simple_baseline_v4_second": ROOT / "candidates" / "kojimar_simple_baseline_v4_second" / "main.py",
    "kojimar_simple_baseline_v5_metal_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v5_metal_pressure" / "main.py",
    "kojimar_simple_baseline_v6_metal_conditional": ROOT / "candidates" / "kojimar_simple_baseline_v6_metal_conditional" / "main.py",
    "kojimar_simple_baseline_v6_alakazam_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v6_alakazam_pressure" / "main.py",
    "kojimar_simple_baseline_v7_boss_ko_only": ROOT / "candidates" / "kojimar_simple_baseline_v7_boss_ko_only" / "main.py",
    "kojimar_simple_baseline_v8_public_boss_guard": ROOT / "candidates" / "kojimar_simple_baseline_v8_public_boss_guard" / "main.py",
    "kojimar_simple_baseline_v9_strict_boss_guard": ROOT / "candidates" / "kojimar_simple_baseline_v9_strict_boss_guard" / "main.py",
    "kojimar_simple_baseline_v10_phantump_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v10_phantump_pressure" / "main.py",
    "kojimar_simple_baseline_v11_metal_boss_guard": ROOT / "candidates" / "kojimar_simple_baseline_v11_metal_boss_guard" / "main.py",
    "kojimar_simple_baseline_v12_dragapult_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v12_dragapult_pressure" / "main.py",
    "kojimar_simple_baseline_v13_v8_dragapult_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v13_v8_dragapult_pressure" / "main.py",
    "kojimar_simple_baseline_v14_v8_prefer_second": ROOT / "candidates" / "kojimar_simple_baseline_v14_v8_prefer_second" / "main.py",
    "kojimar_simple_baseline_v6_meta_pressure": ROOT / "candidates" / "kojimar_simple_baseline_v6_meta_pressure" / "main.py",
    "anti_planner_pressure_v1": ROOT / "controls" / "anti_planner_pressure_v1" / "main.py",
}

AUTHOR_POLICIES = {
    "author_abomasnow_policy": AUTHOR_ROOT / "abomasnow" / "extracted_code.py",
    "author_lucario_policy": AUTHOR_ROOT / "lucario" / "extracted_code.py",
    "author_dragapult_policy": AUTHOR_ROOT / "dragapult" / "extracted_code.py",
    "author_iono_policy": AUTHOR_ROOT / "iono" / "extracted_code.py",
}


@dataclass
class Policy:
    name: str
    agent: Callable[[dict[str, Any]], list[int]]
    deck: list[int]


def reset_policy_state(policy: Policy) -> None:
    """Reset common module-level agent state before a new local game.

    Kaggle episode workers start agents from a clean process, but this local
    evaluator reuses imported modules across many batched games. Several sample
    agents keep turn-level globals such as ``pre_turn``, ``ability_used``, and
    ``plan``. Resetting them before every game keeps local gates from measuring
    cross-game residue.
    """
    namespace = getattr(policy.agent, "__globals__", {})
    if "pre_turn" in namespace:
        namespace["pre_turn"] = -1
    if "ability_used" in namespace:
        namespace["ability_used"] = False
    attack_plan = namespace.get("AttackPlan")
    if "plan" in namespace and callable(attack_plan):
        namespace["plan"] = attack_plan()


def find_sdk_dir() -> Path:
    for candidate in SDK_CANDIDATES:
        if (candidate / "cg").exists() and (candidate / "main.py").exists():
            return candidate
    matches = sorted(SCRATCH.rglob("sample_submission/main.py"))
    for match in matches:
        parent = match.parent
        if (parent / "cg").exists():
            return parent
    raise FileNotFoundError(
        "Could not find the official sample_submission runtime under scratch/. "
        "Download/extract the competition sample files before running this suite."
    )


def read_deck(path: Path) -> list[int]:
    deck = [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards in {path}, found {len(deck)}.")
    return deck


def load_module(name: str, path: Path, cwd: Path | None = None):
    old_cwd = Path.cwd()
    if cwd is not None:
        os.chdir(cwd)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if cwd is not None:
            os.chdir(old_cwd)


def sanitize_author_source(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    cutoff_markers = ("\nimport tarfile", "\nwith tarfile.open", "\nos.remove(")
    cutoff = len(text)
    for marker in cutoff_markers:
        index = text.find(marker)
        if index >= 0:
            cutoff = min(cutoff, index)
    sanitized = text[:cutoff].rstrip() + "\n"
    if "def agent(" not in sanitized:
        raise ValueError(f"No agent() function found before packaging cutoff in {source_path}")
    return sanitized


def stage_runtime(sdk_dir: Path) -> None:
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT, ignore_errors=True)
    shutil.copytree(
        sdk_dir,
        RUNTIME_ROOT,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        dirs_exist_ok=True,
    )
    shutil.copy2(ROOT / "agent" / "deck.csv", RUNTIME_ROOT / "deck.csv")

    # Repeated local evaluations in a synced Drive workspace can leave stale
    # ``cg`` modules pointing at an old runtime. Force the freshly staged SDK to
    # the front and reload it on the next import.
    runtime_path = str(RUNTIME_ROOT.resolve())
    sys.path[:] = [entry for entry in sys.path if entry != runtime_path]
    sys.path.insert(0, runtime_path)
    for module_name in list(sys.modules):
        if module_name == "cg" or module_name.startswith("cg."):
            del sys.modules[module_name]


def load_local_policy(name: str, path: Path) -> Policy:
    if not path.exists():
        raise FileNotFoundError(path)
    module_dir = RUNTIME_ROOT / f"local_{name}"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_path = module_dir / "main.py"
    shutil.copy2(path, module_path)

    source_deck = path.with_name("deck.csv")
    if not source_deck.exists():
        source_deck = ROOT / "agent" / "deck.csv"
    shutil.copy2(source_deck, module_dir / "deck.csv")

    module = load_module(f"local_{name}", module_path, cwd=module_dir)
    if not hasattr(module, "agent"):
        raise AttributeError(f"{path} does not expose agent()")
    if hasattr(module, "read_deck_csv"):
        deck = module.read_deck_csv()
    else:
        deck = read_deck(module_dir / "deck.csv")
    return Policy(name=name, agent=module.agent, deck=deck)


def load_author_policy(name: str, source_path: Path) -> Policy:
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    module_dir = RUNTIME_ROOT / name
    module_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "agent" / "deck.csv", module_dir / "deck.csv")
    module_path = module_dir / "main.py"
    module_path.write_text(sanitize_author_source(source_path), encoding="utf-8")
    module = load_module(f"sanitized_{name}", module_path, cwd=module_dir)
    deck = getattr(module, "my_deck", read_deck(module_dir / "deck.csv"))
    return Policy(name=name, agent=module.agent, deck=list(deck))


def choose_with_forced_first(policy: Policy, obs_dict: dict[str, Any], player_zero_first: bool) -> list[int]:
    from cg.api import OptionType, SelectContext, to_observation_class

    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return policy.deck
    if obs.select.context == SelectContext.IS_FIRST:
        desired = OptionType.YES if player_zero_first else OptionType.NO
        matches = [i for i, option in enumerate(obs.select.option) if option.type == desired]
        if matches:
            return [matches[0]]
    return policy.agent(obs_dict)


def run_game(
    candidate: Policy,
    opponent: Policy,
    candidate_seat: int,
    player_zero_first: bool,
    seed: int,
    max_decisions: int,
) -> dict[str, Any]:
    from cg.api import to_observation_class
    from cg.game import battle_select, battle_start

    reset_policy_state(candidate)
    reset_policy_state(opponent)
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed % (2**32 - 1))
    except Exception:
        pass
    decks = [candidate.deck, opponent.deck] if candidate_seat == 0 else [opponent.deck, candidate.deck]
    policies = [None, None]
    policies[candidate_seat] = candidate
    policies[1 - candidate_seat] = opponent

    obs_dict, start_data = battle_start(decks[0], decks[1])
    if obs_dict is None:
        return {
            "status": "start_error",
            "seed": seed,
            "candidate_reward": 0,
            "candidate_score": 0,
            "error": f"{getattr(start_data, 'errorType', None)} player={getattr(start_data, 'errorPlayer', None)}",
            "candidate_seat": candidate_seat,
            "player_zero_first": player_zero_first,
        }

    for decision in range(max_decisions):
        obs = to_observation_class(obs_dict)
        if obs.current.result != -1:
            winner = int(obs.current.result)
            score = 1.0 if winner == candidate_seat else 0.0 if winner in (0, 1) else 0.5
            candidate_reward = 1 if score == 1.0 else -1 if score == 0.0 else 0
            return {
                "status": "complete",
                "seed": seed,
                "decisions": decision,
                "candidate_reward": candidate_reward,
                "candidate_score": score,
                "winner": winner,
                "candidate_seat": candidate_seat,
                "player_zero_first": player_zero_first,
            }

        player_index = int(obs.current.yourIndex)
        action = choose_with_forced_first(
            policies[player_index],
            obs_dict,
            player_zero_first=player_zero_first,
        )
        obs_dict = battle_select(action)

    return {
        "status": "max_decisions",
        "seed": seed,
        "decisions": max_decisions,
        "candidate_reward": 0,
        "candidate_score": 0.5,
        "candidate_seat": candidate_seat,
        "player_zero_first": player_zero_first,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [row["candidate_score"] for row in rows]
    wins = sum(1 for row in rows if row["candidate_reward"] > 0)
    draws = sum(1 for row in rows if row["candidate_reward"] == 0)
    losses = sum(1 for row in rows if row["candidate_reward"] < 0)
    failures = sum(1 for row in rows if row["status"] != "complete")
    return {
        "games": len(rows),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "score_rate": round(sum(scores) / len(scores), 4) if scores else None,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        nargs="+",
        default=None,
        choices=sorted(AGENT_PATHS),
        help="Optional candidate keys to evaluate. Defaults to every registered candidate.",
    )
    parser.add_argument("--games-per-cell", type=int, default=3)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260627)
    args = parser.parse_args()

    sdk_dir = find_sdk_dir()
    stage_runtime(sdk_dir)

    candidate_items = (
        [(name, AGENT_PATHS[name]) for name in args.candidates]
        if args.candidates
        else list(AGENT_PATHS.items())
    )
    candidates = [load_local_policy(name, path) for name, path in candidate_items if path.exists()]
    opponents = [load_author_policy(name, path) for name, path in AUTHOR_POLICIES.items() if path.exists()]
    if not opponents:
        raise FileNotFoundError(f"No author references found under {AUTHOR_ROOT}")

    all_rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        for opponent in opponents:
            matchup = f"{candidate.name}_vs_{opponent.name}"
            rows = []
            for candidate_seat in (0, 1):
                for player_zero_first in (False, True):
                    for repeat in range(args.games_per_cell):
                        seed = (
                            args.seed
                            + 10_000 * len(all_rows)
                            + 100 * candidate_seat
                            + 10 * int(player_zero_first)
                            + repeat
                        )
                        try:
                            row = run_game(
                                candidate=candidate,
                                opponent=opponent,
                                candidate_seat=candidate_seat,
                                player_zero_first=player_zero_first,
                                seed=seed,
                                max_decisions=args.max_decisions,
                            )
                        except Exception as exc:  # noqa: BLE001 - keep batch running and report failures.
                            row = {
                                "status": "error",
                                "seed": seed,
                                "candidate_reward": 0,
                                "candidate_score": 0,
                                "error": repr(exc),
                                "candidate_seat": candidate_seat,
                                "player_zero_first": player_zero_first,
                            }
                        row["candidate"] = candidate.name
                        row["opponent"] = opponent.name
                        row["matchup"] = matchup
                        rows.append(row)
                        all_rows.append(row)
            summaries[matchup] = summarize(rows)
            summary = summaries[matchup]
            print(
                f"{matchup}: {summary['wins']}-{summary['losses']}"
                f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
                f"score={summary['score_rate']}, failures={summary['failures']}"
            )

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "games_per_cell": args.games_per_cell,
                "max_decisions": args.max_decisions,
                "sdk_dir": str(sdk_dir.relative_to(ROOT)),
                "deck_mode": "all policies run on agent/deck.csv to isolate action-selection logic",
                "summaries": summaries,
                "rows": all_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
