"""Apply final generated-cell normalization and validate observability notebooks."""

from pathlib import Path

import nbformat as nbf


root = Path(__file__).resolve().parents[1] / "notebooks"
controlled_path = root / "07_controlled_turn_order_experiment.ipynb"
controlled = nbf.read(controlled_path, as_version=4)
controlled.cells[6].source = controlled.cells[6].source.replace(
    "                    if score == 0.0 and replay_counts[replay_key] < REPLAYS_PER_CELL:",
    "                if score == 0.0 and replay_counts[replay_key] < REPLAYS_PER_CELL:",
).replace(
    "                        replay_counts[replay_key] += 1",
    "                    replay_counts[replay_key] += 1",
)
nbf.write(controlled, controlled_path)

for filename in (
    "06_first_player_and_replay_observability.ipynb",
    "07_controlled_turn_order_experiment.ipynb",
):
    path = root / filename
    notebook = nbf.read(path, as_version=4)
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"{filename}:cell-{index}", "exec")
            if cell.outputs:
                raise ValueError(f"{filename}: cell {index} contains outputs")
    print(f"PASS {filename}: {len(notebook.cells)} cells")
