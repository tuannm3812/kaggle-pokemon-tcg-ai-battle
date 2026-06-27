"""Development-first deterministic agent for Pok?mon TCG AI Battle."""

from __future__ import annotations

from pathlib import Path

from cg.api import OptionType, SelectContext, SelectType, to_observation_class


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


WATER_ENERGY = 3
RIPTIDE = 1042
SWIRLING_WAVES = 1043
BEAT = 1044
ICY_SNOW = 1045
HAMMER_LANCHE = 1046
FROST_BARRIER = 1047
FIXED_ATTACK_DAMAGE = {
    SWIRLING_WAVES: 130,
    BEAT: 10,
    ICY_SNOW: 30,
    FROST_BARRIER: 200,
}


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


def _opponent_active_hp(obs: object) -> int:
    player = int(obs.current.yourIndex)
    active = obs.current.players[1 - player].active
    if not active or active[0] is None:
        return 0
    try:
        return int(getattr(active[0], "hp", 0))
    except (TypeError, ValueError):
        return 0


def _discard_water_count(obs: object) -> int:
    player = int(obs.current.yourIndex)
    discard = obs.current.players[player].discard
    total = 0
    for card in discard:
        try:
            total += int(getattr(card, "id", None) == WATER_ENERGY)
        except (TypeError, ValueError):
            pass
    return total


def _attack_damage_estimate(obs: object, attack_id: int) -> int:
    if attack_id == RIPTIDE:
        return 20 * _discard_water_count(obs)
    return int(FIXED_ATTACK_DAMAGE.get(attack_id, 0))


def _immediate_knockout_attack_index(obs: object) -> int | None:
    if getattr(obs.select, "type", None) != SelectType.MAIN:
        return None
    target_hp = _opponent_active_hp(obs)
    if target_hp <= 0:
        return None
    scored = []
    for index, option in enumerate(obs.select.option):
        if option.type != OptionType.ATTACK:
            continue
        attack_id = int(getattr(option, "attackId", -1))
        damage = _attack_damage_estimate(obs, attack_id)
        if damage >= target_hp:
            scored.append((-damage, _stable_key(option, index), index))
    if not scored:
        return None
    scored.sort()
    return scored[0][2]


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
    elif getattr(select, "type", None) == SelectType.MAIN:
        knockout_index = _immediate_knockout_attack_index(obs)
        if knockout_index is not None:
            return [knockout_index]
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
