from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "scratch" / "loss_diagnostics" / "54303967_metal_cinderace-alakazam_dunsparce_losses.json"
DEFAULT_OUTPUT_DIR = ROOT / "scratch" / "strategy_eda"


POKEMON_RE = re.compile(r"^(?P<name>.+?) hp=(?P<hp>\d+) e=(?P<energy>\d+) tools=(?P<tools>\d+)$")
KEY_TARGETS = (
    "Archaludon ex",
    "Cinderace",
    "Duraludon",
    "Relicanth",
    "Alakazam",
    "Kadabra",
    "Abra",
    "Dudunsparce",
    "Dunsparce",
)


def parse_pokemon(label: str) -> dict[str, object]:
    match = POKEMON_RE.match(label)
    if not match:
        return {"name": label, "hp": None, "energy": None, "tools": None}
    return {
        "name": match.group("name"),
        "hp": int(match.group("hp")),
        "energy": int(match.group("energy")),
        "tools": int(match.group("tools")),
    }


def compact_board(board: dict) -> dict[str, object]:
    our_active = [parse_pokemon(label) for label in board.get("our_active", [])]
    opponent_active = [parse_pokemon(label) for label in board.get("opponent_active", [])]
    opponent_bench = [parse_pokemon(label) for label in board.get("opponent_bench", [])]
    hand = board.get("interesting_hand", {})

    key_targets = []
    for pokemon in opponent_active + opponent_bench:
        name = str(pokemon["name"])
        if any(target in name for target in KEY_TARGETS):
            key_targets.append(pokemon)

    return {
        "turn": board.get("turn"),
        "our_active": our_active,
        "opponent_active": opponent_active,
        "key_targets": key_targets,
        "boss_in_hand": hand.get("Boss’s Orders", hand.get("Boss's Orders", 0)),
        "energy_in_hand": hand.get("Basic {F} Energy", 0),
        "premium_power_pro_in_hand": hand.get("Premium Power Pro", 0),
        "switch_in_hand": hand.get("Switch", 0),
        "energy_attached": board.get("energy_attached"),
        "supporter_played": board.get("supporter_played"),
    }


def find_midgame_rows(episode: dict, start_turn: int, end_turn: int) -> list[dict[str, object]]:
    rows = []
    seen = set()
    for decision in episode.get("passive_main_decisions", []) + episode.get("early_decisions", []):
        board = decision.get("board", {})
        turn = board.get("turn")
        if turn is None or turn < start_turn or turn > end_turn:
            continue
        key = (decision.get("step"), turn)
        if key in seen:
            continue
        seen.add(key)
        compact = compact_board(board)
        compact.update(
            {
                "episode": episode["episode"],
                "archetype": episode["archetype"],
                "went_first": episode["went_first"],
                "step": decision.get("step"),
                "context": decision.get("context"),
                "action_labels": decision.get("action_labels", []),
                "first_attack_turn": episode.get("first_attack", {}).get("turn"),
            }
        )
        rows.append(compact)
    return sorted(rows, key=lambda row: (row["archetype"], row["episode"], row["turn"], row["step"]))


def summarize(rows: list[dict[str, object]], episodes: list[dict[str, object]]) -> dict[str, object]:
    by_arch = defaultdict(list)
    for row in rows:
        by_arch[row["archetype"]].append(row)

    episode_summary = defaultdict(list)
    for episode in episodes:
        episode_summary[episode["archetype"]].append(episode)

    summary: dict[str, object] = {}
    for archetype, eps in sorted(episode_summary.items()):
        first_attack_turns = [
            ep.get("first_attack", {}).get("turn")
            for ep in eps
            if ep.get("first_attack", {}).get("turn") is not None
        ]
        arch_rows = by_arch.get(archetype, [])
        active_counter = Counter()
        target_counter = Counter()
        boss_rows = 0
        near_ko_rows = 0
        mega_lucario_low_hp_rows = 0

        for row in arch_rows:
            our_active = row.get("our_active", [])
            if our_active:
                active_counter[str(our_active[0]["name"])] += 1
                if "Mega Lucario ex" in str(our_active[0]["name"]) and (our_active[0].get("hp") or 999) <= 100:
                    mega_lucario_low_hp_rows += 1
            if row.get("boss_in_hand", 0):
                boss_rows += 1
            for target in row.get("key_targets", []):
                target_counter[str(target["name"])] += 1
                hp = target.get("hp")
                if isinstance(hp, int) and hp <= 140:
                    near_ko_rows += 1

        summary[archetype] = {
            "episodes": len(eps),
            "went_first": sum(1 for ep in eps if ep.get("went_first")),
            "median_first_attack_turn": median(first_attack_turns) if first_attack_turns else None,
            "midgame_rows": len(arch_rows),
            "our_active_counts_turn_window": dict(active_counter.most_common()),
            "key_target_counts_turn_window": dict(target_counter.most_common()),
            "rows_with_boss_in_hand": boss_rows,
            "rows_with_near_ko_key_target_hp_le_140": near_ko_rows,
            "rows_with_mega_lucario_hp_le_100": mega_lucario_low_hp_rows,
        }
    return summary


