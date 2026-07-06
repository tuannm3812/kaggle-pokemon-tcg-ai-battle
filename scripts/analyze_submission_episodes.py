"""Analyze downloaded Kaggle episode replays for one submission.

The Kaggle API can list/download episodes, but the useful diagnosis for this
project comes from replay contents: opponent deck signatures, seat/first-player
splits, and archetype-level win rates. This script assumes replays already live
under ``scratch/leaderboard_episodes/<submission_id>/``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = ROOT / "scratch" / "leaderboard_episodes"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


def card_names() -> dict[int, str]:
    """Load card names from the staged SDK."""
    suite.stage_runtime(suite.find_sdk_dir())
    runtime = str(suite.RUNTIME_ROOT.resolve())
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    from cg.api import all_card_data  # noqa: PLC0415

    return {card.cardId: getattr(card, "name", str(card.cardId)) for card in all_card_data()}


def card_signature(deck: list[int]) -> tuple[tuple[int, int], ...]:
    """Return a compact Pokemon/energy signature for exact cluster grouping."""
    counts = Counter(deck)
    return tuple(sorted((card_id, counts[card_id]) for card_id in counts if card_id < 1000))


def deck_label(deck: list[int], names: dict[int, str], limit: int = 12) -> str:
    """Human-readable summary of the most frequent Pokemon/energy cards."""
    counts = Counter(deck)
    top = sorted(
        [card_id for card_id in counts if card_id < 1000],
        key=lambda card_id: (-counts[card_id], names.get(card_id, ""), card_id),
    )[:limit]
    return ", ".join(f"{names.get(card_id, card_id)} x{counts[card_id]}" for card_id in top)


def classify_archetype(deck: list[int]) -> str:
    """Map visible deck cards to a coarse opponent family."""
    counts = Counter(deck)
    ids = set(counts)
    if {169, 190, 666} & ids:
        return "metal_cinderace"
    if {741, 742, 743} & ids:
        return "alakazam_dunsparce"
    if {344, 345, 58, 607} & ids:
        return "crustle_libraryout"
    if {677, 678} & ids:
        return "lucario"
    if {721, 722, 723} & ids:
        return "abomasnow"
    if {667, 668, 669} & ids:
        return "dragapult"
    if {349, 350} & ids or {59, 60, 61} & ids:
        return "phantump_trevenant_control"
    if {681, 682, 683} & ids:
        return "grimmsnarl"
    if {385, 386, 387} & ids:
        return "iono"
    return "other"


def load_rows(submission_id: int, team_name: str, names: dict[int, str]) -> list[dict[str, Any]]:
    base = SCRATCH_ROOT / str(submission_id)
    episodes_path = base / "episodes.json"
    if not episodes_path.exists():
        raise FileNotFoundError(f"Missing {episodes_path}. Download episodes first.")

    episodes = json.loads(episodes_path.read_text(encoding="utf-8"))
    episode_meta = {episode["id"]: episode for episode in episodes}
    rows: list[dict[str, Any]] = []
    for path in sorted(base.glob("episode-*-replay.json")):
        episode_id = int(path.name.split("-")[1])
        meta = episode_meta[episode_id]
        data = json.loads(path.read_text(encoding="utf-8"))

        candidates = [
            agent
            for agent in meta["agents"]
            if agent.get("submissionId") == submission_id or agent.get("teamName") == team_name
        ]
        if not candidates:
            continue
        ours = next((agent for agent in candidates if agent.get("submissionId") == submission_id), candidates[0])
        our_seat = int(ours["index"])
        opponent_seat = 1 - our_seat
        opponent = meta["agents"][opponent_seat]
        reward = int(ours["reward"])

        decks = [
            data["steps"][1][0].get("action") or [],
            data["steps"][1][1].get("action") or [],
        ]
        opponent_deck = decks[opponent_seat]
        first_player = -1
        for step in data["steps"][:30]:
            obs = (step[our_seat].get("observation") or {}).get("current")
            if isinstance(obs, dict) and obs.get("firstPlayer") in (0, 1):
                first_player = int(obs["firstPlayer"])
                break

        rows.append(
            {
                "episode": episode_id,
                "reward": reward,
                "win": reward == 1,
                "our_seat": our_seat,
                "went_first": first_player == our_seat,
                "opponent_team": opponent.get("teamName"),
                "opponent_submission": opponent.get("submissionId"),
                "steps": len(data["steps"]),
                "opponent_archetype": classify_archetype(opponent_deck),
                "opponent_signature": str(card_signature(opponent_deck)),
                "opponent_label": deck_label(opponent_deck, names),
                "opponent_deck": opponent_deck,
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    wins = sum(row["win"] for row in rows)
    return {
        "games": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "score_rate": round(wins / len(rows), 4) if rows else None,
    }


def grouped(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    by_key: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[row[key]].append(row)
    out = []
    for value, value_rows in by_key.items():
        item = summarize(value_rows)
        item[key] = value
        item["episodes"] = [row["episode"] for row in value_rows]
        if key == "opponent_signature" and value_rows:
            item["label"] = value_rows[0]["opponent_label"]
            item["archetype"] = value_rows[0]["opponent_archetype"]
            item["teams"] = Counter(row["opponent_team"] for row in value_rows).most_common(5)
        out.append(item)
    return sorted(out, key=lambda item: (item["score_rate"], -item["games"], str(item[key])))


def write_summary(submission_id: int, rows: list[dict[str, Any]]) -> Path:
    base = SCRATCH_ROOT / str(submission_id)
    result = {
        "submission_id": submission_id,
        "summary": summarize(rows),
        "by_seat": grouped(rows, "our_seat"),
        "by_first": grouped(rows, "went_first"),
        "by_archetype": grouped(rows, "opponent_archetype"),
        "by_signature": grouped(rows, "opponent_signature"),
        "rows": rows,
    }
    output = base / "analysis_summary.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"submission {submission_id}",
        f"summary {result['summary']}",
        "",
        "by archetype",
    ]
    for row in result["by_archetype"]:
        lines.append(f"- {row['opponent_archetype']}: {row['wins']}-{row['losses']} score={row['score_rate']} n={row['games']}")
    lines.extend(["", "worst signatures"])
    for row in result["by_signature"][:20]:
        lines.append(
            f"- {row['wins']}-{row['losses']} score={row['score_rate']} n={row['games']} "
            f"{row['archetype']}: {row['label']}"
        )
    (base / "analysis_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-id", type=int, required=True)
    parser.add_argument("--team-name", default="tuannm3812")
    args = parser.parse_args()

    names = card_names()
    rows = load_rows(args.submission_id, args.team_name, names)
    output = write_summary(args.submission_id, rows)
    print(f"Wrote {output.relative_to(ROOT)}")
    print(json.dumps(summarize(rows), indent=2))
    for row in grouped(rows, "opponent_archetype"):
        print(f"{row['opponent_archetype']}: {row['wins']}-{row['losses']} score={row['score_rate']} n={row['games']}")


if __name__ == "__main__":
    main()
