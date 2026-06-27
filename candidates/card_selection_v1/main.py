"""Card-selection-only candidate for Pokemon TCG AI Battle.

This candidate keeps the promoted agent's main-phase action order unchanged and
only applies planner-style scoring to non-main CARD selections such as setup,
search, switch, discard, and attach-from prompts.
"""

from __future__ import annotations

from collections import Counter
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
    OptionType.EVOLVE: 0,
    OptionType.ABILITY: 1,
    OptionType.ATTACH: 2,
    OptionType.PLAY: 3,
    OptionType.ATTACK: 4,
    OptionType.RETREAT: 5,
    OptionType.DISCARD: 6,
    OptionType.END: 7,
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


def _get_card(obs: object, area: object, index: int, player: int):
    state = obs.current
    player_state = state.players[player]
    zones = {
        AreaType.HAND: player_state.hand,
        AreaType.DISCARD: player_state.discard,
        AreaType.ACTIVE: player_state.active,
        AreaType.BENCH: player_state.bench,
        AreaType.PRIZE: player_state.prize,
        AreaType.STADIUM: state.stadium,
        AreaType.LOOKING: state.looking,
    }
    if area == AreaType.DECK:
        zone = getattr(obs.select, "deck", [])
    else:
        zone = zones.get(area, [])
    if index is None or not 0 <= int(index) < len(zone):
        return None
    return zone[int(index)]


def _energy_count(pokemon: object | None) -> int:
    if pokemon is None:
        return 0
    return len(getattr(pokemon, "energies", []))


def _visible_counts(obs: object, player: int) -> tuple[Counter, Counter, Counter]:
    player_state = obs.current.players[player]
    field = Counter()
    hand = Counter()
    discard = Counter()
    for card in list(player_state.active) + list(player_state.bench):
        if card is not None:
            field[int(card.id)] += 1
    for card in player_state.hand:
        hand[int(card.id)] += 1
    for card in player_state.discard:
        discard[int(card.id)] += 1
    return field, hand, discard


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
    return sum(
        1
        for card in obs.current.players[player].discard
        if getattr(card, "id", None) == WATER_ENERGY
    )


def _attack_damage_estimate(obs: object, attack_id: int) -> int:
    if attack_id == RIPTIDE:
        return 20 * _discard_water_count(obs)
    if attack_id == HAMMER_LANCHE:
        return 0
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


def _best_ready_bench_attacker(obs: object, player: int) -> int:
    player_state = obs.current.players[player]
    best = (-1, -1)
    for index, card in enumerate(player_state.bench):
        if card is None:
            continue
        card_id = int(card.id)
        energy = _energy_count(card)
        if card_id == MEGA_ABOMASNOW_EX and energy >= 2:
            best = max(best, (30 + energy, index))
        elif card_id == KYOGRE and energy >= 1:
            best = max(best, (20 + energy, index))
    return best[1]


def _card_score(obs: object, option: object) -> int:
    player = int(obs.current.yourIndex)
    option_player = int(getattr(option, "playerIndex", player))
    card = _get_card(obs, option.area, option.index, option_player)
    if card is None:
        return -10_000

    card_id = int(card.id)
    context = obs.select.context
    energy = _energy_count(card)
    field, hand, _ = _visible_counts(obs, player)

    if context in (
        SelectContext.SWITCH,
        SelectContext.TO_ACTIVE,
        SelectContext.SETUP_ACTIVE_POKEMON,
    ):
        score = energy * 100
        if option_player == player:
            ready_bench = _best_ready_bench_attacker(obs, player)
            if option.area == AreaType.BENCH and option.index == ready_bench:
                score += 3_000
            if context == SelectContext.SETUP_ACTIVE_POKEMON:
                going_first = int(getattr(obs.current, "firstPlayer", -1)) == player
                if going_first:
                    score += 800 if card_id == SNOVER else 500 if card_id == KYOGRE else 0
                else:
                    score += 800 if card_id == KYOGRE else 650 if card_id == SNOVER else 0
            else:
                score += 700 if card_id == MEGA_ABOMASNOW_EX else 500 if card_id == KYOGRE else 200 if card_id == SNOVER else 0
        return score

    if context in (SelectContext.TO_HAND, SelectContext.TO_BENCH):
        if card_id == MEGA_ABOMASNOW_EX:
            return 1_200 if field[SNOVER] and not hand[MEGA_ABOMASNOW_EX] else 250
        if card_id == SNOVER:
            return 900 if not field[SNOVER] else 350
        if card_id == KYOGRE:
            return 700 if not field[KYOGRE] else 150
        if card_id == WATER_ENERGY:
            return 50

    if context == SelectContext.DISCARD:
        score = 800 if card_id == WATER_ENERGY else 0
        score += 600 if hand[card_id] >= 2 else 0
        if card_id == MEGA_ABOMASNOW_EX and field[SNOVER]:
            score -= 1_000
        if card_id == SNOVER and not field[SNOVER]:
            score -= 1_000
        return score

    if context == SelectContext.ATTACH_FROM:
        if card_id == MEGA_ABOMASNOW_EX:
            return 900 if energy < 2 else -500
        if card_id == SNOVER:
            return 700 if energy < 2 else -300
        if card_id == KYOGRE:
            return 600 if energy < 1 else -300

    return energy * 10


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
    elif getattr(select, "type", None) == SelectType.MAIN:
        indexed.sort(
            key=lambda pair: (
                MAIN_ACTION_PRIORITY.get(pair[1].type, 99),
                _stable_key(pair[1], pair[0]),
            )
        )
    elif all(option.type == OptionType.CARD for option in options):
        indexed.sort(
            key=lambda pair: (
                -_card_score(obs, pair[1]),
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