def markdown(summary: dict[str, object], rows: list[dict[str, object]], start_turn: int, end_turn: int) -> str:
    lines = [
        "# Strategy EDA from Public Loss Diagnostics",
        "",
        f"Turn window: {start_turn}-{end_turn}",
        "",
        "## Archetype summary",
        "",
        "| Archetype | Episodes | Went first | Median first attack | Midgame rows | Boss in hand rows | Near-KO target rows | Low-HP Mega Lucario rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for archetype, item in summary.items():
        lines.append(
            "| {archetype} | {episodes} | {went_first} | {median_first_attack_turn} | {midgame_rows} | {rows_with_boss_in_hand} | {rows_with_near_ko_key_target_hp_le_140} | {rows_with_mega_lucario_hp_le_100} |".format(
                archetype=archetype,
                **item,
            )
        )

    lines += ["", "## Active Pokemon in turn window", ""]
    for archetype, item in summary.items():
        lines.append(f"### {archetype}")
        lines.append("")
        for name, count in item["our_active_counts_turn_window"].items():
            lines.append(f"- {name}: {count}")
        lines.append("")

    lines += ["## Key opponent targets in turn window", ""]
    for archetype, item in summary.items():
        lines.append(f"### {archetype}")
        lines.append("")
        for name, count in item["key_target_counts_turn_window"].items():
            lines.append(f"- {name}: {count}")
        lines.append("")

    lines += [
        "## Candidate implication",
        "",
        "- Do not submit v16/v17 based on this EDA alone.",
        "- The next candidate should focus on repeated midgame states, not opening selection.",
        "- A v18 patch should be limited to attack/Boss/retreat scoring when a key evolved target is visible and already KO-able or near-KO.",
        "",
        "## Example midgame rows",
        "",
    ]
    for row in rows[:20]:
        target_text = ", ".join(
            f"{target['name']} hp={target.get('hp')} e={target.get('energy')}" for target in row.get("key_targets", [])
        )
        active_text = ", ".join(
            f"{pokemon['name']} hp={pokemon.get('hp')} e={pokemon.get('energy')}" for pokemon in row.get("our_active", [])
        )
        lines.append(
            f"- episode {row['episode']} ({row['archetype']}), turn {row['turn']}, went_first={row['went_first']}: "
            f"active=[{active_text}], targets=[{target_text}], boss={row.get('boss_in_hand', 0)}, actions={row.get('action_labels', [])}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create strategy EDA tables from public loss diagnostics.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-turn", type=int, default=5)
    parser.add_argument("--end-turn", type=int, default=7)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    episodes = data["episodes"]
    rows = []
    for episode in episodes:
        rows.extend(find_midgame_rows(episode, args.start_turn, args.end_turn))

    summary = summarize(rows, episodes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    json_path = args.output_dir / f"{stem}_strategy_eda.json"
    md_path = args.output_dir / f"{stem}_strategy_eda.md"
    payload = {
        "source": str(args.input),
        "start_turn": args.start_turn,
        "end_turn": args.end_turn,
        "summary": summary,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(markdown(summary, rows, args.start_turn, args.end_turn), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
