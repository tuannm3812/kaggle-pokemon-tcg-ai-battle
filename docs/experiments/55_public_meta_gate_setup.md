# Public meta gate setup

## Goal

Stop relying on a single local head-to-head gate before submitting. Recent v5
and v8 submissions showed that local direct signals can fail to transfer to the
public leaderboard. This step adds a replay-derived public-meta validation layer.

## New tooling

### `scripts/build_public_meta_fixtures.py`

Builds `scratch/public_meta_fixtures.json` from downloaded public episode
summaries. The fixture stores:

- source submissions;
- public episode win rates by archetype;
- representative weak deck signatures;
- source episodes and teams.

Current weak public archetypes from v1/v8 episodes:

| Archetype | Combined public result | Score |
| --- | ---: | ---: |
| Phantump/Trevenant control | 1-5 | 0.167 |
| Alakazam/Dunsparce | 7-13 | 0.350 |
| Metal/Cinderace | 16-22 | 0.421 |
| Dragapult | 7-7 | 0.500 |

### `scripts/evaluate_public_meta_gate.py`

Runs a conservative challenger gate that combines:

- local direct controls:
  - active v1;
  - v8;
  - v5;
  - Lucario v3;
  - Koushikrudra library-out;
  - official random;
- replay-derived weak public archetype summary from the fixture file.

This script does not simulate unknown public opponent policies. Its role is to
prevent a candidate from being promoted based on a narrow local signal while
the current public-meta weaknesses remain unresolved.

## Calibration runs

Compact two-games-per-cell gate:

| Candidate | Active-best gate | Library-out gate | Recommendation |
| --- | ---: | ---: | --- |
| `kojimar_simple_baseline_v1` | 0.375 | 0.375 | hold under challenger rule |
| `kojimar_simple_baseline_v8_public_boss_guard` | 0.500 | 0.500 | hold |
| `kojimar_simple_baseline_v9_strict_boss_guard` | 0.375 | 0.000 | hold |

The gate is intentionally conservative and best interpreted as a challenger
screen. The active best itself can fail the active-best head-to-head cell due to
small-sample asymmetry, so a future version should compare candidates against a
same-seed v1 reference rather than using a fixed absolute threshold alone.

## Strategy implication

Do not submit another Boss guard or target-score patch from the old local gates
alone. A next candidate should first demonstrate:

1. no obvious failure in the public-meta challenger gate;
2. a concrete hypothesis for one weak public archetype;
3. no large regression to library-out/control.

