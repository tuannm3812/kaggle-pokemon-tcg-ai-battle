"""Diagnose public leaderboard loss replays by archetype.

This script is intentionally descriptive rather than counterfactual. It reads
already-downloaded Kaggle replay JSONs and the corresponding
``analysis_summary.json`` produced by ``analyze_submission_episodes.py``. The
output highlights early-game choices, action-type frequencies, first attack
turns, and compact board snapshots for selected losing archetypes.
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
OUTPUT_ROOT = ROOT / "scratch" / "loss_diagnostics"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_author_opponent_suite as suite  # noqa: E402


OPTION_TYPES = {
    0: "NUMBER",
    1: "YES",
    2: "NO",
    3: "CARD",
    4: "TOOL_CARD",
    5: "ENERGY_CARD",
    6: "ENERGY",
    7: "PLAY",
    8: "ATTACH",
    9: "EVOLVE",
    10: "ABILITY",
    11: "DISCARD",
    12: "RETREAT",
    13: "ATTACK",
    14: "END",
    15: "SKILL",
    16: "SPECIAL_CONDITION",
}

CONTEXTS = {
    0: "MAIN",
    1: "SETUP_ACTIVE_POKEMON",
    2: "SETUP_BENCH_POKEMON",
    3: "SWITCH",
    4: "TO_ACTIVE",
    7: "TO_HAND",
    8: "DISCARD",
    21: "ATTACH_FROM",
    22: "ATTACH_TO",
    35: "ATTACK",
    37: "EVOLVE",
    38: "DRAW_COUNT",
    41: "IS_FIRST",
    43: "ACTIVATE",
    42: "MULLIGAN",
}

INTERESTING_IDS = {
    6: "Fighting Energy",
    57: "Relicanth",
    66: "Dudunsparce",
    119: "Dreepy",
    120: "Drakloak",
    121: "Dragapult ex",
    235: "Budew",
    304: "Hop's Snorlax",
    305: "Dunsparce",
    311: "Hop's Cramorant",
    673: "Makuhita",
    674: "Hariyama",
    675: "Lunatone",
    676: "Solrock",
    677: "Riolu",
    678: "Mega Lucario ex",
    878: "Hop's Phantump",
    879: "Hop's Trevenant",
    1102: "Dusk Ball",
    1123: "Switch",
    1141: "Premium Power Pro",
    1142: "Fighting Gong",
    1152: "Poke Pad",
    1159: "Hero Cape",
    1182: "Boss's Orders",
    1192: "Carmine",
    1227: "Lillie's Determination",
    1252: "Gravity Mountain",
}


def card_names() -> dict[int, str]:
    """Load card names from the staged SDK, with a compact fallback map."""
    try:
        suite.stage_runtime(suite.find_sdk_dir())
        runtime = str(suite.RUNTIME_ROOT.resolve())
        if runtime not in sys.path:
            sys.path.insert(0, runtime)
        from cg.api import all_card_data  # noqa: PLC0415

        return {card.cardId: getattr(card, "name", str(card.cardId)) for card in all_card_data()}
    except Exception:  # noqa: BLE001 - diagnostics should still be usable from cached replays.
        return dict(INTERESTING_IDS)


def name(card_id: int | None, names: dict[int, str]) -> str:
    if card_id is None:
        return "None"
    return names.get(card_id, INTERESTING_IDS.get(card_id, str(card_id)))


def pokemon_label(pokemon: dict[str, Any] | None, names: dict[int, str]) -> str:
    if not pokemon:
        return "None"
    energies = pokemon.get("energies") or []
    tools = pokemon.get("tools") or []
    return f"{name(pokemon.get('id'), names)} hp={pokemon.get('hp')} e={len(energies)} tools={len(tools)}"


def board_snapshot(current: dict[str, Any], seat: int, names: dict[int, str]) -> dict[str, Any]:
    player = current["players"][seat]
    opponent = current["players"][1 - seat]
    hand_ids = [card.get("id") for card in player.get("hand", [])]
    hand_counts = Counter(hand_ids)
    interesting_hand = {
        name(card_id, names): count
        for card_id, count in sorted(hand_counts.items())
        if card_id in INTERESTING_IDS and count > 0
    }
    return {
        "turn": current.get("turn"),
        "turn_action_count": current.get("turnActionCount"),
        "energy_attached": current.get("energyAttached"),
        "supporter_played": current.get("supporterPlayed"),
        "deck_count": player.get("deckCount"),
        "hand_count": len(player.get("hand", [])),
        "interesting_hand": interesting_hand,
        "our_active": [pokemon_label(p, names) for p in player.get("active", [])],
        "our_bench": [pokemon_label(p, names) for p in player.get("bench", []) if p],
        "opponent_active": [pokemon_label(p, names) for p in opponent.get("active", [])],
        "opponent_bench": [pokemon_label(p, names) for p in opponent.get("bench", []) if p],
    }


def option_label(option: dict[str, Any], obs: dict[str, Any], seat: int, names: dict[int, str]) -> str:
    option_type = OPTION_TYPES.get(option.get("type"), str(option.get("type")))
    area = option.get("area")
    index = option.get("index")
    card_id = None
    current = obs.get("current") or {}
    try:
        if area == 2 and index is not None:
            card_id = current["players"][seat]["hand"][index]["id"]
        elif area == 4 and index is not None:
            card_id = current["players"][option.get("playerIndex", seat)]["active"][index]["id"]
        elif area == 5 and index is not None:
            card_id = current["players"][option.get("playerIndex", seat)]["bench"][index]["id"]
        elif area == 12 and index is not None:
            card_id = current.get("looking", [])[index]["id"]
    except Exception:  # noqa: BLE001
        card_id = None

    bits = [option_type]
    if card_id is not None:
        bits.append(name(card_id, names))
    if "attackId" in option:
        bits.append(f"attack={option['attackId']}")
    if "inPlayArea" in option:
        bits.append(f"to_area={option.get('inPlayArea')}:{option.get('inPlayIndex')}")
    return " ".join(bits)


def selected_labels(obs: dict[str, Any], action: list[int], seat: int, names: dict[int, str]) -> list[str]:
    options = ((obs.get("select") or {}).get("option") or [])
    labels = []
    for index in action or []:
        if not isinstance(index, int) or index < 0 or index >= len(options):
            labels.append("RAW_ACTION")
            continue
        labels.append(option_label(options[index], obs, seat, names))
    if not labels:
        context = CONTEXTS.get((obs.get("select") or {}).get("context"), str((obs.get("select") or {}).get("context")))
        labels.append(f"NO_ACTION/{context}")
    return labels


def load_analysis(submission_id: int) -> dict[str, Any]:
    path = EPISODE_ROOT / str(submission_id) / "analysis_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run analyze_submission_episodes.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose_episode(path: Path, row: dict[str, Any], names: dict[int, str], max_turn: int) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seat = int(row["our_seat"])
    first_attack = None
    chosen_type_counts: Counter[str] = Counter()
    context_counts: Counter[str] = Counter()
    early_decisions = []
    passive_main_decisions = []
    setup_choices = []

    for step_index, step in enumerate(data["steps"]):
        state = step[seat]
        if state.get("status") != "ACTIVE":
            continue
        obs = state.get("observation") or {}
        select = obs.get("select")
        current = obs.get("current") or {}
        if not select or not current:
            continue
        turn = current.get("turn", -1)
        context = CONTEXTS.get(select.get("context"), str(select.get("context")))
        action = state.get("action") or []
        labels = selected_labels(obs, action, seat, names)
        context_counts[context] += 1
        for label in labels:
            chosen_type_counts[label.split()[0]] += 1
        if any(label.startswith("ATTACK") for label in labels) and first_attack is None:
            first_attack = {"step": step_index, "turn": turn, "labels": labels}
        if context.startswith("SETUP") or context == "IS_FIRST":
            setup_choices.append({"step": step_index, "context": context, "labels": labels})
        if turn <= max_turn:
            record = {
                "step": step_index,
                "context": context,
                "action_labels": labels,
                "board": board_snapshot(current, seat, names),
            }
            early_decisions.append(record)
            if context == "MAIN" and labels == ["NO_ACTION/MAIN"]:
                passive_main_decisions.append(record)

    return {
        "episode": row["episode"],
        "archetype": row["opponent_archetype"],
        "opponent_label": row["opponent_label"],
        "steps": row["steps"],
        "our_seat": row["our_seat"],
        "went_first": row["went_first"],
        "first_attack": first_attack,
        "context_counts": dict(context_counts),
        "chosen_type_counts": dict(chosen_type_counts),
        "setup_choices": setup_choices,
        "passive_main_decisions": passive_main_decisions[:10],
        "early_decisions": early_decisions[:80],
    }


def summarize_episode_diagnostics(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_archetype: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_archetype[item["archetype"]].append(item)
    out = {}
    for archetype, rows in sorted(by_archetype.items()):
        first_attack_turns = [row["first_attack"]["turn"] for row in rows if row.get("first_attack")]
        missing_attack = sum(1 for row in rows if not row.get("first_attack"))
        action_counter: Counter[str] = Counter()
        context_counter: Counter[str] = Counter()
        went_first = sum(1 for row in rows if row["went_first"])
        for row in rows:
            action_counter.update(row["chosen_type_counts"])
            context_counter.update(row["context_counts"])
        out[archetype] = {
            "episodes": len(rows),
            "went_first": went_first,
            "missing_first_attack": missing_attack,
            "first_attack_turns": first_attack_turns,
            "median_first_attack_turn": sorted(first_attack_turns)[len(first_attack_turns) // 2] if first_attack_turns else None,
            "chosen_type_counts": dict(action_counter.most_common()),
            "context_counts": dict(context_counter.most_common()),
            "episode_ids": [row["episode"] for row in rows],
        }
    return out


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        f"# Loss replay diagnosis for submission {result['submission_id']}",
        "",
        f"Archetypes: {', '.join(result['archetypes'])}",
        "",
        "## Summary",
        "",
    ]
    for archetype, summary in result["summary"].items():
        lines.extend([
            f"### {archetype}",
            "",
            f"- episodes: {summary['episodes']}",
            f"- went first: {summary['went_first']}/{summary['episodes']}",
            f"- first attack turns: {summary['first_attack_turns'] or 'none'}",
            f"- missing first attack: {summary['missing_first_attack']}",
            f"- top chosen action types: {summary['chosen_type_counts']}",
            "",
        ])
    lines.append("## Early-turn details")
    lines.append("")
    for item in result["episodes"]:
        lines.extend([
            f"### Episode {item['episode']} — {item['archetype']}",
            "",
            f"Opponent: {item['opponent_label']}",
            f"Went first: {item['went_first']}; seat: {item['our_seat']}; steps: {item['steps']}",
            f"First attack: {item['first_attack']}",
            "",
            "Setup choices:",
            "",
        ])
        for setup in item["setup_choices"]:
            lines.append(f"- step {setup['step']} {setup['context']}: {setup['labels']}")
        lines.extend(["", "Passive early MAIN decisions:", ""])
        for decision in item["passive_main_decisions"][:5]:
            board = decision["board"]
            lines.append(
                f"- step {decision['step']} turn {board['turn']}: active={board['our_active']} "
                f"bench={board['our_bench']} hand={board['interesting_hand']} op_active={board['opponent_active']}"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-id", type=int, default=54391951)
    parser.add_argument("--archetypes", nargs="+", default=["dragapult", "phantump_trevenant_control"])
    parser.add_argument("--max-turn", type=int, default=6)
    parser.add_argument("--losses-only", action="store_true", default=True)
    args = parser.parse_args()

    names = card_names()
    analysis = load_analysis(args.submission_id)
    rows = [row for row in analysis["rows"] if row["opponent_archetype"] in set(args.archetypes)]
    if args.losses_only:
        rows = [row for row in rows if not row["win"]]

    base = EPISODE_ROOT / str(args.submission_id)
    episodes = []
    for row in rows:
        path = base / f"episode-{row['episode']}-replay.json"
        if path.exists():
            episodes.append(diagnose_episode(path, row, names, args.max_turn))

    result = {
        "submission_id": args.submission_id,
        "archetypes": args.archetypes,
        "losses_only": args.losses_only,
        "max_turn": args.max_turn,
        "summary": summarize_episode_diagnostics(episodes),
        "episodes": episodes,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stem = f"{args.submission_id}_{'-'.join(args.archetypes)}_losses"
    json_path = OUTPUT_ROOT / f"{stem}.json"
    md_path = OUTPUT_ROOT / f"{stem}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()