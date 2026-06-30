"""Repo-owned Mega Lucario archetype candidate.

This candidate is intentionally compact: it uses the reconstructed public
Lucario decklist but implements a clean deterministic policy in our own style.
The goal is to test whether moving from Abomasnow/Kyogre to a stronger
archetype improves local episode results before any promotion/submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cg.api import AreaType, OptionType, SelectContext, SelectType, to_observation_class


MAKUHITA = 673
HARIYAMA = 674
LUNATONE = 675
SOLROCK = 676
RIOLU = 677
MEGA_LUCARIO_EX = 678
SWITCH = 1123
BOSS_ORDERS = 1182
FIGHTING_ENERGY = 6

MEGA_LUCARIO_JAB = 982
MEGA_BRAVE = 983


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
    attacker_area: object | None = None
    attacker_index: int = -1
    attacker_id: int = -1
    attack_id: int = -1
    damage: int = 0
    target_hp: int = 0
    energy_needed: int = 0
    ready: bool = False
    immediate_ko: bool = False
    confident: bool = False


def read_deck_csv() -> list[int]:
    """Load and validate this candidate's frozen 60-card deck."""
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
    zone = getattr(obs.select, "deck", []) if area == AreaType.DECK else zones.get(area, [])
    if index is None or not 0 <= int(index) < len(zone):
        return None
    return zone[int(index)]


def _energy_count(pokemon: object | None) -> int:
    return 0 if pokemon is None else len(getattr(pokemon, "energies", []))


def _opponent_active_hp(obs: object, player: int) -> int:
    active = obs.current.players[1 - player].active
    if not active or active[0] is None:
        return 0
    return int(active[0].hp)


def _has_lunatone(obs: object, player: int) -> bool:
    player_state = obs.current.players[player]
    return any(card is not None and int(card.id) == LUNATONE for card in player_state.active + player_state.bench)


def _attack_options(card_id: int, has_lunatone: bool) -> list[tuple[int, int, int]]:
    """Return ``(attack_id, required_energy, damage)`` candidates."""
    if card_id == MEGA_LUCARIO_EX:
        return [(MEGA_LUCARIO_JAB, 1, 130), (MEGA_BRAVE, 2, 270)]
    if card_id in (MAKUHITA, HARIYAMA):
        return [(-1, 3, 210)]
    if card_id == SOLROCK and has_lunatone:
        return [(-1, 1, 70)]
    return []


