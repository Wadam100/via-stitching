# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-04-30T17:35:50.213Z
> Files: 13 tracked | Anatomy hits: 0 | Misses: 0

## ../../../.claude/projects/C--Users-werne-Documents-GitHub-via-stitching/memory/

- `feedback_version_bump.md` (~188 tok)
- `MEMORY.md` — Memory Index (~39 tok)

## ./

- `CLAUDE.md` — OpenWolf entry point (~57 tok)
- `metadata.json` (~338 tok)
- `packages.json` — PCM v2 package list with download_url/sha; built artifact, do not hand-edit (~330 tok)
- `repository.json` — PCM v2 repo manifest (schema_version: 2); built artifact (~120 tok)

## .claude/

- `settings.json` — Claude Code permissions and hooks (~441 tok)

## .claude/rules/

- `openwolf.md` — OpenWolf project rules for Claude (~313 tok)

## releases/


## tools/

- `build_pcm_release.py` — Builds zip + emits PCM v2 packages.json/repository.json from metadata.json; arc path is `plugins/<file>` (flat, no subdir nesting) (~2565 tok)

## via_stitching/

- `__init__.py` — KiCad plugin entry point: imports ViaStitchingPlugin, calls .register() (~51 tok)
- `plugin.py` — ViaStitchingPlugin(ActionPlugin): defaults(), Run(); lazy-imports StitcherDialog (~562 tok)
- `stitcher_dialog.py` — wxPython settings dialog for the Via Stitching plugin. (~2018 tok)
- `via_stitcher.py` — StitchSettings: mm, to_mm, selected_zones, selected_tracks + 2 more (~5390 tok)
