# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-04-30T18:35:00Z
> Files: 8 tracked | Anatomy hits: 0 | Misses: 0

## ./

- `CLAUDE.md` — OpenWolf entry point (~57 tok)
- `metadata.json` — PCM source of truth: identifier, author, versions; edit here then rebuild (~338 tok)
- `packages.json` — PCM v2 package list with download_url/sha; built artifact, do not hand-edit (~330 tok)
- `repository.json` — PCM v2 repo manifest (schema_version: 2); built artifact (~120 tok)

## .claude/

- `settings.json` — Claude Code permissions and hooks (~441 tok)

## .claude/rules/

- `openwolf.md` — OpenWolf project rules for Claude (~313 tok)

## releases/

- `via_stitching-0.1.1.zip` — PCM package zip (flat plugins/ layout — __init__.py at plugins root, NOT plugins/via_stitching/)

## tools/

- `build_pcm_release.py` — Builds zip + emits PCM v2 packages.json/repository.json from metadata.json; arc path is `plugins/<file>` (flat, no subdir nesting) (~2565 tok)

## via_stitching/

- `__init__.py` — KiCad plugin entry point: imports ViaStitchingPlugin, calls .register() (~51 tok)
- `plugin.py` — ViaStitchingPlugin(ActionPlugin): defaults(), Run(); lazy-imports StitcherDialog (~562 tok)
- `stitcher_dialog.py` — wx dialog for via stitching parameters (~unknown tok)
- `via_stitcher.py` — core stitching logic (~unknown tok)

