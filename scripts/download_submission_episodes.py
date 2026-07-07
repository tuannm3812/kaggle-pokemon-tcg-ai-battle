from __future__ import annotations

import argparse
import json
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


ROOT = Path(__file__).resolve().parents[1]
EPISODE_ROOT = ROOT / "scratch" / "leaderboard_episodes"


def episode_to_dict(episode) -> dict:
    payload = json.loads(str(episode))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public Kaggle episode replays for one submission.")
    parser.add_argument("--submission-id", type=int, required=True)
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of newest episodes to download.")
    parser.add_argument("--force", action="store_true", help="Redownload replay JSONs that already exist.")
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()

    output_dir = EPISODE_ROOT / str(args.submission_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    episodes = api.competition_list_episodes(args.submission_id)
    episode_payloads = [episode_to_dict(episode) for episode in episodes]
    (output_dir / "episodes.json").write_text(
        json.dumps(episode_payloads, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    selected = episode_payloads[: args.limit] if args.limit else episode_payloads
    downloaded = 0
    skipped = 0
    for episode in selected:
        episode_id = int(episode["id"])
        replay_path = output_dir / f"episode-{episode_id}-replay.json"
        if replay_path.exists() and not args.force:
            skipped += 1
            continue
        api.competition_episode_replay(episode_id, path=str(output_dir), quiet=True)
        downloaded += 1

    print(
        json.dumps(
            {
                "submission_id": args.submission_id,
                "episodes": len(episode_payloads),
                "selected": len(selected),
                "downloaded": downloaded,
                "skipped": skipped,
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
