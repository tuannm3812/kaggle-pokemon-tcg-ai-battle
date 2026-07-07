"""Analyze opening/setup categories in downloaded public leaderboard replays.

This diagnostic complements ``diagnose_public_loss_replays.py``. Instead of
looking only at critical losses, it compares early-game categories across wins
and losses for a submitted agent:

- setup active Pokemon;
- whether we went first;
- first attack turn and attacker;
- first visible turn-1 hand features;
- early energy attachment targets.

The goal is to find candidate hypotheses that are narrower than broad matchup
target-score changes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EPISODE_ROOT = ROOT / "scratch" / "leaderboard_episodes"
OUTPUT_ROOT = ROOT / "scratch" / "opening_diagnostics"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


OPTION_ATTACH = 8
OPTION_ATTACK = 13
CONTEXT_SETUP_ACTIVE = 1
CONTEXT_SETUP_BENCH = 2
CONTEXT_MAIN = 0


INTERESTING_IDS = {
    6: "Fighting Energy",
    673: "Makuhita",
    674: "Hariyama",
    675: "Lunatone",
    676: "Solrock",
    677: "Riolu",
    678: "Mega Lucario ex",
    1102: "Dusk Ball",
    1123: "Switch",
    1141: "Premium Power Pro",
    1142: "Fighting Gong",
    1159: "Hero Cape",
    1182: "Boss's Orders",
    1192: "Carmine",
    1227: "Lillie's Determination",
    1252: "Gravity Mountain",
}


def card_names() -> dict[int, str]:
    try:
        suite.stage_runtime(suite.find_sdk_dir())
        runtime = str(suite.RUNTIME_ROOT.resolve())
        if runtime not in sys.path:
            sys.path.insert(0, runtime)
        from cg.api import all_card_data  # noqa: PLC0415

        return {card.cardId: getattr(card, "name", str(card.cardId)) for card in all_card_data()}
    except Exception:  # noqa: BLE001
        return dict(INTERESTING_IDS)


def card_name(card_id: int | None, names: dict[int, str]) -> str:
    if card_id is None:
        return "None"
    return names.get(card_id, INTERESTING_IDS.get(card_id, str(card_id)))


def selected_option(options: list[dict[str, Any]], action: list[int]) -> dict[str, Any] | None:
    for index in action or []:
        if isinstance(index, int) and 0 <= index < len(options):
            return options[index]
    return None


def card_from_option(
    option: dict[str, Any] | None,
    current: dict[str, Any],
    seat: int,
) -> int | None:
    if not option:
        return None
    area = option.get("area")
    index = option.get("index")
    player_index = option.get("playerIndex", seat)
    try:
        if area == 2 and index is not None:
            return current["players"][player_index]["hand"][index]["id"]
        if area == 4 and index is not None:
            return current["players"][player_index]["active"][index]["id"]
        if area == 5 and index is not None:
            pokemon = current["players"][player_index]["bench"][index]
            return pokemon["id"] if pokemon else None
        if area == 12 and index is not None:
            return current.get("looking", [])[index]["id"]
    except Exception:  # noqa: BLE001
        return None
    return None


def pokemon_id_from_area(current: dict[str, Any], seat: int, area: int, index: int) -> int | None:
    try:
        if area == 4:
            return current["players"][seat]["active"][index]["id"]
        if area == 5:
            pokemon = current["players"][seat]["bench"][index]
            return pokemon["id"] if pokemon else None
    except Exception:  # noqa: BLE001
        return None
    return None


def hand_features(hand_ids: list[int]) -> dict[str, bool]:
    counts = Counter(hand_ids)
    return {
        "has_riolu": counts[677] > 0,
        "has_lucario": counts[678] > 0,
        "has_energy": counts[6] > 0,
        "has_hero_cape": counts[1159] > 0,
        "has_dusk_ball": counts[1102] > 0,
        "has_switch": counts[1123] > 0,
        "has_boss": counts[1182] > 0,
        "has_draw_supporter": counts[1192] > 0 or counts[1227] > 0,
        "energy_count": counts[6],
    }


def opening_bucket(setup_active: int | None, first_hand_features: dict[str, Any]) -> str:
    if setup_active == 677:
        if first_hand_features.get("has_energy") and (
            first_hand_features.get("has_lucario")
            or first_hand_features.get("has_dusk_ball")
            or first_hand_features.get("has_hero_cape")
        ):
            return "riolu_fast_path"
        return "riolu_slow_path"
    if setup_active == 676:
        return "solrock_active"
    if setup_active == 673:
        return "makuhita_active"
    if setup_active == 675:
        return "lunatone_active"
    if setup_active is None:
        return "unknown_active"
    return f"other_active_{setup_active}"


def analyze_replay(path: Path, row: dict[str, Any], names: dict[int, str]) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seat = int(row["our_seat"])
    setup_active = None
    setup_options: list[int] = []
    first_main_hand_features: dict[str, Any] = {}
    first_main_hand_interesting: dict[str, int] = {}
    first_attack_turn = None
    first_attack_attacker = None
    early_attach_targets: list[int] = []

    for step in data["steps"]:
        state = step[seat]
        if state.get("status") != "ACTIVE":
            continue
        obs = state.get("observation") or {}
        select = obs.get("select")
        current = obs.get("current")
        if not select or not current:
            continue
        context = select.get("context")
        options = select.get("option") or []
        action = state.get("action") or []
        if context == CONTEXT_SETUP_ACTIVE:
            for option in options:
                card_id = card_from_option(option, current, seat)
                if card_id is not None:
                    setup_options.append(card_id)
            chosen = selected_option(options, action)
            chosen_card = card_from_option(chosen, current, seat)
            if chosen_card is not None:
                setup_active = chosen_card
        if context == CONTEXT_MAIN and not first_main_hand_features:
            hand_ids = [card["id"] for card in current["players"][seat].get("hand", [])]
            first_main_hand_features = hand_features(hand_ids)
            counts = Counter(hand_ids)
            first_main_hand_interesting = {
                card_name(card_id, names): count
                for card_id, count in sorted(counts.items())
                if card_id in INTERESTING_IDS
            }
        if context == CONTEXT_MAIN:
            for index in action or []:
                if not isinstance(index, int) or index < 0 or index >= len(options):
                    continue
                option = options[index]
                if option.get("type") == OPTION_ATTACH:
                    target = pokemon_id_from_area(
                        current,
                        seat,
                        option.get("inPlayArea"),
                        option.get("inPlayIndex"),
                    )
                    if target is not None and current.get("turn", 99) <= 6:
                        early_attach_targets.append(target)
                if option.get("type") == OPTION_ATTACK and first_attack_turn is None:
                    first_attack_turn = current.get("turn")
                    active = current["players"][seat].get("active") or []
                    first_attack_attacker = active[0]["id"] if active else None

    if first_attack_turn is None:
        for step in data["steps"]:
            state = step[seat]
            obs = state.get("observation") or {}
            select = obs.get("select")
            current = obs.get("current")
            if not select or not current:
                continue
            options = select.get("option") or []
            action = state.get("action") or []
            for index in action or []:
                if isinstance(index, int) and 0 <= index < len(options) and options[index].get("type") == OPTION_ATTACK:
                    first_attack_turn = current.get("turn")
                    active = current["players"][seat].get("active") or []
                    first_attack_attacker = active[0]["id"] if active else None
                    break
            if first_attack_turn is not None:
                break

    bucket = opening_bucket(setup_active, first_main_hand_features)
    return {
        "episode": row["episode"],
        "win": row["win"],
        "archetype": row["opponent_archetype"],
        "went_first": row["went_first"],
        "steps": row["steps"],
        "setup_active": setup_active,
        "setup_active_name": card_name(setup_active, names),
        "setup_options": sorted(set(setup_options)),
        "setup_option_names": [card_name(card_id, names) for card_id in sorted(set(setup_options))],
        "opening_bucket": bucket,
        "first_main_hand_features": first_main_hand_features,
        "first_main_hand_interesting": first_main_hand_interesting,
        "first_attack_turn": first_attack_turn,
        "first_attack_attacker": first_attack_attacker,
        "first_attack_attacker_name": card_name(first_attack_attacker, names),
        "early_attach_targets": early_attach_targets,
        "early_attach_target_names": [card_name(card_id, names) for card_id in early_attach_targets],
    }


def summarize(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    out = []
    for value, value_rows in grouped.items():
        wins = sum(1 for row in value_rows if row["win"])
        first_attacks = [row["first_attack_turn"] for row in value_rows if row["first_attack_turn"] is not None]
        out.append(
            {
                key: value,
                "games": len(value_rows),
                "wins": wins,
                "losses": len(value_rows) - wins,
                "score_rate": round(wins / len(value_rows), 4) if value_rows else None,
                "went_first": sum(1 for row in value_rows if row["went_first"]),
                "first_attack_turns": first_attacks,
                "median_first_attack_turn": sorted(first_attacks)[len(first_attacks) // 2] if first_attacks else None,
                "episodes": [row["episode"] for row in value_rows],
            }
        )
    return sorted(out, key=lambda item: (item["score_rate"], -item["games"], str(item[key])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-id", type=int, default=54391951)
    parser.add_argument("--archetypes", nargs="*", default=[])
    args = parser.parse_args()

    names = card_names()
    base = EPISODE_ROOT / str(args.submission_id)
    analysis = json.loads((base / "analysis_summary.json").read_text(encoding="utf-8"))
    rows = analysis["rows"]
    if args.archetypes:
        rows = [row for row in rows if row["opponent_archetype"] in set(args.archetypes)]

    diagnostics = []
    for row in rows:
        path = base / f"episode-{row['episode']}-replay.json"
        if path.exists():
            diagnostics.append(analyze_replay(path, row, names))

    result = {
        "submission_id": args.submission_id,
        "archetypes": args.archetypes,
        "summary_by_archetype": summarize(diagnostics, "archetype"),
        "summary_by_opening_bucket": summarize(diagnostics, "opening_bucket"),
        "summary_by_setup_active": summarize(diagnostics, "setup_active_name"),
        "rows": diagnostics,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = "-".join(args.archetypes) if args.archetypes else "all"
    output_path = OUTPUT_ROOT / f"{args.submission_id}_{suffix}_opening_categories.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("summary_by_opening_bucket")
    for row in result["summary_by_opening_bucket"]:
        print(row)
    print("summary_by_setup_active")
    for row in result["summary_by_setup_active"]:
        print(row)
    print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
