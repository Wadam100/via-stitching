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
            size=wx.Size(400, 460),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.board = board
        self.last_run: ViaStitcher | None = None

        settings = self._load_preset()
        self._build_ui(settings)
        self.Layout()
        self.Fit()
        self.SetMinSize(wx.Size(360, 420))

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

        self.pitch = self._add_float_row(grid, "Pitch", s.pitch_mm)
        self.via_diam = self._add_float_row(grid, "Via diameter", s.via_diameter_mm)
        self.via_drill = self._add_float_row(grid, "Via drill", s.via_drill_mm)
        self.clearance = self._add_float_row(grid, "Clearance to other nets", s.clearance_mm)
        self.edge_clearance = self._add_float_row(grid, "Board edge clearance", s.edge_clearance_mm)
        geo.Add(grid, 0, wx.EXPAND | wx.ALL, pad)
        outer.Add(geo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

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
        s.pitch_mm = self._float(self.pitch, 2.54)
        s.via_diameter_mm = self._float(self.via_diam, 0.6)
        s.via_drill_mm = self._float(self.via_drill, 0.3)
        s.clearance_mm = self._float(self.clearance, 0.25)
        s.edge_clearance_mm = self._float(self.edge_clearance, 0.5)
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
