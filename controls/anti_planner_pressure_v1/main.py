"""Frozen anti-planner pressure control for local evaluation only.

This is not a submission candidate. It intentionally stresses candidates that
over-plan board development and delay taking attacks.
"""

from __future__ import annotations

from pathlib import Path

from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class


KYOGRE = 721
SNOVER = 722
MEGA_ABOMASNOW_EX = 723
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

MAIN_ACTION_PRIORITY = {
    OptionType.ATTACK: 0,
    OptionType.EVOLVE: 1,
    OptionType.ATTACH: 2,
    OptionType.ABILITY: 3,
    OptionType.PLAY: 4,
    OptionType.RETREAT: 5,
    OptionType.DISCARD: 6,
    OptionType.END: 7,
}


def read_deck_csv() -> list[int]:
    """Load the frozen 60-card deck from common local/Kaggle paths."""
    candidates = [
        Path("/kaggle_simulations/agent/deck.csv"),
        Path("deck.csv"),
    ]
    module_file = globals().get("__file__")
    if module_file:
        candidates.insert(0, Path(module_file).resolve().with_name("deck.csv"))
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        raise FileNotFoundError("Could not locate deck.csv beside the control or at runtime paths.")
    deck = [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards in {path}, found {len(deck)}.")
    return deck


def _stable_key(option: object, index: int) -> tuple[int, ...]:
    fields = (
        "number", "playerIndex", "area", "index", "inPlayArea",
        "inPlayIndex", "attackId", "cardId", "serial",
    )
    values = []
    for field in fields:
        value = getattr(option, field, None)
        try:
            values.append(int(value) if value is not None else 1_000_000)
        except (TypeError, ValueError):
            values.append(1_000_000)
    return (*values, index)


def _get_card(obs: object, area: object, index: int, player: int):
    player_state = obs.current.players[player]
    zones = {
        AreaType.HAND: player_state.hand,
        AreaType.DISCARD: player_state.discard,
        AreaType.ACTIVE: player_state.active,
        AreaType.BENCH: player_state.bench,
        AreaType.PRIZE: player_state.prize,
        AreaType.LOOKING: obs.current.looking,
    }
    if area == AreaType.DECK:
        zone = getattr(obs.select, "deck", [])
    else:
        zone = zones.get(area, [])
    if index is None or not 0 <= int(index) < len(zone):
        return None
    return zone[int(index)]


def _discard_water_count(obs: object) -> int:
    player = int(obs.current.yourIndex)
    return sum(
        1
        for card in obs.current.players[player].discard
        if getattr(card, "id", None) == WATER_ENERGY
    )


def _attack_damage(obs: object, option: object) -> int:
    attack_id = int(getattr(option, "attackId", -1))
    if attack_id == RIPTIDE:
        return 20 * _discard_water_count(obs)
    if attack_id == HAMMER_LANCHE:
        # Unknown top-deck-dependent attack. Give it enough priority to attack
        # under pressure, but do not pretend it is always a knockout.
        return 120
    return int(FIXED_ATTACK_DAMAGE.get(attack_id, 0))


def _card_score(obs: object, option: object) -> int:
    player = int(obs.current.yourIndex)
    card = _get_card(obs, option.area, option.index, int(getattr(option, "playerIndex", player)))
    if card is None:
        return -10_000
    card_id = int(getattr(card, "id", -1))
    context = obs.select.context
    energy_count = len(getattr(card, "energies", []))

    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        going_first = int(getattr(obs.current, "firstPlayer", -1)) == player
        if going_first:
            return 900 if card_id == SNOVER else 750 if card_id == KYOGRE else 0
        return 950 if card_id == KYOGRE else 700 if card_id == SNOVER else 0
    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        score = energy_count * 200
        score += 800 if card_id == MEGA_ABOMASNOW_EX else 650 if card_id == KYOGRE else 200 if card_id == SNOVER else 0
        return score
    if context in (SelectContext.TO_HAND, SelectContext.TO_BENCH):
        if card_id == KYOGRE:
            return 800
        if card_id == SNOVER:
            return 700
        if card_id == MEGA_ABOMASNOW_EX:
            return 650
        if card_id == WATER_ENERGY:
            return 100
    if context == SelectContext.DISCARD:
        return 900 if card_id == WATER_ENERGY else 100
    if context == SelectContext.ATTACH_FROM:
        if card_id == KYOGRE:
            return 800 if energy_count < 1 else -100
        if card_id in (SNOVER, MEGA_ABOMASNOW_EX):
            return 700 if energy_count < 2 else -100
    return energy_count * 10


def _choose_indices(obs: object) -> list[int]:
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
    elif context == SelectContext.IS_FIRST:
        # Prefer going second to enable immediate pressure.
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            indexed = no_choices
    elif getattr(select, "type", None) == SelectType.MAIN:
        indexed.sort(
            key=lambda pair: (
                MAIN_ACTION_PRIORITY.get(pair[1].type, 99),
                -_attack_damage(obs, pair[1]) if pair[1].type == OptionType.ATTACK else 0,
                _stable_key(pair[1], pair[0]),
            )
        )
    elif all(option.type == OptionType.CARD for option in options):
        indexed.sort(key=lambda pair: (-_card_score(obs, pair[1]), _stable_key(pair[1], pair[0])))
    else:
        indexed.sort(key=lambda pair: _stable_key(pair[1], pair[0]))

    required = max(0, int(select.minCount))
    requested = required if required > 0 else min(1, int(select.maxCount))
    count = min(requested, int(select.maxCount), len(indexed))
    chosen = [index for index, _ in indexed[:count]]

    if not (select.minCount <= len(chosen) <= select.maxCount):
        raise ValueError("Control produced an invalid selection count.")
    if len(chosen) != len(set(chosen)):
        raise ValueError("Control produced duplicate option indices.")
    return chosen


def agent(obs_dict: dict) -> list[int]:
    """Return the frozen deck or a deterministic pressure action."""
    if not isinstance(obs_dict, dict):
        return read_deck_csv()
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
