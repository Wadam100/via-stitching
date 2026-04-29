"""wxPython settings dialog for the Via Stitching plugin."""
from __future__ import annotations

import json
import os

import pcbnew
import wx

from .via_stitcher import StitchSettings, ViaStitcher

# Path next to this file; persists last-used settings between runs.
_PRESET_FILE = os.path.join(os.path.dirname(__file__), "last_settings.json")

_PATTERN_LABELS = [
    ("Grid (rectangular)", "grid"),
    ("Staggered / hex", "staggered"),
    ("Perimeter (along Edge.Cuts)", "perimeter"),
    ("Along selected tracks", "tracks"),
]


class StitcherDialog(wx.Dialog):
    def __init__(self, parent, board: "pcbnew.BOARD"):
        super().__init__(
            parent,
            title="Via Stitching",
            size=wx.Size(440, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.board = board
        self.last_run: ViaStitcher | None = None

        settings = self._load_preset()
        self._build_ui(settings)
        self.Layout()
        self.Fit()
        self.SetMinSize(wx.Size(420, 560))

    # -- UI construction --------------------------------------------------

    def _build_ui(self, s: StitchSettings) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)
        pad = 8

        # --- Pattern picker ---
        pat_box = wx.StaticBox(self, label="Pattern")
        pat_sizer = wx.StaticBoxSizer(pat_box, wx.VERTICAL)
        self.pattern_choice = wx.RadioBox(
            self,
            choices=[lbl for lbl, _ in _PATTERN_LABELS],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
        )
        # Restore selection
        for i, (_lbl, key) in enumerate(_PATTERN_LABELS):
            if key == s.pattern:
                self.pattern_choice.SetSelection(i)
                break
        pat_sizer.Add(self.pattern_choice, 0, wx.EXPAND | wx.ALL, pad)
        outer.Add(pat_sizer, 0, wx.EXPAND | wx.ALL, pad)

        # --- Geometry ---
        geo_box = wx.StaticBox(self, label="Geometry (mm)")
        geo = wx.StaticBoxSizer(geo_box, wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=8)
        grid.AddGrowableCol(1, 1)

        self.pitch_x = self._add_float_row(grid, "Pitch X / along-line", s.pitch_x_mm)
        self.pitch_y = self._add_float_row(grid, "Pitch Y", s.pitch_y_mm)
        self.via_diam = self._add_float_row(grid, "Via diameter", s.via_diameter_mm)
        self.via_drill = self._add_float_row(grid, "Via drill", s.via_drill_mm)
        self.clearance = self._add_float_row(grid, "Clearance to other nets", s.clearance_mm)
        self.min_spacing = self._add_float_row(
            grid, "Min via-to-via spacing", s.min_via_spacing_mm
        )
        geo.Add(grid, 0, wx.EXPAND | wx.ALL, pad)
        outer.Add(geo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

        # --- Net + layers ---
        net_box = wx.StaticBox(self, label="Net + layers")
        net_sizer = wx.StaticBoxSizer(net_box, wx.VERTICAL)

        self.use_zone_net = wx.CheckBox(
            self, label="Use net of selected zone(s) / track(s)"
        )
        self.use_zone_net.SetValue(s.use_zone_net)
        net_sizer.Add(self.use_zone_net, 0, wx.ALL, pad)

        net_grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=8)
        net_grid.AddGrowableCol(1, 1)

        net_grid.Add(
            wx.StaticText(self, label="Fallback net:"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.net_combo = wx.ComboBox(
            self,
            value=s.net_name,
            choices=self._board_net_names(),
            style=wx.CB_DROPDOWN,
        )
        net_grid.Add(self.net_combo, 1, wx.EXPAND)

        layer_choices, layer_ids = self._copper_layer_choices()
        net_grid.Add(
            wx.StaticText(self, label="Top layer:"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.layer_top = wx.Choice(self, choices=layer_choices)
        self._select_layer(self.layer_top, layer_ids, s.layer_top)
        net_grid.Add(self.layer_top, 1, wx.EXPAND)

        net_grid.Add(
            wx.StaticText(self, label="Bottom layer:"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.layer_bottom = wx.Choice(self, choices=layer_choices)
        self._select_layer(self.layer_bottom, layer_ids, s.layer_bottom)
        net_grid.Add(self.layer_bottom, 1, wx.EXPAND)

        self._layer_ids = layer_ids
        net_sizer.Add(net_grid, 0, wx.EXPAND | wx.ALL, pad)
        outer.Add(net_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

        # --- Action buttons ---
        btns = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_btn = wx.Button(self, label="Apply")
        self.undo_btn = wx.Button(self, label="Undo last run")
        self.undo_btn.Disable()
        self.close_btn = wx.Button(self, id=wx.ID_CLOSE, label="Close")
        btns.Add(self.apply_btn, 0, wx.RIGHT, pad)
        btns.Add(self.undo_btn, 0, wx.RIGHT, pad)
        btns.AddStretchSpacer(1)
        btns.Add(self.close_btn, 0)
        outer.Add(btns, 0, wx.EXPAND | wx.ALL, pad)

        self.status = wx.StaticText(self, label="Ready.")
        outer.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

        self.SetSizer(outer)

        self.apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        self.undo_btn.Bind(wx.EVT_BUTTON, self.on_undo)
        self.close_btn.Bind(wx.EVT_BUTTON, lambda _e: self.EndModal(wx.ID_CLOSE))
        self.Bind(wx.EVT_CLOSE, lambda _e: self.EndModal(wx.ID_CLOSE))

    def _add_float_row(self, grid: wx.FlexGridSizer, label: str, value: float) -> wx.TextCtrl:
        grid.Add(
            wx.StaticText(self, label=label + ":"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        ctrl = wx.TextCtrl(self, value=f"{value:g}")
        grid.Add(ctrl, 1, wx.EXPAND)
        return ctrl

    # -- board introspection ---------------------------------------------

    def _board_net_names(self) -> list[str]:
        nets = self.board.GetNetsByName()
        names = []
        # GetNetsByName returns a wxString-keyed map; iterate keys
        try:
            for name in nets.keys():
                s = str(name)
                if s and s != "":
                    names.append(s)
        except Exception:
            for net in self.board.GetNetInfo().NetsByNetcode().values():
                names.append(net.GetNetname())
        names = sorted(set(names))
        # Make sure "GND" is first if present, else just leave alphabetical.
        if "GND" in names:
            names.remove("GND")
            names.insert(0, "GND")
        return names

    def _copper_layer_choices(self):
        names = []
        ids = []
        for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT):
            if not pcbnew.IsCopperLayer(layer_id):
                continue
            try:
                name = self.board.GetLayerName(layer_id)
            except Exception:
                name = pcbnew.LayerName(layer_id)
            names.append(name)
            ids.append(layer_id)
        return names, ids

    @staticmethod
    def _select_layer(choice_ctrl: wx.Choice, ids: list, target_id: int) -> None:
        try:
            idx = ids.index(target_id)
        except ValueError:
            idx = 0
        choice_ctrl.SetSelection(idx)

    # -- presets ----------------------------------------------------------

    def _load_preset(self) -> StitchSettings:
        s = StitchSettings()
        if not os.path.isfile(_PRESET_FILE):
            return s
        try:
            with open(_PRESET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(s, k):
                    setattr(s, k, v)
        except Exception:
            pass
        return s

    def _save_preset(self, s: StitchSettings) -> None:
        try:
            with open(_PRESET_FILE, "w", encoding="utf-8") as f:
                json.dump(s.__dict__, f, indent=2)
        except Exception:
            pass

    # -- collecting form values ------------------------------------------

    def _collect_settings(self) -> StitchSettings:
        s = StitchSettings()
        s.pattern = _PATTERN_LABELS[self.pattern_choice.GetSelection()][1]
        s.pitch_x_mm = self._float(self.pitch_x, 2.54)
        s.pitch_y_mm = self._float(self.pitch_y, 2.54)
        s.via_diameter_mm = self._float(self.via_diam, 0.6)
        s.via_drill_mm = self._float(self.via_drill, 0.3)
        s.clearance_mm = self._float(self.clearance, 0.25)
        s.min_via_spacing_mm = self._float(self.min_spacing, 0.5)
        s.use_zone_net = self.use_zone_net.GetValue()
        s.net_name = self.net_combo.GetValue().strip() or "GND"
        s.layer_top = self._layer_ids[self.layer_top.GetSelection()]
        s.layer_bottom = self._layer_ids[self.layer_bottom.GetSelection()]
        return s

    @staticmethod
    def _float(ctrl: wx.TextCtrl, default: float) -> float:
        try:
            return float(ctrl.GetValue().replace(",", "."))
        except (TypeError, ValueError):
            return default

    # -- event handlers ---------------------------------------------------

    def on_apply(self, _event) -> None:
        s = self._collect_settings()
        if s.layer_top == s.layer_bottom:
            wx.MessageBox(
                "Top and bottom layers must differ for a through-via.",
                "Via Stitching",
                wx.OK | wx.ICON_WARNING,
            )
            return

        self._save_preset(s)
        self.status.SetLabel("Stitching...")
        wx.SafeYield()

        stitcher = ViaStitcher(self.board, s)
        try:
            n = stitcher.run()
        except RuntimeError as e:
            wx.MessageBox(str(e), "Via Stitching", wx.OK | wx.ICON_WARNING)
            self.status.SetLabel("No vias placed.")
            return
        except Exception as e:
            import traceback

            wx.MessageBox(
                f"Stitching failed:\n\n{traceback.format_exc()}",
                "Via Stitching",
                wx.OK | wx.ICON_ERROR,
            )
            self.status.SetLabel(f"Error: {e}")
            return

        # Update connectivity + redraw
        try:
            self.board.BuildConnectivity()
        except Exception:
            pass
        try:
            pcbnew.Refresh()
        except Exception:
            pass

        self.last_run = stitcher
        self.undo_btn.Enable(n > 0)
        self.status.SetLabel(f"Placed {n} via{'s' if n != 1 else ''}.")

    def on_undo(self, _event) -> None:
        if self.last_run is None:
            return
        n = self.last_run.undo_last_run()
        try:
            self.board.BuildConnectivity()
        except Exception:
            pass
        try:
            pcbnew.Refresh()
        except Exception:
            pass
        self.last_run = None
        self.undo_btn.Disable()
        self.status.SetLabel(f"Removed {n} via{'s' if n != 1 else ''}.")
