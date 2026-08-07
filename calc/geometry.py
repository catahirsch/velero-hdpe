"""Hull geometry: parametric stations, and exact area/centroid at any heel.

The hull is described as a set of transverse stations, each a closed polygon in
the (y, z) plane running keel -> chine -> sheer -> deck crown -> and back down
the other side. Closing the section over the deck is what makes it possible to
compute buoyancy at large heel and when inverted; a hull described only up to
the sheer has no answer at 140 degrees.

Buoyancy at heel is computed by rotating each station into the earth frame and
clipping it against the horizontal waterplane with Sutherland-Hodgman. Clipping
a simple polygon against a single half-plane leaves any degenerate edges lying
exactly along the clip line, where they contribute zero to the shoelace area and
to the area-weighted centroid -- so area and centroid come out exact without
needing a general-purpose geometry library.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator

from .params import Cockpit, Hull

RHO_LEAD = 11340.0  # kg/m^3


# ---------------------------------------------------------------------------
# Polygon primitives
# ---------------------------------------------------------------------------


def polygon_area_centroid(pts: np.ndarray) -> tuple[float, float, float]:
    """Return (area, centroid_y, centroid_z) for a closed polygon.

    ``pts`` is (n, 2) of (y, z), implicitly closed. Area is unsigned. Returns
    zeros for degenerate input.
    """
    if len(pts) < 3:
        return 0.0, 0.0, 0.0
    y = pts[:, 0]
    z = pts[:, 1]
    y2 = np.roll(y, -1)
    z2 = np.roll(z, -1)
    cross = y * z2 - y2 * z
    a2 = cross.sum()
    if abs(a2) < 1e-14:
        return 0.0, 0.0, 0.0
    area = a2 / 2.0
    cy = ((y + y2) * cross).sum() / (3.0 * a2)
    cz = ((z + z2) * cross).sum() / (3.0 * a2)
    return abs(area), cy, cz


def clip_below(pts: np.ndarray, z_cut: float) -> np.ndarray:
    """Clip a closed polygon to the half-plane z <= z_cut (Sutherland-Hodgman)."""
    if len(pts) < 3:
        return np.empty((0, 2))
    out: list[tuple[float, float]] = []
    n = len(pts)
    for i in range(n):
        cur = pts[i]
        nxt = pts[(i + 1) % n]
        cur_in = cur[1] <= z_cut
        nxt_in = nxt[1] <= z_cut
        if cur_in:
            out.append((cur[0], cur[1]))
        if cur_in != nxt_in:
            dz = nxt[1] - cur[1]
            if abs(dz) > 1e-15:
                t = (z_cut - cur[1]) / dz
                out.append((cur[0] + t * (nxt[0] - cur[0]), z_cut))
    return np.asarray(out, dtype=float) if out else np.empty((0, 2))


def rotate(pts: np.ndarray, heel_deg: float) -> np.ndarray:
    """Rotate body-frame (y, z) into the earth frame for a starboard heel.

    A masthead point (0, h) moves to (+h, 0) at 90 degrees, i.e. to starboard.
    """
    phi = np.radians(heel_deg)
    c, s = np.cos(phi), np.sin(phi)
    y, z = pts[:, 0], pts[:, 1]
    return np.column_stack([y * c + z * s, -y * s + z * c])


def rotate_point(y: float, z: float, heel_deg: float) -> tuple[float, float]:
    phi = np.radians(heel_deg)
    c, s = np.cos(phi), np.sin(phi)
    return y * c + z * s, -y * s + z * c


# ---------------------------------------------------------------------------
# Station generation
# ---------------------------------------------------------------------------


def _interp(curve: list[tuple[float, float]]) -> PchipInterpolator:
    t = np.array([p[0] for p in curve], dtype=float)
    v = np.array([p[1] for p in curve], dtype=float)
    return PchipInterpolator(t, v, extrapolate=True)


class HullGeometry:
    """Discretised hull, ready for hydrostatics."""

    def __init__(self, hull: Hull, cockpit: Cockpit):
        self.hull = hull
        self.cockpit = cockpit

        n = hull.n_stations if hull.n_stations % 2 == 1 else hull.n_stations + 1
        self.x = np.linspace(0.0, hull.loa, n)
        # Station parameter runs on LWL; the small overhang forward is clamped.
        t = np.clip(self.x / hull.lwl, 0.0, 1.0)

        f_sheer_b = _interp(hull.sheer_beam_curve)
        f_chine_b = _interp(hull.chine_beam_curve)
        f_keel_z = _interp(hull.keel_curve)
        f_sheer_z = _interp(hull.sheer_curve)

        half_sheer = hull.beam_sheer / 2.0
        half_chine = half_sheer * hull.beam_chine_frac

        self.y_sheer = np.clip(f_sheer_b(t), 0.0, None) * half_sheer
        self.y_chine = np.clip(f_chine_b(t), 0.0, None) * half_chine
        self.z_keel = f_keel_z(t)
        self.z_sheer = f_sheer_z(t)

        # Chine sits a fixed fraction of the local depth above the keel line.
        depth = self.z_sheer - self.z_keel
        self.z_chine = self.z_keel + hull.deadrise_frac * depth
        self.z_crown = self.z_sheer + hull.deck_camber

        # Keep the chine inboard of the sheer so sections stay convex.
        self.y_chine = np.minimum(self.y_chine, self.y_sheer * 0.98)

        self._sections = [self._section(i) for i in range(len(self.x))]
        self._voids = [self._cockpit_void(i) for i in range(len(self.x))]

    # -- section builders ---------------------------------------------------

    def _section(self, i: int) -> np.ndarray:
        """Closed hull section: keel -> chine -> sheer -> crown -> mirrored."""
        ys, yc = self.y_sheer[i], self.y_chine[i]
        zk, zc, zs, zx = (
            self.z_keel[i],
            self.z_chine[i],
            self.z_sheer[i],
            self.z_crown[i],
        )
        if ys < 1e-6:
            return np.empty((0, 2))
        return np.array(
            [
                [0.0, zk],
                [yc, zc],
                [ys, zs],
                [0.0, zx],
                [-ys, zs],
                [-yc, zc],
            ],
            dtype=float,
        )

    def _deck_z_at(self, i: int, y: float) -> float:
        """Deck height at offset |y|, linear from crown to sheer."""
        ys = self.y_sheer[i]
        if ys < 1e-9:
            return self.z_crown[i]
        f = min(abs(y) / ys, 1.0)
        return self.z_crown[i] + f * (self.z_sheer[i] - self.z_crown[i])

    def _cockpit_void(self, i: int) -> np.ndarray:
        """The floodable cockpit volume at this station, or empty.

        The bench boxes along each side are sealed (they are the water ballast
        tanks and the reserve buoyancy), so the floodable region is the
        footwell between them plus the volume above the bench tops -- a
        T-shaped section, not the full cockpit box.
        """
        cp = self.cockpit
        if not (cp.x_aft <= self.x[i] <= cp.x_fwd):
            return np.empty((0, 2))
        yw = min(cp.half_width, self.y_sheer[i] * 0.95)
        if yw < 1e-6 or cp.sole_z >= self._deck_z_at(i, yw) - 1e-6:
            return np.empty((0, 2))
        z_top_edge = self._deck_z_at(i, yw)
        z_top_mid = self._deck_z_at(i, 0.0)
        yf = min(cp.bench_inner_y, yw)  # footwell half-width
        zb = cp.bench_top_z
        if zb <= cp.sole_z or yf >= yw - 1e-6 or zb >= z_top_edge:
            # no meaningful bench: fall back to the full box
            return np.array(
                [
                    [-yw, cp.sole_z],
                    [yw, cp.sole_z],
                    [yw, z_top_edge],
                    [0.0, z_top_mid],
                    [-yw, z_top_edge],
                ],
                dtype=float,
            )
        return np.array(
            [
                [-yf, cp.sole_z],
                [yf, cp.sole_z],
                [yf, zb],
                [yw, zb],
                [yw, z_top_edge],
                [0.0, z_top_mid],
                [-yw, z_top_edge],
                [-yw, zb],
                [-yf, zb],
            ],
            dtype=float,
        )

    # -- integration -------------------------------------------------------

    def submerged_areas(
        self, z_wl: float, heel_deg: float, flooded: bool
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Per-station submerged area and centroid, in the earth frame."""
        n = len(self.x)
        area = np.zeros(n)
        cy = np.zeros(n)
        cz = np.zeros(n)
        for i in range(n):
            sec = self._sections[i]
            if len(sec) < 3:
                continue
            clipped = clip_below(rotate(sec, heel_deg), z_wl)
            a, y_c, z_c = polygon_area_centroid(clipped)
            if a <= 0.0:
                continue
            my, mz = a * y_c, a * z_c
            if flooded:
                void = self._voids[i]
                if len(void) >= 3 and self._void_is_open(i, z_wl, heel_deg):
                    vc = clip_below(rotate(void, heel_deg), z_wl)
                    av, yv, zv = polygon_area_centroid(vc)
                    if av > 0.0:
                        a -= av
                        my -= av * yv
                        mz -= av * zv
            if a <= 1e-9:
                area[i] = 0.0
                continue
            area[i] = a
            cy[i] = my / a
            cz[i] = mz / a
        return area, cy, cz

    def _void_is_open(self, i: int, z_wl: float, heel_deg: float) -> bool:
        """True if the cockpit opening is immersed at this station, so it floods."""
        yw = min(self.cockpit.half_width, self.y_sheer[i] * 0.95)
        for y in (yw, -yw, 0.0):
            _, z_e = rotate_point(y, self._deck_z_at(i, y), heel_deg)
            if z_e < z_wl:
                return True
        return False

    def volume(
        self, z_wl: float, heel_deg: float, flooded: bool = False
    ) -> tuple[float, float, float, float]:
        """Return (volume, LCB_x, y_B, z_B) in earth frame for y/z."""
        area, cy, cz = self.submerged_areas(z_wl, heel_deg, flooded)
        vol = float(np.trapezoid(area, self.x))
        if vol <= 1e-9:
            return 0.0, 0.0, 0.0, 0.0
        lcb = float(np.trapezoid(area * self.x, self.x) / vol)
        y_b = float(np.trapezoid(area * cy, self.x) / vol)
        z_b = float(np.trapezoid(area * cz, self.x) / vol)
        return vol, lcb, y_b, z_b

    def waterplane_area(self, z_wl: float, heel_deg: float = 0.0) -> float:
        """Waterplane area, for sinkage per unit immersion."""
        widths = np.zeros(len(self.x))
        for i in range(len(self.x)):
            sec = self._sections[i]
            if len(sec) < 3:
                continue
            clipped = clip_below(rotate(sec, heel_deg), z_wl)
            if len(clipped) < 3:
                continue
            on = np.isclose(clipped[:, 1], z_wl, atol=1e-9)
            if on.sum() >= 2:
                ys = clipped[on][:, 0]
                widths[i] = float(ys.max() - ys.min())
        return float(np.trapezoid(widths, self.x))

    # -- areas for the weight budget --------------------------------------

    def shell_area(self) -> float:
        """Girth-integrated hull shell area, keel to sheer, both sides."""
        girth = np.zeros(len(self.x))
        for i in range(len(self.x)):
            if self.y_sheer[i] < 1e-6:
                continue
            p_keel = np.array([0.0, self.z_keel[i]])
            p_chine = np.array([self.y_chine[i], self.z_chine[i]])
            p_sheer = np.array([self.y_sheer[i], self.z_sheer[i]])
            girth[i] = 2.0 * (
                np.linalg.norm(p_chine - p_keel) + np.linalg.norm(p_sheer - p_chine)
            )
        return float(np.trapezoid(girth, self.x))

    def deck_area(self) -> float:
        """Deck plus cockpit sole and cockpit sides."""
        deck = np.zeros(len(self.x))
        sole = np.zeros(len(self.x))
        sides = np.zeros(len(self.x))
        cp = self.cockpit
        for i, x in enumerate(self.x):
            ys = self.y_sheer[i]
            if ys < 1e-6:
                continue
            crown_len = 2.0 * np.hypot(ys, self.z_crown[i] - self.z_sheer[i])
            in_cockpit = cp.x_aft <= x <= cp.x_fwd
            yw = min(cp.half_width, ys * 0.95) if in_cockpit else 0.0
            # Side decks only, where the cockpit is open.
            deck[i] = crown_len * (1.0 - (yw / ys if ys > 0 else 0.0))
            if in_cockpit:
                sole[i] = 2.0 * yw
                sides[i] = 2.0 * max(self._deck_z_at(i, yw) - cp.sole_z, 0.0)
        return float(
            np.trapezoid(deck, self.x)
            + np.trapezoid(sole, self.x)
            + np.trapezoid(sides, self.x)
        )

    # -- convenience -------------------------------------------------------

    @property
    def max_beam(self) -> float:
        return 2.0 * float(self.y_sheer.max())

    def keel_appendage_volume(self, keel_mass: float) -> float:
        """Displaced volume of a lead keel of the given mass."""
        return keel_mass / RHO_LEAD
