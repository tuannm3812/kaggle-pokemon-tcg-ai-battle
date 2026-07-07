from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = ROOT / "scratch" / "leaderboard_episodes"
RESULTS_DIR = ROOT / "scratch" / "midgame_decision_deltas"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import compare_replay_decisions as replay_compare  # noqa: E402
from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


def load_policy(name: str) -> suite.Policy:
    path = suite.AGENT_PATHS.get(name)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Unknown candidate: {name}")
    return suite.load_local_policy(name, path)


def option_label(obs: dict[str, Any], action: list[int]) -> list[str]:
    select = obs.get("select") or {}
    options = select.get("option") or []
    labels = []
    for index in action or []:
        if not isinstance(index, int) or index < 0 or index >= len(options):
            labels.append(f"INVALID:{index}")
            continue
        option = options[index]
        option_type = option.get("type")
        labels.append(
            "type={type} idx={idx} atk={atk} area={area} inPlay={in_area}:{in_idx}".format(
                type=option_type,
                idx=option.get("index"),
                atk=option.get("attackId"),
                area=option.get("area"),
                in_area=option.get("inPlayArea"),
                in_idx=option.get("inPlayIndex"),
            )
        )
    return labels


def compact_board(obs: dict[str, Any], our_seat: int) -> dict[str, Any]:
    current = obs.get("current") or {}
    players = current.get("players") or []
    if len(players) < 2:
        return {}
    us = players[our_seat]
    opp = players[1 - our_seat]

    def pokemon_labels(cards: list[dict[str, Any] | None]) -> list[str]:
        out = []
        for card in cards or []:
            if not card:
                continue
            out.append(
                "id={id} hp={hp} e={energy} tools={tools}".format(
                    id=card.get("id"),
                    hp=card.get("hp"),
                    energy=len(card.get("energies") or []),
                    tools=len(card.get("tools") or []),
                )
            )
        return out

    return {
        "turn": current.get("turn"),
        "our_active": pokemon_labels(us.get("active") or []),
        "our_bench": pokemon_labels(us.get("bench") or []),
        "opponent_active": pokemon_labels(opp.get("active") or []),
        "opponent_bench": pokemon_labels(opp.get("bench") or []),
        "hand_ids": [card.get("id") for card in us.get("hand") or [] if card],
        "energy_attached": current.get("energyAttached"),
        "supporter_played": current.get("supporterPlayed"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare candidate vs reference on filtered public midgame replay states.")
    parser.add_argument("--candidate", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--reference", default="kojimar_simple_baseline_v1", choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--submission-id", type=int, default=54303967)
    parser.add_argument("--team-name", default="tuannm3812")
    parser.add_argument("--archetypes", nargs="+", default=["metal_cinderace", "alakazam_dunsparce"])
    parser.add_argument("--start-turn", type=int, default=5)
    parser.add_argument("--end-turn", type=int, default=7)
    parser.add_argument("--max-states", type=int, default=200)
    parser.add_argument("--loss-diagnostics", type=Path, default=ROOT / "scratch" / "loss_diagnostics" / "54303967_metal_cinderace-alakazam_dunsparce_losses.json")
    args = parser.parse_args()

    suite.stage_runtime(suite.find_sdk_dir())
    candidate = load_policy(args.candidate)
    reference = load_policy(args.reference)
    base = SCRATCH_ROOT / str(args.submission_id)
    if args.loss_diagnostics.exists():
        diag = json.loads(args.loss_diagnostics.read_text(encoding="utf-8"))
        episode_rows = [
            {
                "episode": int(item["episode"]),
                "win": False,
                "our_seat": int(item["our_seat"]),
                "opponent_archetype": item["archetype"],
            }
            for item in diag.get("episodes", [])
            if item.get("archetype") in set(args.archetypes)
        ]
    else:
        rows_by_episode = replay_compare.load_episode_rows(args.submission_id, args.team_name)
        episode_rows = [
            {"episode": episode_id, **row}
            for episode_id, row in rows_by_episode.items()
            if not row["win"] and row["opponent_archetype"] in set(args.archetypes)
        ]

    comparisons = []
    changed_by_archetype: dict[str, Counter[str]] = defaultdict(Counter)
    seen_states = 0

    for row in sorted(episode_rows, key=lambda item: item["episode"], reverse=True):
        episode_id = int(row["episode"])
        path = base / f"episode-{episode_id}-replay.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        our_seat = int(row["our_seat"])
        for step_index, step in enumerate(data.get("steps") or []):
            agent_state = step[our_seat]
            if agent_state.get("status") != "ACTIVE":
                continue
            obs = agent_state.get("observation") or {}
            current = obs.get("current") or {}
            select = obs.get("select") or {}
            turn = current.get("turn")
            if turn is None or turn < args.start_turn or turn > args.end_turn:
                continue
            if select.get("context") not in {0, "MAIN"}:
                continue
            if not select.get("option"):
                continue

            try:
                suite.reset_policy_state(candidate)
                suite.reset_policy_state(reference)
                cand_action = candidate.agent(obs)
                ref_action = reference.agent(obs)
            except Exception as exc:  # noqa: BLE001
                comparisons.append(
                    {
                        "episode": episode_id,
                        "step": step_index,
                        "archetype": row["opponent_archetype"],
                        "turn": turn,
                        "error": repr(exc),
                    }
                )
                continue

            changed = list(cand_action) != list(ref_action)
            if changed:
                changed_by_archetype[row["opponent_archetype"]]["changed"] += 1
            changed_by_archetype[row["opponent_archetype"]]["states"] += 1
            comparisons.append(
                {
                    "episode": episode_id,
                    "step": step_index,
                    "archetype": row["opponent_archetype"],
                    "turn": turn,
                    "candidate_action": cand_action,
                    "reference_action": ref_action,
                    "candidate_labels": option_label(obs, cand_action),
                    "reference_labels": option_label(obs, ref_action),
                    "recorded_action": agent_state.get("action") or [],
                    "changed": changed,
                    "board": compact_board(obs, our_seat),
                }
            )
            seen_states += 1
            if args.max_states and seen_states >= args.max_states:
                break
        if args.max_states and seen_states >= args.max_states:
            break

    summary = {
        "candidate": args.candidate,
        "reference": args.reference,
        "submission_id": args.submission_id,
        "turn_window": [args.start_turn, args.end_turn],
        "states": seen_states,
        "changed": sum(1 for row in comparisons if row.get("changed")),
        "by_archetype": {
            archetype: {
                "states": counter["states"],
                "changed": counter["changed"],
                "changed_rate": round(counter["changed"] / counter["states"], 4) if counter["states"] else 0,
            }
            for archetype, counter in sorted(changed_by_archetype.items())
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"{args.candidate}_vs_{args.reference}_{args.submission_id}_t{args.start_turn}_{args.end_turn}.json"
    output_path.write_text(json.dumps({"summary": summary, "comparisons": comparisons}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    if "POKEMON_TCG_RUNTIME_ROOT" not in os.environ:
        os.environ["POKEMON_TCG_RUNTIME_ROOT"] = str(ROOT / "scratch" / "midgame_delta_runtime")
    main()
