"""Derive planner v2 from the frozen v1 source using two resource guards."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "candidates" / "abomasnow_planner_v1"
V2 = ROOT / "candidates" / "abomasnow_planner_v2"

source = (V1 / "main.py").read_text()
source = source.replace(
    '            attack_id, damage = _attack_damage(\n'
    '                int(card.id), discard[WATER_ENERGY], hammer_estimate\n'
    '            )\n'
    '            ready = needed == 0\n',
    '            attack_id, damage = _attack_damage(\n'
    '                int(card.id), discard[WATER_ENERGY], hammer_estimate\n'
    '            )\n'
    '            if int(card.id) == KYOGRE and damage <= 0:\n'
    '                continue\n'
    '            ready = needed == 0\n',
)
source = source.replace(
    '    if plan.confident and option.inPlayArea == plan.attacker_area and option.inPlayIndex == plan.attacker_index:\n'
    '        score += 4_000\n',
    '    if (\n'
    '        plan.confident\n'
    '        and plan.energy_needed > 0\n'
    '        and option.inPlayArea == plan.attacker_area\n'
    '        and option.inPlayIndex == plan.attacker_index\n'
    '    ):\n'
    '        score += 4_000\n',
)

if "if int(card.id) == KYOGRE and damage <= 0:" not in source:
    raise RuntimeError("Failed to install the zero-damage Kyogre guard.")
if "and plan.energy_needed > 0" not in source:
    raise RuntimeError("Failed to install the completed-attachment guard.")

V2.mkdir(parents=True, exist_ok=True)
(V2 / "main.py").write_text(source)
(V2 / "deck.csv").write_text((V1 / "deck.csv").read_text())
print("Wrote abomasnow_planner_v2 with resource-completion guards")
