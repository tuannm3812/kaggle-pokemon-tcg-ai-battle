"""Development-first agent with a conservative ready-bench retreat rule."""

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


def read_deck_csv() -> list[int]:
    """Load the 60 card IDs from the submission directory."""
    candidates = (
        Path(__file__).resolve().with_name("deck.csv"),
        Path("deck.csv"),
        Path("/kaggle_simulations/agent/deck.csv"),
    )
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


def _energy_count(pokemon: object | None) -> int:
    if pokemon is None:
        return 0
    energies = getattr(pokemon, "energies", None)
    if energies is None:
        energies = getattr(pokemon, "energyCards", [])
    return len(energies)


def _card_id(pokemon: object | None) -> int:
    if pokemon is None:
        return -1
    try:
        return int(getattr(pokemon, "id", -1))
    except (TypeError, ValueError):
        return -1


def _ready_bench_indices(obs: object) -> set[int]:
    """Return indices of benched Pokémon with at least one attached Energy."""
    player = int(obs.current.yourIndex)
    bench = obs.current.players[player].bench
    return {
        index
        for index, pokemon in enumerate(bench)
        if pokemon is not None and _energy_count(pokemon) >= 1
    }


def _should_retreat_to_ready_bench(obs: object) -> bool:
    """Retreat only when active is unready and a ready bench attacker exists."""
    player = int(obs.current.yourIndex)
    active = obs.current.players[player].active
    active_energy = _energy_count(active[0] if active else None)
    if active_energy > 0:
        return False
    if not _ready_bench_indices(obs):
        return False
    return any(option.type == OptionType.RETREAT for option in obs.select.option)


def _bench_target_score(obs: object, option: object, index: int) -> tuple[int, tuple[int, ...]]:
    player = int(obs.current.yourIndex)
    if int(getattr(option, "playerIndex", player)) != player:
        return (-10_000, _stable_key(option, index))
    if getattr(option, "area", None) != AreaType.BENCH:
        return (-10_000, _stable_key(option, index))
    bench_index = int(getattr(option, "index", -1))
    if bench_index not in _ready_bench_indices(obs):
        return (-10_000, _stable_key(option, index))
    pokemon = obs.current.players[player].bench[bench_index]
    card_id = _card_id(pokemon)
    energy = _energy_count(pokemon)
    score = 10_000 + 1_000 * energy
    if card_id == 723:
        score += 500
    elif card_id == 721:
        score += 300
    elif card_id == 722:
        score += 100
    return (score, _stable_key(option, index))


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
        if _should_retreat_to_ready_bench(obs):
            retreat_choices = [pair for pair in indexed if pair[1].type == OptionType.RETREAT]
            indexed = retreat_choices or indexed
        indexed.sort(
            key=lambda pair: (
                0 if pair[1].type == OptionType.RETREAT and _should_retreat_to_ready_bench(obs)
                else MAIN_ACTION_PRIORITY.get(pair[1].type, 99),
                _stable_key(pair[1], pair[0]),
            )
        )
    elif context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        indexed.sort(key=lambda pair: (-_bench_target_score(obs, pair[1], pair[0])[0], _stable_key(pair[1], pair[0])))
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
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return read_deck_csv()
    return _choose_indices(obs)
