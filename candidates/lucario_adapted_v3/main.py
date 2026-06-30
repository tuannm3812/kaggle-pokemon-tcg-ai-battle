"""Repo-owned Mega Lucario archetype candidate v3.

This candidate uses the reconstructed public Lucario decklist but implements a
clean deterministic policy in our own style. V3 keeps v2 target planning but
prioritizes the Riolu -> Mega Lucario line more aggressively and demotes Solrock
from attacker to setup/support.
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
PREMIUM_POWER_PRO = 1141
FIGHTING_GONG = 1142
POKE_PAD = 1152
HERO_CAPE = 1159
BOSS_ORDERS = 1182
CARMINE = 1192
LILLIE_DETERMINATION = 1227
GRAVITY_MOUNTAIN = 1252
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
    target_area: object | None = None
    target_index: int = -1
    target_hp: int = 0
    energy_needed: int = 0
    ready: bool = False
    immediate_ko: bool = False
    needs_switch: bool = False
    needs_boss: bool = False
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
        return [(-1, 1, 70)]  # fallback only; scoring keeps this below Lucario lines
    return []


def _can_play_card(obs: object, player: int, card_id: int) -> bool:
    if obs.select is None or obs.select.context != SelectContext.MAIN:
        return False
    for option in obs.select.option:
        if option.type != OptionType.PLAY:
            continue
        card = _get_card(obs, AreaType.HAND, option.index, player)
        if card is not None and int(card.id) == card_id:
            return True
    return False


def _can_switch_active(obs: object, player: int) -> bool:
    if obs.select is None or obs.select.context != SelectContext.MAIN:
        return False
    for option in obs.select.option:
        if option.type == OptionType.RETREAT:
            return True
        if option.type == OptionType.PLAY:
            card = _get_card(obs, AreaType.HAND, option.index, player)
            if card is not None and int(card.id) == SWITCH:
                return True
    return False


def _target_score(pokemon: object | None) -> int:
    if pokemon is None:
        return -1
    hp = int(getattr(pokemon, "hp", 0))
    energy = _energy_count(pokemon)
    tools = len(getattr(pokemon, "tools", []))
    card_id = int(getattr(pokemon, "id", 0))
    score = hp + 140 * energy + 80 * tools
    if card_id in (MEGA_LUCARIO_EX,):
        score += 600
    if card_id in (678, 723, 121, 269):  # visible ex/mega-ex public archetype anchors
        score += 500
    return score


def _build_plan(obs: object) -> AttackPlan:
    state = obs.current
    player = int(state.yourIndex)
    player_state = state.players[player]
    opponent_state = state.players[1 - player]
    has_lunatone = _has_lunatone(obs, player)
    can_switch = _can_switch_active(obs, player)
    can_boss = _can_play_card(obs, player, BOSS_ORDERS)

    opponent_targets = [(AreaType.ACTIVE, 0, opponent_state.active[0] if opponent_state.active else None)]
    if can_boss:
        opponent_targets.extend((AreaType.BENCH, i, card) for i, card in enumerate(opponent_state.bench))

    candidates = []
    for attacker_area, cards in ((AreaType.ACTIVE, player_state.active), (AreaType.BENCH, player_state.bench)):
        for attacker_index, attacker in enumerate(cards):
            if attacker is None:
                continue
            attacker_id = int(attacker.id)
            for attack_id, required, damage in _attack_options(attacker_id, has_lunatone):
                attached = _energy_count(attacker)
                needed = max(0, required - attached)
                ready = needed == 0
                needs_switch = attacker_area == AreaType.BENCH
                if needs_switch and not can_switch:
                    # Still plan future attachments, but do not pretend we can attack this turn.
                    ready_for_attack = False
                else:
                    ready_for_attack = ready
                for target_area, target_index, target in opponent_targets:
                    if target is None:
                        continue
                    target_hp = int(target.hp)
                    needs_boss = target_area == AreaType.BENCH
                    immediate_ko = ready_for_attack and damage >= target_hp
                    score = damage
                    score += 12_000 if immediate_ko else 0
                    score += min(1_500, _target_score(target))
                    score += 900 if ready_for_attack else -420 * needed
                    score += 320 if attacker_area == AreaType.ACTIVE else -260
                    if attacker_id == MEGA_LUCARIO_EX:
                        score += 1_800
                        if attack_id == MEGA_BRAVE:
                            score += 700
                    elif attacker_id == HARIYAMA:
                        score += 120
                    elif attacker_id == SOLROCK:
                        score -= 1_100
                    elif attacker_id == MAKUHITA:
                        score -= 450
                    if needs_switch:
                        score -= 700
                    if needs_boss:
                        score -= 300
                    if attacker_id == MEGA_LUCARIO_EX and attack_id == MEGA_BRAVE and immediate_ko:
                        score += 1_400
                    candidates.append((
                        score, attacker_area, attacker_index, attacker_id, attack_id, damage,
                        target_area, target_index, target_hp, needed, ready, immediate_ko,
                        needs_switch, needs_boss,
                    ))

    if not candidates:
        return AttackPlan()
    (
        _, attacker_area, attacker_index, attacker_id, attack_id, damage,
        target_area, target_index, target_hp, needed, ready, immediate_ko,
        needs_switch, needs_boss,
    ) = max(candidates, key=lambda item: (item[0], -item[2], -item[7]))
    return AttackPlan(
        attacker_area=attacker_area,
        attacker_index=attacker_index,
        attacker_id=attacker_id,
        attack_id=attack_id,
        damage=damage,
        target_area=target_area,
        target_index=target_index,
        target_hp=target_hp,
        energy_needed=needed,
        ready=ready,
        immediate_ko=immediate_ko,
        needs_switch=needs_switch,
        needs_boss=needs_boss,
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
        active = obs.current.players[player].active[0] if obs.current.players[player].active else None
        active_id = int(active.id) if active is not None else -1
        if plan.confident and plan.needs_switch and plan.ready and plan.attacker_id == MEGA_LUCARIO_EX:
            base += 5_500
        elif active_id == MEGA_LUCARIO_EX:
            base -= 8_000
        else:
            base -= 5_000
    elif option.type == OptionType.PLAY:
        card = _get_card(obs, AreaType.HAND, option.index, player)
        if card is not None:
            card_id = int(card.id)
            if card_id == SWITCH:
                active = obs.current.players[player].active[0] if obs.current.players[player].active else None
                active_id = int(active.id) if active is not None else -1
                if active_id == MEGA_LUCARIO_EX and plan.attacker_id != MEGA_LUCARIO_EX:
                    base -= 8_000
                else:
                    base += 5_500 if plan.needs_switch and plan.ready and plan.attacker_id == MEGA_LUCARIO_EX else -3_000
            elif card_id == BOSS_ORDERS:
                base += 5_800 if plan.needs_boss and plan.ready else -3_500
            elif card_id in (CARMINE, LILLIE_DETERMINATION):
                base += 1_800 if not plan.immediate_ko else -1_500
            elif card_id in (FIGHTING_GONG, PREMIUM_POWER_PRO, POKE_PAD):
                base += 1_200 if not plan.immediate_ko else -800
            elif card_id == GRAVITY_MOUNTAIN:
                base += 500
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
        else:
            if plan.confident and option.area == plan.target_area and option.index == plan.target_index:
                score += 10_000
            score += _target_score(card)
        return score
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        if card_id == RIOLU:
            return 850
        if card_id == SOLROCK:
            return 520
        if card_id == MAKUHITA:
            return 330
        if card_id == LUNATONE:
            return 240
    if context in (SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH):
        if card_id == RIOLU:
            return 780
        if card_id == LUNATONE:
            return 560
        if card_id == SOLROCK:
            return 520
        if card_id == MAKUHITA:
            return 300
    if context == SelectContext.TO_HAND:
        if card_id == MEGA_LUCARIO_EX:
            return 1_450
        if card_id == RIOLU:
            return 1_200
        if card_id == FIGHTING_ENERGY:
            return 850 if plan.energy_needed > 0 else 500
        if card_id == BOSS_ORDERS and plan.needs_boss and plan.attacker_id == MEGA_LUCARIO_EX:
            return 900
        if card_id == SWITCH and plan.needs_switch and plan.attacker_id == MEGA_LUCARIO_EX:
            return 850
        if card_id in (LILLIE_DETERMINATION, CARMINE):
            return 700
        if card_id in (LUNATONE, SOLROCK):
            return 420
        if card_id in (HARIYAMA, MAKUHITA):
            return 360
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
