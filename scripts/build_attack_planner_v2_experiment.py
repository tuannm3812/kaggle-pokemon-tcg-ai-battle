"""Derive the controlled v2 planner experiment from the validated v1 notebook."""

from pathlib import Path
import runpy

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "build_abomasnow_planner_v2.py"))
runpy.run_path(str(ROOT / "scripts" / "build_attack_planner_experiment.py"))

source_path = ROOT / "notebooks" / "08_abomasnow_attack_planner_experiment.ipynb"
output_path = ROOT / "notebooks" / "09_abomasnow_planner_resource_guard_experiment.ipynb"
v1_source = (ROOT / "candidates" / "abomasnow_planner_v1" / "main.py").read_text()
v2_source = (ROOT / "candidates" / "abomasnow_planner_v2" / "main.py").read_text()
notebook = nbf.read(source_path, as_version=4)

notebook.cells[0].source = """# Abomasnow Planner Resource-Guard Experiment

**Purpose.** Test a focused correction to planner v1 after its primary result
was held at `25-15` against the promoted policy.

**Single intended change.** Exclude zero-damage Kyogre from confident attack
plans and grant the planned-attacker attachment bonus only while that attacker
still needs Energy.

The frozen deck, all other planner rules, controlled seat/turn-order design,
legality checks, telemetry, and replay policy remain unchanged."""

notebook.cells[1].source = """## 1. Configuration and frozen policy sources

Both v1 and v2 are embedded by the deterministic local builder. The experiment
includes direct v2-versus-v1 games for causal attribution, v2 versus promoted
for the production gate, and v2 versus random for regression protection."""

lines = notebook.cells[2].source.splitlines()
lines = [
    f"CANDIDATE_SOURCE = {v2_source!r}" if line.startswith("CANDIDATE_SOURCE = ") else line
    for line in lines
]
candidate_line = next(i for i, line in enumerate(lines) if line.startswith("CANDIDATE_SOURCE = "))
lines.insert(candidate_line + 1, f"V1_SOURCE = {v1_source!r}")
notebook.cells[2].source = "\n".join(lines).replace(
    'WORK_DIR = Path("/kaggle/working/attack_planner_runtime")',
    'WORK_DIR = Path("/kaggle/working/attack_planner_v2_runtime")',
)

notebook.cells[4].source = notebook.cells[4].source.replace(
    '(WORK_DIR / "candidate_main.py").write_text(CANDIDATE_SOURCE, encoding="utf-8")',
    '(WORK_DIR / "candidate_main.py").write_text(CANDIDATE_SOURCE, encoding="utf-8")\n'
    '(WORK_DIR / "planner_v1_main.py").write_text(V1_SOURCE, encoding="utf-8")',
).replace(
    'candidate = load_module("abomasnow_planner_v1", WORK_DIR / "candidate_main.py")',
    'candidate = load_module("abomasnow_planner_v2", WORK_DIR / "candidate_main.py")\n'
    'planner_v1 = load_module("abomasnow_planner_v1_frozen", WORK_DIR / "planner_v1_main.py")',
).replace(
    'assert deck == baseline.read_deck_csv() and len(deck) == 60',
    'assert deck == baseline.read_deck_csv() == planner_v1.read_deck_csv() and len(deck) == 60',
)

notebook.cells[8].source = """## 4. Balanced three-matchup tournament

Each matchup has ten games in every candidate-seat by forced-turn-order cell:

1. v2 versus v1 isolates the resource guards;
2. v2 versus promoted is the production gate;
3. v2 versus random checks for broad regression."""

notebook.cells[9].source = notebook.cells[9].source.replace(
    'matchups = [\n    ("planner_vs_promoted", baseline),\n    ("planner_vs_random", random_control),\n]',
    'matchups = [\n'
    '    ("planner_v2_vs_v1", planner_v1),\n'
    '    ("planner_v2_vs_promoted", baseline),\n'
    '    ("planner_v2_vs_random", random_control),\n'
    ']',
)

notebook.cells[10].source = """## 5. Outcome uncertainty and promotion gate

Promotion requires zero failures and intervals above parity in all three
matchups. A v2-versus-v1 interval crossing parity means the guards have not yet
shown a reproducible causal gain, even if point estimates look favorable."""

old_gate = '''primary = summary_df.loc["planner_vs_promoted"]
regression = summary_df.loc["planner_vs_random"]
if len(failures):
    decision = "REJECT: runtime failures"
elif primary.ci_low > 0.5 and regression.ci_low > 0.5:
    decision = "PROMOTE: planner clears primary and regression gates"
elif primary.ci_high < 0.5:
    decision = "REJECT: planner is worse than promoted control"
else:
    decision = "HOLD: primary interval overlaps parity"'''
new_gate = '''improvement = summary_df.loc["planner_v2_vs_v1"]
primary = summary_df.loc["planner_v2_vs_promoted"]
regression = summary_df.loc["planner_v2_vs_random"]
if len(failures):
    decision = "REJECT: runtime failures"
elif improvement.ci_low > 0.5 and primary.ci_low > 0.5 and regression.ci_low > 0.5:
    decision = "PROMOTE: resource guards clear causal, primary, and regression gates"
elif improvement.ci_high < 0.5 or primary.ci_high < 0.5:
    decision = "REJECT: v2 is clearly worse in a required matchup"
else:
    decision = "HOLD: at least one required interval overlaps parity"'''
if old_gate not in notebook.cells[11].source:
    raise RuntimeError("Could not locate the v1 promotion gate.")
notebook.cells[11].source = notebook.cells[11].source.replace(old_gate, new_gate)

notebook.cells[15].source = notebook.cells[15].source.replace(
    '"candidate": "abomasnow_planner_v1"',
    '"candidate": "abomasnow_planner_v2"',
).replace(
    '"single_change": "stateless attack-plan coordination on frozen deck"',
    '"single_change": "zero-damage and completed-attachment resource guards"',
).replace(
    'Path("/kaggle/working/abomasnow_planner_experiment.json")',
    'Path("/kaggle/working/abomasnow_planner_v2_experiment.json")',
)

notebook.cells[16].source = """## 8. Interpretation

Promote only if the resource guards beat frozen v1, clear the promoted-policy
gate, and preserve random-control strength. Otherwise keep production unchanged
and use attacker/action telemetry plus one loss replay per controlled cell to
choose the next single correction."""

for index, cell in enumerate(notebook.cells):
    cell["id"] = f"cell-{index:02d}"
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

nbf.write(notebook, output_path)
print(f"Wrote {output_path.name}: {len(notebook.cells)} cells")
