# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.

## Session: 2026-04-29 19:24

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 19:30 | Diagnosed KiCad PCM "invalid repository URL" — anonymous fetch of raw repository.json returned 404 while local git ls-remote worked, so repo is private | repository.json, packages.json, metadata.json | Root cause: private GitHub repo blocks PCM's anonymous fetch. Logged to buglog + cerebrum. | ~6k |
| 17:58 | Diagnosed KiCad 10 PCM "fetching repository never finished" — root cause is the v1 schema. KiCad 10 introduced PCM schema v2 (go.kicad.org/pcm/schemas/v2) which adds a top-level `schema_version: 2` field on repository.json and a `runtime` field on package versions. Updated metadata.json + build_pcm_release.py to v2, dropped `kicad_version_max: "10.0"` (was excluding KiCad 10 itself), added `runtime: "swig"`, regenerated zip + packages.json + repository.json with fresh matching SHA-256s. | metadata.json, packages.json, repository.json, releases/via_stitching-0.1.0.zip, tools/build_pcm_release.py | Repo now serves PCM v2; fetch should complete on KiCad 10 and the package will appear as installable. | ~10k |

## Session: 2026-04-29 17:53

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 17:58 | Created metadata.json | — | ~332 |
| 17:58 | Edited tools/build_pcm_release.py | modified build_repository_json() | ~240 |
| 18:00 | Session end: 2 writes across 2 files (metadata.json, build_pcm_release.py) | 4 reads | ~572 tok |

## Session: 2026-04-29 18:04

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:10 | Edited metadata.json | inline fix | ~8 |
| 18:10 | Edited via_stitching/plugin.py | modified isfile() | ~65 |
| 18:11 | Session end: 2 writes across 2 files (metadata.json, plugin.py) | 9 reads | ~3840 tok |

## Session: 2026-04-30 04:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 11:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 18:31

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:34 | Edited tools/build_pcm_release.py | inline fix | ~18 |
| 18:34 | Edited metadata.json | inline fix | ~8 |
| 18:35 | Fixed PCM zip layout bug — removed extra PLUGIN_PKG_DIR nesting from arc path so files pack as plugins/__init__.py not plugins/via_stitching/__init__.py. Bumped to v0.1.1, rebuilt artifacts. Also patched installed plugin by copying via_stitching/* up to plugin root so it works immediately. | tools/build_pcm_release.py, metadata.json, releases/via_stitching-0.1.1.zip, packages.json, repository.json | Plugin now correctly installs; verified zip layout. | ~8k |
| 18:37 | Session end: 2 writes across 2 files (build_pcm_release.py, metadata.json) | 7 reads | ~26 tok |
| 18:42 | Edited via_stitching/via_stitcher.py | modified __init__() | ~126 |
| 18:42 | Edited via_stitching/via_stitcher.py | modified resolve_net() | ~67 |
| 18:42 | Edited via_stitching/via_stitcher.py | 2→2 lines | ~19 |
| 18:42 | Edited via_stitching/via_stitcher.py | modified _collect_edge_chords() | ~30 |
| 18:43 | Edited via_stitching/via_stitcher.py | 10→5 lines | ~45 |
| 18:43 | Edited via_stitching/via_stitcher.py | 4→4 lines | ~34 |
| 18:43 | Edited via_stitching/via_stitcher.py | inline fix | ~15 |
| 18:43 | Edited via_stitching/via_stitcher.py | 5→2 lines | ~22 |
| 18:43 | Edited via_stitching/via_stitcher.py | modified _clear_of_obstacles() | ~136 |
| 18:44 | Created via_stitching/stitcher_dialog.py | — | ~1969 |
| 18:44 | Edited metadata.json | inline fix | ~8 |
| 18:45 | Session end: 13 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~2497 tok |
| 18:55 | Edited via_stitching/via_stitcher.py | 2→1 lines | ~13 |
| 18:55 | Edited metadata.json | inline fix | ~8 |
| 18:56 | Session end: 15 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~7741 tok |
| 19:07 | Edited via_stitching/via_stitcher.py | 2→3 lines | ~34 |
| 19:07 | Edited via_stitching/via_stitcher.py | 4→6 lines | ~102 |
| 19:07 | Edited via_stitching/via_stitcher.py | expanded (+10 lines) | ~148 |
| 19:07 | Edited via_stitching/stitcher_dialog.py | 4→5 lines | ~122 |
| 19:07 | Edited via_stitching/stitcher_dialog.py | 2→3 lines | ~41 |
| 19:08 | Edited metadata.json | inline fix | ~8 |
| 19:08 | Session end: 21 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~8221 tok |
| 19:13 | Session end: 21 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~8221 tok |
| 19:13 | Session end: 21 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~8559 tok |
| 19:16 | Edited via_stitching/via_stitcher.py | 8→8 lines | ~140 |
| 19:16 | Session end: 22 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~8813 tok |
| 19:34 | Edited metadata.json | inline fix | ~8 |
| 19:35 | Session end: 23 writes across 4 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py) | 9 reads | ~8821 tok |
| 19:35 | Created ../../../.claude/projects/C--Users-werne-Documents-GitHub-via-stitching/memory/MEMORY.md | — | ~42 |
| 19:35 | Created ../../../.claude/projects/C--Users-werne-Documents-GitHub-via-stitching/memory/feedback_version_bump.md | — | ~187 |
| 19:36 | Session end: 25 writes across 6 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py, MEMORY.md) | 10 reads | ~9066 tok |
| 19:37 | Session end: 25 writes across 6 files (build_pcm_release.py, metadata.json, via_stitcher.py, stitcher_dialog.py, MEMORY.md) | 10 reads | ~9066 tok |
