"""Stateless attack-planner candidate for the Mega Abomasnow/Kyogre deck."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class


KYOGRE = 721
SNOVER = 722
MEGA_ABOMASNOW_EX = 723
WATER_ENERGY = 3

RIPTIDE = 1042
HAMMER_LANCHE = 1046

DECK_WATER_ENERGY = 35

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


@dataclass(frozen=True)
class AttackPlan:
    """A plan reconstructed from the current public observation."""

    attacker_area: object | None = None
    attacker_index: int = -1
    attacker_id: int = -1
    attack_id: int = -1
    expected_damage: float = 0.0
    target_hp: int = 0
    energy_needed: int = 0
    ready: bool = False
    immediate_ko: bool = False
    confident: bool = False


def read_deck_csv() -> list[int]:
    """Load and validate the candidate's frozen 60-card deck."""
    candidates = (
        Path(__file__).resolve().with_name("deck.csv"),
        Path("deck.csv"),
        Path("/kaggle_simulations/agent/deck.csv"),
    )
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        raise FileNotFoundError("Could not locate deck.csv.")
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
    """Resolve a visible card without assuming that every zone is populated."""
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


def _opponent_active_hp(obs: object, player: int) -> int:
    active = obs.current.players[1 - player].active
    if not active or active[0] is None:
        return 0
    return int(active[0].hp)


def _expected_hammer_lanche(obs: object, player: int) -> float:
    """Estimate six-card Energy hits using only the candidate's visible cards."""
    player_state = obs.current.players[player]
    visible_water = 0
    for card in player_state.hand:
        visible_water += int(card.id == WATER_ENERGY)
    for card in player_state.discard:
        visible_water += int(card.id == WATER_ENERGY)
    for pokemon in list(player_state.active) + list(player_state.bench):
        if pokemon is None:
            continue
        for energy in getattr(pokemon, "energyCards", []):
            visible_water += int(energy.id == WATER_ENERGY)
    remaining_water = max(0, DECK_WATER_ENERGY - visible_water)
    deck_count = max(1, int(player_state.deckCount))
    return 600.0 * min(1.0, remaining_water / deck_count)


def _attack_damage(card_id: int, discard_water: int, hammer_estimate: float) -> tuple[int, float]:
    if card_id == KYOGRE:
        return RIPTIDE, float(discard_water * 20)
    if card_id == MEGA_ABOMASNOW_EX:
        return HAMMER_LANCHE, hammer_estimate
    return -1, 0.0


def _build_plan(obs: object) -> AttackPlan:
    """Choose one attacker using readiness, expected damage, and switch cost."""
    state = obs.current
    player = int(state.yourIndex)
    player_state = state.players[player]
    _, _, discard = _visible_counts(obs, player)
    target_hp = _opponent_active_hp(obs, player)
    if target_hp <= 0:
        return AttackPlan()

    hammer_estimate = _expected_hammer_lanche(obs, player)
    candidates = []
    for area, cards in ((AreaType.ACTIVE, player_state.active), (AreaType.BENCH, player_state.bench)):
        for index, card in enumerate(cards):
            if card is None or int(card.id) not in (KYOGRE, MEGA_ABOMASNOW_EX):
                continue
            required = 1 if int(card.id) == KYOGRE else 2
            attached = _energy_count(card)
            needed = max(0, required - attached)
            attack_id, damage = _attack_damage(
                int(card.id), discard[WATER_ENERGY], hammer_estimate
            )
            if int(card.id) == KYOGRE and damage <= 0:
                continue
            ready = needed == 0
            immediate_ko = ready and damage >= target_hp
            score = damage
            score += 10_000 if immediate_ko else 0
            score += 600 if ready else -350 * needed
            score += 150 if area == AreaType.ACTIVE else -100
            score += 40 if int(card.id) == MEGA_ABOMASNOW_EX else 0
            candidates.append((score, area, index, card, attack_id, damage, needed, ready, immediate_ko))

    if not candidates:
        return AttackPlan()
    best = max(candidates, key=lambda item: (item[0], -item[2]))
    _, area, index, card, attack_id, damage, needed, ready, immediate_ko = best
    return AttackPlan(
        attacker_area=area,
        attacker_index=index,
        attacker_id=int(card.id),
        attack_id=attack_id,
        expected_damage=damage,
        target_hp=target_hp,
        energy_needed=needed,
        ready=ready,
        immediate_ko=immediate_ko,
        confident=True,
    )


def _attachment_score(obs: object, option: object, plan: AttackPlan) -> int:
    player = int(obs.current.yourIndex)
    pokemon = _get_card(obs, option.inPlayArea, option.inPlayIndex, player)
    if pokemon is None:
        return -10_000
    card_id = int(pokemon.id)
    energy = _energy_count(pokemon)
    required = 1 if card_id == KYOGRE else 2 if card_id in (SNOVER, MEGA_ABOMASNOW_EX) else 99
    score = 0
    if (
        plan.confident
        and plan.energy_needed > 0
        and option.inPlayArea == plan.attacker_area
        and option.inPlayIndex == plan.attacker_index
    ):
        score += 4_000
    if energy < required:
        score += 1_000 - 100 * energy
    else:
        score -= 2_000 + 200 * (energy - required)
    if card_id == MEGA_ABOMASNOW_EX:
        score += 250
    elif card_id == SNOVER:
        score += 150
    elif card_id == KYOGRE:
        score += 100
    if option.inPlayArea == AreaType.ACTIVE:
        score += 40
    return score


