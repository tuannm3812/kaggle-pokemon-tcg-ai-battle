"""Evaluate local candidates against author-reference policies on their decks.

The existing author-opponent suite intentionally runs every policy on our
``agent/deck.csv`` so it can isolate action-selection quality. This suite is the
next pressure test: it reconstructs the public author sample decklists from the
locally extracted reference notebooks and runs each author policy on its own
archetype deck.

Use this when leaderboard score is low and we need to separate two questions:

1. Is our policy weak against known public archetypes?
2. Is our submitted deck composition the larger bottleneck?

The script does not commit generated runtime files; it writes a JSON report
under ``scratch/`` for local analysis.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_author_opponent_suite as suite  # noqa: E402


RESULTS_PATH = suite.SCRATCH / "author_archetype_deck_suite_results.json"


@dataclass(frozen=True)
class ArchetypeDeck:
    name: str
    policy_name: str
    cards: tuple[tuple[int, int], ...]
    source_note: str

    def expanded(self) -> list[int]:
        deck: list[int] = []
        for card_id, count in self.cards:
            deck.extend([card_id] * count)
        if len(deck) != 60:
            raise ValueError(f"{self.name} must contain 60 cards, found {len(deck)}")
        return deck


AUTHOR_ARCHETYPE_DECKS: dict[str, ArchetypeDeck] = {
    "abomasnow": ArchetypeDeck(
        name="abomasnow",
        policy_name="author_abomasnow_policy",
        source_note="scratch/author_references/abomasnow/extracted_code.py decklist comments",
        cards=(
            (721, 2),   # Kyogre
            (722, 4),   # Snover
            (723, 4),   # Mega Abomasnow ex
            (1121, 4),  # Ultra Ball
            (1126, 1),  # Precious Trolley
            (1192, 4),  # Carmine
            (1227, 4),  # Lillie's Determination
            (1262, 3),  # Surfing Beach
            (3, 34),    # Basic Water Energy
        ),
    ),
    "lucario": ArchetypeDeck(
        name="lucario",
        policy_name="author_lucario_policy",
        source_note="scratch/author_references/lucario/extracted_code.py decklist comments",
        cards=(
            (673, 2),   # Makuhita
            (674, 2),   # Hariyama
            (675, 2),   # Lunatone
            (676, 3),   # Solrock
            (677, 3),   # Riolu
            (678, 4),   # Mega Lucario ex
            (1102, 4),  # Dusk Ball
            (1123, 2),  # Switch
            (1141, 4),  # Premium Power Pro
            (1142, 4),  # Fighting Gong
            (1152, 4),  # Poke Pad
            (1159, 1),  # Hero Cape
            (1182, 2),  # Boss's Orders
            (1192, 4),  # Carmine
            (1227, 4),  # Lillie's Determination
            (1252, 2),  # Gravity Mountain
            (6, 13),    # Basic Fighting Energy
        ),
    ),
    "dragapult": ArchetypeDeck(
        name="dragapult",
        policy_name="author_dragapult_policy",
        source_note="scratch/author_references/dragapult/extracted_code.py decklist comments",
        cards=(
            (119, 4),   # Dreepy
            (120, 4),   # Drakloak
            (121, 3),   # Dragapult ex
            (140, 1),   # Fezandipiti ex
            (184, 1),   # Latias ex
            (235, 2),   # Budew
            (1071, 1),  # Meowth ex
            (1079, 2),  # Rare Candy
            (1080, 1),  # Unfair Stamp
            (1086, 4),  # Buddy-Buddy Poffin
            (1097, 2),  # Night Stretcher
            (1120, 4),  # Crushing Hammer
            (1121, 4),  # Ultra Ball
            (1152, 3),  # Poke Pad
            (1156, 1),  # Lucky Helmet
            (1182, 3),  # Boss's Orders
            (1198, 4),  # Crispin
            (1210, 2),  # Brock's Scouting
            (1227, 4),  # Lillie's Determination
            (1256, 2),  # Team Rocket Watchtower
            (2, 4),     # Basic Fire Energy
            (5, 4),     # Basic Psychic Energy
        ),
    ),
    "iono": ArchetypeDeck(
        name="iono",
        policy_name="author_iono_policy",
        source_note="scratch/author_references/iono/extracted_code.py decklist comments",
        cards=(
            (265, 3),   # Iono's Voltorb
            (268, 3),   # Iono's Tadbulb
            (269, 3),   # Iono's Bellibolt ex
            (270, 3),   # Iono's Wattrel
            (271, 3),   # Iono's Kilowattrel
            (1086, 3),  # Buddy-Buddy Poffin
            (1097, 2),  # Night Stretcher
            (1110, 1),  # Max Rod
            (1118, 1),  # Energy Retrieval
            (1121, 3),  # Ultra Ball
            (1152, 2),  # Poke Pad
            (1227, 4),  # Lillie's Determination
            (1233, 4),  # Canari
            (1254, 3),  # Levincia
            (4, 22),    # Basic Lightning Energy
        ),
    ),
}


def write_deck_csv(deck: list[int], path: Path) -> None:
    path.write_text("\n".join(str(card_id) for card_id in deck) + "\n", encoding="utf-8")


def load_author_policy_with_archetype_deck(archetype: ArchetypeDeck) -> suite.Policy:
    source_path = suite.AUTHOR_POLICIES[archetype.policy_name]
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    module_dir = suite.RUNTIME_ROOT / f"{archetype.policy_name}_own_deck"
    module_dir.mkdir(parents=True, exist_ok=True)
    write_deck_csv(archetype.expanded(), module_dir / "deck.csv")

    module_path = module_dir / "main.py"
    module_path.write_text(suite.sanitize_author_source(source_path), encoding="utf-8")
    module = suite.load_module(f"sanitized_{archetype.policy_name}_own_deck", module_path, cwd=module_dir)
    deck = getattr(module, "my_deck", suite.read_deck(module_dir / "deck.csv"))
    return suite.Policy(name=f"{archetype.policy_name}_own_deck", agent=module.agent, deck=list(deck))


def evaluate_matchup(
    candidate: suite.Policy,
    opponent: suite.Policy,
    games_per_cell: int,
    max_decisions: int,
    seed: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_seat in (0, 1):
        for player_zero_first in (False, True):
            for repeat in range(games_per_cell):
                game_seed = seed + 10_000 * len(rows) + 100 * candidate_seat + 10 * int(player_zero_first) + repeat
                try:
                    row = suite.run_game(
                        candidate=candidate,
                        opponent=opponent,
                        candidate_seat=candidate_seat,
                        player_zero_first=player_zero_first,
                        seed=game_seed,
                        max_decisions=max_decisions,
                    )
                except Exception as exc:  # noqa: BLE001 - batch evaluator should report and continue.
                    row = {
                        "status": "error",
                        "seed": game_seed,
                        "candidate_reward": 0,
                        "candidate_score": 0,
                        "error": repr(exc),
                        "candidate_seat": candidate_seat,
                        "player_zero_first": player_zero_first,
                    }
                row["candidate"] = candidate.name
                row["opponent"] = opponent.name
                rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        nargs="+",
        default=["promoted", "planner_main_only_v1"],
        choices=sorted(suite.AGENT_PATHS),
        help="Local candidate keys from evaluate_author_opponent_suite.AGENT_PATHS.",
    )
    parser.add_argument(
        "--archetypes",
        nargs="+",
        default=sorted(AUTHOR_ARCHETYPE_DECKS),
        choices=sorted(AUTHOR_ARCHETYPE_DECKS),
        help="Author archetype decks to reconstruct and evaluate.",
    )
    parser.add_argument(
        "--author-candidate-archetypes",
        nargs="*",
        default=[],
        choices=sorted(AUTHOR_ARCHETYPE_DECKS),
        help=(
            "Also evaluate selected reconstructed author archetypes as candidate baselines. "
            "Use this to rank public archetypes before adapting a deck/policy."
        ),
    )
    parser.add_argument("--games-per-cell", type=int, default=3)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260629)
    args = parser.parse_args()

    sdk_dir = suite.find_sdk_dir()
    suite.stage_runtime(sdk_dir)

    candidates = []
    for name in args.candidates:
        path = suite.AGENT_PATHS[name]
        if not path.exists():
            raise FileNotFoundError(path)
        candidates.append(suite.load_local_policy(name, path))
    for name in args.author_candidate_archetypes:
        candidates.append(load_author_policy_with_archetype_deck(AUTHOR_ARCHETYPE_DECKS[name]))

    opponents = [load_author_policy_with_archetype_deck(AUTHOR_ARCHETYPE_DECKS[name]) for name in args.archetypes]

    all_rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        for opponent in opponents:
            matchup = f"{candidate.name}_vs_{opponent.name}"
            rows = evaluate_matchup(
                candidate=candidate,
                opponent=opponent,
                games_per_cell=args.games_per_cell,
                max_decisions=args.max_decisions,
                seed=args.seed + 100_000 * len(all_rows),
            )
            for row in rows:
                row["matchup"] = matchup
            all_rows.extend(rows)
            summaries[matchup] = suite.summarize(rows)
            summary = summaries[matchup]
            print(
                f"{matchup}: {summary['wins']}-{summary['losses']}"
                f"{'-' + str(summary['draws']) if summary['draws'] else ''}, "
                f"score={summary['score_rate']}, failures={summary['failures']}"
            )

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "games_per_cell": args.games_per_cell,
                "max_decisions": args.max_decisions,
                "sdk_dir": str(sdk_dir.relative_to(ROOT)),
                "deck_mode": "candidate uses its own deck; author policy uses reconstructed public author archetype deck",
                "archetype_sources": {
                    name: AUTHOR_ARCHETYPE_DECKS[name].source_note for name in args.archetypes
                },
                "summaries": summaries,
                "rows": all_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
