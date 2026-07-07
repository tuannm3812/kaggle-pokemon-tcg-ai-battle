"""Run a direct matchup without overriding each policy's first-player choice.

Most local gates force seat and turn-order cells so candidate action quality can
be compared independently of first-player selection. This script is intentionally
different: it lets each policy answer ``SelectContext.IS_FIRST`` on its own, so
we can test live-style first/second preference changes.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "scratch" / "unforced_direct_gates"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402
from scripts.evaluate_direct_gate import summarize  # noqa: E402


def run_unforced_game(
    candidate: suite.Policy,
    opponent: suite.Policy,
    candidate_seat: int,
    seed: int,
    max_decisions: int,
) -> dict[str, Any]:
    """Run one game and let both policies choose first/second naturally."""
    from cg.api import SelectContext, to_observation_class
    from cg.game import battle_select, battle_start

    suite.reset_policy_state(candidate)
    suite.reset_policy_state(opponent)
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed % (2**32 - 1))
    except Exception:
        pass

    decks = [candidate.deck, opponent.deck] if candidate_seat == 0 else [opponent.deck, candidate.deck]
    policies = [None, None]
    policies[candidate_seat] = candidate
    policies[1 - candidate_seat] = opponent

    obs_dict, start_data = battle_start(decks[0], decks[1])
    if obs_dict is None:
        return {
            "status": "start_error",
            "seed": seed,
            "candidate_reward": 0,
            "candidate_score": 0,
            "candidate_seat": candidate_seat,
            "error": f"{getattr(start_data, 'errorType', None)} player={getattr(start_data, 'errorPlayer', None)}",
        }

    observed_first_player: int | None = None
    first_choice_actor: int | None = None
    first_choice_action: list[int] | None = None

    for decision in range(max_decisions):
        obs = to_observation_class(obs_dict)
        if getattr(obs.current, "firstPlayer", -1) in (0, 1):
            observed_first_player = int(obs.current.firstPlayer)
        if obs.current.result != -1:
            winner = int(obs.current.result)
            score = 1.0 if winner == candidate_seat else 0.0 if winner in (0, 1) else 0.5
            return {
                "status": "complete",
                "seed": seed,
                "decisions": decision,
                "candidate_reward": 1 if score == 1.0 else -1 if score == 0.0 else 0,
                "candidate_score": score,
                "winner": winner,
                "candidate_seat": candidate_seat,
                "first_player": observed_first_player,
                "candidate_went_first": observed_first_player == candidate_seat,
                "first_choice_actor": first_choice_actor,
                "first_choice_action": first_choice_action,
            }

        player_index = int(obs.current.yourIndex)
        action = policies[player_index].agent(obs_dict)
        if obs.select is not None and obs.select.context == SelectContext.IS_FIRST:
            first_choice_actor = player_index
            first_choice_action = list(action)
        obs_dict = battle_select(action)

    return {
        "status": "max_decisions",
        "seed": seed,
        "decisions": max_decisions,
        "candidate_reward": 0,
        "candidate_score": 0.5,
        "candidate_seat": candidate_seat,
        "first_player": observed_first_player,
        "candidate_went_first": observed_first_player == candidate_seat,
        "first_choice_actor": first_choice_actor,
        "first_choice_action": first_choice_action,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--control", required=True, choices=sorted(suite.AGENT_PATHS))
    parser.add_argument("--games-per-seat", type=int, default=10)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260704)
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)
    candidate = suite.load_local_policy(args.candidate, suite.AGENT_PATHS[args.candidate])
    opponent = suite.load_local_policy(args.control, suite.AGENT_PATHS[args.control])

    rows: list[dict[str, Any]] = []
    for candidate_seat in (0, 1):
        for repeat in range(args.games_per_seat):
            seed = args.seed + 10_000 * candidate_seat + repeat
            try:
                row = run_unforced_game(candidate, opponent, candidate_seat, seed, args.max_decisions)
            except Exception as exc:  # noqa: BLE001
                row = {
                    "status": "error",
                    "seed": seed,
                    "candidate_reward": 0,
                    "candidate_score": 0,
                    "candidate_seat": candidate_seat,
                    "error": repr(exc),
                }
            row["candidate"] = candidate.name
            row["opponent"] = opponent.name
            row["matchup"] = f"{candidate.name}_vs_{opponent.name}"
            rows.append(row)

    summary = summarize(rows)
    by_seat = {
        f"seat_{seat}": summarize([row for row in rows if row["candidate_seat"] == seat])
        for seat in (0, 1)
    }
    went_first = {
        str(flag).lower(): summarize([row for row in rows if row.get("candidate_went_first") is flag])
        for flag in (False, True)
    }

    print(
        f"{candidate.name}_vs_{opponent.name}: "
        f"{summary['wins']}-{summary['losses']}"
        f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
        f"score={summary['score_rate']}, failures={summary['failures']}"
    )
    print("by_seat:", by_seat)
    print("candidate_went_first:", went_first)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"{candidate.name}_vs_{opponent.name}.json"
    output_path.write_text(
        json.dumps(
            {
                "candidate": candidate.name,
                "control": opponent.name,
                "games_per_seat": args.games_per_seat,
                "max_decisions": args.max_decisions,
                "seed": args.seed,
                "summary": summary,
                "by_seat": by_seat,
                "candidate_went_first": went_first,
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
