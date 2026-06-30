"""Repo-owned Iono archetype candidate v1.

This candidate uses the reconstructed public Iono decklist and a clean
deterministic policy focused on the core plan: establish Iono's Voltorb,
Bellibolt ex, and Kilowattrel; attach Lightning Energy broadly; and use
draw/search resources to keep the board developing.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class


IONO_VOLTORB = 265
IONO_TADBULB = 268
IONO_BELLIBOLT_EX = 269
IONO_WATTREL = 270
IONO_KILOWATTREL = 271
BUDDY_BUDDY_POFFIN = 1086
NIGHT_STRETCHER = 1097
MAX_ROD = 1110
ENERGY_RETRIEVAL = 1118
ULTRA_BALL = 1121
POKE_PAD = 1152
LILLIE_DETERMINATION = 1227
CANARI = 1233
LEVINCIA = 1254
LIGHTNING_ENERGY = 4


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
    zone = getattr(obs.select, "deck", []) if area == AreaType.DECK else zones.get(area, [])
    if index is None or not 0 <= int(index) < len(zone):
        return None
    return zone[int(index)]


def _energy_count(pokemon: object | None) -> int:
    return 0 if pokemon is None else len(getattr(pokemon, "energies", []))


def _field_counts(obs: object, player: int) -> Counter:
    player_state = obs.current.players[player]
    counts = Counter()
    for card in list(player_state.active) + list(player_state.bench):
        if card is not None:
            counts[int(card.id)] += 1
    return counts


def _hand_counts(obs: object, player: int) -> Counter:
    return Counter(int(card.id) for card in obs.current.players[player].hand)


def _discard_counts(obs: object, player: int) -> Counter:
    return Counter(int(card.id) for card in obs.current.players[player].discard)


def _opponent_active_hp(obs: object, player: int) -> int:
    active = obs.current.players[1 - player].active
    if not active or active[0] is None:
        return 0
    return int(active[0].hp)


def _total_field_energy(obs: object, player: int) -> int:
    total = 0
    player_state = obs.current.players[player]
    for pokemon in list(player_state.active) + list(player_state.bench):
        total += _energy_count(pokemon)
    return total


def _best_attacker_key(obs: object, pokemon: object | None, active: bool) -> tuple[int, int]:
    if pokemon is None:
        return (-10_000, 0)
    card_id = int(pokemon.id)
    energy = _energy_count(pokemon)
    total_energy = _total_field_energy(obs, int(obs.current.yourIndex))
    hp = getattr(pokemon, "hp", 0)
    score = -int(hp)
    if card_id == IONO_VOLTORB:
        score += 2_000 + 800 * min(2, energy) + 80 * total_energy
    elif card_id == IONO_BELLIBOLT_EX:
        score += 1_700 + 350 * min(4, energy)
    elif card_id == IONO_KILOWATTREL:
        score += 1_200 + 500 * min(1, energy)
    elif card_id == IONO_TADBULB:
        score += 300
    elif card_id == IONO_WATTREL:
        score += 250
    if active:
        score += 150
    return (score, energy)


def _attachment_score(obs: object, area: object, index: int) -> int:
    player = int(obs.current.yourIndex)
    pokemon = _get_card(obs, area, index, player)
    if pokemon is None:
        return -10_000
    card_id = int(pokemon.id)
    energy = _energy_count(pokemon)
    score = 30_000
    if card_id == IONO_VOLTORB:
        score += 6_000 if energy < 2 else 800
    elif card_id == IONO_BELLIBOLT_EX:
        score += 4_500 if energy < 4 else 500
    elif card_id == IONO_KILOWATTREL:
        score += 5_500 if energy < 1 else 600
    elif card_id == IONO_WATTREL:
        score += 3_200 if energy < 1 else 100
    elif card_id == IONO_TADBULB:
        score += 800
    else:
        score -= 5_000
    if area == AreaType.ACTIVE:
        score += 500
    return score - 120 * energy


def _field_need_score(card_id: int, field: Counter, hand: Counter) -> int:
    if card_id == IONO_VOLTORB:
        return 1_400 if field[IONO_VOLTORB] == 0 else 350 if field[IONO_VOLTORB] == 1 else -2_000
    if card_id == IONO_TADBULB:
        return 1_100 if field[IONO_TADBULB] + field[IONO_BELLIBOLT_EX] == 0 else 250
    if card_id == IONO_BELLIBOLT_EX:
        return 1_600 if field[IONO_TADBULB] and not hand[IONO_BELLIBOLT_EX] else 900
    if card_id == IONO_WATTREL:
        return 1_250 if field[IONO_WATTREL] + field[IONO_KILOWATTREL] == 0 else 250
    if card_id == IONO_KILOWATTREL:
        return 1_500 if field[IONO_WATTREL] and not hand[IONO_KILOWATTREL] else 800
    if card_id == LIGHTNING_ENERGY:
        return 650
    if card_id in (CANARI, LILLIE_DETERMINATION):
        return 500
    return 100


def _card_score(obs: object, option: object) -> int:
    player = int(obs.current.yourIndex)
    card = _get_card(obs, option.area, option.index, int(option.playerIndex))
    if card is None:
        return -10_000
    card_id = int(card.id)
    context = obs.select.context
    field = _field_counts(obs, player)
    hand = _hand_counts(obs, player)

    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE, SelectContext.SETUP_ACTIVE_POKEMON):
        if int(option.playerIndex) == player:
            return _best_attacker_key(obs, card, active=False)[0]
        return int(getattr(card, "hp", 0)) + 250 * _energy_count(card)
    if context in (SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH, SelectContext.TO_HAND):
        score = _field_need_score(card_id, field, hand)
        if context == SelectContext.TO_BENCH and card_id in (IONO_VOLTORB, IONO_TADBULB, IONO_WATTREL):
            score += 1_000
        if card_id != LIGHTNING_ENERGY and hand[card_id] >= 1:
            score -= 600
        return score
    if context == SelectContext.DISCARD:
        score = 0
        if card_id == LIGHTNING_ENERGY:
            score += 800
        if hand[card_id] >= 2:
            score += 600
        if card_id in (IONO_VOLTORB, IONO_BELLIBOLT_EX, IONO_KILOWATTREL):
            score -= 900
        return score
    if context == SelectContext.ATTACH_FROM:
        return _attachment_score(obs, option.area, option.index)
    return _energy_count(card) * 10


def _main_score(obs: object, option: object) -> int:
    player = int(obs.current.yourIndex)
    field = _field_counts(obs, player)
    discard = _discard_counts(obs, player)
    base = 8_000 - 1_000 * MAIN_ACTION_PRIORITY.get(option.type, 8)
    no_draw = int(obs.current.players[player].deckCount) <= 5

    if option.type == OptionType.EVOLVE:
        target = _get_card(obs, option.inPlayArea, option.inPlayIndex, player)
        evolve_card = _get_card(obs, AreaType.HAND, option.index, player)
        if target is not None and evolve_card is not None:
            if int(target.id) == IONO_TADBULB and int(evolve_card.id) == IONO_BELLIBOLT_EX:
                base += 4_000
            elif int(target.id) == IONO_WATTREL and int(evolve_card.id) == IONO_KILOWATTREL:
                base += 4_000
            else:
                base += 1_000
    elif option.type == OptionType.ABILITY:
        card = _get_card(obs, option.area, option.index, player)
        if card is not None and int(card.id) in (IONO_BELLIBOLT_EX, IONO_KILOWATTREL, LEVINCIA):
            base += 5_000
    elif option.type == OptionType.ATTACH:
        base += _attachment_score(obs, option.inPlayArea, option.inPlayIndex)
    elif option.type == OptionType.PLAY:
        card = _get_card(obs, AreaType.HAND, option.index, player)
        if card is not None:
            card_id = int(card.id)
            if card_id in (IONO_VOLTORB, IONO_TADBULB, IONO_WATTREL):
                base += 6_000 + _field_need_score(card_id, field, _hand_counts(obs, player))
            elif card_id in (CANARI, LILLIE_DETERMINATION):
                base += 3_000 if not no_draw else -6_000
            elif card_id == BUDDY_BUDDY_POFFIN:
                base += 4_000 if len(obs.current.players[player].bench) < 4 else -1_000
            elif card_id == ULTRA_BALL:
                base += 2_000 if not no_draw else -5_000
            elif card_id == POKE_PAD:
                base += 2_500 if not no_draw else -5_000
            elif card_id == LEVINCIA:
                base += 2_000 if discard[LIGHTNING_ENERGY] or field[IONO_KILOWATTREL] else 200
            elif card_id in (ENERGY_RETRIEVAL, NIGHT_STRETCHER):
                base += 2_200 if discard else -1_000
            elif card_id == MAX_ROD:
                base += 1_000 if discard[LIGHTNING_ENERGY] >= 2 else -2_000
    elif option.type == OptionType.RETREAT:
        active = obs.current.players[player].active[0] if obs.current.players[player].active else None
        active_key = _best_attacker_key(obs, active, active=True)
        best_bench = max(
            (_best_attacker_key(obs, card, active=False) for card in obs.current.players[player].bench),
            default=(-10_000, 0),
        )
        base += 4_000 if best_bench[0] > active_key[0] + 1_000 else -5_000
    elif option.type == OptionType.ATTACK:
        # Prefer larger attack IDs as a stable proxy; the Iono public policy does
        # the same and the simulator exposes only legal attacks here.
        base += int(getattr(option, "attackId", 0)) * 10
        total_energy = _total_field_energy(obs, player)
        hp = _opponent_active_hp(obs, player)
        if 20 + total_energy * 20 >= hp:
            base += 8_000
    return base


def _fallback_pairs(obs: object) -> list[tuple[int, object]]:
    indexed = list(enumerate(obs.select.option))
    if obs.select.context == SelectContext.MULLIGAN:
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            return no_choices
    if obs.select.type == SelectType.MAIN:
        return sorted(indexed, key=lambda pair: (MAIN_ACTION_PRIORITY.get(pair[1].type, 99), _stable_key(pair[1], pair[0])))
    return sorted(indexed, key=lambda pair: _stable_key(pair[1], pair[0]))


def _choose_indices(obs: object) -> list[int]:
    select = obs.select
    if not select.option:
        return []
    fallback = _fallback_pairs(obs)
    scored = []
    for fallback_rank, (index, option) in enumerate(fallback):
        score = -fallback_rank
        if select.type == SelectType.MAIN:
            score += _main_score(obs, option) * 100
        elif option.type == OptionType.CARD:
            score += _card_score(obs, option) * 100
        elif option.type == OptionType.YES:
            score += 10_000
        elif option.type == OptionType.NUMBER:
            score += int(option.number) * 100
        scored.append((score, _stable_key(option, index), index))
    scored.sort(key=lambda item: (-item[0], item[1]))
    required = max(0, int(select.minCount))
    requested = required if required > 0 else min(1, int(select.maxCount))
    count = min(requested, int(select.maxCount), len(scored))
    chosen = [index for _, _, index in scored[:count]]
    if not (select.minCount <= len(chosen) <= select.maxCount):
        raise ValueError("Policy produced an invalid selection count.")
    if len(chosen) != len(set(chosen)):
        raise ValueError("Policy produced duplicate option indices.")
    return chosen


def agent(obs_dict: dict) -> list[int]:
    if not isinstance(obs_dict, dict):
        return read_deck_csv()
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
