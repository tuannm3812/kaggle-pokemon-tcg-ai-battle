"""Build replay-derived public meta fixtures from downloaded episode summaries.

The output is a compact JSON artifact under ``scratch/``. It is intentionally
not a full simulator opponent: public submissions do not expose opponent policy
code. Instead, it freezes representative deck signatures and archetype win-rate
evidence so candidate decisions can be judged against the current public meta
before spending a submission slot.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EPISODE_ROOT = ROOT / "scratch" / "leaderboard_episodes"
OUTPUT_PATH = ROOT / "scratch" / "public_meta_fixtures.json"


def load_summary(submission_id: int) -> dict[str, Any]:
    path = EPISODE_ROOT / str(submission_id) / "analysis_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run analyze_submission_episodes.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def signature_key(row: dict[str, Any]) -> str:
    return row["opponent_signature"]


def build_fixtures(submission_ids: list[int], max_signatures_per_archetype: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    submission_summaries = {}
    for submission_id in submission_ids:
        summary = load_summary(submission_id)
        submission_summaries[str(submission_id)] = summary["summary"]
        for row in summary["rows"]:
            row = dict(row)
            row["source_submission"] = submission_id
            rows.append(row)

    by_archetype: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_archetype[row["opponent_archetype"]].append(row)

    archetypes = {}
    for archetype, archetype_rows in sorted(by_archetype.items()):
        wins = sum(row["win"] for row in archetype_rows)
        losses = len(archetype_rows) - wins
        signatures: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in archetype_rows:
            signatures[signature_key(row)].append(row)

        signature_summaries = []
        for sig, sig_rows in signatures.items():
            sig_wins = sum(row["win"] for row in sig_rows)
            # Prioritize common weak signatures first, then common signatures.
            signature_summaries.append(
                {
                    "signature": sig,
                    "games": len(sig_rows),
                    "wins": sig_wins,
                    "losses": len(sig_rows) - sig_wins,
                    "score_rate": round(sig_wins / len(sig_rows), 4),
                    "label": sig_rows[0]["opponent_label"],
                    "deck": sig_rows[0]["opponent_deck"],
                    "episodes": [row["episode"] for row in sig_rows],
                    "source_submissions": sorted({row["source_submission"] for row in sig_rows}),
                    "teams": Counter(row["opponent_team"] for row in sig_rows).most_common(8),
                }
            )

        signature_summaries.sort(key=lambda item: (item["score_rate"], -item["games"], item["label"]))
        archetypes[archetype] = {
            "games": len(archetype_rows),
            "wins": wins,
            "losses": losses,
            "score_rate": round(wins / len(archetype_rows), 4),
            "representative_signatures": signature_summaries[:max_signatures_per_archetype],
        }

    return {
        "source_submissions": submission_ids,
        "submission_summaries": submission_summaries,
        "archetypes": archetypes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-ids", nargs="+", type=int, default=[54303967, 54391951])
    parser.add_argument("--max-signatures-per-archetype", type=int, default=5)
    args = parser.parse_args()

    output = build_fixtures(args.submission_ids, args.max_signatures_per_archetype)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    for archetype, info in sorted(output["archetypes"].items(), key=lambda item: (item[1]["score_rate"], -item[1]["games"])):
        print(f"{archetype}: {info['wins']}-{info['losses']} score={info['score_rate']} n={info['games']}")
        for signature in info["representative_signatures"][:2]:
            print(f"  {signature['wins']}-{signature['losses']} n={signature['games']}: {signature['label']}")


if __name__ == "__main__":
    main()
