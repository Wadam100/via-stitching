# Via Stitching for KiCad

A KiCad action plugin that places stitching vias inside copper zones, along
the board edge, or along selected tracks. Useful for tying ground planes
together on multilayer boards, building shielding fences for RF, and
return-path stitching alongside high-speed traces.

Targets the **KiCad 9** `pcbnew` Python API. KiCad 10 keeps the same
ActionPlugin entry point, but a couple of API names have moved over the
years — see [KiCad 10 notes](#kicad-10-notes) below.

## Patterns

The plugin offers four patterns, all selectable from the dialog:

1. **Grid (rectangular)** — fills the selected zone(s) with a regular
   X/Y grid of vias.
2. **Staggered / hex** — the same as Grid but every other row is offset by
   half a pitch. Higher density and better RF behaviour.
3. **Perimeter (along Edge.Cuts)** — walks every shape on the `Edge.Cuts`
   layer and drops vias at the chosen pitch. Good for shielding fences.
4. **Along selected tracks** — for each selected track segment, places vias
   at the chosen pitch along its length. Useful for return-path stitching
   on RF/high-speed traces.

For Grid and Staggered the plugin only places vias **inside selected
zones**, and respects the zone net (or a fallback you pick in the dialog).

For all patterns the plugin enforces:

- Minimum centre-to-centre spacing between any two stitch vias.
- Clearance to tracks, vias, and pads on **other** nets.
- Skipping placement that would land inside same-net pads.

## Install

### Recommended: KiCad Plugin and Content Manager (PCM)

Add this custom repository to KiCad once and the plugin (plus future
updates) installs with one click.

1. Open KiCad's main window.
2. **Plugin and Content Manager → Manage** (gear icon, top right of the
   PCM dialog).
3. **Add** a new repository with URL:

   ```
   https://raw.githubusercontent.com/Wadam100/via-stitching/main/repository.json
   ```

4. Save. Switch to the **Plugins** tab in PCM, find **Via Stitching**, and
   click **Install**. Apply the pending changes.
5. Open pcbnew → **Tools → External Plugins → Refresh Plugins**.

### Quick install (manual)

Copy the `via_stitching/` folder into KiCad's user plugin directory:

| OS      | Path                                                                  |
| ------- | --------------------------------------------------------------------- |
| Linux   | `~/.local/share/kicad/9.0/scripting/plugins/via_stitching/`           |
| macOS   | `~/Documents/KiCad/9.0/scripting/plugins/via_stitching/`              |
| Windows | `%APPDATA%\kicad\9.0\scripting\plugins\via_stitching\`                |

For KiCad 10 the path is the same with `9.0` replaced by `10.0`.

Then in pcbnew: **Tools → External Plugins → Refresh Plugins**. You should
see "Via Stitching" appear, with a toolbar button.

### From within KiCad (alternative)

Open pcbnew → **Tools → External Plugins → Open Plugin Directory**, and
drop the `via_stitching/` folder there. Restart pcbnew or refresh plugins.

## Usage

1. Open your `.kicad_pcb` in pcbnew.
2. Pick the items the plugin should work on:
   - **Grid / Staggered:** select one or more copper zones (click each zone
     edge while holding Shift).
   - **Perimeter:** nothing to select — the plugin walks `Edge.Cuts`
     automatically.
   - **Along selected tracks:** select one or more tracks.
3. Click the **Via Stitching** toolbar button (or **Tools → External
   Plugins → Via Stitching**).
4. In the dialog, set:
   - Pattern.
   - Pitch (X is along-line for non-grid patterns).
   - Via diameter / drill.
   - Clearance to other-net copper (added on top of via radius).
   - Minimum via-to-via spacing.
   - Net: leave **Use net of selected zone(s) / track(s)** ticked to
     inherit, or untick and pick a fallback net (defaults to `GND`).
   - Layer pair: defaults to F.Cu / B.Cu — through-vias only for now.
5. **Apply.** The status line at the bottom reports how many vias were
   placed. Hit **Undo last run** if you don't like the result, tweak the
   settings, and apply again. Settings persist between runs in
   `last_settings.json` next to the plugin.

## Tips

- Run a DRC pass after applying — the plugin checks clearance against
  copper but does not run KiCad's full DRC.
- For RF shielding fences along Edge.Cuts, set pitch to roughly λ/20 at
  your highest frequency of concern (e.g. 2 mm for 2.4 GHz, smaller for
  mmWave).
- For return-path stitching alongside high-speed differential pairs, place
  ground vias every λ/10 along the trace.
- The plugin does not currently support blind/buried vias. Layer pair is
  exposed in the dialog but only F.Cu/B.Cu through-vias are produced.

## KiCad 10 notes

KiCad 10 should run this plugin unchanged in most cases. If you hit an
error, the most common API drifts are:

- `pcbnew.PCB_VIA` — was `pcbnew.VIA` before KiCad 7.
- `VECTOR2I` vs `wxPoint` — KiCad 7+ uses `VECTOR2I`. Older code used
  `wxPoint` which is now deprecated; this plugin already targets the
  modern names.
- `zone.GetFilledPolysList(layer)` — signature has changed across versions;
  the plugin falls back to `zone.Outline()` if the call fails.
- `pcbnew.IsCopperLayer(layer_id)` — still present in KiCad 10.

If the plugin breaks under KiCad 10, the file to look at first is
`via_stitcher.py` — that's where the pcbnew calls live.

## File layout

```
Via-Stitching/
├── README.md
├── metadata.json              # KiCad PCM metadata (for future packaging)
└── via_stitching/             # ← copy this folder into KiCad's plugin dir
    ├── __init__.py            # registers the plugin with pcbnew
    ├── plugin.py              # ActionPlugin subclass + Run()
    ├── stitcher_dialog.py     # wxPython settings dialog
    └── via_stitcher.py        # core algorithms
```

## Publishing a new release (maintainer notes)

The repo is its own KiCad PCM custom repository, served straight from
`raw.githubusercontent.com`. To cut a new release:

1. Bump the `versions[0].version` field in `metadata.json` at the repo
   root. Optionally update `description_full`, `kicad_version`,
   `kicad_version_max`.
2. From the repo root run:

   ```
   python3 tools/build_pcm_release.py
   ```

   This produces:

   - `releases/via_stitching-<VERSION>.zip` — the package KiCad downloads.
   - `packages.json` — list of available versions, with `download_url`,
     `download_sha256`, `download_size`, `install_size` filled in.
   - `repository.json` — top-level pointer to `packages.json`, with the
     packages.json hash pinned.

3. Commit and push everything to `main`:

   ```
   git add metadata.json packages.json repository.json releases/
   git commit -m "Release v<VERSION>"
   git push origin main
   ```

4. KiCad clients that already have the repository URL added will see the
   new version on their next PCM refresh.

To override the base URL (e.g. for testing on a fork):

```
python3 tools/build_pcm_release.py --base-url https://example.com/path/
```

## License

MIT — do whatever you want, no warranty.
