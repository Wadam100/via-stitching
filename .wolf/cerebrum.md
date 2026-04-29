# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-04-29

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **Project:** via_stitching
- **KiCad PCM custom repos must be served publicly.** PCM fetches `repository.json` anonymously with no credential support, so a private GitHub repo causes the generic error "The given repository URL does not look like a valid KiCad package repository." Always verify the raw URL with an anonymous fetch (curl / WebFetch / incognito browser) before troubleshooting JSON schema issues — `git ls-remote` succeeds with stored creds and will mislead you.
- **KiCad 10 PCM requires schema v2 — silent hang on v1.** KiCad 10's PCM client expects `repository.json` to declare `"$schema": "https://go.kicad.org/pcm/schemas/v2"` and a top-level `"schema_version": 2`. With a v1 file, KiCad 10 freezes on "Fetching repository" instead of returning an error. The v2 schema also adds an optional `runtime: "swig" | "ipc"` field on each version (default "swig" — set explicitly for SWIG-based action plugins; use "ipc" for the new KiCad 10 IPC API). Build artifacts are produced by `tools/build_pcm_release.py` from `metadata.json` (the source of truth).
- **`kicad_version_max` excludes the listed version itself.** Setting `kicad_version_max: "10.0"` keeps the package off KiCad 10. If a plugin works on the latest KiCad, omit the field rather than guessing. KiCad's PCM compares versions in a way that treats this bound as exclusive in practice.
- **PCM schema URLs:** `https://go.kicad.org/pcm/schemas/v1` and `…/v2` both 302-redirect to `gitlab.com/kicad/code/kicad/-/raw/master/kicad/pcm/schemas/pcm.v{1,2}.schema.json`. Use these for ground-truth field requirements.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-04-29] When troubleshooting a KiCad 10 PCM fetch hang, don't waste time on hash mismatches if the local hashes and the served hashes already agree — check the **schema version** first. KiCad 10 hangs (no error) when given a v1 repository.json. Fix is to bump to `$schema` v2 + add `schema_version: 2`.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-04-29] Dropped `kicad_version_max` from `metadata.json` rather than bumping it. The plugin only depends on the long-stable `pcbnew` SWIG API; setting an explicit upper bound creates a recurring maintenance burden and risks excluding future KiCads with no benefit. Rather, declare a minimum `kicad_version: "9.0"` and let the user discover incompatibility if KiCad ever ships a breaking change. Set `runtime: "swig"` explicitly for clarity even though it's the default.