def _build_plan(obs: object) -> AttackPlan:
    state = obs.current
    player = int(state.yourIndex)
    player_state = state.players[player]
    target_hp = _opponent_active_hp(obs, player)
    has_lunatone = _has_lunatone(obs, player)
    if target_hp <= 0:
        return AttackPlan()

    candidates = []
    for area, cards in ((AreaType.ACTIVE, player_state.active), (AreaType.BENCH, player_state.bench)):
        for index, card in enumerate(cards):
            if card is None:
                continue
            card_id = int(card.id)
            for attack_id, required, damage in _attack_options(card_id, has_lunatone):
                attached = _energy_count(card)
                needed = max(0, required - attached)
                ready = needed == 0
                immediate_ko = ready and damage >= target_hp
                score = damage
                score += 10_000 if immediate_ko else 0
                score += 700 if ready else -450 * needed
                score += 180 if area == AreaType.ACTIVE else -120
                score += 450 if card_id == MEGA_LUCARIO_EX else 120 if card_id == HARIYAMA else 0
                candidates.append((score, area, index, card_id, attack_id, damage, needed, ready, immediate_ko))

    if not candidates:
        return AttackPlan()
    _, area, index, card_id, attack_id, damage, needed, ready, immediate_ko = max(
        candidates, key=lambda item: (item[0], -item[2])
    )
    return AttackPlan(
        attacker_area=area,
        attacker_index=index,
        attacker_id=card_id,
        attack_id=attack_id,
        damage=damage,
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
    attached = _energy_count(pokemon)
    required = 2 if card_id in (RIOLU, MEGA_LUCARIO_EX) else 3 if card_id in (MAKUHITA, HARIYAMA) else 1 if card_id == SOLROCK else 99
    score = 0
    if (
        plan.confident
        and plan.energy_needed > 0
        and option.inPlayArea == plan.attacker_area
        and option.inPlayIndex == plan.attacker_index
    ):
        score += 4_000
    if attached < required:
        score += 1_200 - 140 * attached
    else:
        score -= 2_500 + 250 * (attached - required)
    if card_id == MEGA_LUCARIO_EX:
        score += 500
    elif card_id == RIOLU:
        score += 350
    elif card_id == HARIYAMA:
        score += 250
    elif card_id == MAKUHITA:
        score += 180
    elif card_id == SOLROCK:
        score += 80
    if option.inPlayArea == AreaType.ACTIVE:
        score += 40
    return score


def _main_score(obs: object, option: object, plan: AttackPlan) -> int:
    player = int(obs.current.yourIndex)
    base = 8_000 - 1_000 * MAIN_ACTION_PRIORITY.get(option.type, 8)
    if option.type == OptionType.EVOLVE:
        target = _get_card(obs, option.inPlayArea, option.inPlayIndex, player)
        evolve_card = _get_card(obs, AreaType.HAND, option.index, player)
        if target is not None and evolve_card is not None:
            if int(target.id) == RIOLU and int(evolve_card.id) == MEGA_LUCARIO_EX:
                base += 3_000
            elif int(target.id) == MAKUHITA and int(evolve_card.id) == HARIYAMA:
                base += 1_500
    elif option.type == OptionType.ATTACH:
        base += _attachment_score(obs, option, plan)
    elif option.type == OptionType.ATTACK:
        if plan.confident and plan.attacker_area == AreaType.ACTIVE:
            attack_id = int(getattr(option, "attackId", -1))
            if plan.attack_id == -1 or attack_id == plan.attack_id:
                base += 2_000 + (8_000 if plan.immediate_ko else 0)
        else:
            base -= 2_000
    elif option.type == OptionType.RETREAT:
        if plan.confident and plan.attacker_area == AreaType.BENCH and plan.ready:
            base += 5_000
        else:
            base -= 5_000
    elif option.type == OptionType.PLAY:
        card = _get_card(obs, AreaType.HAND, option.index, player)
        if card is not None:
            card_id = int(card.id)
            if card_id in (SWITCH, BOSS_ORDERS) and plan.immediate_ko:
                base += 2_500
            elif card_id == FIGHTING_ENERGY:
                base -= 2_000
    return base


def _card_score(obs: object, option: object, plan: AttackPlan) -> int:
    player = int(obs.current.yourIndex)
    card = _get_card(obs, option.area, option.index, int(option.playerIndex))
    if card is None:
        return -10_000
    card_id = int(card.id)
    context = obs.select.context
    energy = _energy_count(card)

    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        score = energy * 100
        if int(option.playerIndex) == player:
            if plan.confident and option.area == AreaType.BENCH and option.index == plan.attacker_index:
                score += 10_000
            score += 500 if card_id == MEGA_LUCARIO_EX else 250 if card_id == HARIYAMA else 100 if card_id == SOLROCK else 0
        return score
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        if card_id == RIOLU:
            return 700
        if card_id == SOLROCK:
            return 500
        if card_id == MAKUHITA:
            return 350
        if card_id == LUNATONE:
            return 250
    if context in (SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH):
        if card_id == RIOLU:
            return 700
        if card_id == SOLROCK:
            return 550
        if card_id == LUNATONE:
            return 500
        if card_id == MAKUHITA:
            return 350
    if context == SelectContext.TO_HAND:
        if card_id == MEGA_LUCARIO_EX:
            return 1_100
        if card_id == RIOLU:
            return 950
        if card_id == FIGHTING_ENERGY:
            return 650
        if card_id in (HARIYAMA, MAKUHITA, SOLROCK, LUNATONE):
            return 450
    if context == SelectContext.DISCARD:
        score = 500 if card_id == FIGHTING_ENERGY else 0
        score -= 1_000 if card_id in (MEGA_LUCARIO_EX, RIOLU) else 0
        return score
    if context == SelectContext.ATTACH_FROM:
        pseudo = type("AttachTarget", (), {"inPlayArea": option.area, "inPlayIndex": option.index})()
        return _attachment_score(obs, pseudo, plan)
    return energy * 10


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
    plan = _build_plan(obs)
    scored = []
    for fallback_rank, (index, option) in enumerate(fallback):
        score = -fallback_rank
        if select.type == SelectType.MAIN:
            score += _main_score(obs, option, plan) * 100
        elif option.type == OptionType.CARD:
            score += _card_score(obs, option, plan) * 100
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
    """Return the frozen deck or a legal deterministic action."""
    if not isinstance(obs_dict, dict):
        return read_deck_csv()
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
