"""Package and locally validate a Kaggle submission candidate.

The archive layout matches the competition expectation:

- main.py
- deck.csv
- cg/

By default this packages the current promotion candidate,
``planner_main_only_v1``.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import importlib.util
import json
import random
import shutil
import sys
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
PACKAGE_ROOT = SCRATCH / "submission_packages"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_action(obs: object, action: list[int]) -> None:
    select = obs.select
    if not isinstance(action, list):
        raise TypeError(f"Action must be list[int], got {type(action).__name__}")
    if not all(isinstance(index, int) for index in action):
        raise TypeError(f"Action contains non-int values: {action!r}")
    if len(action) != len(set(action)):
        raise ValueError(f"Action contains duplicate option indices: {action!r}")
    if not (select.minCount <= len(action) <= select.maxCount):
        raise ValueError(
            f"Action count {len(action)} outside [{select.minCount}, {select.maxCount}]"
        )
    if any(index < 0 or index >= len(select.option) for index in action):
        raise IndexError(f"Action index outside option range: {action!r}")


def stage_candidate(candidate: str) -> tuple[Path, Path]:
    candidate_dir = ROOT / "candidates" / candidate
    if candidate == "agent":
        candidate_dir = ROOT / "agent"
    if not candidate_dir.exists():
        raise FileNotFoundError(f"Candidate directory not found: {candidate_dir}")
    source_main = candidate_dir / "main.py"
    source_deck = candidate_dir / "deck.csv"
    if not source_main.exists() or not source_deck.exists():
        raise FileNotFoundError(f"Candidate must contain main.py and deck.csv: {candidate_dir}")

    sdk_dir = suite.find_sdk_dir()
    package_dir = PACKAGE_ROOT / candidate
    stage_dir = package_dir / "stage"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(sdk_dir / "cg", stage_dir / "cg")
    shutil.copy2(source_main, stage_dir / "main.py")
    shutil.copy2(source_deck, stage_dir / "deck.csv")
    return package_dir, stage_dir


def static_validate(stage_dir: Path) -> dict[str, Any]:
    main_path = stage_dir / "main.py"
    deck_path = stage_dir / "deck.csv"
    cg_dir = stage_dir / "cg"
    if not main_path.exists():
        raise FileNotFoundError(main_path)
    if not deck_path.exists():
        raise FileNotFoundError(deck_path)
    if not cg_dir.exists():
        raise FileNotFoundError(cg_dir)
    compile(main_path.read_text(encoding="utf-8"), str(main_path), "exec")
    deck = [int(line.strip()) for line in deck_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards in deck.csv, found {len(deck)}")
    return {
        "main_bytes": main_path.stat().st_size,
        "deck_count": len(deck),
        "cg_files": sum(1 for path in cg_dir.rglob("*") if path.is_file()),
    }


def smoke_test(stage_dir: Path, games: int, max_decisions: int, seed: int) -> dict[str, Any]:
    old_sys_path = list(sys.path)
    sys.path.insert(0, str(stage_dir))
    try:
        from cg.api import to_observation_class
        from cg.game import battle_select, battle_start

        module = load_module("staged_submission_main", stage_dir / "main.py")
        deck = module.read_deck_csv() if hasattr(module, "read_deck_csv") else module.agent({})
        results = []
        for game in range(games):
            game_seed = seed + game
            random.seed(game_seed)
            try:
                import numpy as np

                np.random.seed(game_seed % (2**32 - 1))
            except Exception:
                pass
            obs_dict, start_data = battle_start(deck, deck)
            if obs_dict is None:
                raise RuntimeError(
                    f"battle_start failed: {getattr(start_data, 'errorType', None)} "
                    f"player={getattr(start_data, 'errorPlayer', None)}"
                )
            for decision in range(max_decisions):
                obs = to_observation_class(obs_dict)
                if obs.current.result != -1:
                    results.append(
                        {
                            "game": game,
                            "status": "complete",
                            "winner": int(obs.current.result),
                            "decisions": decision,
                        }
                    )
                    break
                action = module.agent(obs_dict)
                validate_action(obs, action)
                obs_dict = battle_select(action)
            else:
                raise RuntimeError(f"Smoke game {game} reached decision limit {max_decisions}")
        return {"games": games, "results": results}
    finally:
        sys.path[:] = old_sys_path


def write_archive(stage_dir: Path, archive_path: Path) -> list[str]:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    def include_filter(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
        parts = Path(info.name).parts
        if "__pycache__" in parts or info.name.endswith((".pyc", ".pyo")):
            return None
        return info

    with tarfile.open(archive_path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for member in ("main.py", "deck.csv", "cg"):
            archive.add(stage_dir / member, arcname=member, filter=include_filter)
    with tarfile.open(archive_path, "r:gz") as archive:
        members = sorted(archive.getnames())
    required = {"main.py", "deck.csv", "cg/api.py", "cg/game.py"}
    missing = [member for member in required if member not in members]
    if missing:
        raise ValueError(f"Archive missing required members: {missing}")
    return members


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="planner_main_only_v1")
    parser.add_argument("--games", type=int, default=6)
    parser.add_argument("--max-decisions", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=2026062811)
    args = parser.parse_args()

    package_dir, stage_dir = stage_candidate(args.candidate)
    static_info = static_validate(stage_dir)
    smoke_info = smoke_test(
        stage_dir=stage_dir,
        games=args.games,
        max_decisions=args.max_decisions,
        seed=args.seed,
    )
    archive_path = package_dir / "submission.tar.gz"
    members = write_archive(stage_dir, archive_path)
    report = {
        "candidate": args.candidate,
        "archive": str(archive_path.relative_to(ROOT)),
        "archive_bytes": archive_path.stat().st_size,
        "static": static_info,
        "smoke": smoke_info,
        "member_count": len(members),
        "members_preview": members[:12],
    }
    report_path = package_dir / "package_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {archive_path.relative_to(ROOT)}")
    print(f"Wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
