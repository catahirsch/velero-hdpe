"""Hydrostatics and the righting-arm curve, 0 to 180 degrees.

Two curves are produced for every case, and the difference between them is the
whole argument about self-righting in an open boat:

  intact   -- the cockpit is treated as watertight all the way round. This is
              the optimistic curve, and it is the one a spec sheet usually
              quotes. It is valid only up to the downflooding angle.
  flooded  -- the cockpit floods as soon as its opening immerses, and stays
              flooded. Beyond the downflooding angle this is the real curve.

A boat self-rights from fully inverted if and only if GZ stays positive for
every angle in (0, 180). At exactly 180 degrees GZ is zero by symmetry, so the
test is the sign just short of it: GZ < 0 near 180 means there is a stable
inverted equilibrium and the boat stays upside down.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import HullGeometry, rotate, rotate_point
from .params import RHO_SEA, Design

RHO_LEAD = 11340.0


@dataclass
class Hydrostatics:
    displacement: float  # kg
    volume: float  # m^3
    draft: float  # m, below waterline at the deepest canoe-body point
    z_wl: float  # m above baseline
    lcb: float  # m from transom
    waterplane_area: float  # m^2
    tpc: float  # kg per cm immersion


@dataclass
class GZCurve:
    heel: np.ndarray  # deg
    gz: np.ndarray  # m
    label: str
    downflooding_angle: float | None
    afloat: np.ndarray  # bool per angle: could a waterline be found at all

    @property
    def gz_max(self) -> float:
        valid = self.gz[np.isfinite(self.gz)]
        return float(valid.max()) if valid.size else float("nan")

    @property
    def angle_gz_max(self) -> float:
        g = np.where(np.isfinite(self.gz), self.gz, -np.inf)
        return float(self.heel[int(np.argmax(g))])

    @property
    def avs(self) -> float:
        """Angle of vanishing stability: first zero crossing after peak GZ."""
        i_peak = int(np.argmax(np.where(np.isfinite(self.gz), self.gz, -np.inf)))
        for i in range(i_peak, len(self.heel) - 1):
            a, b = self.gz[i], self.gz[i + 1]
            if not (np.isfinite(a) and np.isfinite(b)):
                continue
            if a > 0.0 >= b:
                frac = a / (a - b)
                return float(self.heel[i] + frac * (self.heel[i + 1] - self.heel[i]))
        return 180.0

    @property
    def self_righting(self) -> bool:
        """True if GZ never goes negative before 180 degrees."""
        interior = (self.heel > 1.0) & (self.heel < 179.0)
        g = self.gz[interior]
        g = g[np.isfinite(g)]
        return bool(g.size and (g > 0.0).all())

    def area_under(self, lo: float, hi: float) -> float:
        """Dynamic stability, in m.rad, between two heel angles."""
        m = (self.heel >= lo) & (self.heel <= hi) & np.isfinite(self.gz)
        if m.sum() < 2:
            return 0.0
        return float(np.trapezoid(self.gz[m], np.radians(self.heel[m])))

    @property
    def negative_area(self) -> float:
        """Energy holding the boat inverted, m.rad. Zero if self-righting."""
        g = np.where(np.isfinite(self.gz), self.gz, 0.0)
        neg = np.minimum(g, 0.0)
        return float(abs(np.trapezoid(neg, np.radians(self.heel))))


def _keel_centroid_body(design: Design) -> tuple[float, float]:
    """Ballast centroid in the body frame (y, z). Below baseline, so z < 0."""
    return 0.0, -design.ballast.keel_vcg_below_bl


def solve_waterline(
    geom: HullGeometry,
    target_volume: float,
    heel_deg: float,
    flooded: bool,
    keel_volume: float = 0.0,
) -> float | None:
    """Bisect for the waterplane height that displaces ``target_volume``.

    Returns None if the hull cannot displace that much at this heel -- which is
    the honest answer for a flooded open boat at large heel: it does not float
    at its design displacement, it settles until something else changes.
    """
    hull_target = target_volume - keel_volume
    if hull_target <= 0.0:
        return None

    all_z = []
    for sec in geom._sections:
        if len(sec) >= 3:
            all_z.append(rotate(sec, heel_deg)[:, 1])
    if not all_z:
        return None
    z_lo = float(np.min([z.min() for z in all_z])) - 0.05
    z_hi = float(np.max([z.max() for z in all_z])) + 0.05

    v_hi = geom.volume(z_hi, heel_deg, flooded)[0]
    if v_hi < hull_target:
        return None  # fully submerged and still not enough buoyancy

    for _ in range(70):
        z_mid = 0.5 * (z_lo + z_hi)
        v = geom.volume(z_mid, heel_deg, flooded)[0]
        if v < hull_target:
            z_lo = z_mid
        else:
            z_hi = z_mid
        if z_hi - z_lo < 1e-7:
            break
    return 0.5 * (z_lo + z_hi)


def upright_hydrostatics(
    geom: HullGeometry, design: Design, mass: float
) -> Hydrostatics | None:
    """Upright floating condition at the given mass."""
    keel_vol = geom.keel_appendage_volume(design.ballast.keel_mass)
    target = mass / RHO_SEA
    z_wl = solve_waterline(geom, target, 0.0, flooded=False, keel_volume=keel_vol)
    if z_wl is None:
        return None
    vol, lcb, _, _ = geom.volume(z_wl, 0.0, False)
    awp = geom.waterplane_area(z_wl, 0.0)
    return Hydrostatics(
        displacement=mass,
        volume=vol + keel_vol,
        draft=z_wl - float(geom.z_keel.min()),
        z_wl=z_wl,
        lcb=lcb,
        waterplane_area=awp,
        tpc=awp * RHO_SEA / 100.0,
    )


def downflooding_angle(geom: HullGeometry, design: Design, mass: float) -> float | None:
    """Heel at which the cockpit opening first immerses.

    For an open boat this is early, and it is the moment the intact curve stops
    being the curve that matters.
    """
    keel_vol = geom.keel_appendage_volume(design.ballast.keel_mass)
    target = mass / RHO_SEA
    for angle in np.arange(0.0, 180.5, 0.5):
        z_wl = solve_waterline(geom, target, angle, False, keel_vol)
        if z_wl is None:
            return float(angle)
        for i in range(len(geom.x)):
            if len(geom._voids[i]) < 3:
                continue
            if geom._void_is_open(i, z_wl, angle):
                return float(angle)
    return None


def gz_curve(
    geom: HullGeometry,
    design: Design,
    mass: float,
    vcg: float,
    flooded: bool,
    heel: np.ndarray | None = None,
    label: str = "",
    ycg: float = 0.0,
) -> GZCurve:
    """Righting-arm curve at the given mass and VCG.

    ``vcg`` is measured above the baseline, in the body frame. ``ycg`` is the
    transverse CG offset: negative is to windward for a heel in the positive
    direction, which is how a windward-only water ballast tank enters.
    """
    if heel is None:
        heel = np.arange(0.0, 181.0, 2.0)

    keel_mass = design.ballast.keel_mass
    keel_vol = geom.keel_appendage_volume(keel_mass)
    ky, kz = _keel_centroid_body(design)
    target = mass / RHO_SEA

    gz = np.full(len(heel), np.nan)
    afloat = np.zeros(len(heel), dtype=bool)

    for j, angle in enumerate(heel):
        z_wl = solve_waterline(geom, target, float(angle), flooded, keel_vol)
        if z_wl is None:
            continue
        vol, _, y_b_hull, _ = geom.volume(z_wl, float(angle), flooded)
        if vol <= 1e-9:
            continue
        # Combine hull buoyancy with the always-submerged keel appendage.
        ky_e, _ = rotate_point(ky, kz, float(angle))
        v_total = vol + keel_vol
        y_b = (vol * y_b_hull + keel_vol * ky_e) / v_total
        y_g, _ = rotate_point(ycg, vcg, float(angle))
        gz[j] = y_b - y_g
        afloat[j] = True

    df = downflooding_angle(geom, design, mass) if flooded else None
    return GZCurve(heel=np.asarray(heel, dtype=float), gz=gz, label=label,
                   downflooding_angle=df, afloat=afloat)


# ---------------------------------------------------------------------------
# Sail-carrying capacity
# ---------------------------------------------------------------------------


RHO_AIR = 1.225
CH_UPWIND = 1.05  # [ASSUM] effective heeling coefficient, close-hauled


def heeling_moment(design: Design, wind_ms: float, heel_deg: float,
                   vcg: float, z_wl: float) -> float:
    """Aerodynamic heeling moment, N.m, at a given true wind and heel."""
    a = design.rig.sail_area_upwind
    lever = (design.hull.sheer_curve[3][1] + design.rig.ce_height_above_sheer) - vcg
    lever = max(lever, 0.1)
    phi = np.radians(heel_deg)
    return 0.5 * RHO_AIR * wind_ms**2 * a * CH_UPWIND * lever * np.cos(phi) ** 2


def equilibrium_heel(curve: GZCurve, design: Design, mass: float,
                     vcg: float, wind_ms: float, z_wl: float) -> float | None:
    """Steady heel angle where sail moment balances the righting moment."""
    from .params import G

    # The stable equilibrium is the FIRST angle where the righting moment
    # overtakes the heeling moment, i.e. an upward zero crossing of (RM - HM).
    # A downward crossing further up the curve is the unstable capsize point.
    # If the net moment is already restoring at zero heel (an off-centre CG,
    # e.g. a windward ballast tank in light air), the equilibrium is at or to
    # weather of upright -- report 0 rather than scanning past it.
    if np.isfinite(curve.gz[0]):
        f0 = mass * G * curve.gz[0] - heeling_moment(
            design, wind_ms, float(curve.heel[0]), vcg, z_wl
        )
        if f0 >= 0.0:
            return 0.0
    for i in range(len(curve.heel) - 1):
        if not (np.isfinite(curve.gz[i]) and np.isfinite(curve.gz[i + 1])):
            continue
        rm_a = mass * G * curve.gz[i]
        rm_b = mass * G * curve.gz[i + 1]
        hm_a = heeling_moment(design, wind_ms, float(curve.heel[i]), vcg, z_wl)
        hm_b = heeling_moment(design, wind_ms, float(curve.heel[i + 1]), vcg, z_wl)
        fa, fb = rm_a - hm_a, rm_b - hm_b
        if fa < 0.0 <= fb:
            frac = -fa / (fb - fa)
            return float(curve.heel[i] + frac * (curve.heel[i + 1] - curve.heel[i]))
    return None


def knockdown_wind(curve: GZCurve, design: Design, mass: float,
                   vcg: float, z_wl: float) -> float:
    """Steady wind speed (m/s) whose moment equals peak righting moment."""
    from .params import G

    rm_max = mass * G * curve.gz_max
    angle = curve.angle_gz_max
    unit = heeling_moment(design, 1.0, angle, vcg, z_wl)
    return float(np.sqrt(rm_max / unit)) if unit > 0 else float("nan")
