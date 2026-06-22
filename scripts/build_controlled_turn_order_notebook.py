"""Derive the controlled seat-by-turn-order Kaggle experiment notebook."""

from copy import deepcopy
from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks" / "06_first_player_and_replay_observability.ipynb"
OUTPUT = ROOT / "notebooks" / "07_controlled_turn_order_experiment.ipynb"

notebook = nbf.read(SOURCE, as_version=4)
cells = deepcopy(notebook.cells)

cells[0].source = """# Controlled Turn-Order Experiment

**Purpose.** Estimate turn-order effects without confounding them with player
index or the policy's own first-player choice.

**Decision question.** Holding the promoted policy, deck, and opponent fixed,
does the candidate perform differently when forced to go first versus second?

This notebook changes only the `IS_FIRST` selection made by player 0. All later
decisions are delegated to the frozen promoted or official random policy."""

cells[1].source = """## 1. Balanced factorial design

The observational run showed that the promoted policy chose first whenever it
occupied player 0. Seat balance alone therefore could not identify turn-order
effects. This follow-up crosses candidate seat `{0, 1}` with forced candidate
turn order `{first, second}`, producing four equal cells.

Only one loss replay per cell is retained, preventing early games from using the
entire replay quota."""

cells[2].source = cells[2].source.replace(
    "GAMES_PER_SEAT = 20", "GAMES_PER_CELL = 10"
).replace(
    "MAX_REPLAYS = 4", "REPLAYS_PER_CELL = 1"
).replace(
    'WORK_DIR = Path("/kaggle/working/first_player_runtime")',
    'WORK_DIR = Path("/kaggle/working/controlled_turn_order_runtime")',
)

cells[5].source = """## 3. Controlled first-player choice and runner

`ForcedFirstChoice` intercepts only `SelectContext.IS_FIRST`. The wrapper
selects `YES` or `NO` for player 0, then delegates every subsequent observation
to the frozen base policy. Contract validation, actual `state.firstPlayer`
recording, named telemetry, and replay serialization remain unchanged."""

cells[6].source = cells[6].source.replace(
    "replay_paths = []\n",
    '''replay_paths = []
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
''',
).replace(
    "if score < 1.0 and len(replay_paths) < MAX_REPLAYS:",
    '''replay_key = (candidate_player, first_player == candidate_player)
                    if score == 0.0 and replay_counts[replay_key] < REPLAYS_PER_CELL:''',
).replace(
    "replay_paths.append(str(replay_path))",
    "replay_paths.append(str(replay_path))\n                        replay_counts[replay_key] += 1",
)

cells[7].source = """## 4. Controlled 2x2 tournament

For a candidate in seat 0, forcing player 0 to choose `YES` makes the candidate
go first. For a candidate in seat 1, player 0 is the control, so its choice is
reversed. The post-run assertion verifies the simulator realized every intended
turn order."""

cells[8].source = '''results = []
game_id = 70_000
for candidate_player in (0, 1):
    for candidate_should_go_first in (False, True):
        for repetition in range(GAMES_PER_CELL):
            player_zero_goes_first = (
                candidate_should_go_first
                if candidate_player == 0
                else not candidate_should_go_first
            )
            if candidate_player == 0:
                policies = {
                    0: ForcedFirstChoice(candidate, player_zero_goes_first),
                    1: control,
                }
            else:
                policies = {
                    0: ForcedFirstChoice(control, player_zero_goes_first),
                    1: candidate,
                }
            result = play_game(policies, game_id, candidate_player)
            result["forced_candidate_went_first"] = candidate_should_go_first
            results.append(result)
            game_id += 1

results_df = pd.DataFrame(results)
failures = results_df[results_df.status != "finished"]
finished = results_df[results_df.status == "finished"].copy()
assert failures.empty, failures.to_dict("records")
assert finished.first_player.isin([0, 1]).all(), "Missing first-player attribution"
assert (finished.candidate_went_first == finished.forced_candidate_went_first).all()

cell_counts = finished.groupby(
    ["candidate_player", "candidate_went_first"]
).size()
assert (cell_counts == GAMES_PER_CELL).all(), cell_counts.to_dict()
display(finished.drop(columns=["contexts", "candidate_actions"], errors="ignore"))
print(f"Completed {len(finished)} games; saved {len(replay_paths)} replays.")'''

cells[9].source = """## 5. Outcome uncertainty and controlled attribution

The overall interval is a regression screen. The primary comparison is the
candidate's score rate when forced first versus forced second. The joint table
checks that the direction is not merely a seat artifact. With ten games per
cell, treat differences as screening evidence rather than a final estimate."""

cells[13].source = cells[13].source.replace(
    '"experiment": "first-player attribution and bounded replay capture"',
    '"experiment": "controlled candidate seat by turn-order factorial"',
).replace(
    '"base_seed": BASE_SEED, "games_per_seat": GAMES_PER_SEAT,\n            "max_replays": MAX_REPLAYS, "simulator_seed_exposed": False,',
    '"base_seed": BASE_SEED, "games_per_cell": GAMES_PER_CELL,\n            "replays_per_cell": REPLAYS_PER_CELL, "simulator_seed_exposed": False,',
).replace(
    'Path("/kaggle/working/first_player_observability.json")',
    'Path("/kaggle/working/controlled_turn_order_experiment.json")',
)

cells[14].source = """## 7. Interpretation gate

This experiment still does not promote a policy. If a turn-order difference is
consistent across both seats, make setup and attack planning explicitly aware
of `state.firstPlayer`. If the difference is weak or reverses by seat, prioritize
the deck-specific attack planner and stronger opponents instead."""

for index, cell in enumerate(cells):
    cell["id"] = f"cell-{index:02d}"
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

output_notebook = nbf.v4.new_notebook(cells=cells, metadata=notebook.metadata)
nbf.write(output_notebook, OUTPUT)
print(f"Wrote {OUTPUT.name}: {len(cells)} cells")
