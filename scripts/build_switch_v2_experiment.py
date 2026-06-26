"""Derive the conservative switch v2 notebook from the validated v1 builder."""

from pathlib import Path
import runpy

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "build_switch_experiment.py"))

source_path = ROOT / "notebooks" / "11_conservative_switch_experiment.ipynb"
output_path = ROOT / "notebooks" / "12_conservative_switch_v2_experiment.ipynb"
v2_source = (ROOT / "candidates" / "conservative_switch_v2" / "main.py").read_text(encoding="utf-8")
notebook = nbf.read(source_path, as_version=4)

notebook.cells[0].source = """# Conservative Switch v2 Experiment

**Purpose.** Test a broader retreat rule after switch v1 never selected
`RETREAT`.

**Single intended change.** Keep the promoted development-first ordering, but
prioritize legal `RETREAT` when the active Pokemon is clearly worse than a bench
option: no Energy with a better bench, or low HP with a healthier bench.

**Promotion gate.** The candidate must clear promoted, planner v2, random, and
pressure controls without runtime failures. Production remains frozen unless
the gate clears."""

notebook.cells[2].source = notebook.cells[2].source.replace(
    'WORK_DIR = Path("/kaggle/working/switch_v1_runtime")',
    'WORK_DIR = Path("/kaggle/working/switch_v2_runtime")',
).replace(
    'REPLAY_DIR = Path("/kaggle/working/switch_v1_replays")',
    'REPLAY_DIR = Path("/kaggle/working/switch_v2_replays")',
)

lines = notebook.cells[2].source.splitlines()
lines = [
    f"CANDIDATE_SOURCE = {v2_source!r}" if line.startswith("CANDIDATE_SOURCE = ") else line
    for line in lines
]
notebook.cells[2].source = "\n".join(lines)

notebook.cells[4].source = notebook.cells[4].source.replace(
    'candidate = load_module("conservative_switch_v1", WORK_DIR / "candidate_main.py")',
    'candidate = load_module("conservative_switch_v2", WORK_DIR / "candidate_main.py")',
)

notebook.cells[7].source = notebook.cells[7].source.replace(
    'matchup = f"switch_v1_vs_{opponent_name}"',
    'matchup = f"switch_v2_vs_{opponent_name}"',
)

notebook.cells[11].source = notebook.cells[11].source.replace(
    'required = ["switch_v1_vs_promoted", "switch_v1_vs_planner_v2", "switch_v1_vs_random", "switch_v1_vs_pressure"]',
    'required = ["switch_v2_vs_promoted", "switch_v2_vs_planner_v2", "switch_v2_vs_random", "switch_v2_vs_pressure"]',
).replace(
    '"PROMOTE: switch v1 clears all controlled gates"',
    '"PROMOTE: switch v2 clears all controlled gates"',
).replace(
    'summary_df.loc["switch_v1_vs_promoted"].ci_high',
    'summary_df.loc["switch_v2_vs_promoted"].ci_high',
).replace(
    '"REJECT: switch v1 is clearly worse than promoted"',
    '"REJECT: switch v2 is clearly worse than promoted"',
)

notebook.cells[15].source = notebook.cells[15].source.replace(
    '"candidate": "conservative_switch_v1"',
    '"candidate": "conservative_switch_v2"',
).replace(
    '"single_change": "retreat when active is unready and a benched attacker is ready"',
    '"single_change": "retreat when active has no Energy or low HP and a better bench exists"',
).replace(
    'Path("/kaggle/working/conservative_switch_experiment.json")',
    'Path("/kaggle/working/conservative_switch_v2_experiment.json")',
)

for index, cell in enumerate(notebook.cells):
    cell["id"] = f"cell-{index:02d}"
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

nbf.write(notebook, output_path)
print(f"Wrote {output_path.name}: {len(notebook.cells)} cells")
