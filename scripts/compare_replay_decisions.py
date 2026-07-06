"""Compare a candidate's choices against recorded leaderboard replay actions.

This is not a counterfactual simulator. It answers a narrower but useful
question: on the exact public observations from a submitted agent's episodes,
would a new candidate choose a different action? That helps validate whether a
patch actually touches the failure situations it is meant to address.
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
RESULTS_DIR = ROOT / "scratch" / "replay_decision_diffs"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


def option_type_names() -> dict[int, str]:
    """Return best-effort option type names without importing the native SDK."""
    return {}


def load_policy(name: str) -> suite.Policy:
    path = suite.AGENT_PATHS.get(name)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Unknown candidate: {name}")
    suite.stage_runtime(suite.find_sdk_dir())
    return suite.load_local_policy(name, path)


def classify_archetype(deck: list[int]) -> str:
    ids = set(deck)
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


def deck_label(deck: list[int]) -> str:
    counts = Counter(deck)
    top = sorted([card_id for card_id in counts if card_id < 1000], key=lambda card_id: (-counts[card_id], card_id))[:12]
    return ", ".join(f"{card_id}x{counts[card_id]}" for card_id in top)


def load_episode_rows(submission_id: int, team_name: str) -> dict[int, dict[str, Any]]:
    """Load minimal episode metadata without restaging the SDK."""
    base = SCRATCH_ROOT / str(submission_id)
    episodes_path = base / "episodes.json"
    metadata = {episode["id"]: episode for episode in json.loads(episodes_path.read_text(encoding="utf-8"))}
    rows: dict[int, dict[str, Any]] = {}
    for path in sorted(base.glob("episode-*-replay.json")):
        episode_id = int(path.name.split("-")[1])
        meta = metadata[episode_id]
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
        decks = [
            data["steps"][1][0].get("action") or [],
            data["steps"][1][1].get("action") or [],
        ]
        opponent_deck = decks[opponent_seat]
        rows[episode_id] = {
            "episode": episode_id,
            "win": int(ours["reward"]) == 1,
            "our_seat": our_seat,
            "opponent_archetype": classify_archetype(opponent_deck),
            "opponent_label": deck_label(opponent_deck),
        }
    return rows


def selected_option_types(obs: dict[str, Any], action: list[int], names: dict[int, str]) -> list[str]:
    select = obs.get("select") or {}
    options = select.get("option") or []
    out = []
    for index in action or []:
        if not isinstance(index, int) or index < 0 or index >= len(options):
            out.append("INVALID")
            continue
        option = options[index]
        type_id = option.get("type")
        out.append(names.get(type_id, str(type_id)))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--submission-id", type=int, default=54303967)
    parser.add_argument("--team-name", default="tuannm3812")
    parser.add_argument("--only-losses", action="store_true")
    parser.add_argument("--max-episodes", type=int, default=0)
    args = parser.parse_args()

    policy = load_policy(args.candidate)
    rows_by_episode = load_episode_rows(args.submission_id, args.team_name)
    type_names = option_type_names()
    base = SCRATCH_ROOT / str(args.submission_id)

    episode_paths = sorted(base.glob("episode-*-replay.json"), reverse=True)
    if args.max_episodes > 0:
        episode_paths = episode_paths[: args.max_episodes]

    comparisons: list[dict[str, Any]] = []
    changed_by_archetype: dict[str, Counter[str]] = defaultdict(Counter)
    decisions_by_archetype: Counter[str] = Counter()

    for path in episode_paths:
        episode_id = int(path.name.split("-")[1])
        row = rows_by_episode.get(episode_id)
        if row is None:
            continue
        if args.only_losses and row["win"]:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        our_seat = int(row["our_seat"])
        for step_index, step in enumerate(data["steps"]):
            agent_state = step[our_seat]
            if agent_state.get("status") != "ACTIVE":
                continue
            obs = agent_state.get("observation") or {}
            if obs.get("select") is None:
                continue
            recorded = agent_state.get("action") or []
            try:
                candidate_action = policy.agent(obs)
            except Exception as exc:  # noqa: BLE001
                candidate_action = []
                error = repr(exc)
            else:
                error = None
            archetype = row["opponent_archetype"]
            decisions_by_archetype[archetype] += 1
            changed = list(candidate_action) != list(recorded)
            if changed:
                for option_type in selected_option_types(obs, candidate_action, type_names):
                    changed_by_archetype[archetype][option_type] += 1
            comparisons.append(
                {
                    "episode": episode_id,
                    "step": step_index,
                    "opponent_archetype": archetype,
                    "opponent_label": row["opponent_label"],
                    "win": row["win"],
                    "recorded_action": recorded,
                    "candidate_action": candidate_action,
                    "recorded_types": selected_option_types(obs, recorded, type_names),
                    "candidate_types": selected_option_types(obs, candidate_action, type_names),
                    "changed": changed,
                    "error": error,
                }
            )

    changed_total = sum(item["changed"] for item in comparisons)
    summary = {
        "candidate": args.candidate,
        "submission_id": args.submission_id,
        "only_losses": args.only_losses,
        "decisions": len(comparisons),
        "changed": changed_total,
        "changed_rate": round(changed_total / len(comparisons), 4) if comparisons else None,
        "by_archetype": {
            archetype: {
                "decisions": decisions_by_archetype[archetype],
                "changed_types": dict(counter),
            }
            for archetype, counter in sorted(changed_by_archetype.items())
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "losses" if args.only_losses else "all"
    output_path = RESULTS_DIR / f"{args.candidate}_vs_{args.submission_id}_{suffix}.json"
    output_path.write_text(
        json.dumps({"summary": summary, "comparisons": comparisons}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
