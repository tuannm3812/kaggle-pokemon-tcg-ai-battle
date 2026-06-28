"""Apply the stricter no-submission promotion gate to saved evaluation outputs.

The gate is intentionally conservative after `planner_main_only_v1` validated
locally but underperformed on the ladder.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def author_matchups(candidate: str, author_results_path: Path) -> dict[str, float]:
    if not author_results_path.exists():
        return {}
    data = load_json(author_results_path)
    summaries = data.get("summaries", {})
    prefix = f"{candidate}_vs_"
    return {
        name.removeprefix(prefix): float(summary["score_rate"])
        for name, summary in summaries.items()
        if name.startswith(prefix)
    }


def decide(
    candidate: str,
    direct: dict,
    random_regression: dict | None,
    authors: dict[str, float],
    min_direct_ci_low: float,
    min_direct_cell: float,
    min_random_score: float,
    min_author_score: float,
) -> dict:
    reasons = []
    direct_summary = direct["summary"]
    direct_score = float(direct_summary["score_rate"])
    direct_ci_low = float(direct_summary["wilson_score_ci"][0])
    direct_cells = {
        name: float(summary["score_rate"])
        for name, summary in direct.get("cells", {}).items()
    }

    if direct_ci_low <= min_direct_ci_low:
        reasons.append(
            f"direct CI low {direct_ci_low:.3f} <= required {min_direct_ci_low:.3f}"
        )
    weak_cells = {
        name: score
        for name, score in direct_cells.items()
        if score < min_direct_cell
    }
    if weak_cells:
        reasons.append(
            "weak direct cells below "
            f"{min_direct_cell:.2f}: "
            + ", ".join(f"{name}={score:.3f}" for name, score in weak_cells.items())
        )

    random_score = None
    if random_regression is not None:
        random_score = float(random_regression["summary"]["score_rate"])
        if random_score < min_random_score:
            reasons.append(
                f"random regression score {random_score:.3f} < required {min_random_score:.3f}"
            )
    else:
        reasons.append("missing official-random regression result")

    weak_authors = {
        name: score
        for name, score in authors.items()
        if score < min_author_score
    }
    if weak_authors:
        reasons.append(
            "weak author matchups below "
            f"{min_author_score:.2f}: "
            + ", ".join(f"{name}={score:.3f}" for name, score in weak_authors.items())
        )
    if not authors:
        reasons.append("missing author-suite result")

    return {
        "candidate": candidate,
        "decision": "PROMOTE" if not reasons else "REJECT",
        "reasons": reasons,
        "direct_score": direct_score,
        "direct_ci_low": direct_ci_low,
        "direct_cells": direct_cells,
        "random_score": random_score,
        "author_scores": authors,
        "thresholds": {
            "min_direct_ci_low": min_direct_ci_low,
            "min_direct_cell": min_direct_cell,
            "min_random_score": min_random_score,
            "min_author_score": min_author_score,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="planner_main_only_v1")
    parser.add_argument("--control", default="promoted")
    parser.add_argument("--random-control", default="official_random")
    parser.add_argument("--min-direct-ci-low", type=float, default=0.50)
    parser.add_argument("--min-direct-cell", type=float, default=0.40)
    parser.add_argument("--min-random-score", type=float, default=0.65)
    parser.add_argument("--min-author-score", type=float, default=0.45)
    args = parser.parse_args()

    direct_path = SCRATCH / "direct_gates" / f"{args.candidate}_vs_{args.control}.json"
    random_path = SCRATCH / "direct_gates" / f"{args.candidate}_vs_{args.random_control}.json"
    author_path = SCRATCH / "author_opponent_suite_results.json"
    direct = load_json(direct_path)
    random_regression = load_json(random_path) if random_path.exists() else None
    authors = author_matchups(args.candidate, author_path)

    result = decide(
        candidate=args.candidate,
        direct=direct,
        random_regression=random_regression,
        authors=authors,
        min_direct_ci_low=args.min_direct_ci_low,
        min_direct_cell=args.min_direct_cell,
        min_random_score=args.min_random_score,
        min_author_score=args.min_author_score,
    )
    output_path = SCRATCH / "promotion_gates" / f"{args.candidate}_gate.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
