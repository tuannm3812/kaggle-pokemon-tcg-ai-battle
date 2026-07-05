# Leaderboard episode analysis and v5 metal-pressure candidate

## Goal

Use current public leaderboard episodes for active submission
`54303967` / `kojimar_simple_baseline_v1` to design the next candidate from
real failure patterns instead of guessing.

## Current submission status

Checked on 2026-07-05 through the Kaggle API:

| Submission | Candidate | Status | Public score |
| ---: | --- | --- | ---: |
| `54303967` | `kojimar_simple_baseline_v1` | complete | `874.5` |
| `54283898` | `lucario_public_sample_v3` | complete | `711.2` |

## Episode sample

Downloaded all 92 public episodes for submission `54303967` into
`scratch/leaderboard_episodes/54303967/`.

Compact replay summary:

| Slice | Games | Wins | Score |
| --- | ---: | ---: | ---: |
| all public episodes | 92 | 52 | 0.565 |
| candidate seat 0 | 37 | 24 | 0.649 |
| candidate seat 1 | 55 | 28 | 0.509 |
| candidate went first | 53 | 30 | 0.566 |
| candidate went second | 39 | 22 | 0.564 |

Main lesson: the current losses are not primarily first-player driven. They
cluster by opponent archetype.

## Loss clusters

The most useful repeatable opponent signatures:

| Opponent family | Public replay result | Notes |
| --- | ---: | --- |
| Archaludon/Cinderace/Relicanth variants | roughly break-even, but many one-off losses | Largest visible repeat loss family |
| Alakazam/Dunsparce variants | below break-even in several clusters | Fighting resistance and control shell |
| Phantump/Trevenant/Dunsparce control | small sample, poor result | Control/disruption family |
| Lucario mirrors | near break-even to positive | Not the main current weakness |
| Marnie/Grimmsnarl variants | positive | No immediate need to target |

Loss-heavy cards appearing in downloaded opponent decks included:

- `190` Archaludon ex
- `169` Duraludon
- `666` Cinderace
- `57` Relicanth
- `741/742/743` Abra/Kadabra/Alakazam
- `305/66` Dunsparce/Dudunsparce

## Candidate: `kojimar_simple_baseline_v5_metal_pressure`

Built from `kojimar_simple_baseline_v1`.

Change scope:

- add constants for the Metal/Cinderace family:
  - `57` Relicanth
  - `169` Duraludon
  - `190` Archaludon ex
  - `666` Cinderace
- add target-score pressure only:
  - Archaludon ex `+900`
  - Cinderace `+850`
  - Duraludon `+450`
  - Relicanth `+250`

This intentionally avoids setup, draw, first-player, and low-deck changes.

## Local gate results

Compact meta gate:

| Matchup | Result | Score |
| --- | ---: | ---: |
| vs `kojimar_simple_baseline_v1` | 9-3 | 0.750 |
| vs `lucario_public_sample_v3` | 8-4 | 0.667 |
| vs `koushikrudra_libraryout_v1` | 5-7 | 0.417 |
| vs official random | 12-0 | 1.000 |
| vs author Abomasnow | 6-2 | 0.750 |
| vs author Lucario | 4-3-1 | 0.563 |
| vs author Dragapult | 5-3 | 0.625 |
| vs author Iono | 5-3 | 0.625 |

Deeper same-seed direct-control check:

| Candidate | Control | Result | Score |
| --- | --- | ---: | ---: |
| v5 | v1 | 17-15 | 0.531 |
| v1 reference | v1 | 16-16 | 0.500 |
| v5 | Lucario v3 | 19-13 | 0.594 |
| v1 reference | Lucario v3 | 18-14 | 0.563 |
| v5 | library-out | 10-22 | 0.313 |
| v1 reference | library-out | 9-23 | 0.281 |

The deeper check suggests v5 is a small positive challenger, not a decisive
local upgrade.

Unforced live-style check was mixed:

| Candidate | Control | Result | Score |
| --- | --- | ---: | ---: |
| v5 | v1 | 7-17 | 0.292 |
| v1 reference | v1 | 11-13 | 0.458 |

The v5 diff is target-only, so the unforced result is likely noisy/seat-driven,
but it is still a caution flag.

## Packaging

`kojimar_simple_baseline_v5_metal_pressure` package smoke passed:

- archive:
  `scratch/submission_packages/kojimar_simple_baseline_v5_metal_pressure/submission.tar.gz`
- six local smoke games completed;
- archive contains `main.py`, `deck.csv`, and `cg/`.

## Decision

`kojimar_simple_baseline_v5_metal_pressure` is the best new challenger from
this round, but not an automatic submit.

Recommended decision:

1. If we want a leaderboard probe against the growing Metal/Cinderace field,
   submit v5.
2. If we want to be conservative with submission slots, run one more v5-focused
   validation round after collecting newer episodes.

