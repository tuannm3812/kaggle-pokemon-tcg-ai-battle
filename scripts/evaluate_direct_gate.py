"""Run a controlled direct gate between one candidate and the promoted agent."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
RESULTS_DIR = SCRATCH / "direct_gates"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


def wilson_interval(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Approximate 95% Wilson interval for binary win-rate style scores."""
    if total <= 0:
        return (0.0, 0.0)
    p = wins / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4))


def summarize(rows: list[dict]) -> dict:
    scores = [float(row["candidate_score"]) for row in rows]
    wins = sum(1 for row in rows if row["candidate_reward"] > 0)
    losses = sum(1 for row in rows if row["candidate_reward"] < 0)
    draws = sum(1 for row in rows if row["candidate_reward"] == 0)
    failures = sum(1 for row in rows if row["status"] != "complete")
    binary_points = int(sum(scores) * 2)
    binary_total = len(rows) * 2
    ci_low, ci_high = wilson_interval(binary_points, binary_total)
    return {
        "games": len(rows),
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "score_rate": round(sum(scores) / len(scores), 4) if scores else None,
        "wilson_score_ci": [ci_low, ci_high],
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="setup_active_v1")
    parser.add_argument("--control", default="promoted")
    parser.add_argument("--games-per-cell", type=int, default=20)
    parser.add_argument("--max-decisions", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=20260628)
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)

    candidate_path = suite.AGENT_PATHS.get(args.candidate)
    if candidate_path is None or not candidate_path.exists():
        raise FileNotFoundError(f"Unknown or missing candidate: {args.candidate}")
    if args.control == "promoted":
        control_path = ROOT / "agent" / "main.py"
    elif args.control == "official_random":
        control_path = sdk_dir / "main.py"
    else:
        control_path = suite.AGENT_PATHS.get(args.control)
    if control_path is None or not control_path.exists():
        raise FileNotFoundError(f"Unknown or missing control: {args.control}")

    candidate = suite.load_local_policy(args.candidate, candidate_path)
    if args.control == "official_random":
        random_module = suite.load_module("official_random_direct_gate", control_path, cwd=suite.RUNTIME_ROOT)
        control = suite.Policy(name=args.control, agent=random_module.agent, deck=candidate.deck)
    else:
        control = suite.load_local_policy(args.control, control_path)

    rows = []
    for candidate_seat in (0, 1):
        for player_zero_first in (False, True):
            for repeat in range(args.games_per_cell):
                seed = (
                    args.seed
                    + 10_000 * candidate_seat
                    + 1_000 * int(player_zero_first)
                    + repeat
                )
                try:
                    row = suite.run_game(
                        candidate=candidate,
                        opponent=control,
                        candidate_seat=candidate_seat,
                        player_zero_first=player_zero_first,
                        seed=seed,
                        max_decisions=args.max_decisions,
                    )
                except Exception as exc:  # noqa: BLE001
                    row = {
                        "status": "error",
                        "seed": seed,
                        "candidate_reward": 0,
                        "candidate_score": 0,
                        "error": repr(exc),
                        "candidate_seat": candidate_seat,
                        "player_zero_first": player_zero_first,
                    }
                row["candidate"] = args.candidate
                row["control"] = args.control
                rows.append(row)

    by_cell = defaultdict(list)
    for row in rows:
        by_cell[(row["candidate_seat"], row["player_zero_first"])].append(row)

    cell_summary = {
        f"seat_{seat}_player_zero_first_{str(first).lower()}": summarize(cell_rows)
        for (seat, first), cell_rows in sorted(by_cell.items())
    }
    summary = summarize(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / f"{args.candidate}_vs_{args.control}.json"
    output = {
        "candidate": args.candidate,
        "control": args.control,
        "games_per_cell": args.games_per_cell,
        "max_decisions": args.max_decisions,
        "seed": args.seed,
        "summary": summary,
        "cells": cell_summary,
        "rows": rows,
    }
    results_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(
        f"{args.candidate}_vs_{args.control}: "
        f"{summary['wins']}-{summary['losses']}"
        f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
        f"score={summary['score_rate']}, ci={summary['wilson_score_ci']}, "
        f"failures={summary['failures']}"
    )
    for key, value in cell_summary.items():
        print(
            f"{key}: {value['wins']}-{value['losses']}"
            f"{'-' + str(value['draws']) if value['draws'] else ''}, "
            f"score={value['score_rate']}"
        )
    print(f"Wrote {results_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
