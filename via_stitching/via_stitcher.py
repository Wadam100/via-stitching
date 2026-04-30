"""
Core via-stitching algorithms.

All public coordinates are in KiCad internal units (nm). Use ``mm()`` /
``to_mm()`` to convert to/from millimetres.
"""
from __future__ import annotations

import math

import pcbnew


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def mm(v: float) -> int:
    """Millimetres -> KiCad internal units (nm)."""
    return pcbnew.FromMM(v)


def to_mm(iu: int) -> float:
    """KiCad internal units (nm) -> millimetres."""
    return pcbnew.ToMM(iu)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class StitchSettings:
    """All user-configurable knobs for one stitching run."""

    PATTERNS = ("grid", "staggered", "perimeter", "tracks")

    def __init__(self) -> None:
        self.pattern: str = "grid"
        self.pitch_mm: float = 2.54
        self.via_diameter_mm: float = 0.6
        self.via_drill_mm: float = 0.3
        self.clearance_mm: float = 0.25
        self.edge_clearance_mm: float = 0.5
        self.dry_run: bool = False


# ---------------------------------------------------------------------------
# Stitcher
# ---------------------------------------------------------------------------

class ViaStitcher:
    def __init__(self, board: "pcbnew.BOARD", settings: StitchSettings) -> None:
        self.board = board
        self.s = settings
        self.added: list = []
        # Cache of newly placed positions for fast self-collision checks.
        self._placed_positions: list[tuple[int, int]] = []
        # Lazily populated on first clearance check; reused for the whole run.
        self._edge_chords_cache: list | None = None
        # PCB_GROUP that all vias placed in this run get added to.
        self._group = None

    # -- selection helpers ------------------------------------------------

    def selected_zones(self) -> list:
        return [z for z in self.board.Zones() if z.IsSelected()]

    def selected_tracks(self) -> list:
        out = []
        for t in self.board.GetTracks():
            # Skip vias; we only walk along tracks.
            if isinstance(t, pcbnew.PCB_VIA):
                continue
            if t.IsSelected():
                out.append(t)
        return out

    # -- net resolution ---------------------------------------------------

    def resolve_net(self, zone=None):
        if zone is not None:
            return zone.GetNet()
        # Perimeter pattern: no zone, fall back to GND else net 0.
        return self.board.FindNet("GND") or self.board.FindNet(0)

    def _net_code(self, zone=None) -> int:
        net = self.resolve_net(zone)
        return net.GetNetCode() if net is not None else 0

    # -- pattern entry points --------------------------------------------

    def run(self) -> int:
        # Fresh group for this run; only added to the board if we actually
        # place at least one via.
        self._group = self._make_group() if not self.s.dry_run else None

        p = self.s.pattern
        if p == "grid":
            n = self._stitch_zones(staggered=False)
        elif p == "staggered":
            n = self._stitch_zones(staggered=True)
        elif p == "perimeter":
            n = self._stitch_perimeter()
        elif p == "tracks":
            n = self._stitch_along_tracks()
        else:
            raise ValueError(f"Unknown pattern: {p!r}")

        # If we ended up adding vias, attach the group to the board.
        if n > 0 and self._group is not None:
            try:
                self.board.Add(self._group)
            except Exception:
                self._group = None
        else:
            self._group = None
        return n

    def _make_group(self):
        """Create a PCB_GROUP named for this run, or return None if the
        running KiCad version doesn't expose PCB_GROUP."""
        if not hasattr(pcbnew, "PCB_GROUP"):
            return None
        try:
            g = pcbnew.PCB_GROUP(self.board)
            label = self._group_name()
            try:
                g.SetName(label)
            except Exception:
                pass
            return g
        except Exception:
            return None

    def _group_name(self) -> str:
        pattern_label = {
            "grid": "Grid",
            "staggered": "Hex",
            "perimeter": "Perimeter",
            "tracks": "Tracks",
        }.get(self.s.pattern, self.s.pattern)
        return f"Stitching: {pattern_label}"

    # -- area patterns (grid + staggered) --------------------------------

    def _stitch_zones(self, staggered: bool) -> int:
        zones = self.selected_zones()
        if not zones:
            raise RuntimeError(
                "No zones selected. Select one or more copper zones in pcbnew "
                "before running."
            )
        clearance_iu = mm(self.s.clearance_mm)
        count = 0
        for zone in zones:
            net = self.resolve_net(zone)
            count += self._stitch_one_zone(zone, net, clearance_iu, staggered)
        return count

    def _stitch_one_zone(self, zone, net, clearance_iu: int, staggered: bool) -> int:
        outline = self._zone_polygon(zone)
        if outline is None or outline.IsEmpty():
            return 0
        bbox = zone.GetBoundingBox()
        x0, y0 = bbox.GetLeft(), bbox.GetTop()
        x1, y1 = bbox.GetRight(), bbox.GetBottom()
        px = mm(self.s.pitch_mm)
        py = mm(self.s.pitch_mm)
        if staggered:
            # Hex packing: row spacing = py * sqrt(3)/2
            py = int(py * math.sqrt(3) / 2)

        net_code = net.GetNetCode() if net is not None else 0
        count = 0
        row = 0
        y = y0
        while y <= y1:
            x_offset = (px // 2) if (staggered and row % 2 == 1) else 0
            x = x0 + x_offset
            while x <= x1:
                pos = pcbnew.VECTOR2I(int(x), int(y))
                if self._inside_polygon(outline, pos) and self._clear_of_obstacles(
                    pos, net_code, clearance_iu
                ):
                    self._add_via(pos, net)
                    count += 1
                x += px
            y += py
            row += 1
        return count

    # -- perimeter pattern (along Edge.Cuts) -----------------------------

    def _stitch_perimeter(self) -> int:
        net = self.resolve_net()
        net_code = net.GetNetCode() if net is not None else 0
        clearance_iu = mm(self.s.clearance_mm)
        pitch = mm(self.s.pitch_mm)
        count = 0
        for a, b in self._collect_edge_chords():
            count += self._walk_segment(a, b, pitch, net, net_code, clearance_iu)
        return count

    def _collect_edge_chords(self) -> list:
        """Return [(start, end), ...] approximating Edge.Cuts as straight chords."""
        chords: list = []
        for d in self.board.GetDrawings():
            if d.GetLayer() != pcbnew.Edge_Cuts:
                continue
            shape = d.GetShape() if hasattr(d, "GetShape") else None
            if shape == pcbnew.S_SEGMENT:
                chords.append((d.GetStart(), d.GetEnd()))
            elif shape == pcbnew.S_ARC:
                chords.extend(self._arc_to_chords(d))
            elif shape == pcbnew.S_CIRCLE:
                chords.extend(self._circle_to_chords(d))
            elif shape == pcbnew.S_RECT:
                p0 = d.GetStart()
                p1 = d.GetEnd()
                tl = pcbnew.VECTOR2I(p0.x, p0.y)
                tr = pcbnew.VECTOR2I(p1.x, p0.y)
                br = pcbnew.VECTOR2I(p1.x, p1.y)
                bl = pcbnew.VECTOR2I(p0.x, p1.y)
                chords.extend([(tl, tr), (tr, br), (br, bl), (bl, tl)])
            elif shape == pcbnew.S_POLYGON:
                # Walk the polygon outline as chords
                poly = d.GetPolyShape() if hasattr(d, "GetPolyShape") else None
                if poly is not None:
                    for outline_idx in range(poly.OutlineCount()):
                        pts = poly.Outline(outline_idx)
                        n = pts.PointCount()
                        for i in range(n):
                            a = pts.CPoint(i)
                            b = pts.CPoint((i + 1) % n)
                            chords.append(
                                (
                                    pcbnew.VECTOR2I(a.x, a.y),
                                    pcbnew.VECTOR2I(b.x, b.y),
                                )
                            )
            else:
                # Last resort: treat as a single segment from start to end
                if hasattr(d, "GetStart") and hasattr(d, "GetEnd"):
                    chords.append((d.GetStart(), d.GetEnd()))
        return chords

    def _arc_to_chords(self, drawing) -> list:
        center = drawing.GetCenter()
        start = drawing.GetStart()
        end = drawing.GetEnd()
        radius = math.hypot(start.x - center.x, start.y - center.y)
        a0 = math.atan2(start.y - center.y, start.x - center.x)
        a1 = math.atan2(end.y - center.y, end.x - center.x)
        # Normalise to a positive sweep, choosing the short way unless KiCad
        # tells us otherwise.
        sweep = a1 - a0
        # KiCad arcs have a defined direction; query if available
        try:
            angle = drawing.GetArcAngle().AsRadians()
            sweep = angle if angle != 0 else sweep
        except Exception:
            pass
        if sweep == 0:
            return []
        # Step roughly every 0.5 mm along the arc
        step_len = mm(0.5)
        steps = max(8, int(abs(sweep) * radius / step_len))
        out = []
        prev = start
        for k in range(1, steps + 1):
            t = a0 + sweep * (k / steps)
            nxt = pcbnew.VECTOR2I(
                int(center.x + radius * math.cos(t)),
                int(center.y + radius * math.sin(t)),
            )
            out.append((prev, nxt))
            prev = nxt
        return out

    def _circle_to_chords(self, drawing) -> list:
        center = drawing.GetCenter()
        # KiCad: a circle's "end" point lies on the circumference
        end = drawing.GetEnd() if hasattr(drawing, "GetEnd") else drawing.GetStart()
        radius = math.hypot(end.x - center.x, end.y - center.y)
        step_len = mm(0.5)
        steps = max(16, int(2 * math.pi * radius / step_len))
        out = []
        prev = pcbnew.VECTOR2I(int(center.x + radius), int(center.y))
        for k in range(1, steps + 1):
            t = 2 * math.pi * k / steps
            nxt = pcbnew.VECTOR2I(
                int(center.x + radius * math.cos(t)),
                int(center.y + radius * math.sin(t)),
            )
            out.append((prev, nxt))
            prev = nxt
        return out

    # -- along-tracks pattern --------------------------------------------

    def _stitch_along_tracks(self) -> int:
        tracks = self.selected_tracks()
        if not tracks:
            raise RuntimeError(
                "No tracks selected. Select one or more tracks in pcbnew "
                "before running the 'along selected tracks' pattern."
            )
        clearance_iu = mm(self.s.clearance_mm)
        pitch = mm(self.s.pitch_mm)
        count = 0
        for tr in tracks:
            net = tr.GetNet()
            net_code = net.GetNetCode() if net is not None else 0
            count += self._walk_segment(
                tr.GetStart(), tr.GetEnd(), pitch, net, net_code, clearance_iu
            )
        return count

    # -- shared segment walker -------------------------------------------

    def _walk_segment(self, a, b, pitch_iu, net, net_code, clearance_iu) -> int:
        dx = b.x - a.x
        dy = b.y - a.y
        length = math.hypot(dx, dy)
        if length < 1 or pitch_iu <= 0:
            return 0
        ux = dx / length
        uy = dy / length
        n_steps = int(length // pitch_iu)
        count = 0
        for i in range(n_steps + 1):
            x = a.x + ux * pitch_iu * i
            y = a.y + uy * pitch_iu * i
            pos = pcbnew.VECTOR2I(int(x), int(y))
            if self._clear_of_obstacles(pos, net_code, clearance_iu):
                self._add_via(pos, net)
                count += 1
        return count

    # -- geometry helpers ------------------------------------------------

    def _zone_polygon(self, zone):
        """Best-effort SHAPE_POLY_SET for a zone (filled if available, else
        outline)."""
        # Try the filled polys on the top layer first — they reflect actual
        # copper after avoidances.
        try:
            layers = zone.GetLayerSet().Seq()
        except Exception:
            layers = [pcbnew.F_Cu]
        for layer in layers:
            try:
                polys = zone.GetFilledPolysList(layer)
            except Exception:
                polys = None
            if polys is not None and not polys.IsEmpty():
                return polys
        # Fall back to user outline
        try:
            return zone.Outline()
        except Exception:
            return None

    @staticmethod
    def _inside_polygon(poly, pos) -> bool:
        try:
            return bool(poly.Contains(pos))
        except Exception:
            try:
                return bool(poly.Contains(pcbnew.VECTOR2I(pos.x, pos.y)))
            except Exception:
                return False

    @staticmethod
    def _point_to_seg_dist(p, a, b) -> float:
        ax, ay = a.x, a.y
        bx, by = b.x, b.y
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(p.x - ax, p.y - ay)
        t = ((p.x - ax) * dx + (p.y - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        cx = ax + t * dx
        cy = ay + t * dy
        return math.hypot(p.x - cx, p.y - cy)

    def _clear_of_obstacles(self, pos, my_net_code: int, clearance_iu: int) -> bool:
        via_r = mm(self.s.via_diameter_mm) // 2
        foreign_min = via_r + clearance_iu
        # Min centre-to-centre between any two vias = via diameter + clearance.
        spacing_iu = via_r * 2 + clearance_iu

        # Self-collision against newly placed vias (any net)
        for (px, py) in self._placed_positions:
            if math.hypot(px - pos.x, py - pos.y) < spacing_iu:
                return False

        # Existing tracks + vias
        for t in self.board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                tp = t.GetPosition()
                d = math.hypot(tp.x - pos.x, tp.y - pos.y)
                if t.GetNetCode() == my_net_code:
                    if d < spacing_iu:
                        return False
                else:
                    if d < (foreign_min + t.GetWidth() // 2):
                        return False
            else:
                d = self._point_to_seg_dist(pos, t.GetStart(), t.GetEnd())
                t_r = t.GetWidth() // 2
                if t.GetNetCode() == my_net_code:
                    # same-net track is fine to be near; vias are through
                    # all layers anyway.
                    pass
                else:
                    if d < (foreign_min + t_r):
                        return False

        # Pads
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                pp = pad.GetPosition()
                pw = max(pad.GetSize().x, pad.GetSize().y) // 2
                d = math.hypot(pp.x - pos.x, pp.y - pos.y)
                if pad.GetNetCode() == my_net_code:
                    # Don't drop a via inside a same-net pad (creates a mess).
                    if d < (via_r + pw):
                        return False
                else:
                    if d < (foreign_min + pw):
                        return False

        # Board edge clearance
        if self.s.edge_clearance_mm > 0:
            edge_iu = mm(self.s.edge_clearance_mm)
            if self._edge_chords_cache is None:
                self._edge_chords_cache = self._collect_edge_chords()
            for a, b in self._edge_chords_cache:
                if self._point_to_seg_dist(pos, a, b) < edge_iu:
                    return False

        return True

    # -- mutation --------------------------------------------------------

    def _add_via(self, pos, net) -> None:
        self._placed_positions.append((pos.x, pos.y))
        if self.s.dry_run:
            self.added.append(("DRY", pos.x, pos.y))
            return
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(pos)
        via.SetWidth(mm(self.s.via_diameter_mm))
        via.SetDrill(mm(self.s.via_drill_mm))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        if net is not None:
            via.SetNet(net)
        self.board.Add(via)
        self.added.append(via)
        # Add to the run's group so the user can select/move/delete them
        # together. Tolerate older KiCad APIs where AddItem is missing.
        if self._group is not None:
            try:
                self._group.AddItem(via)
            except Exception:
                try:
                    via.SetParentGroup(self._group)
                except Exception:
                    pass

    def undo_last_run(self) -> int:
        """Remove vias added in the most recent ``run()`` (and the group)."""
        n = 0
        for via in self.added:
            if isinstance(via, tuple):  # dry-run sentinel
                continue
            try:
                # Detach from group first so Remove() doesn't trip over it
                # on some KiCad versions.
                try:
                    via.SetParentGroup(None)
                except Exception:
                    pass
                self.board.Remove(via)
                n += 1
            except Exception:
                pass
        if self._group is not None:
            try:
                self.board.Remove(self._group)
            except Exception:
                pass
            self._group = None
        self.added.clear()
        self._placed_positions.clear()
        return n
