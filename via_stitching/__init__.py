# Via Stitching - KiCad Action Plugin
# Registers the plugin so KiCad's pcbnew picks it up at startup.

from .plugin import ViaStitchingPlugin

ViaStitchingPlugin().register()
