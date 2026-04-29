"""
Via Stitching - KiCad ActionPlugin entry point.

Tested against the KiCad 9 pcbnew Python API. KiCad 10 keeps the same
ActionPlugin interface; if you hit an attribute error in KiCad 10+, see
README.md for the API-shim notes.
"""
import os
import traceback

import pcbnew
import wx


class ViaStitchingPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Via Stitching"
        self.category = "Modify PCB"
        self.description = (
            "Place stitching vias in patterns: grid, staggered/hex, "
            "perimeter along Edge.Cuts, or along selected tracks. "
            "Constrains to selected zones and respects clearance."
        )
        self.show_toolbar_button = True
        self.icon_file_name = ""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.isfile(icon_path):
            self.icon_file_name = icon_path

    def Run(self):
        # Imported lazily so KiCad can still load the plugin even if wx is
        # being weird at startup.
        try:
            from .stitcher_dialog import StitcherDialog
        except Exception:
            wx.MessageBox(
                "Failed to import Via Stitching dialog:\n\n"
                + traceback.format_exc(),
                "Via Stitching",
                wx.OK | wx.ICON_ERROR,
            )
            return

        board = pcbnew.GetBoard()
        if board is None:
            wx.MessageBox(
                "No board is open in pcbnew.",
                "Via Stitching",
                wx.OK | wx.ICON_WARNING,
            )
            return

        parent = wx.GetActiveWindow()
        try:
            dlg = StitcherDialog(parent, board)
            dlg.ShowModal()
            dlg.Destroy()
        except Exception:
            wx.MessageBox(
                "Via Stitching crashed:\n\n" + traceback.format_exc(),
                "Via Stitching",
                wx.OK | wx.ICON_ERROR,
            )
