"""Run the full calculation chain and emit a report plus plots.

    python3 -m calc.report

Writes out/report.txt, out/gz_curves.png, out/hull_lines.png.
"""

from __future__ import annotations

import os
import sys

import numpy as np

from . import scantlings, stability, weights
from .geometry import HullGeometry
from .params import AIRA_22, FLOW_19, RHO_SEA, Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


class Tee:
    """Write to stdout and a file at once."""

    def __init__(self, path: str):
        self.f = open(path, "w")

    def __call__(self, *parts: object) -> None:
        line = " ".join(str(p) for p in parts)
        print(line)
        self.f.write(line + "\n")

    def close(self) -> None:
        self.f.close()


def rule(say, title: str = "", char: str = "=") -> None:
    if title:
        say(f"\n{char * 78}\n{title}\n{char * 78}")
    else:
        say(char * 78)


def run(design: Design | None = None, quiet: bool = False) -> dict:
    design = design or Design()
    os.makedirs(OUT, exist_ok=True)
    say = Tee(os.path.join(OUT, "report.txt"))

    geom = HullGeometry(design.hull, design.cockpit)

    # -- geometry --------------------------------------------------------
    rule(say, "1. HULL GEOMETRY")
    hull_area = geom.shell_area()
    deck_area = geom.deck_area()
    say(f"  LOA                     {design.hull.loa:.3f} m")
    say(f"  LWL                     {design.hull.lwl:.3f} m")
    say(f"  Max beam (sheer)        {geom.max_beam:.3f} m")
    say(f"  Beam at chine           {design.hull.beam_sheer * design.hull.beam_chine_frac:.3f} m")
    say(f"  Depth of canoe body     {float(geom.z_sheer.min() - geom.z_keel.min()):.3f} m")
    say(f"  Hull shell area         {hull_area:.2f} m2")
    say(f"  Deck + cockpit area     {deck_area:.2f} m2")
    say(f"  Total shell area        {hull_area + deck_area:.2f} m2")
    say(f"  Cockpit                 {design.cockpit.x_fwd - design.cockpit.x_aft:.2f} m long"
        f" x {2 * design.cockpit.half_width:.2f} m wide, sole at z={design.cockpit.sole_z:.3f} m")

    # -- scantlings ------------------------------------------------------
    rule(say, "2. HDPE SCANTLINGS")
    m_ldc_guess = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc_guess)
    say(f"  Design category {design.design_category}, m_LDC assumed {m_ldc_guess:.0f} kg")
    say(f"  Material: {design.material.name}")
    say(f"    short-term flex modulus  {design.material.E_short / 1e6:.0f} MPa")
    say(f"    creep-derated modulus    {design.material.E_long / 1e6:.0f} MPa  <- design value")
    say(f"    allowable bending stress {design.material.sigma_allow / 1e6:.1f} MPa")
    say("")
    say(f"  {'panel':<16}{'p (kPa)':>9}{'span':>7}{'t_str':>8}{'t_defl':>8}{'governs':>12}")
    for name, r in sc["panels"].items():
        say(f"  {name:<16}{r.pressure / 1000:>9.1f}{r.span:>7.2f}"
            f"{r.t_stress * 1000:>8.1f}{r.t_deflection * 1000:>8.1f}{r.governing:>12}")
    say("")
    say(f"  Single-skin thickness required : {sc['single_skin_required_t'] * 1000:.1f} mm")
    say(f"  Equivalent GRP thickness       : {sc['grp_equivalent_t'] * 1000:.1f} mm")
    say(f"  HDPE/GRP thickness ratio       : {sc['stiffness_thickness_ratio']:.2f} x")
    say(f"  Single-skin areal mass         : {sc['single_skin_required_t'] * design.material.rho:.1f} kg/m2")
    say(f"  -> single skin on {hull_area + deck_area:.0f} m2 would weigh "
        f"{sc['single_skin_required_t'] * design.material.rho * (hull_area + deck_area):.0f} kg. Not viable.")

    if "sandwich" in sc:
        st = design.structure
        say("")
        say(f"  DOUBLE SKIN: {st.skin_t * 1000:.1f} mm skins, {st.core_depth * 1000:.0f} mm gap,"
            f" kiss-offs at {st.kiss_off_pitch * 1000:.0f} mm")
        say(f"  {'panel':<16}{'t_equiv':>9}{'need':>8}{'face MPa':>10}{'skin req':>10}{'verdict':>10}")
        for name, s in sc["sandwich"].items():
            need = sc["panels"][name].t_required
            ok = "PASS" if (s.passes_global and s.passes_local and s.passes_stress) else "FAIL"
            say(f"  {name:<16}{s.t_equivalent * 1000:>9.1f}{need * 1000:>8.1f}"
                f"{s.face_stress / 1e6:>10.2f}{s.skin_t_required_local * 1000:>10.1f}{ok:>10}")
        say(f"  Areal mass: {sc['mass_per_area']:.1f} kg/m2"
            f"  ({sc['mass_per_area'] / (sc['single_skin_required_t'] * design.material.rho):.2f}x"
            f" the single-skin mass)")
        say(f"  All panels pass: {sc['all_pass']}")

    # -- weights ---------------------------------------------------------
    rule(say, "3. WEIGHT BUDGET  (750 kg cap, light incl. ballast)")
    wb = weights.build(design, sc["mass_per_area"], hull_area, deck_area)
    say(wb.table())
    say("")
    cal = weights.aira_calibration(design, wb)
    say("  Like-for-like against the RS Aira, backed out from its published figures:")
    say(f"    Aira shell mass, implied  : {cal['aira_shell_implied']:.0f} kg  (GRP)")
    say(f"    This shell, HDPE double   : {cal['hdpe_shell']:.0f} kg")
    say(f"    Material penalty          : {cal['material_penalty']:+.0f} kg"
        f"   <- HDPE is roughly weight-neutral here")
    say(f"    Electric drive adds       : {cal['propulsion_mass']:+.0f} kg"
        f"   <- this is what costs the ballast")
    say("")
    say(f"  Ballast available           : {wb.ballast_available:.0f} kg")
    say(f"  Ballast ratio               : {wb.ballast_ratio * 100:.1f} %")
    say(f"  RS Aira 22 (GRP) for compare: {AIRA_22['ballast']:.0f} kg"
        f" = {AIRA_22['ballast'] / AIRA_22['disp'] * 100:.1f} %")
    say(f"  Ballast delta vs Aira       : {cal['ballast_delta']:+.0f} kg")

    if not wb.ballast_is_feasible:
        say("\n  *** The 750 kg cap is exceeded before any ballast is fitted. ***")

    # Feed the solved ballast back into the design.
    design.ballast.keel_mass = max(wb.ballast_available, 0.0)

    # -- hydrostatics ----------------------------------------------------
    rule(say, "4. HYDROSTATICS")
    hs_light = stability.upright_hydrostatics(geom, design, wb.disp_light)
    hs_loaded = stability.upright_hydrostatics(geom, design, wb.disp_loaded)
    for name, hs, vcg in (("LIGHT", hs_light, wb.vcg_light),
                          ("LOADED", hs_loaded, wb.vcg_loaded)):
        if hs is None:
            say(f"  {name}: does not float at this displacement.")
            continue
        say(f"  {name:<7} disp {hs.displacement:6.1f} kg   draft {hs.draft:.3f} m"
            f"   z_wl {hs.z_wl:.3f} m   LCB {hs.lcb:.2f} m   Awp {hs.waterplane_area:.2f} m2"
            f"   TPc {hs.tpc:.1f} kg/cm   VCG {vcg:.3f} m")

    # -- self-draining cockpit ------------------------------------------
    rule(say, "5. SELF-DRAINING COCKPIT  (notes.txt line 30, the open question)")
    sole = design.cockpit.sole_z
    for name, hs in (("light ship", hs_light), ("6 crew + water ballast", hs_loaded)):
        if hs is None:
            continue
        margin = sole - hs.z_wl
        verdict = "drains" if margin > 0.02 else ("marginal" if margin > 0 else "FLOODS")
        say(f"  {name:<24} waterline z={hs.z_wl:.3f}  sole z={sole:.3f}"
            f"  freeboard to sole {margin * 1000:+6.0f} mm  -> {verdict}")
    say(f"  Sheer freeboard, light : {float(geom.z_sheer.min()) - (hs_light.z_wl if hs_light else 0):.3f} m")

    # -- stability -------------------------------------------------------
    rule(say, "6. RIGHTING ARM CURVES")
    heel = np.arange(0.0, 181.0, 2.0)
    curves = {}
    for case, mass, vcg in (("light", wb.disp_light, wb.vcg_light),
                            ("loaded", wb.disp_loaded, wb.vcg_loaded)):
        for mode, flooded in (("intact", False), ("flooded", True)):
            key = f"{case}/{mode}"
            curves[key] = stability.gz_curve(
                geom, design, mass, vcg, flooded=flooded, heel=heel, label=key
            )

    say(f"  {'case':<18}{'GZmax':>8}{'@deg':>7}{'AVS':>8}{'A(0-90)':>10}"
        f"{'neg area':>10}{'self-right':>12}")
    for key, c in curves.items():
        say(f"  {key:<18}{c.gz_max:>8.3f}{c.angle_gz_max:>7.0f}{c.avs:>8.1f}"
            f"{c.area_under(0, 90):>10.3f}{c.negative_area:>10.3f}"
            f"{str(c.self_righting):>12}")

    df = curves["loaded/flooded"].downflooding_angle
    say("")
    say(f"  Downflooding angle (cockpit opening immerses): "
        f"{df:.1f} deg" if df is not None else "  Downflooding angle: not reached")
    say("  Beyond that angle only the 'flooded' curve is physically meaningful.")

    # -- self-righting verdict ------------------------------------------
    rule(say, "7. SELF-RIGHTING VERDICT  (the stated requirement)")
    key = "light/flooded"
    c = curves[key]
    say(f"  Requirement: recover unaided from 180 deg (fully inverted).")
    say(f"  Governing case: {key} -- crew are in the water, cockpit is full.")
    say("")
    if c.self_righting:
        say("  RESULT: self-righting. GZ stays positive to 180 deg.")
    else:
        say(f"  RESULT: NOT self-righting.")
        say(f"    AVS                     {c.avs:.1f} deg")
        say(f"    Stable inverted?        yes -- GZ is negative approaching 180 deg")
        say(f"    Energy holding inverted {c.negative_area:.3f} m.rad")
        say(f"    Ballast ratio           {wb.ballast_ratio * 100:.1f} %")
        say("")
        say("  Reference points (neither self-rights from 180 deg either):")
        say("    Contessa 26, fully decked, GRP           ballast ratio ~43 %, AVS ~157 deg")
        say(f"    RS Aira 22, fully decked, GRP            ballast ratio "
            f"{AIRA_22['ballast'] / AIRA_22['disp'] * 100:.0f} %, not self-righting")
        say("  Note: the open cockpit is NOT the main culprit. Sealing it entirely")
        say("  moves AVS by about a degree (see trade study section 4), because when")
        say("  inverted the boat floats so high that the cockpit is mostly out of")
        say("  the water anyway. The binding constraint is beam-to-depth ratio:")
        say(f"  {geom.max_beam:.2f} m beam on {float(geom.z_sheer.min() - geom.z_keel.min()):.2f} m"
            f" of depth is a hull that is stable upside down.")

    # -- sail carrying ---------------------------------------------------
    rule(say, "8. SAIL-CARRYING CAPACITY")
    c_load = curves["loaded/intact"]
    z_wl = hs_loaded.z_wl if hs_loaded else 0.3
    say(f"  Upwind sail area  {design.rig.sail_area_upwind:.1f} m2"
        f"  (main {design.rig.main_area:.1f} + jib {design.rig.jib_area:.1f})")
    sad = design.rig.sail_area_upwind / (wb.disp_loaded / RHO_SEA) ** (2.0 / 3.0)
    say(f"  SA/D ratio        {sad:.1f}   (18-20 brisk daysailer, >22 overpowered)")

    # Windward-tank-only condition: one 250 kg tank filled to weather.
    wb_one = design.ballast.water_ballast_each
    crew = design.crew_mass_each * design.cockpit.seats
    crew_z = design.cockpit.bench_top_z + 0.30
    m_ww = wb.disp_light + crew + wb_one
    vcg_ww = (wb.disp_light * wb.vcg_light + crew * crew_z
              + wb_one * design.ballast.water_ballast_z) / m_ww
    ycg_ww = -wb_one * design.ballast.water_ballast_y / m_ww
    c_ww = stability.gz_curve(geom, design, m_ww, vcg_ww, flooded=False,
                              heel=heel, label="windward tank", ycg=ycg_ww)

    say("")
    say(f"  {'true wind':>11}   {'tanks symmetric':>16}   {'windward tank only':>19}")
    for wind_kt in (8, 12, 16, 20, 25):
        v = wind_kt * 0.5144
        a_sym = stability.equilibrium_heel(c_load, design, wb.disp_loaded, wb.vcg_loaded, v, z_wl)
        a_ww = stability.equilibrium_heel(c_ww, design, m_ww, vcg_ww, v, z_wl)
        t_sym = f"{a_sym:.0f} deg" if a_sym is not None else "knocked down"
        t_ww = f"{a_ww:.0f} deg" if a_ww is not None else "knocked down"
        say(f"  {wind_kt:>8} kt   {t_sym:>16}   {t_ww:>19}")
    kd = stability.knockdown_wind(c_load, design, wb.disp_loaded, wb.vcg_loaded, z_wl)
    kd_ww = stability.knockdown_wind(c_ww, design, m_ww, vcg_ww, z_wl)
    say(f"  Wind at peak righting moment: {kd / 0.5144:.0f} kt symmetric,"
        f" {kd_ww / 0.5144:.0f} kt with the windward tank  (gusts arrive sooner)")
    say(f"  One tank to weather = {wb_one:.0f} kg at"
        f" {design.ballast.water_ballast_y:.2f} m: about the righting moment of"
        f" {wb_one * design.ballast.water_ballast_y / (design.crew_mass_each * 0.9):.0f}"
        f" crew on the rail")

    # -- envelope --------------------------------------------------------
    rule(say, "9. ENVELOPE COMPLIANCE")
    water_l = design.ballast.water_ballast_total / (RHO_SEA / 1000.0)
    violations = design.envelope.check(
        loa=design.hull.loa,
        beam=geom.max_beam,
        disp=wb.disp_light,
        sail_area=design.rig.sail_area_upwind,
        water_ballast_l=water_l,
        draft=design.ballast.keel_draft,
    )
    checks = [
        ("LOA", design.hull.loa, design.envelope.loa_max, "m"),
        ("Beam", geom.max_beam, design.envelope.beam_max, "m"),
        ("Displacement (light)", wb.disp_light, design.envelope.disp_max, "kg"),
        ("Sail area upwind", design.rig.sail_area_upwind, design.envelope.sail_area_max, "m2"),
        ("Water ballast", water_l, design.envelope.water_ballast_max_l, "L"),
        ("Draft, keel down", design.ballast.keel_draft, design.envelope.draft_max, "m"),
    ]
    for name, val, lim, unit in checks:
        ok = "ok" if val <= lim else "EXCEEDS"
        say(f"  {name:<22}{val:>8.2f} {unit:<3} limit {lim:>7.2f}  {ok}")
    say("")
    say(f"  Violations: {len(violations)}")
    for v in violations:
        say(f"    - {v}")

    say("")
    rule(say, "BASE MODEL PROVENANCE", "-")
    say(f"  RS Aira 22 (published): LOA {AIRA_22['loa']} m, beam {AIRA_22['beam']} m,"
        f" disp {AIRA_22['disp']} kg, ballast {AIRA_22['ballast']} kg,"
        f" sail {AIRA_22['main']}+{AIRA_22['jib']} m2, {AIRA_22['material']}")
    say(f"  Flow 19 (from notes.txt, URL 403): beam {FLOW_19['beam']} m,"
        f" disp {FLOW_19['disp']} kg, swing keel {FLOW_19['swing_keel']} kg,"
        f" water ballast {FLOW_19['water_ballast_tanks']}x{FLOW_19['water_ballast_each']} kg")

    say("")
    say(f"Report written to {os.path.join(OUT, 'report.txt')}")
    say.close()

    _plot(geom, curves, design, wb)

    return {
        "geom": geom,
        "scantlings": sc,
        "weights": wb,
        "hydrostatics": {"light": hs_light, "loaded": hs_loaded},
        "curves": curves,
        "design": design,
    }


