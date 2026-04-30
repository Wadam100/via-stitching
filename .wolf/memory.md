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