def _main_score(obs: object, option: object, plan: AttackPlan) -> int:
    player = int(obs.current.yourIndex)
    base = 8_000 - 1_000 * MAIN_ACTION_PRIORITY.get(option.type, 8)
    if option.type == OptionType.EVOLVE:
        pokemon = _get_card(obs, option.inPlayArea, option.inPlayIndex, player)
        if pokemon is not None and int(pokemon.id) == SNOVER:
            base += 2_000
            if option.inPlayArea == plan.attacker_area and option.inPlayIndex == plan.attacker_index:
                base += 1_000
    elif option.type == OptionType.ATTACH:
        base += _attachment_score(obs, option, plan)
    elif option.type == OptionType.RETREAT:
        if plan.confident and plan.attacker_area == AreaType.BENCH and plan.ready:
            base += 5_000
        else:
            base -= 5_000
    elif option.type == OptionType.ATTACK:
        if plan.confident and plan.attacker_area == AreaType.ACTIVE:
            if int(getattr(option, "attackId", -1)) == plan.attack_id:
                base += 2_000
                if plan.immediate_ko:
                    base += 8_000
        else:
            base -= 2_000
    elif option.type == OptionType.PLAY:
        card = _get_card(obs, AreaType.HAND, option.index, player)
        if card is not None and int(card.id) == 1227:
            field, hand, _ = _visible_counts(obs, player)
            if field[SNOVER] and hand[MEGA_ABOMASNOW_EX]:
                base -= 4_000
    return base


def _card_score(obs: object, option: object, plan: AttackPlan) -> int:
    player = int(obs.current.yourIndex)
    card = _get_card(obs, option.area, option.index, int(option.playerIndex))
    if card is None:
        return -10_000
    card_id = int(card.id)
    context = obs.select.context
    energy = _energy_count(card)
    field, hand, _ = _visible_counts(obs, player)

    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        score = energy * 100
        if int(option.playerIndex) == player:
            if plan.confident and option.area == AreaType.BENCH and option.index == plan.attacker_index:
                score += 10_000
            score += 500 if card_id == MEGA_ABOMASNOW_EX else 300 if card_id == KYOGRE else 0
        return score
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        going_first = int(obs.current.firstPlayer) == player
        if going_first:
            return 500 if card_id == SNOVER else 350 if card_id == KYOGRE else 0
        return 500 if card_id == KYOGRE else 400 if card_id == SNOVER else 0
    if context in (SelectContext.TO_HAND, SelectContext.TO_BENCH):
        if card_id == MEGA_ABOMASNOW_EX:
            return 1_000 if field[SNOVER] and not hand[MEGA_ABOMASNOW_EX] else 250
        if card_id == SNOVER:
            return 800 if not field[SNOVER] else 300
        if card_id == KYOGRE:
            return 600 if not field[KYOGRE] else 150
    if context == SelectContext.DISCARD:
        score = 1_000 if card_id == WATER_ENERGY else 0
        score += 500 if hand[card_id] >= 2 else 0
        if card_id == MEGA_ABOMASNOW_EX and field[SNOVER]:
            score -= 1_000
        return score
    if context == SelectContext.ATTACH_FROM:
        pseudo = type("AttachTarget", (), {
            "inPlayArea": option.area,
            "inPlayIndex": option.index,
        })()
        return _attachment_score(obs, pseudo, plan)
    return energy * 10


def _fallback_pairs(obs: object) -> list[tuple[int, object]]:
    indexed = list(enumerate(obs.select.option))
    if obs.select.context == SelectContext.MULLIGAN:
        no_choices = [pair for pair in indexed if pair[1].type == OptionType.NO]
        if no_choices:
            return no_choices
    if obs.select.type == SelectType.MAIN:
        return sorted(indexed, key=lambda pair: (
            MAIN_ACTION_PRIORITY.get(pair[1].type, 99), _stable_key(pair[1], pair[0])
        ))
    return sorted(indexed, key=lambda pair: _stable_key(pair[1], pair[0]))


def _choose_indices(obs: object) -> list[int]:
    select = obs.select
    if not select.option:
        return []
    fallback = _fallback_pairs(obs)
    plan = _build_plan(obs)

    scored = []
    for fallback_rank, (index, option) in enumerate(fallback):
        score = -fallback_rank
        if select.type == SelectType.MAIN and plan.confident:
            score += _main_score(obs, option, plan) * 100
        elif option.type == OptionType.YES and select.context == SelectContext.IS_FIRST:
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
        raise ValueError("Planner produced an invalid selection count.")
    if len(chosen) != len(set(chosen)):
        raise ValueError("Planner produced duplicate indices.")
    return chosen


def agent(obs_dict: dict) -> list[int]:
    """Return the frozen deck or a legal stateless planner action."""
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
