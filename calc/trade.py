"""Self-righting trade study.

The brief asks for true recovery from 180 degrees in an open boat. The baseline
does not achieve it. This module finds out what would, by sweeping the levers
that actually move the angle of vanishing stability:

  ballast      -- more lead, lower down. Costs displacement.
  beam         -- the dominant term. A beamy hull is *stable inverted*; that is
                  the same form stability that makes it stiff upright.
  canoe depth  -- deeper body raises AVS for the same beam.
  cockpit size -- narrowing the cockpit converts floodable volume into sealed
                  side tanks, which is the only buoyancy that helps at 180.

Run:  python3 -m calc.trade
Writes out/trade_study.txt and out/trade_frontier.png
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass

import numpy as np

from . import scantlings, weights
from .geometry import HullGeometry
from .params import Design
from .stability import gz_curve

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

# Coarser than the main report: these sweeps run hundreds of curves.
HEEL = np.arange(0.0, 181.0, 5.0)
STATIONS = 31


@dataclass
class Case:
    label: str
    ballast: float
    beam: float
    depth_scale: float
    cockpit_half_width: float
    displacement: float
    ballast_ratio: float
    avs: float
    gz_max: float
    self_righting: bool
    negative_area: float


def _fixed_mass(design: Design) -> tuple[float, float, float, float]:
    """Non-ballast mass and its moment, plus shell areas, for a given design."""
    geom = HullGeometry(design.hull, design.cockpit)
    hull_area, deck_area = geom.shell_area(), geom.deck_area()
    m_ldc = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc)
    wb = weights.build(design, sc["mass_per_area"], hull_area, deck_area)
    non_ballast = [i for i in wb.items if "keel ballast" not in i.name]
    mass = sum(i.mass for i in non_ballast)
    moment = sum(i.moment for i in non_ballast)
    return mass, moment, hull_area, deck_area


def evaluate_case(
    base: Design,
    ballast: float,
    beam: float | None = None,
    depth_scale: float = 1.0,
    cockpit_half_width: float | None = None,
    flooded: bool = True,
    label: str = "",
    deck_camber: float | None = None,
) -> Case:
    """Build a variant, solve its GZ curve, and report whether it self-rights.

    Displacement is *not* held at 750 kg here -- ballast is added on top of the
    fixed weight, so the sweep shows what displacement each ballast figure
    implies. Holding 750 would just re-derive the baseline.
    """
    d = copy.deepcopy(base)
    d.hull.n_stations = STATIONS
    if beam is not None:
        d.hull.beam_sheer = beam
    if cockpit_half_width is not None:
        d.cockpit.half_width = cockpit_half_width
    if deck_camber is not None:
        d.hull.deck_camber = deck_camber
    if depth_scale != 1.0:
        d.hull.sheer_curve = [(t, z * depth_scale) for t, z in d.hull.sheer_curve]
        d.cockpit.sole_z = d.cockpit.sole_z * depth_scale

    fixed_mass, fixed_moment, _, _ = _fixed_mass(d)
    d.ballast.keel_mass = ballast

    disp = fixed_mass + ballast
    vcg = (fixed_moment + ballast * -d.ballast.keel_vcg_below_bl) / disp

    geom = HullGeometry(d.hull, d.cockpit)
    c = gz_curve(geom, d, disp, vcg, flooded=flooded, heel=HEEL, label=label)

    return Case(
        label=label or f"bal={ballast:.0f}",
        ballast=ballast,
        beam=d.hull.beam_sheer,
        depth_scale=depth_scale,
        cockpit_half_width=d.cockpit.half_width,
        displacement=disp,
        ballast_ratio=ballast / disp,
        avs=c.avs,
        gz_max=c.gz_max,
        self_righting=c.self_righting,
        negative_area=c.negative_area,
    )


def min_ballast_for_self_righting(
    base: Design, beam: float, depth_scale: float = 1.0,
    cockpit_half_width: float | None = None,
    lo: float = 150.0, hi: float = 1400.0,
    deck_camber: float | None = None,
) -> float | None:
    """Bisect the smallest ballast that self-rights, or None inside the range."""
    kw = dict(beam=beam, depth_scale=depth_scale,
              cockpit_half_width=cockpit_half_width, deck_camber=deck_camber)
    if not evaluate_case(base, hi, **kw).self_righting:
        return None
    if evaluate_case(base, lo, **kw).self_righting:
        return lo
    for _ in range(9):
        mid = 0.5 * (lo + hi)
        if evaluate_case(base, mid, **kw).self_righting:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def run() -> dict:
    os.makedirs(OUT, exist_ok=True)
    base = Design()
    lines: list[str] = []

    def say(*parts: object) -> None:
        line = " ".join(str(p) for p in parts)
        print(line)
        lines.append(line)

    say("=" * 78)
    say("SELF-RIGHTING TRADE STUDY")
    say("=" * 78)
    say("Requirement: GZ > 0 at every angle up to 180 deg, cockpit flooded,")
    say("light ship (crew in the water). Displacement floats free in these")
    say("sweeps -- ballast is added on top of the fixed weight.")
    say("")

    # -- 1. ballast alone ------------------------------------------------
    say("-" * 78)
    say("1. BALLAST ALONE  (beam 2.35 m as designed)")
    say("-" * 78)
    say(f"  {'ballast':>8}{'disp':>8}{'ratio':>8}{'GZmax':>8}{'AVS':>8}{'self-right':>12}")
    ballast_sweep = []
    for bal in (213, 300, 400, 500, 600, 800, 1000):
        c = evaluate_case(base, float(bal))
        ballast_sweep.append(c)
        say(f"  {c.ballast:>8.0f}{c.displacement:>8.0f}{c.ballast_ratio * 100:>7.1f}%"
            f"{c.gz_max:>8.3f}{c.avs:>8.1f}{str(c.self_righting):>12}")
    say("")
    if not any(c.self_righting for c in ballast_sweep):
        say("  Ballast alone does not get there at this beam, at any weight that")
        say("  could float on a 6.5 m hull. Form stability inverted wins.")

    # -- 2. beam ---------------------------------------------------------
    say("")
    say("-" * 78)
    say("2. BEAM  (ballast held at the 213 kg the budget allows)")
    say("-" * 78)
    say(f"  {'beam':>8}{'GZmax':>8}{'AVS':>8}{'neg area':>10}{'self-right':>12}")
    for beam in (1.80, 1.95, 2.10, 2.25, 2.35, 2.50):
        c = evaluate_case(base, 213.0, beam=beam)
        say(f"  {beam:>8.2f}{c.gz_max:>8.3f}{c.avs:>8.1f}{c.negative_area:>10.3f}"
            f"{str(c.self_righting):>12}")

    # -- 3. cockpit volume ------------------------------------------------
    say("")
    say("-" * 78)
    say("3. COCKPIT WIDTH  (narrower cockpit = more sealed side tank)")
    say("-" * 78)
    say(f"  {'half-w':>8}{'seats':>8}{'GZmax':>8}{'AVS':>8}{'self-right':>12}")
    for hw in (0.45, 0.55, 0.65, 0.75, 0.86):
        c = evaluate_case(base, 213.0, cockpit_half_width=hw)
        seats = "6 abreast" if hw >= 0.80 else ("4-5" if hw >= 0.62 else "2-3")
        say(f"  {hw:>8.2f}{seats:>8}{c.gz_max:>8.3f}{c.avs:>8.1f}"
            f"{str(c.self_righting):>12}")

    # -- 4. fully decked bound -------------------------------------------
    say("")
    say("-" * 78)
    say("4. UPPER BOUND: fully decked (watertight cockpit, not an open boat)")
    say("-" * 78)
    for bal in (213, 300, 400):
        c = evaluate_case(base, float(bal), flooded=False)
        say(f"  ballast {bal:>4.0f} kg, sealed: AVS {c.avs:>6.1f} deg,"
            f" self-righting {c.self_righting}")
    say("  Even sealed, this beam-to-depth ratio has a stable inverted state.")

    # -- 5. combined frontier --------------------------------------------
    say("")
    say("-" * 78)
    say("5. FRONTIER: minimum ballast for true self-righting, vs beam")
    say("-" * 78)
    beams = [1.70, 1.80, 1.90, 2.00, 2.10, 2.20, 2.35]
    frontier: list[tuple[float, float | None]] = []
    for beam in beams:
        need = min_ballast_for_self_righting(base, beam)
        frontier.append((beam, need))
        if need is None:
            say(f"  beam {beam:.2f} m : not achievable below 1400 kg of ballast")
        else:
            fixed, _, _, _ = _fixed_mass(base)
            say(f"  beam {beam:.2f} m : needs {need:.0f} kg ballast"
                f"  -> displacement {fixed + need:.0f} kg"
                f"  ({need / (fixed + need) * 100:.0f}% ratio)")

    # -- 6. deeper canoe body --------------------------------------------
    say("")
    say("-" * 78)
    say("6. DEEPER CANOE BODY  (freeboard scaled up, beam 2.10 m)")
    say("-" * 78)
    for ds in (1.0, 1.15, 1.30, 1.45):
        c = evaluate_case(base, 400.0, beam=2.10, depth_scale=ds)
        say(f"  depth x{ds:.2f} (sheer {0.76 * ds:.2f} m): AVS {c.avs:>6.1f} deg,"
            f" self-righting {c.self_righting}")

    say("")
    say("=" * 78)
    say("READING")
    say("=" * 78)
    say("  True 180-degree self-righting is a beam problem before it is a")
    say("  ballast problem. The same wide, shallow hull that carries a 6-seat")
    say("  cockpit and 22 m2 of sail is stable upside down, and no amount of")
    say("  lead that a 6.5 m hull can float changes that at 2.35 m beam.")
    say("")
    say("  The requirement and the brief are mutually exclusive as written.")
    say("  Something has to give -- see docs/03-self-righting.md.")

    path = os.path.join(OUT, "trade_study.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWritten to {path}")

    _plot_frontier(frontier, ballast_sweep)
    return {"frontier": frontier, "ballast_sweep": ballast_sweep}


def _plot_frontier(frontier, ballast_sweep) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

    ax = axes[0]
    beams = [b for b, n in frontier]
    needs = [n if n is not None else np.nan for b, n in frontier]
    ax.plot(beams, needs, "o-", color="#4477aa")
    ax.axvline(2.35, color="#cc6677", linestyle="--", label="as designed 2.35 m")
    ax.axhline(213, color="#999933", linestyle=":", label="ballast available 213 kg")
    ax.set_xlabel("beam (m)")
    ax.set_ylabel("ballast needed to self-right (kg)")
    ax.set_title("Self-righting frontier")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.25)

    ax = axes[1]
    ax.plot([c.ballast_ratio * 100 for c in ballast_sweep],
            [c.avs for c in ballast_sweep], "o-", color="#4477aa")
    ax.axhline(180, color="#117733", linestyle="--", label="self-righting")
    ax.set_xlabel("ballast ratio (%)")
    ax.set_ylabel("AVS (deg)")
    ax.set_title("AVS vs ballast at 2.35 m beam")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "trade_frontier.png"), dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    run()
