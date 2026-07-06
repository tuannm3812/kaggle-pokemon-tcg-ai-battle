"""Run the current public-meta promotion gate for one candidate.

This gate combines:

1. local full-game controls that we can simulate;
2. a same-seed active-best reference run for those controls;
3. replay-derived public archetype fixtures that describe the live meta slices
   a candidate should improve.

It does not pretend to simulate unknown public opponent policies. The point is
to prevent another submission from relying on a single local head-to-head score.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
RESULTS_DIR = SCRATCH / "public_meta_gates"
FIXTURE_PATH = SCRATCH / "public_meta_fixtures.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402
from scripts.evaluate_meta_gate import run_direct_rows, load_control, cell_summary  # noqa: E402
from scripts.evaluate_direct_gate import summarize  # noqa: E402


DEFAULT_CONTROLS = [
    "kojimar_simple_baseline_v1",
    "kojimar_simple_baseline_v8_public_boss_guard",
    "kojimar_simple_baseline_v5_metal_pressure",
    "lucario_public_sample_v3",
    "koushikrudra_libraryout_v1",
    "official_random",
]


def load_fixtures() -> dict[str, Any]:
    if not FIXTURE_PATH.exists():
        cmd = [sys.executable, str(ROOT / "scripts" / "build_public_meta_fixtures.py")]
        subprocess.run(cmd, cwd=ROOT, check=True)
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def summarize_public_fixtures(fixtures: dict[str, Any]) -> dict[str, Any]:
    weak_archetypes = {}
    for name, info in fixtures["archetypes"].items():
        if info["games"] >= 4 and info["score_rate"] < 0.5:
            weak_archetypes[name] = {
                "games": info["games"],
                "wins": info["wins"],
                "losses": info["losses"],
                "score_rate": info["score_rate"],
                "representative_signatures": info["representative_signatures"][:3],
            }
    return weak_archetypes


def summary_score(result: dict[str, Any] | None) -> float | None:
    if not result:
        return None
    summary = result.get("summary", result)
    return summary.get("score_rate")


def evaluate_direct_matchup(
    candidate: suite.Policy,
    control_name: str,
    sdk_dir: Path,
    games_per_cell: int,
    max_decisions: int,
    seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate one candidate/control matchup and return its JSON-ready record."""
    control = load_control(control_name, sdk_dir, candidate.deck)
    matchup = f"{candidate.name}_vs_{control.name}"
    rows = run_direct_rows(
        candidate=candidate,
        opponent=control,
        games_per_cell=games_per_cell,
        max_decisions=max_decisions,
        seed=seed,
    )
    for row in rows:
        row["matchup"] = matchup
    return {
        "matchup": matchup,
        "summary": summarize(rows),
        "cells": cell_summary(rows),
    }, rows


def print_summary(matchup: str, summary: dict[str, Any], suffix: str = "") -> None:
    print(
        f"{matchup}: {summary['wins']}-{summary['losses']}"
        f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
        f"score={summary['score_rate']}, failures={summary['failures']}"
        f"{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--direct-controls", nargs="+", default=DEFAULT_CONTROLS)
    parser.add_argument("--direct-games-per-cell", type=int, default=3)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260706)
    parser.add_argument("--reference-candidate", default="kojimar_simple_baseline_v1", choices=sorted(suite.AGENT_PATHS))
    parser.add_argument(
        "--min-reference-delta",
        type=float,
        default=-0.05,
        help="Minimum acceptable challenger score delta versus the same-seed reference on direct controls.",
    )
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)

    candidate = suite.load_local_policy(args.candidate, suite.AGENT_PATHS[args.candidate])
    reference = suite.load_local_policy(args.reference_candidate, suite.AGENT_PATHS[args.reference_candidate])
    fixtures = load_fixtures()
    weak_public_archetypes = summarize_public_fixtures(fixtures)

    direct_results: dict[str, dict[str, Any]] = {}
    reference_results: dict[str, dict[str, Any]] = {}
    relative_results: dict[str, dict[str, Any]] = {}
    direct_rows: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []

    for index, control_name in enumerate(args.direct_controls):
        matchup_seed = args.seed + 100_000 * index

        direct_record, rows = evaluate_direct_matchup(
            candidate=candidate,
            control_name=control_name,
            sdk_dir=sdk_dir,
            games_per_cell=args.direct_games_per_cell,
            max_decisions=args.max_decisions,
            seed=matchup_seed,
        )
        direct_rows.extend(rows)
        direct_results[direct_record["matchup"]] = {
            "summary": direct_record["summary"],
            "cells": direct_record["cells"],
        }
        print_summary(direct_record["matchup"], direct_record["summary"])

        reference_record, rows = evaluate_direct_matchup(
            candidate=reference,
            control_name=control_name,
            sdk_dir=sdk_dir,
            games_per_cell=args.direct_games_per_cell,
            max_decisions=args.max_decisions,
            seed=matchup_seed,
        )
        reference_rows.extend(rows)
        reference_results[reference_record["matchup"]] = {
            "summary": reference_record["summary"],
            "cells": reference_record["cells"],
        }

        candidate_score = summary_score(direct_record)
        reference_score = summary_score(reference_record)
        delta = (
            round(candidate_score - reference_score, 4)
            if candidate_score is not None and reference_score is not None
            else None
        )
        relative_results[control_name] = {
            "candidate_matchup": direct_record["matchup"],
            "reference_matchup": reference_record["matchup"],
            "candidate_score_rate": candidate_score,
            "reference_score_rate": reference_score,
            "delta_vs_reference": delta,
            "candidate_failures": direct_record["summary"]["failures"],
            "reference_failures": reference_record["summary"]["failures"],
        }
        print_summary(reference_record["matchup"], reference_record["summary"], suffix=f", candidate_delta={delta}")

    decision_flags = []
    active_best = direct_results.get(f"{candidate.name}_vs_kojimar_simple_baseline_v1", {}).get("summary")
    if active_best and active_best["score_rate"] is not None and active_best["score_rate"] < 0.45:
        decision_flags.append("fails_active_best_direct_gate")
    library = direct_results.get(f"{candidate.name}_vs_koushikrudra_libraryout_v1", {}).get("summary")
    if library and library["score_rate"] is not None and library["score_rate"] < 0.3:
        decision_flags.append("very_weak_libraryout_gate")
    for control_name, relative in relative_results.items():
        delta = relative["delta_vs_reference"]
        if delta is not None and delta < args.min_reference_delta:
            decision_flags.append(f"under_reference_on_{control_name}")

    result = {
        "candidate": args.candidate,
        "reference_candidate": args.reference_candidate,
        "direct_games_per_cell": args.direct_games_per_cell,
        "max_decisions": args.max_decisions,
        "seed": args.seed,
        "min_reference_delta": args.min_reference_delta,
        "direct_results": direct_results,
        "reference_results": reference_results,
        "relative_results": relative_results,
        "weak_public_archetypes": weak_public_archetypes,
        "decision_flags": decision_flags,
        "recommendation": "hold" if decision_flags else "candidate_for_deeper_validation",
        "direct_rows": direct_rows,
        "reference_rows": reference_rows,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"{args.candidate}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Weak public archetypes: {', '.join(sorted(weak_public_archetypes))}")
    print(f"Recommendation: {result['recommendation']} {decision_flags}")
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