def _plot(geom, curves, design, wb) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5.5))
    styles = {
        "light/intact": ("#4477aa", "--"),
        "light/flooded": ("#4477aa", "-"),
        "loaded/intact": ("#cc6677", "--"),
        "loaded/flooded": ("#cc6677", "-"),
    }
    for key, c in curves.items():
        col, ls = styles.get(key, ("k", "-"))
        ax.plot(c.heel, c.gz, color=col, linestyle=ls, linewidth=1.9, label=key)
    ax.axhline(0.0, color="#333333", linewidth=0.9)
    df = curves["loaded/flooded"].downflooding_angle
    if df is not None:
        ax.axvline(df, color="#999933", linewidth=1.2, linestyle=":",
                   label=f"downflooding {df:.0f}°")
    ax.set_xlabel("heel angle (deg)")
    ax.set_ylabel("righting arm GZ (m)")
    ax.set_title(f"GZ curves — HDPE open daysailer, ballast "
                 f"{design.ballast.keel_mass:.0f} kg ({wb.ballast_ratio * 100:.0f}%)")
    ax.set_xlim(0, 180)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gz_curves.png"), dpi=140)
    plt.close(fig)

    # Lines plan: stations, profile, plan.
    fig, axes = plt.subplots(3, 1, figsize=(9, 9))
    ax = axes[0]
    for i in range(0, len(geom.x), max(1, len(geom.x) // 14)):
        sec = geom._sections[i]
        if len(sec) < 3:
            continue
        closed = np.vstack([sec, sec[:1]])
        ax.plot(closed[:, 0], closed[:, 1], color="#4477aa", linewidth=1.0)
    ax.set_aspect("equal")
    ax.set_title("body plan")
    ax.set_xlabel("y (m)")
    ax.set_ylabel("z (m)")
    ax.grid(alpha=0.2)

    ax = axes[1]
    ax.plot(geom.x, geom.z_keel, color="#333333", label="keel")
    ax.plot(geom.x, geom.z_chine, color="#cc6677", label="chine")
    ax.plot(geom.x, geom.z_sheer, color="#4477aa", label="sheer")
    ax.axhline(design.cockpit.sole_z, color="#999933", linestyle=":", label="cockpit sole")
    ax.set_aspect("equal")
    ax.set_title("profile")
    ax.set_xlabel("x from transom (m)")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.2)

    ax = axes[2]
    ax.plot(geom.x, geom.y_sheer, color="#4477aa", label="sheer")
    ax.plot(geom.x, -geom.y_sheer, color="#4477aa")
    ax.plot(geom.x, geom.y_chine, color="#cc6677", label="chine")
    ax.plot(geom.x, -geom.y_chine, color="#cc6677")
    ax.set_aspect("equal")
    ax.set_title("plan")
    ax.set_xlabel("x from transom (m)")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "hull_lines.png"), dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    run()
    sys.exit(0)
