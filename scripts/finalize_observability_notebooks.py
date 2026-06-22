"""Normalize generated observability notebooks after their base builders run."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def normalize(path: Path) -> None:
    notebook = nbf.read(path, as_version=4)
    for index, cell in enumerate(notebook.cells):
        cell["id"] = f"cell-{index:02d}"
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    nbf.write(notebook, path)


controlled_path = NOTEBOOKS / "07_controlled_turn_order_experiment.ipynb"
controlled = nbf.read(controlled_path, as_version=4)
runner = controlled.cells[6].source
start = runner.index("replay_paths = []")
end = runner.index("\ndef play_game", start)
wrapper = '''replay_paths = []
replay_counts = Counter()

class ForcedFirstChoice:
    def __init__(self, base_policy, player_zero_goes_first: bool):
        self.base_policy = base_policy
        self.player_zero_goes_first = player_zero_goes_first

    def agent(self, obs_dict: dict) -> list[int]:
        obs = to_observation_class(obs_dict)
        if obs.select is not None and obs.select.context == SelectContext.IS_FIRST:
            desired = OptionType.YES if self.player_zero_goes_first else OptionType.NO
            matches = [
                index for index, option in enumerate(obs.select.option)
                if option.type == desired
            ]
            if not matches:
                raise ValueError(f"IS_FIRST does not expose {desired.name}")
            return [matches[0]]
        return self.base_policy.agent(obs_dict)
'''
controlled.cells[6].source = runner[:start] + wrapper + runner[end:]
nbf.write(controlled, controlled_path)

for filename in (
    "06_first_player_and_replay_observability.ipynb",
    "07_controlled_turn_order_experiment.ipynb",
):
    normalize(NOTEBOOKS / filename)
    print(f"Normalized {filename}")
