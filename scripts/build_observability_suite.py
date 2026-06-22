"""Build and validate the complete first-player observability notebook suite."""

from pathlib import Path
import runpy

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NOTEBOOKS = ROOT / "notebooks"

runpy.run_path(str(SCRIPTS / "build_observability_notebook.py"))
runpy.run_path(str(SCRIPTS / "build_controlled_turn_order_notebook.py"))
runpy.run_path(str(SCRIPTS / "finalize_observability_notebooks.py"))
runpy.run_path(str(SCRIPTS / "validate_observability_notebooks.py"))

controlled_path = NOTEBOOKS / "07_controlled_turn_order_experiment.ipynb"
controlled = nbf.read(controlled_path, as_version=4)
controlled.cells[13].source = controlled.cells[13].source.replace(
    '"games_per_seat": GAMES_PER_SEAT',
    '"games_per_cell": GAMES_PER_CELL',
).replace(
    '"max_replays": MAX_REPLAYS',
    '"replays_per_cell": REPLAYS_PER_CELL',
).replace(
    'Path("/kaggle/working/first_player_observability.json")',
    'Path("/kaggle/working/controlled_turn_order_experiment.json")',
)
nbf.write(controlled, controlled_path)

for filename in (
    "06_first_player_and_replay_observability.ipynb",
    "07_controlled_turn_order_experiment.ipynb",
):
    path = NOTEBOOKS / filename
    notebook = nbf.read(path, as_version=4)
    for index, cell in enumerate(notebook.cells):
        cell["id"] = f"cell-{index:02d}"
        if cell.cell_type == "code":
            compile(cell.source, f"{filename}:cell-{index}", "exec")
            if cell.outputs:
                raise ValueError(f"{filename}: cell {index} contains outputs")
    nbf.write(notebook, path)
    print(f"SUITE PASS {filename}: {len(notebook.cells)} cells")
