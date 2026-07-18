"""Find concrete missed-opportunity patterns in Phantump/Trevenant losses.

This is a replay-state diagnostic, not a simulator. It scans cached public
replay JSONs and asks whether our actual selected action appeared to miss one
of a few repeated tactical opportunities:

- active attack knockout available but not selected;
- Boss's Orders available while a bench knockout target exists;
- Switch/retreat available while the active attacker is critically damaged;
- draw/support cards available while the hand is mostly energy or otherwise
  narrow.

The goal is to generate evidence for a future v25 candidate only if the same
missed pattern appears repeatedly.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EPISODE_ROOT = ROOT / "scratch" / "leaderboard_episodes"
LOSS_DIAGNOSTIC = ROOT / "scratch" / "loss_diagnostics" / "54391951_dragapult-phantump_trevenant_control_losses.json"
OUTPUT_ROOT = ROOT / "scratch" / "opportunity_diagnostics"


class C:
    BASIC_FIGHTING_ENERGY = 6
    HOPS_SNORLAX = 304
    HOPS_CRAMORANT = 311
    HOPS_PHANTUMP = 878
    HOPS_TREVENANT = 879
    SWITCH = 1123
    PREMIUM_POWER_PRO = 1141
    BOSS_ORDERS = 1182
    CARMINE = 1192
    LILLIE_DETERMINATION = 1227
    MEGA_LUCARIO_EX = 678
    HARIYAMA = 674
    SOLROCK = 676


OPTION_TYPES = {
    7: "PLAY",
    8: "ATTACH",
    9: "EVOLVE",
    10: "ABILITY",
    12: "RETREAT",
    13: "ATTACK",
    14: "END",
}

PHANTUMP_IDS = {C.HOPS_PHANTUMP, C.HOPS_TREVENANT, C.HOPS_CRAMORANT, C.HOPS_SNORLAX}
DRAW_CARD_IDS = {C.PREMIUM_POWER_PRO, C.CARMINE, C.LILLIE_DETERMINATION}


def load_loss_rows(path: Path, archetype: str) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data.get("episodes", []) if row.get("archetype") == archetype]


def option_card_id(obs: dict[str, Any], option: dict[str, Any], seat: int) -> int | None:
    current = obs.get("current") or {}
    players = current.get("players") or []
    area = option.get("area")
    index = option.get("index")
    player_index = option.get("playerIndex", seat)
    try:
        if area == 2 and index is not None:
            return int(players[player_index]["hand"][index]["id"])
        if area == 4 and index is not None:
            return int(players[player_index]["active"][index]["id"])
        if area == 5 and index is not None:
            card = players[player_index]["bench"][index]
            return int(card["id"]) if card else None
    except Exception:  # noqa: BLE001 - replay states can be partial.
        return None
    return None


def selected_option_indexes(state: dict[str, Any]) -> set[int]:
    return {index for index in (state.get("action") or []) if isinstance(index, int)}


def board(obs: dict[str, Any], seat: int) -> tuple[dict[str, Any], dict[str, Any]]:
    current = obs.get("current") or {}
    players = current.get("players") or [{}, {}]
    return players[seat], players[1 - seat]


def pokemon_label(pokemon: dict[str, Any] | None) -> str:
    if not pokemon:
        return "None"
    return f"id={pokemon.get('id')} hp={pokemon.get('hp')} e={len(pokemon.get('energies') or [])}"


def all_pokemon(player: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    out: list[tuple[int, dict[str, Any]]] = []
    for index, pokemon in enumerate(player.get("active") or []):
        if pokemon:
            out.append((index, pokemon))
    for index, pokemon in enumerate(player.get("bench") or [], start=1):
        if pokemon:
            out.append((index, pokemon))
    return out


def attack_damage(active: dict[str, Any] | None, attack_id: int | None, has_lunatone: bool) -> int:
    """Approximate printed damage used only for opportunity triage."""
    if not active or attack_id is None:
        return 0
    active_id = active.get("id")
    if active_id == C.MEGA_LUCARIO_EX:
        if attack_id == 983:
            return 270
        return 130
    if active_id == C.HARIYAMA:
        return 210
    if active_id == C.SOLROCK and has_lunatone:
        return 70
    return 0


def available_attack_kos(obs: dict[str, Any], seat: int) -> list[dict[str, Any]]:
    us, opponent = board(obs, seat)
    active = (us.get("active") or [None])[0]
    has_lunatone = any(p and p.get("id") == 675 for _, p in all_pokemon(us))
    options = ((obs.get("select") or {}).get("option") or [])
    attack_options = [
        (index, option)
        for index, option in enumerate(options)
        if option.get("type") == 13
    ]
    kos: list[dict[str, Any]] = []
    for option_index, option in attack_options:
        damage = attack_damage(active, option.get("attackId"), has_lunatone)
        if damage <= 0:
            continue
        for target_index, pokemon in all_pokemon(opponent):
            if pokemon.get("hp", 9999) <= damage:
                kos.append(
                    {
                        "option_index": option_index,
                        "attack_id": option.get("attackId"),
                        "target_index": target_index,
                        "target_id": pokemon.get("id"),
                        "target_hp": pokemon.get("hp"),
                        "damage": damage,
                        "target_family": "phantump_control" if pokemon.get("id") in PHANTUMP_IDS else "other",
                    }
                )
    return kos


def boss_bench_ko_opportunities(obs: dict[str, Any], seat: int) -> list[dict[str, Any]]:
    options = ((obs.get("select") or {}).get("option") or [])
    boss_options = [
        index
        for index, option in enumerate(options)
        if option.get("type") == 7 and option_card_id(obs, option, seat) == C.BOSS_ORDERS
    ]
    if not boss_options:
        return []
    return [ko | {"boss_option_indexes": boss_options} for ko in available_attack_kos(obs, seat) if ko["target_index"] >= 1]


def selected_labels(obs: dict[str, Any], state: dict[str, Any], seat: int) -> list[str]:
    options = ((obs.get("select") or {}).get("option") or [])
    labels = []
    for index in state.get("action") or []:
        if not isinstance(index, int) or index < 0 or index >= len(options):
            labels.append(f"RAW:{index}")
            continue
        option = options[index]
        card_id = option_card_id(obs, option, seat)
        label = OPTION_TYPES.get(option.get("type"), str(option.get("type")))
        if card_id is not None:
            label += f":{card_id}"
        if option.get("attackId") is not None:
            label += f":attack={option.get('attackId')}"
        labels.append(label)
    return labels or ["NO_ACTION"]


def detect_opportunities(path: Path, row: dict[str, Any], max_turn: int) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seat = int(row["our_seat"])
    turn_attack_steps: dict[int, list[int]] = defaultdict(list)
    for step_index, step in enumerate(data.get("steps") or []):
        state = step[seat]
        if state.get("status") != "ACTIVE":
            continue
        obs = state.get("observation") or {}
        current = obs.get("current") or {}
        select = obs.get("select") or {}
        turn = current.get("turn")
        if turn is None or turn > max_turn:
            continue
        options = select.get("option") or []
        for index in selected_option_indexes(state):
            if 0 <= index < len(options) and options[index].get("type") == 13:
                turn_attack_steps[int(turn)].append(step_index)

    out = []
    for step_index, step in enumerate(data.get("steps") or []):
        state = step[seat]
        if state.get("status") != "ACTIVE":
            continue
        obs = state.get("observation") or {}
        current = obs.get("current") or {}
        select = obs.get("select") or {}
        if not current or not select or select.get("context") not in {0, "MAIN"}:
            continue
        turn = current.get("turn")
        if turn is None or turn > max_turn:
            continue

        us, opponent = board(obs, seat)
        active = (us.get("active") or [None])[0]
        hand_ids = [card.get("id") for card in us.get("hand") or [] if card]
        hand_counts = Counter(hand_ids)
        option_indexes = selected_option_indexes(state)
        options = select.get("option") or []
        chosen_types = {options[i].get("type") for i in option_indexes if 0 <= i < len(options)}
        chosen_cards = {option_card_id(obs, options[i], seat) for i in option_indexes if 0 <= i < len(options)}

        attack_kos = available_attack_kos(obs, seat)
        selected_attack_ko = any(ko["option_index"] in option_indexes for ko in attack_kos)
        later_attack_same_turn = any(later_step > step_index for later_step in turn_attack_steps.get(int(turn), []))
        any_attack_same_turn = bool(turn_attack_steps.get(int(turn), []))
        boss_kos = boss_bench_ko_opportunities(obs, seat)
        selected_boss = C.BOSS_ORDERS in chosen_cards

        switch_options = [
            index
            for index, option in enumerate(options)
            if option.get("type") == 12 or (option.get("type") == 7 and option_card_id(obs, option, seat) == C.SWITCH)
        ]
        selected_switch = any(index in option_indexes for index in switch_options)
        active_hp = active.get("hp", 9999) if active else 9999
        bench_ready = [
            pokemon_label(pokemon)
            for _, pokemon in all_pokemon(us)
            if pokemon is not active and pokemon.get("id") in {C.MEGA_LUCARIO_EX, C.HARIYAMA} and len(pokemon.get("energies") or []) >= 1
        ]

        draw_options = [
            index
            for index, option in enumerate(options)
            if option.get("type") == 7 and option_card_id(obs, option, seat) in DRAW_CARD_IDS
        ]
        selected_draw = any(index in option_indexes for index in draw_options)
        energy_heavy_hand = hand_counts[C.BASIC_FIGHTING_ENERGY] >= max(3, len(hand_ids) // 2)

        flags = []
        if attack_kos and not selected_attack_ko:
            if later_attack_same_turn:
                flags.append("delayed_available_attack_ko")
            elif not any_attack_same_turn:
                flags.append("missed_active_attack_ko")
            else:
                flags.append("selected_non_ko_attack_with_ko_available")
        if boss_kos and not selected_boss:
            flags.append("missed_boss_bench_ko")
        if switch_options and not selected_switch and active_hp <= 80 and bench_ready:
            flags.append("missed_low_hp_switch_or_retreat")
        if draw_options and not selected_draw and (energy_heavy_hand or len(hand_ids) <= 4):
            flags.append("missed_draw_in_narrow_hand")

        if flags:
            out.append(
                {
                    "episode": row["episode"],
                    "step": step_index,
                    "turn": turn,
                    "flags": flags,
                    "selected": selected_labels(obs, state, seat),
                    "active": pokemon_label(active),
                    "bench": [pokemon_label(pokemon) for _, pokemon in all_pokemon(us) if pokemon is not active],
                    "opponent_active": pokemon_label((opponent.get("active") or [None])[0]),
                    "opponent_bench": [pokemon_label(pokemon) for _, pokemon in all_pokemon(opponent)[1:]],
                    "hand_counts": dict(hand_counts),
                    "attack_kos": attack_kos,
                    "boss_kos": boss_kos,
                    "later_attack_same_turn": later_attack_same_turn,
                    "any_attack_same_turn": any_attack_same_turn,
                    "switch_options": switch_options,
                    "draw_options": draw_options,
                }
            )
    return out


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    flag_counts = Counter(flag for item in items for flag in item["flags"])
    by_episode: dict[int, Counter[str]] = defaultdict(Counter)
    by_turn: Counter[int] = Counter()
    selected_counter: Counter[str] = Counter()
    for item in items:
        by_turn[int(item["turn"])] += 1
        selected_counter.update(item["selected"])
        for flag in item["flags"]:
            by_episode[int(item["episode"])][flag] += 1
    return {
        "states_with_flags": len(items),
        "flag_counts": dict(flag_counts.most_common()),
        "by_episode": {str(episode): dict(counter.most_common()) for episode, counter in sorted(by_episode.items())},
        "by_turn": dict(sorted(by_turn.items())),
        "top_selected_actions_in_flagged_states": dict(selected_counter.most_common(12)),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        f"# Phantump/Trevenant missed-opportunity diagnosis for submission {result['submission_id']}",
        "",
        f"Loss diagnostic source: `{result['loss_diagnostic']}`",
        f"Max turn scanned: {result['max_turn']}",
        "",
        "## Summary",
        "",
        f"- episodes scanned: {result['episodes_scanned']}",
        f"- flagged states: {result['summary']['states_with_flags']}",
        f"- flag counts: `{result['summary']['flag_counts']}`",
        f"- by turn: `{result['summary']['by_turn']}`",
        "",
        "## Flagged states",
        "",
    ]
    for item in result["opportunities"][:80]:
        lines.extend(
            [
                f"### Episode {item['episode']} step {item['step']} turn {item['turn']}",
                "",
                f"- flags: `{item['flags']}`",
                f"- selected: `{item['selected']}`",
                f"- active: {item['active']}",
                f"- bench: `{item['bench']}`",
                f"- opponent active: {item['opponent_active']}",
                f"- opponent bench: `{item['opponent_bench']}`",
                f"- attack KOs: `{item['attack_kos']}`",
                f"- boss KOs: `{item['boss_kos']}`",
                f"- switch options: `{item['switch_options']}`",
                f"- draw options: `{item['draw_options']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-id", type=int, default=54391951)
    parser.add_argument("--loss-diagnostic", type=Path, default=LOSS_DIAGNOSTIC)
    parser.add_argument("--archetype", default="phantump_trevenant_control")
    parser.add_argument("--max-turn", type=int, default=15)
    args = parser.parse_args()

    rows = load_loss_rows(args.loss_diagnostic, args.archetype)
    opportunities: list[dict[str, Any]] = []
    base = EPISODE_ROOT / str(args.submission_id)
    for row in rows:
        path = base / f"episode-{row['episode']}-replay.json"
        if path.exists():
            opportunities.extend(detect_opportunities(path, row, args.max_turn))

    result = {
        "submission_id": args.submission_id,
        "loss_diagnostic": str(args.loss_diagnostic.relative_to(ROOT)),
        "archetype": args.archetype,
        "max_turn": args.max_turn,
        "episodes_scanned": len(rows),
        "summary": summarize(opportunities),
        "opportunities": opportunities,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stem = f"{args.submission_id}_{args.archetype}_missed_opportunities_t{args.max_turn}"
    json_path = OUTPUT_ROOT / f"{stem}.json"
    md_path = OUTPUT_ROOT / f"{stem}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
