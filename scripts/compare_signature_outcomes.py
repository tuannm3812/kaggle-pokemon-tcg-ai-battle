"""Compare replay outcomes by exact opponent deck signature across submissions.

This script consumes ``analysis_summary.json`` files produced by
``scripts/analyze_submission_episodes.py`` and creates a compact cross-submission
view for selected archetypes. It is useful when a broad archetype looks noisy:
the same archetype can contain multiple exact public decks with very different
matchup profiles.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import argparse
import json
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EPISODE_ROOT = ROOT / "scratch" / "leaderboard_episodes"
OUTPUT_ROOT = ROOT / "scratch" / "signature_outcomes"


def load_rows(submission_id: int) -> list[dict[str, Any]]:
    """Load cached replay-analysis rows for one submission."""
    path = EPISODE_ROOT / str(submission_id) / "analysis_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run analyze_submission_episodes.py first.")
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a small win-rate summary for already-filtered rows."""
    wins = sum(1 for row in rows if row["win"])
    games = len(rows)
    went_first = sum(1 for row in rows if row["went_first"])
    return {
        "games": games,
        "wins": wins,
        "losses": games - wins,
        "score_rate": round(wins / games, 4) if games else None,
        "went_first": went_first,
        "episodes": [row["episode"] for row in rows],
    }


def signature_table(submission_ids: list[int], archetypes: set[str]) -> list[dict[str, Any]]:
    """Build a table grouped by archetype + exact visible deck signature."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for submission_id in submission_ids:
        rows = load_rows(submission_id)
        for row in rows:
            archetype = row["opponent_archetype"]
            if archetypes and archetype not in archetypes:
                continue
            key = (archetype, row["opponent_signature"])
            item = grouped.setdefault(
                key,
                {
                    "archetype": archetype,
                    "signature": row["opponent_signature"],
                    "label": row["opponent_label"],
                    "submissions": defaultdict(list),
                },
            )
            item["submissions"][str(submission_id)].append(row)

    table = []
    for item in grouped.values():
        summaries = {
            submission_id: summarize(rows)
            for submission_id, rows in sorted(item["submissions"].items())
        }
        total_games = sum(summary["games"] for summary in summaries.values())
        table.append(
            {
                "archetype": item["archetype"],
                "signature": item["signature"],
                "label": item["label"],
                "total_games": total_games,
                "submissions": summaries,
            }
        )
    return sorted(table, key=lambda row: (row["archetype"], -row["total_games"], row["label"]))


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    """Write a concise human-readable report."""
    submission_ids = [str(item) for item in result["submission_ids"]]
    lines = [
        "# Cross-submission exact signature outcomes",
        "",
        f"Submissions: {', '.join(submission_ids)}",
        f"Archetypes: {', '.join(result['archetypes']) if result['archetypes'] else 'all'}",
        "",
        "| Archetype | Exact signature label | Total games | " + " | ".join(submission_ids) + " |",
        "| --- | --- | ---: | " + " | ".join(["---:" for _ in submission_ids]) + " |",
    ]
    for row in result["rows"]:
        cells = []
        for submission_id in submission_ids:
            summary = row["submissions"].get(submission_id)
            if not summary:
                cells.append("-")
                continue
            cells.append(
                f"{summary['wins']}-{summary['losses']} "
                f"({summary['score_rate']:.4f}, first {summary['went_first']}/{summary['games']})"
            )
        label = row["label"].replace("|", "/")
        lines.append(
            f"| `{row['archetype']}` | {label} | {row['total_games']} | "
            + " | ".join(cells)
            + " |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-ids", nargs="+", type=int, required=True)
    parser.add_argument("--archetypes", nargs="*", default=[])
    parser.add_argument("--output-stem", default=None)
    args = parser.parse_args()

    archetypes = set(args.archetypes)
    rows = signature_table(args.submission_ids, archetypes)
    result = {
        "submission_ids": args.submission_ids,
        "archetypes": args.archetypes,
        "rows": rows,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stem = args.output_stem or (
        "-".join(str(item) for item in args.submission_ids)
        + "_"
        + ("-".join(args.archetypes) if args.archetypes else "all")
    )
    json_path = OUTPUT_ROOT / f"{stem}.json"
    md_path = OUTPUT_ROOT / f"{stem}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, result)

    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {md_path.relative_to(ROOT)}")
    for row in rows:
        print(f"{row['archetype']} n={row['total_games']}: {row['label']}")
        for submission_id, summary in row["submissions"].items():
            print(
                f"  {submission_id}: {summary['wins']}-{summary['losses']} "
                f"score={summary['score_rate']} first={summary['went_first']}/{summary['games']}"
            )


if __name__ == "__main__":
    main()
