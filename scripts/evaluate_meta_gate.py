"""Run a compact meta gate for candidate promotion decisions.

This wrapper combines the direct gates that matter most after the Kojimar v1
submission became the active best:

- candidate vs active best (`kojimar_simple_baseline_v1`);
- candidate vs previous strong Lucario (`lucario_public_sample_v3`);
- candidate vs library-out/control (`koushikrudra_libraryout_v1`);
- candidate vs official random;
- candidate vs reconstructed author archetype decks.

It writes one JSON summary under ``scratch/meta_gates`` and delegates game
execution to the existing evaluators.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import argparse
import json
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
RESULTS_DIR = SCRATCH / "meta_gates"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_archetype_deck_suite as archetype_suite  # noqa: E402
from scripts import evaluate_author_opponent_suite as suite  # noqa: E402
from scripts.evaluate_direct_gate import summarize  # noqa: E402


def run_direct_rows(
    candidate: suite.Policy,
    opponent: suite.Policy,
    games_per_cell: int,
    max_decisions: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Run a seat/first-player balanced direct matchup."""
    rows: list[dict[str, Any]] = []
    for candidate_seat in (0, 1):
        for player_zero_first in (False, True):
            for repeat in range(games_per_cell):
                game_seed = seed + 10_000 * candidate_seat + 1_000 * int(player_zero_first) + repeat
                try:
                    row = suite.run_game(
                        candidate=candidate,
                        opponent=opponent,
                        candidate_seat=candidate_seat,
                        player_zero_first=player_zero_first,
                        seed=game_seed,
                        max_decisions=max_decisions,
                    )
                except Exception as exc:  # noqa: BLE001
                    row = {
                        "status": "error",
                        "seed": game_seed,
                        "candidate_reward": 0,
                        "candidate_score": 0,
                        "error": repr(exc),
                        "candidate_seat": candidate_seat,
                        "player_zero_first": player_zero_first,
                    }
                row["candidate"] = candidate.name
                row["opponent"] = opponent.name
                rows.append(row)
    return rows


def cell_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize direct rows by candidate seat and first-player flag."""
    by_cell: dict[tuple[int, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[(row["candidate_seat"], row["player_zero_first"])].append(row)
    return {
        f"seat_{seat}_player_zero_first_{str(first).lower()}": summarize(cell_rows)
        for (seat, first), cell_rows in sorted(by_cell.items())
    }


def load_control(name: str, sdk_dir: Path, candidate_deck: list[int]) -> suite.Policy:
    """Load direct-gate control by registry key or official random."""
    if name == "official_random":
        random_module = suite.load_module("official_random_meta_gate", sdk_dir / "main.py", cwd=suite.RUNTIME_ROOT)
        return suite.Policy(name=name, agent=random_module.agent, deck=candidate_deck)
    path = suite.AGENT_PATHS.get(name)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Unknown or missing control: {name}")
    return suite.load_local_policy(name, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument(
        "--direct-controls",
        nargs="+",
        default=["kojimar_simple_baseline_v1", "lucario_public_sample_v3", "koushikrudra_libraryout_v1", "official_random"],
    )
    parser.add_argument("--direct-games-per-cell", type=int, default=3)
    parser.add_argument("--archetype-games-per-cell", type=int, default=2)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260704)
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)

    candidate_path = suite.AGENT_PATHS[args.candidate]
    candidate = suite.load_local_policy(args.candidate, candidate_path)

    direct_results: dict[str, dict[str, Any]] = {}
    direct_rows: list[dict[str, Any]] = []
    for index, control_name in enumerate(args.direct_controls):
        control = load_control(control_name, sdk_dir, candidate.deck)
        matchup = f"{candidate.name}_vs_{control.name}"
        rows = run_direct_rows(
            candidate=candidate,
            opponent=control,
            games_per_cell=args.direct_games_per_cell,
            max_decisions=args.max_decisions,
            seed=args.seed + 100_000 * index,
        )
        for row in rows:
            row["matchup"] = matchup
        direct_rows.extend(rows)
        direct_results[matchup] = {
            "summary": summarize(rows),
            "cells": cell_summary(rows),
        }
        summary = direct_results[matchup]["summary"]
        print(
            f"{matchup}: {summary['wins']}-{summary['losses']}"
            f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
            f"score={summary['score_rate']}, failures={summary['failures']}"
        )

    archetype_results: dict[str, dict[str, Any]] = {}
    archetype_rows: list[dict[str, Any]] = []
    opponents = [
        archetype_suite.load_author_policy_with_archetype_deck(archetype)
        for archetype in archetype_suite.AUTHOR_ARCHETYPE_DECKS.values()
    ]
    for index, opponent in enumerate(opponents):
        matchup = f"{candidate.name}_vs_{opponent.name}"
        rows = archetype_suite.evaluate_matchup(
            candidate=candidate,
            opponent=opponent,
            games_per_cell=args.archetype_games_per_cell,
            max_decisions=args.max_decisions,
            seed=args.seed + 500_000 + 100_000 * index,
        )
        for row in rows:
            row["matchup"] = matchup
        archetype_rows.extend(rows)
        archetype_results[matchup] = suite.summarize(rows)
        summary = archetype_results[matchup]
        print(
            f"{matchup}: {summary['wins']}-{summary['losses']}"
            f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
            f"score={summary['score_rate']}, failures={summary['failures']}"
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"{args.candidate}.json"
    output_path.write_text(
        json.dumps(
            {
                "candidate": args.candidate,
                "direct_games_per_cell": args.direct_games_per_cell,
                "archetype_games_per_cell": args.archetype_games_per_cell,
                "max_decisions": args.max_decisions,
                "seed": args.seed,
                "direct_results": direct_results,
                "archetype_results": archetype_results,
                "direct_rows": direct_rows,
                "archetype_rows": archetype_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
