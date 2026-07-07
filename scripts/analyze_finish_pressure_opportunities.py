from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "scratch"
    / "strategy_eda"
    / "54303967_metal_cinderace-alakazam_dunsparce_losses_strategy_eda.json"
)
OUTPUT_DIR = ROOT / "scratch" / "strategy_eda"

POKEMON_RE = re.compile(r"^(?P<name>.+?) hp=(?P<hp>\d+) e=(?P<energy>\d+) tools=(?P<tools>\d+)$")


def parse_label(label: str) -> dict[str, Any]:
    match = POKEMON_RE.match(label)
    if not match:
        return {"name": label, "hp": None, "energy": None}
    return {
        "name": match.group("name"),
        "hp": int(match.group("hp")),
        "energy": int(match.group("energy")),
    }


def normalize_pokemon(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return parse_label(raw)
    return {"name": str(raw), "hp": None, "energy": None}


def is_mega_lucario(pokemon: dict[str, Any]) -> bool:
    return "Mega Lucario ex" in str(pokemon.get("name"))


def is_weak_family_active(archetype: str, pokemon: dict[str, Any]) -> bool:
    name = str(pokemon.get("name"))
    if archetype == "metal_cinderace":
        return any(key in name for key in ("Archaludon ex", "Duraludon", "Cinderace", "Relicanth"))
    if archetype == "alakazam_dunsparce":
        return any(key in name for key in ("Alakazam", "Kadabra", "Abra", "Dunsparce", "Dudunsparce"))
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="No-SDK diagnostic for whether finish-pressure patches have replay-state opportunities."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--near-hp", type=int, default=160)
    parser.add_argument("--min-lucario-energy", type=int, default=1)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    rows = data["rows"]

    by_arch: dict[str, Counter[str]] = defaultdict(Counter)
    examples: list[dict[str, Any]] = []

    for row in rows:
        archetype = row["archetype"]
        by_arch[archetype]["rows"] += 1

        active_list = [normalize_pokemon(item) for item in row.get("our_active", [])]
        opponent_active = [normalize_pokemon(item) for item in row.get("opponent_active", [])]
        if not active_list:
            by_arch[archetype]["missing_our_active"] += 1
            continue
        if not opponent_active:
            by_arch[archetype]["missing_opponent_active"] += 1
            continue

        our_active = active_list[0]
        target = opponent_active[0]

        if is_mega_lucario(our_active):
            by_arch[archetype]["mega_lucario_active"] += 1
        if is_mega_lucario(our_active) and int(our_active.get("energy") or 0) >= args.min_lucario_energy:
            by_arch[archetype]["mega_lucario_with_energy"] += 1

        if is_weak_family_active(archetype, target):
            by_arch[archetype]["weak_family_active"] += 1
            hp = target.get("hp")
            if isinstance(hp, int) and hp <= args.near_hp:
                by_arch[archetype]["active_target_near_hp"] += 1
                if is_mega_lucario(our_active) and int(our_active.get("energy") or 0) >= args.min_lucario_energy:
                    by_arch[archetype]["v19_style_opportunity"] += 1
                    if len(examples) < 20:
                        examples.append(
                            {
                                "episode": row["episode"],
                                "turn": row["turn"],
                                "archetype": archetype,
                                "our_active": our_active,
                                "opponent_active": target,
                                "boss_in_hand": row.get("boss_in_hand", 0),
                                "action_labels": row.get("action_labels", []),
                            }
                        )

    summary = {
        archetype: {
            **dict(counter),
            "weak_family_active_rate": round(counter["weak_family_active"] / counter["rows"], 4)
            if counter["rows"]
            else 0,
            "v19_style_opportunity_rate": round(counter["v19_style_opportunity"] / counter["rows"], 4)
            if counter["rows"]
            else 0,
        }
        for archetype, counter in sorted(by_arch.items())
    }

    payload = {
        "source": str(args.input),
        "near_hp": args.near_hp,
        "min_lucario_energy": args.min_lucario_energy,
        "summary": summary,
        "examples": examples,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_json = OUTPUT_DIR / "finish_pressure_opportunities.json"
    output_md = OUTPUT_DIR / "finish_pressure_opportunities.md"
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Finish Pressure Opportunity Diagnostic",
        "",
        f"Source: `{args.input}`",
        "",
        "| Archetype | Rows | Weak active rows | Near-HP active rows | Mega Lucario + energy rows | v19-style opportunities | Opportunity rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for archetype, item in summary.items():
        lines.append(
            f"| {archetype} | {item.get('rows', 0)} | {item.get('weak_family_active', 0)} | "
            f"{item.get('active_target_near_hp', 0)} | {item.get('mega_lucario_with_energy', 0)} | "
            f"{item.get('v19_style_opportunity', 0)} | {item.get('v19_style_opportunity_rate', 0)} |"
        )
    lines += ["", "## Example opportunities", ""]
    for example in examples:
        lines.append(
            f"- episode {example['episode']} turn {example['turn']} ({example['archetype']}): "
            f"our={example['our_active']}, opp={example['opponent_active']}, "
            f"boss={example['boss_in_hand']}, actions={example['action_labels']}"
        )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {output_json.relative_to(ROOT)}")
    print(f"Wrote {output_md.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
