# Candidate Agent Index

Each candidate folder is a self-contained local agent package with:

- `main.py`: Kaggle agent entrypoint;
- `deck.csv`: 60-card deck used by local gates and packaging.

The folder names are intentionally stable because `scripts/evaluate_author_opponent_suite.py`
registers candidates by path. Do not move or rename candidate folders without
updating the evaluator registry and experiment notes in the same commit.

## Current active best

| Candidate | Status | Notes |
| --- | --- | --- |
| `kojimar_simple_baseline_v1` | Active best submitted | Public score remains `864.5` as of 2026-07-07; strongest local and leaderboard evidence so far |

## Current Kojimar ablations

| Candidate | Status | Main lesson |
| --- | --- | --- |
| `kojimar_simple_baseline_v22_midgame_metal_boss_guard` | Hold / not submitted | Stricter midgame Metal/Cinderace Boss guard; helped v5/library-out cells but failed active-best/Lucario/random gate checks |
| `kojimar_simple_baseline_v21_midgame_ko_attack_enable` | Hold / not submitted | KO-only version of v20; safer conceptually but still failed public-meta gate protected cells |
| `kojimar_simple_baseline_v20_midgame_attack_enable` | Hold / not submitted | Midgame attack-ordering patch; improved random/library-out in quick gate but regressed active-best and v8 controls |
| `kojimar_simple_baseline_v19_active_threat_finish_pressure` | Hold / not submitted | Active-only finish-pressure patch; safe on Lucario/library-out quick gate but did not improve v5/v8 pressure controls |
| `kojimar_simple_baseline_v18_midgame_finish_pressure` | Hold / not submitted | Strategy-EDA midgame conversion patch; protected Lucario in quick gate but did not improve v5/v8 pressure controls and underperformed mirror/random reference cells |
| `kojimar_simple_baseline_v17_setup_riolu_pressure` | Rejected | Setup-active Riolu pressure looked plausible from loss replays but regressed v5/Lucario/library-out gates |
| `kojimar_simple_baseline_v16_meta_target_guard` | Hold / not submitted | Conservative v1 target-only meta patch; quick gate gained vs v8/random but flagged Lucario v3 regression, so needs replay-level proof before submission |
| `kojimar_simple_baseline_v15_lucario_tempo` | Rejected | Lucario-line tempo routing was too coarse and regressed v5/Lucario controls without improving author Dragapult |
| `kojimar_simple_baseline_v14_v8_prefer_second` | Rejected but informative | Always choosing second addressed the observed went-first loss pattern too bluntly and failed unforced controls |
| `kojimar_simple_baseline_v13_v8_dragapult_pressure` | Rejected but informative | v8 plus Dragapult target pressure improved author Dragapult but still trailed v1/v8/Lucario gate cells |
| `kojimar_simple_baseline_v12_dragapult_pressure` | Rejected | v1 plus Dragapult pressure was target-positive but regressed v5/Lucario controls |
| `kojimar_simple_baseline_v11_metal_boss_guard` | Rejected | Metal-only Boss guard did not clear the same-seed reference gate |
| `kojimar_simple_baseline_v10_phantump_pressure` | Rejected but informative | Phantump/Trevenant target pressure passed a compact public-meta screen but failed deeper active-best controls |
| `kojimar_simple_baseline_v9_strict_boss_guard` | Rejected | Stricter Boss guard avoided generic Dunsparce trigger but failed active-best gate |
| `kojimar_simple_baseline_v8_public_boss_guard` | Rejected but informative | Improved some public slices but scored below v1 and struggled into Dragapult/Phantump/Trevenant |
| `kojimar_simple_baseline_v7_boss_ko_only` | Rejected | Broad KO-only Boss timing tied v1 but hurt library-out gate |
| `kojimar_simple_baseline_v6_alakazam_pressure` | Rejected | Alakazam/Dunsparce target pressure did not beat v1 and hurt library-out gate |
| `kojimar_simple_baseline_v6_metal_conditional` | Rejected | Narrower Metal/Cinderace pressure beat v5 locally but not v1 |
| `kojimar_simple_baseline_v6_meta_pressure` | Rejected | Combined Metal and Alakazam pressure failed active-best gate |
| `kojimar_simple_baseline_v5_metal_pressure` | Rejected but informative | Improved Metal/Cinderace public episodes, but public score stayed below v1 and control weaknesses remained |
| `kojimar_simple_baseline_v4_second` | Rejected | Live-style go-second choice did not clearly beat v1 |
| `kojimar_simple_baseline_v3` | Rejected | Anti-library-out target priority alone lost to v1 |
| `kojimar_simple_baseline_v2` | Rejected | Broader anti-library-out patch did not survive deeper direct-control check |

## Important submitted candidates

| Candidate | Status | Notes |
| --- | --- | --- |
| `lucario_public_sample_v3` | Previous active best | Reached strong public scores after drift; superseded by Kojimar v1 |
| `lucario_public_sample_v1` | Submitted baseline | First successful public Lucario sample probe |
| `planner_main_only_v1` | Submitted historical | Older Abomasnow/planner branch, now superseded |

## Watchlist / rejected Lucario variants

| Candidate | Status | Main lesson |
| --- | --- | --- |
| `lucario_public_sample_v7` | Watchlist only | Conditional Crustle guard is conceptually useful but needs direct Crustle validation |
| `lucario_public_sample_v6` | Rejected | Search-only Lucario pressure did not beat v3 |
| `lucario_public_sample_v5` | Rejected | Mild Lucario pressure split 10-10 vs v3 |
| `lucario_public_sample_v4` | Watchlist only | Strong upside but unstable first-player cell |
| `lucario_public_sample_v2` | Rejected | Broad Lucario-line bias hurt earlier Abomasnow gate |

## Historical development candidates

Older folders such as `abomasnow_planner_*`, `setup_*`, `conservative_switch_*`,
and `lucario_adapted_*` are retained as reproducibility artifacts for the
experiment notes. Prefer creating a new candidate folder for new ideas instead
of mutating an old candidate in place.
