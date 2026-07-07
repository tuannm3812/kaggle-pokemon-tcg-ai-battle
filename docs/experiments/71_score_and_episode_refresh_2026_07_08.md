# Score and Episode Refresh

Date: 2026-07-08

## Purpose

After committing the v16-v21 research checkpoint, refresh the live score and
public replay evidence before deciding whether to submit or continue
experimenting.

## Current submission scores

Checked with:

```powershell
python -m kaggle competitions submissions pokemon-tcg-ai-battle -v
```

| Submission | Description | Public score |
| ---: | --- | ---: |
| `54303967` | kojimar simple baseline v1 | 864.5 |
| `54391951` | kojimar v8 public boss guard | 808.6 |
| `54348833` | kojimar v5 metal pressure | 724.6 |
| `54283898` | lucario public sample v3 | 711.2 |

Active-best remains `kojimar_simple_baseline_v1`.

## Episode cache refresh

Added:

```text
scripts/download_submission_episodes.py
```

Kaggle current public episode counts:

| Submission | Kaggle episodes | Local before | Refresh result |
| ---: | ---: | ---: | --- |
| `54303967` | 135 | 135 | already current |
| `54391951` | 76 | 61 | downloaded 15 |
| `54348833` | 103 | 68 | downloaded 35 |
| `54283898` | 91 | 0 | not refreshed yet |

## Refreshed public replay analysis

### v8: `54391951`

Overall: `46-30`, score rate `0.6053`, public score `808.6`.

| Archetype | Record | Score | n |
| --- | --- | ---: | ---: |
| dragapult | 0-5 | 0.0000 | 5 |
| phantump_trevenant_control | 0-4 | 0.0000 | 4 |
| alakazam_dunsparce | 3-5 | 0.3750 | 8 |
| grimmsnarl | 3-3 | 0.5000 | 6 |
| metal_cinderace | 12-5 | 0.7059 | 17 |
| other | 5-2 | 0.7143 | 7 |
| lucario | 15-5 | 0.7500 | 20 |
| crustle_libraryout | 8-1 | 0.8889 | 9 |

### v5: `54348833`

Overall: `54-49`, score rate `0.5243`, public score `724.6`.

| Archetype | Record | Score | n |
| --- | --- | ---: | ---: |
| phantump_trevenant_control | 0-4 | 0.0000 | 4 |
| crustle_libraryout | 1-4 | 0.2000 | 5 |
| alakazam_dunsparce | 5-8 | 0.3846 | 13 |
| metal_cinderace | 10-9 | 0.5263 | 19 |
| grimmsnarl | 5-4 | 0.5556 | 9 |
| other | 10-7 | 0.5882 | 17 |
| iono | 3-2 | 0.6000 | 5 |
| lucario | 13-8 | 0.6190 | 21 |
| dragapult | 6-3 | 0.6667 | 9 |
| abomasnow | 1-0 | 1.0000 | 1 |

## Interpretation

Do not submit v8 or any v18-v21 branch.

The refreshed v8 evidence explains why its public score drifted up: it is good
into Metal/Cinderace, Lucario, and library-out. However, it remains a severe
risk into Dragapult and Phantump/Trevenant control. Since v1 is still much
higher on the public leaderboard, v8 is not a replacement candidate.

The refreshed v5 evidence is weaker overall and does not solve the core public
meta problem.

## Next step

Keep `kojimar_simple_baseline_v1` as active-best.

For the next candidate cycle, do not continue v18-v21 scoring tweaks. Instead,
use the refreshed replay cache to design a new branch that preserves v1's
Dragapult/Phantump behavior while borrowing only the safe parts of v8's
Metal/Cinderace and library-out behavior.
