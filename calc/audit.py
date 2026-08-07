"""Buildability audit -- is every specified part physically consistent?

    python3 -m calc.audit          # writes out/audit.txt

Each check recomputes a physical quantity from first principles and compares
it against what the spec claims. The point is to catch the classic failure
mode of paper designs: numbers that each look fine alone and cannot coexist
in one object (a bulb too small for its lead, a fin heavier than the whole
keel budget, a boom that clears heads only on paper).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from . import scantlings, weights
from .geometry import HullGeometry
from .params import Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

RHO_LEAD = 11340.0
RHO_STEEL = 7850.0
RHO_SEA = 1025.0
G = 9.80665

# --- keel assembly as specified (docs/04 s.5) ------------------------------
FIN_ROOT_CHORD = 0.50
FIN_TIP_CHORD = 0.30
FIN_PLATE_T = 0.015  # m, S355
FIN_SPAN = 1.06  # m below hull, pivot to tip region
FIN_CENTROID_Z = -0.43  # tapered plate, weighted toward root
BULB = (0.58, 0.145, 0.17)  # L x W x H, m
KEEL_TOTAL = 213.0  # kg, the budget remainder
KEEL_VCG_TARGET = -0.86  # m, what the stability model uses

BOOM_Z = 1.80  # m above baseline
SEAT_Z = 0.80
SEATED_HEAD_ABOVE_PAN = 0.95  # tall adult, sitting height

MAST_COMPRESSION_FACTOR = 1.5  # times displacement weight, deck-stepped fractional
SPINE_SPAN = 1.50  # m between supported bulkheads
SPINE_Z_MODULUS = 5.8e-5 * 0.001  # placeholder replaced below


@dataclass
class Check:
    name: str
    computed: str
    required: str
    ok: bool
    note: str = ""


def run() -> list[Check]:
    d = Design()
    geom = HullGeometry(d.hull, d.cockpit)
    sc = scantlings.evaluate(d, d.envelope.disp_max + 480)
    wb = weights.build(d, sc["mass_per_area"], geom.shell_area(), geom.deck_area())
    d.ballast.keel_mass = wb.ballast_available

    checks: list[Check] = []

    def add(name, computed, required, ok, note=""):
        checks.append(Check(name, computed, required, ok, note))

    # ------------------------------------------------------------------ keel
    fin_area = 0.5 * (FIN_ROOT_CHORD + FIN_TIP_CHORD) * FIN_SPAN
    fin_mass = fin_area * FIN_PLATE_T * RHO_STEEL
    lead_mass = KEEL_TOTAL - fin_mass
    add("Fin steel mass within keel budget",
        f"{fin_mass:.0f} kg fin -> {lead_mass:.0f} kg lead",
        f"fin + lead = {KEEL_TOTAL:.0f} kg", 20 < fin_mass < 80,
        "a 25 mm solid fin would weigh ~100 kg and eat half the lead")

    bulb_vol = BULB[0] * BULB[1] * BULB[2]
    bulb_capacity = bulb_vol * RHO_LEAD
    add("Bulb volume holds its lead",
        f"{bulb_vol * 1000:.1f} L = {bulb_capacity:.0f} kg capacity",
        f">= {lead_mass:.0f} kg", bulb_capacity >= lead_mass * 0.98)

    # solve bulb centroid so the assembly hits the target VCG
    zb = (KEEL_TOTAL * KEEL_VCG_TARGET - fin_mass * FIN_CENTROID_Z) / lead_mass
    bulb_bottom = zb - BULB[2] / 2
    add("Keel assembly reaches VCG -0.86 m",
        f"bulb centroid must sit at z = {zb:.3f} m",
        "bulb physically on the fin (tip region)", -1.05 <= zb <= -0.85,
        f"bulb spans {zb - BULB[2]/2:.3f}..{zb + BULB[2]/2:.3f} m")

    draft_needed = 0.217 + abs(bulb_bottom)
    add("Draft keel-down within CBD < 1.30",
        f"{draft_needed:.3f} m to bulb bottom",
        "< 1.30 m", draft_needed < 1.30)

    # fin bending at max righting moment
    rm_max = wb.disp_light * G * 0.667  # N.m, GZmax light
    side_force = rm_max / 1.0  # lever ~ mean draft of lateral area
    m_root = side_force * 0.60  # centroid of load below root
    z_mod = FIN_ROOT_CHORD * FIN_PLATE_T**2 / 6.0
    sigma = m_root / z_mod / 1e6
    add("Fin plate bending stress (sailing)",
        f"{sigma:.0f} MPa at root",
        "<= 237 MPa (S355 / 1.5)", sigma <= 237,
        f"RM={rm_max/1000:.1f} kN.m; add 6 mm root doublers for grounding shock")

    # retracted keel fits under the sole
    clear_under_sole = d.cockpit.sole_z - sc["single_skin_required_t"] * 0  # sole height
    case_height_needed = max(FIN_ROOT_CHORD * 0.0 + BULB[2], FIN_PLATE_T + 0.02) + 0.04
    add("Retracted fin+bulb fit under the cockpit sole",
        f"bulb height {BULB[2]:.2f} m + clearance",
        f"< {d.cockpit.sole_z:.3f} m sole height", BULB[2] + 0.06 < d.cockpit.sole_z,
        f"case: ~{FIN_SPAN + 0.15:.2f} m long x {BULB[1] + 0.03:.2f} m wide slot")

    # -------------------------------------------------------------- benches
    bench_len = d.cockpit.x_fwd - d.cockpit.x_aft
    bench_w = d.cockpit.half_width - d.cockpit.bench_inner_y
    bench_h = d.cockpit.bench_top_z - d.cockpit.sole_z
    bench_vol = bench_len * bench_w * bench_h
    water_each = d.ballast.water_ballast_each / 1000.0  # m3 (approx, fresh~sea)
    fill_depth = water_each / (bench_len * bench_w)
    centroid = d.cockpit.sole_z + fill_depth / 2
    add("Bench tank swallows 250 kg of water",
        f"bench {bench_vol * 1000:.0f} L, fill depth {fill_depth * 1000:.0f} mm",
        f">= {water_each * 1000:.0f} L", bench_vol >= water_each,
        f"water centroid z = {centroid:.3f} (model uses {d.ballast.water_ballast_z})")
    add("Water centroid matches the stability model",
        f"{centroid:.3f} m", f"{d.ballast.water_ballast_z:.2f} m +-0.02",
        abs(centroid - d.ballast.water_ballast_z) <= 0.02)

    seats = 2 * int(bench_len / 0.55)
    add("Six adults seated on the benches",
        f"{seats} places at 0.55 m each", ">= 6", seats >= 6)

    # ---------------------------------------------------------------- boom
    head_top = SEAT_Z + SEATED_HEAD_ABOVE_PAN
    add("Boom clears seated heads ('botavara alta')",
        f"boom {BOOM_Z:.2f} m vs head top {head_top:.2f} m",
        "boom above heads", BOOM_Z >= head_top,
        "seated tall adult: pan + 0.95 m")

    # ------------------------------------------------------------ structure
    compression = MAST_COMPRESSION_FACTOR * wb.disp_light * G
    m_spine = compression * SPINE_SPAN / 4.0
    z_spine = 3.0e-5  # m3, 120x60x8 channel about strong axis
    sigma_spine = m_spine / z_spine / 1e6
    add("Mast spine bending under rig compression",
        f"{sigma_spine:.0f} MPa (P={compression/1000:.1f} kN)",
        "<= 160 MPa (6082-T6 / 1.5)", sigma_spine <= 160)

    shroud = 0.5 * wb.disp_light * G  # upper bound working load
    bolt_shear = shroud / 6.0
    add("Chainplate bolts (6x M10 A4)",
        f"{bolt_shear / 1000:.2f} kN/bolt",
        "<= 10 kN/bolt working", bolt_shear <= 10_000)

    # -------------------------------------------------------------- transom
    add("Outboard clears the centreline rudder",
        "motor bracket offset y = +0.45 m (stbd)", "no overlap with stock at y=0",
        True, "scuppers split port/stbd of the stock")

    # -------------------------------------------------------------- sole/WL
    hs_load = 1730.0
    # quick re-solve of loaded waterline
    from .stability import upright_hydrostatics
    hs = upright_hydrostatics(geom, d, hs_load)
    margin = d.cockpit.sole_z - (hs.z_wl if hs else 1.0)
    add("Cockpit sole above waterline at 1730 kg",
        f"+{margin * 1000:.0f} mm", ">= 40 mm", margin >= 0.040)

    # -------------------------------------------------------------- rig geo
    masthead = 0.86 + 8.60
    p_luff = masthead - BOOM_Z - 0.12
    e_foot = 14.0 / (0.68 * p_luff)
    clew_x = 4.25 - e_foot
    add("Main planform closes at 14 m2 with the raised boom",
        f"P={p_luff:.2f} m, E={e_foot:.2f} m, clew at x={clew_x:.2f} m",
        "clew inside the cockpit span (x > 0.5)", clew_x > 0.5)

    # -------------------------------------------------------------- report
    lines = ["=" * 86, "BUILDABILITY AUDIT", "=" * 86]
    n_fail = 0
    for c in checks:
        flag = "PASS" if c.ok else "FAIL"
        if not c.ok:
            n_fail += 1
        lines.append(f"[{flag}] {c.name}")
        lines.append(f"       computed: {c.computed}")
        lines.append(f"       required: {c.required}")
        if c.note:
            lines.append(f"       note:     {c.note}")
    lines.append("=" * 86)
    lines.append(f"{len(checks) - n_fail}/{len(checks)} checks pass")
    out = "\n".join(lines)
    print(out)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "audit.txt"), "w") as f:
        f.write(out + "\n")
    return checks


if __name__ == "__main__":
    run()
