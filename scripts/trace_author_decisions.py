"""Trace candidate decisions against sanitized author-reference policies.

The author-opponent score suite tells us whether a candidate is better. This
script explains where it changed behavior by recording compact, public-state
decision telemetry for candidate turns.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
RESULTS_PATH = SCRATCH / "author_decision_trace_results.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


ENUM_NAMES = {
    "OptionType": {
        0: "NUMBER", 1: "YES", 2: "NO", 3: "CARD", 4: "TOOL_CARD",
        5: "ENERGY_CARD", 6: "ENERGY", 7: "PLAY", 8: "ATTACH",
        9: "EVOLVE", 10: "ABILITY", 11: "DISCARD", 12: "RETREAT",
        13: "ATTACK", 14: "END", 15: "SKILL", 16: "SPECIAL_CONDITION",
    },
    "SelectContext": {
        0: "MAIN", 1: "SETUP_ACTIVE_POKEMON", 2: "SETUP_BENCH_POKEMON",
        3: "SWITCH", 4: "TO_ACTIVE", 5: "TO_BENCH", 6: "TO_FIELD",
        7: "TO_HAND", 8: "DISCARD", 9: "TO_DECK", 10: "TO_DECK_BOTTOM",
        11: "TO_PRIZE", 12: "NOT_MOVE", 13: "DAMAGE_COUNTER",
        14: "DAMAGE_COUNTER_ANY", 15: "DAMAGE", 16: "REMOVE_DAMAGE_COUNTER",
        17: "HEAL", 18: "EVOLVES_FROM", 19: "EVOLVES_TO", 20: "DEVOLVE",
        21: "ATTACH_FROM", 22: "ATTACH_TO", 23: "DETACH_FROM", 24: "LOOK",
        25: "EFFECT_TARGET", 26: "DISCARD_ENERGY_CARD", 27: "DISCARD_TOOL_CARD",
        28: "SWITCH_ENERGY_CARD", 29: "DISCARD_CARD_OR_ATTACHED_CARD",
        30: "DISCARD_ENERGY", 31: "TO_HAND_ENERGY", 32: "TO_DECK_ENERGY",
        33: "SWITCH_ENERGY", 34: "SKILL_ORDER", 35: "ATTACK",
        36: "DISABLE_ATTACK", 37: "EVOLVE", 38: "DRAW_COUNT",
        39: "DAMAGE_COUNTER_COUNT", 40: "REMOVE_DAMAGE_COUNTER_COUNT",
        41: "IS_FIRST", 42: "MULLIGAN", 43: "ACTIVATE", 44: "FIRST_EFFECT",
        45: "MORE_DEVOLVE", 46: "COIN_HEAD", 47: "AFFECT_SPECIAL_CONDITION",
        48: "RECOVER_SPECIAL_CONDITION",
    },
    "SelectType": {
        0: "MAIN", 1: "CARD", 2: "ATTACHED_CARD", 3: "CARD_OR_ATTACHED_CARD",
        4: "ENERGY", 5: "SKILL", 6: "ATTACK", 7: "EVOLVE", 8: "COUNT",
        9: "YES_NO", 10: "SPECIAL_CONDITION",
    },
    "AreaType": {
        1: "DECK", 2: "HAND", 3: "DISCARD", 4: "ACTIVE", 5: "BENCH",
        6: "PRIZE", 7: "STADIUM", 8: "ENERGY", 9: "TOOL",
        10: "PRE_EVOLUTION", 11: "PLAYER", 12: "LOOKING",
    },
}


def enum_name(value: object, enum_type: str | None = None) -> str:
    name = getattr(value, "name", None)
    if name is not None:
        return str(name)
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return str(value)
    if enum_type and integer in ENUM_NAMES.get(enum_type, {}):
        return ENUM_NAMES[enum_type][integer]
    for mapping in ENUM_NAMES.values():
        if integer in mapping:
            return mapping[integer]
    return str(value)


def option_signature(obs: object, option: object, index: int) -> dict[str, Any]:
    from cg.api import AreaType, OptionType

    row: dict[str, Any] = {
        "index": index,
        "type": enum_name(getattr(option, "type", None), "OptionType"),
        "area": enum_name(getattr(option, "area", None), "AreaType"),
        "in_play_area": enum_name(getattr(option, "inPlayArea", None), "AreaType"),
        "option_index": getattr(option, "index", None),
        "in_play_index": getattr(option, "inPlayIndex", None),
        "attack_id": getattr(option, "attackId", None),
        "number": getattr(option, "number", None),
        "card_id": None,
        "card_hp": None,
        "card_energy": None,
    }

    try:
        if option.type == OptionType.CARD:
            player = int(getattr(option, "playerIndex", obs.current.yourIndex))
            area = option.area
            zone = None
            player_state = obs.current.players[player]
            if area == AreaType.HAND:
                zone = player_state.hand
            elif area == AreaType.DISCARD:
                zone = player_state.discard
            elif area == AreaType.ACTIVE:
                zone = player_state.active
            elif area == AreaType.BENCH:
                zone = player_state.bench
            elif area == AreaType.PRIZE:
                zone = player_state.prize
            elif area == AreaType.LOOKING:
                zone = obs.current.looking
            elif area == AreaType.DECK:
                zone = getattr(obs.select, "deck", [])
            if zone is not None and 0 <= int(option.index) < len(zone):
                card = zone[int(option.index)]
                row["card_id"] = getattr(card, "id", None)
                row["card_hp"] = getattr(card, "hp", None)
                row["card_energy"] = len(getattr(card, "energies", []))
    except Exception:  # noqa: BLE001 - telemetry should never alter game behavior.
        pass
    return row


def board_summary(obs: object, candidate_player: int) -> dict[str, Any]:
    player = obs.current.players[candidate_player]
    opponent = obs.current.players[1 - candidate_player]

    def ids(cards):
        return [getattr(card, "id", None) if card is not None else None for card in cards]

    return {
        "turn": int(getattr(obs.current, "turn", -1)),
        "candidate_deck_count": int(getattr(player, "deckCount", -1)),
        "candidate_hand_count": int(getattr(player, "handCount", -1)),
        "candidate_active": ids(player.active),
        "candidate_bench": ids(player.bench),
        "candidate_discard_tail": ids(player.discard[-5:]),
        "opponent_active": ids(opponent.active),
        "opponent_bench": ids(opponent.bench),
    }


def trace_game(
    candidate: suite.Policy,
    opponent: suite.Policy,
    candidate_seat: int,
    player_zero_first: bool,
    seed: int,
    max_decisions: int,
) -> dict[str, Any]:
    from cg.api import SelectType, to_observation_class
    from cg.game import battle_select, battle_start

    random.seed(seed)
    decks = [candidate.deck, opponent.deck] if candidate_seat == 0 else [opponent.deck, candidate.deck]
    policies = [None, None]
    policies[candidate_seat] = candidate
    policies[1 - candidate_seat] = opponent

    obs_dict, start_data = battle_start(decks[0], decks[1])
    if obs_dict is None:
        return {
            "status": "start_error",
            "seed": seed,
            "error": f"{getattr(start_data, 'errorType', None)} player={getattr(start_data, 'errorPlayer', None)}",
            "decisions": [],
            "candidate_score": 0,
        }

    trace = []
    for decision in range(max_decisions):
        obs = to_observation_class(obs_dict)
        if obs.current.result != -1:
            winner = int(obs.current.result)
            score = 1.0 if winner == candidate_seat else 0.0 if winner in (0, 1) else 0.5
            return {
                "status": "complete",
                "seed": seed,
                "winner": winner,
                "candidate_score": score,
                "candidate_reward": 1 if score == 1.0 else -1 if score == 0.0 else 0,
                "candidate_seat": candidate_seat,
                "player_zero_first": player_zero_first,
                "decisions_seen": decision,
                "trace": trace,
            }

        player_index = int(obs.current.yourIndex)
        action = suite.choose_with_forced_first(
            policies[player_index],
            obs_dict,
            player_zero_first=player_zero_first,
        )

        if player_index == candidate_seat:
            chosen_options = [
                option_signature(obs, obs.select.option[index], index)
                for index in action
                if 0 <= index < len(obs.select.option)
            ]
            option_type_counts = Counter(enum_name(option.type, "OptionType") for option in obs.select.option)
            trace.append(
                {
                    "decision": decision,
                    "select_type": enum_name(getattr(obs.select, "type", None), "SelectType"),
                    "context": enum_name(getattr(obs.select, "context", None), "SelectContext"),
                    "min_count": int(getattr(obs.select, "minCount", 0)),
                    "max_count": int(getattr(obs.select, "maxCount", 0)),
                    "chosen_indices": list(action),
                    "chosen": chosen_options,
                    "available_type_counts": dict(option_type_counts),
                    "is_main": getattr(obs.select, "type", None) == SelectType.MAIN,
                    "board": board_summary(obs, candidate_seat),
                }
            )

        obs_dict = battle_select(action)

    return {
        "status": "max_decisions",
        "seed": seed,
        "candidate_score": 0.5,
        "candidate_reward": 0,
        "candidate_seat": candidate_seat,
        "player_zero_first": player_zero_first,
        "decisions_seen": max_decisions,
        "trace": trace,
    }


def summarize(traced_games: list[dict[str, Any]]) -> dict[str, Any]:
    by_context: dict[str, Counter] = defaultdict(Counter)
    by_chosen: dict[str, Counter] = defaultdict(Counter)
    first_card_choice: dict[str, Counter] = defaultdict(Counter)
    for game in traced_games:
        outcome = "win" if game.get("candidate_score") == 1.0 else "loss" if game.get("candidate_score") == 0.0 else "draw"
        for decision in game.get("trace", []):
            context = decision["context"]
            by_context[context][outcome] += 1
            for chosen in decision["chosen"]:
                key = f"{context}|{chosen['type']}|{chosen.get('card_id')}|{chosen.get('attack_id')}"
                by_chosen[key][outcome] += 1
                if chosen["type"] == "CARD":
                    first_card_choice[context][str(chosen.get("card_id"))] += 1
    return {
        "contexts": {key: dict(value) for key, value in sorted(by_context.items())},
        "chosen": {key: dict(value) for key, value in sorted(by_chosen.items())},
        "card_choices_by_context": {key: dict(value.most_common()) for key, value in sorted(first_card_choice.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games-per-cell", type=int, default=2)
    parser.add_argument("--max-decisions", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument("--candidates", nargs="+", default=["promoted", "card_selection_v1"])
    parser.add_argument(
        "--opponents",
        nargs="+",
        default=["author_abomasnow_policy", "author_iono_policy", "author_lucario_policy"],
    )
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)

    candidates = {
        name: suite.load_local_policy(name, path)
        for name, path in suite.AGENT_PATHS.items()
        if name in set(args.candidates) and path.exists()
    }
    opponents = {
        name: suite.load_author_policy(name, path)
        for name, path in suite.AUTHOR_POLICIES.items()
        if name in set(args.opponents) and path.exists()
    }
    if set(args.candidates) - set(candidates):
        raise FileNotFoundError(f"Missing candidates: {sorted(set(args.candidates) - set(candidates))}")
    if set(args.opponents) - set(opponents):
        raise FileNotFoundError(f"Missing opponents: {sorted(set(args.opponents) - set(opponents))}")

    rows = []
    summaries = {}
    game_index = 0
    for candidate_name, candidate in candidates.items():
        for opponent_name, opponent in opponents.items():
            matchup = f"{candidate_name}_vs_{opponent_name}"
            games = []
            for candidate_seat in (0, 1):
                for player_zero_first in (False, True):
                    for repeat in range(args.games_per_cell):
                        seed = args.seed + game_index * 10_000 + candidate_seat * 100 + int(player_zero_first) * 10 + repeat
                        game_index += 1
                        try:
                            row = trace_game(
                                candidate=candidate,
                                opponent=opponent,
                                candidate_seat=candidate_seat,
                                player_zero_first=player_zero_first,
                                seed=seed,
                                max_decisions=args.max_decisions,
                            )
                        except Exception as exc:  # noqa: BLE001
                            row = {
                                "status": "error",
                                "seed": seed,
                                "candidate_score": 0,
                                "candidate_reward": 0,
                                "error": repr(exc),
                                "candidate_seat": candidate_seat,
                                "player_zero_first": player_zero_first,
                                "trace": [],
                            }
                        row["candidate"] = candidate_name
                        row["opponent"] = opponent_name
                        row["matchup"] = matchup
                        games.append(row)
                        rows.append(row)
            wins = sum(game.get("candidate_score") == 1.0 for game in games)
            losses = sum(game.get("candidate_score") == 0.0 for game in games)
            draws = sum(game.get("candidate_score") == 0.5 for game in games)
            summaries[matchup] = {
                "games": len(games),
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "score_rate": round(sum(game.get("candidate_score", 0) for game in games) / len(games), 4),
                "decision_summary": summarize(games),
            }
            print(f"{matchup}: {wins}-{losses}{'-' + str(draws) if draws else ''}, score={summaries[matchup]['score_rate']}")

    RESULTS_PATH.write_text(
        json.dumps(
            {
                "games_per_cell": args.games_per_cell,
                "max_decisions": args.max_decisions,
                "seed": args.seed,
                "deck_mode": "all policies run on agent/deck.csv",
                "summaries": summaries,
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
