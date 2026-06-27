"""Development-first deterministic agent for Pok?mon TCG AI Battle."""

from __future__ import annotations

from pathlib import Path

from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class


MAIN_ACTION_PRIORITY = {
    OptionType.EVOLVE: 0,
    OptionType.ABILITY: 1,
    OptionType.ATTACH: 2,
    OptionType.PLAY: 3,
    OptionType.ATTACK: 4,
    OptionType.RETREAT: 5,
    OptionType.DISCARD: 6,
    OptionType.END: 7,
}


KYOGRE = 721
SNOVER = 722


def _get_card(obs: object, area: object, index: int, player: int):
    state = obs.current
    player_state = state.players[player]
    zones = {AreaType.HAND: player_state.hand, AreaType.ACTIVE: player_state.active, AreaType.BENCH: player_state.bench}
    zone = zones.get(area, [])
    if index is None or not 0 <= int(index) < len(zone):
        return None
    return zone[int(index)]


def _setup_active_score(obs: object, option: object) -> int:
    player = int(obs.current.yourIndex)
    card = _get_card(obs, option.area, option.index, int(getattr(option, "playerIndex", player)))
    if card is None:
        return -10_000
    card_id = int(getattr(card, "id", -1))
    going_first = int(getattr(obs.current, "firstPlayer", -1)) == player
    if going_first:
        return 900 if card_id == SNOVER else 650 if card_id == KYOGRE else 0
    return 900 if card_id == KYOGRE else 750 if card_id == SNOVER else 0


def read_deck_csv() -> list[int]:
    """Load the 60 card IDs from the submission directory."""
    candidates = [
        Path("/kaggle_simulations/agent/deck.csv"),
        Path("deck.csv"),
    ]
    module_file = globals().get("__file__")
    if module_file:
        candidates.insert(0, Path(module_file).resolve().with_name("deck.csv"))
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        raise FileNotFoundError("Could not locate deck.csv beside the agent or at runtime paths.")
    deck = [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards in {path}, found {len(deck)}.")
    return deck


def _stable_key(option: object, index: int) -> tuple[int, ...]:
    """Build a stable tie-break key without assuming all SDK fields exist."""
    fields = (
        "number",
        "playerIndex",
        "area",
        "index",
        "inPlayArea",
        "inPlayIndex",
        "attackId",
        "cardId",
        "serial",
    )
    values = []
    for field in fields:
        value = getattr(option, field, None)
        try:
            values.append(int(value) if value is not None else 1_000_000)
        except (TypeError, ValueError):
            values.append(1_000_000)
    return (*values, index)


def _choose_indices(obs: object) -> list[int]:
    """Return deterministic legal indices for the current selection."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    indexed = list(enumerate(options))
    context = getattr(select, "context", None)

    if context == SelectContext.MULLIGAN:
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            indexed = no_choices
    elif context == SelectContext.SETUP_ACTIVE_POKEMON and all(option.type == OptionType.CARD for option in options):
        indexed.sort(
            key=lambda pair: (
                -_setup_active_score(obs, pair[1]),
                _stable_key(pair[1], pair[0]),
            )
        )
    elif getattr(select, "type", None) == SelectType.MAIN:
        indexed.sort(
            key=lambda pair: (
                MAIN_ACTION_PRIORITY.get(pair[1].type, 99),
                _stable_key(pair[1], pair[0]),
            )
        )
    else:
        indexed.sort(key=lambda pair: _stable_key(pair[1], pair[0]))

    required = max(0, int(select.minCount))
    requested = required if required > 0 else min(1, int(select.maxCount))
    count = min(requested, int(select.maxCount), len(indexed))
    chosen = [index for index, _ in indexed[:count]]

    if not (select.minCount <= len(chosen) <= select.maxCount):
        raise ValueError("Policy produced an invalid selection count.")
    if len(chosen) != len(set(chosen)):
        raise ValueError("Policy produced duplicate option indices.")
    return chosen


def agent(obs_dict: dict) -> list[int]:
    """Return a legal deck or deterministic action for an observation."""
    if not isinstance(obs_dict, dict):
        return read_deck_csv()
    try:
        obs = to_observation_class(obs_dict)
    except (AttributeError, KeyError, TypeError, ValueError):
        return read_deck_csv()
    if obs.select is None:
        return read_deck_csv()
    try:
        return _choose_indices(obs)
    except (AttributeError, KeyError, TypeError, ValueError):
        options = list(obs.select.option)
        required = max(0, int(obs.select.minCount))
        requested = max(required, min(int(obs.select.maxCount), len(options)))
        count = min(requested, len(options))
        return list(range(count))
