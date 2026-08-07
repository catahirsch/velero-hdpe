"""Weight and VCG budget.

The structure is: total displacement is capped at 750 kg (light, including
ballast), so ballast is not an input -- it is *whatever is left over*. That
framing is the point. On the GRP Aira the leftover is 250 kg. Every kilogram
that HDPE construction and the electric auxiliary add is a kilogram taken
directly out of the keel, and the keel is the only thing that rights the boat.

VCG is measured from the baseline (lowest point of the canoe body). The keel's
ballast VCG is *below* the baseline and enters as a negative z.
"""

from __future__ import annotations

from dataclasses import dataclass

from .params import Design


@dataclass
class Item:
    name: str
    mass: float  # kg
    z: float  # m above baseline (negative below)
    note: str = ""

    @property
    def moment(self) -> float:
        return self.mass * self.z


@dataclass
class WeightBudget:
    items: list[Item]
    ballast_available: float
    ballast_is_feasible: bool
    disp_light: float
    vcg_light: float
    disp_loaded: float
    vcg_loaded: float
    ballast_ratio: float
    shell_mass: float

    def table(self) -> str:
        w = max(len(i.name) for i in self.items) + 2
        lines = [f"{'item':<{w}}{'kg':>8}{'z (m)':>9}{'kg.m':>10}   note"]
        lines.append("-" * (w + 27 + 40))
        for i in self.items:
            lines.append(
                f"{i.name:<{w}}{i.mass:>8.1f}{i.z:>9.3f}{i.moment:>10.1f}   {i.note}"
            )
        lines.append("-" * (w + 27 + 40))
        lines.append(
            f"{'LIGHT (incl. ballast)':<{w}}{self.disp_light:>8.1f}"
            f"{self.vcg_light:>9.3f}"
        )
        lines.append(
            f"{'LOADED (6 crew + water)':<{w}}{self.disp_loaded:>8.1f}"
            f"{self.vcg_loaded:>9.3f}"
        )
        return "\n".join(lines)


def structure_mass(design: Design, mass_per_area: float,
                   hull_area: float, deck_area: float) -> float:
    """Shell mass including local reinforcement."""
    return (hull_area + deck_area) * mass_per_area * design.structure.reinforcement_factor


def build(
    design: Design,
    mass_per_area: float,
    hull_area: float,
    deck_area: float,
) -> WeightBudget:
    """Assemble the weight budget and solve for available ballast."""
    st = design.structure
    rig = design.rig
    prop = design.propulsion
    env = design.envelope

    shell = structure_mass(design, mass_per_area, hull_area, deck_area)

    # [ASSUM] VCGs. The shell VCG sits a little below mid-depth because the
    # bottom is thicker-supported and the topsides are short.
    items: list[Item] = [
        Item("HDPE shell (hull+deck)", shell, 0.42,
             f"{mass_per_area:.1f} kg/m2 x {hull_area + deck_area:.1f} m2"),
        Item("keel case + pivot structure", 22.0, 0.35, "welded PE bosses, bolted"),
        Item("rudder + tiller (single, kick-up)", 15.0, 0.55,
             "centreline transom-hung; client amendment 2026-08-06"),
        Item("mast + boom + standing rig", 32.0, 3.10, "short mast, no backstay"),
        Item("sails (main + jib + furler)", 16.0, 2.20, "square-top, lazy bag"),
        Item("deck hardware + 2:1 systems", 19.0, 0.78, "no winches"),
        Item("electric motor", prop.motor_mass, prop.motor_z, "~4 kW outboard format"),
        Item("battery", prop.battery_mass, prop.battery_z,
             f"{prop.battery_kwh:.1f} kWh LiFePO4"),
        Item("spray hood + cockpit tent", 11.0, 0.95, "stowed"),
        Item("anchor, lines, safety gear", 18.0, 0.40, ""),
    ]

    fixed = sum(i.mass for i in items)
    ballast_available = env.disp_max - fixed

    # The keel takes whatever is left. Water ballast is *added* on top when
    # sailing, so it does not compete with the keel for the light-ship budget.
    keel_mass = max(ballast_available, 0.0)
    items.append(
        Item("keel ballast (lead)", keel_mass, -design.ballast.keel_vcg_below_bl,
             "REMAINDER of the 750 kg cap")
    )

    disp_light = sum(i.mass for i in items)
    vcg_light = sum(i.moment for i in items) / disp_light if disp_light else 0.0

    # Loaded: crew sit high, water ballast sits low.
    crew = design.crew_mass_each * design.cockpit.seats
    water = design.ballast.water_ballast_total
    # Seated on the bench tops; a seated adult's CG is ~0.30 m above the pan.
    crew_z = design.cockpit.bench_top_z + 0.30
    loaded_items = items + [
        Item("crew", crew, crew_z, f"{design.cockpit.seats} x {design.crew_mass_each:.0f} kg"),
        Item("water ballast", water, design.ballast.water_ballast_z, "2 tanks, symmetric"),
    ]
    disp_loaded = sum(i.mass for i in loaded_items)
    vcg_loaded = sum(i.moment for i in loaded_items) / disp_loaded

    return WeightBudget(
        items=items,
        ballast_available=ballast_available,
        ballast_is_feasible=ballast_available > 0.0,
        disp_light=disp_light,
        vcg_light=vcg_light,
        disp_loaded=disp_loaded,
        vcg_loaded=vcg_loaded,
        ballast_ratio=keel_mass / disp_light if disp_light else 0.0,
        shell_mass=shell,
    )


def aira_calibration(design: Design, budget: WeightBudget) -> dict:
    """Back out the real RS Aira shell mass and compare like for like.

    A plate-theory GRP number is not a fair comparison: the Aira's shell is
    stiffened and cored in reality, not a bare 8 mm single skin. So instead of
    predicting the GRP weight, back it out from the published figures --
    750 kg total, 250 kg ballast -- by subtracting the same non-shell items this
    design carries, minus the ones the Aira does not have (electric drive).

    This is the honest comparison, and it says something different from the
    plate calc: the material is roughly weight-neutral. The ballast is lost to
    the *electric auxiliary*, not to HDPE.
    """
    from .params import AIRA_22

    prop_mass = design.propulsion.motor_mass + design.propulsion.battery_mass
    non_shell = sum(
        i.mass for i in budget.items
        if "shell" not in i.name and "keel ballast" not in i.name
    )
    aira_non_shell = non_shell - prop_mass  # no electric drive on the Aira
    aira_shell = AIRA_22["disp"] - AIRA_22["ballast"] - aira_non_shell

    return {
        "aira_shell_implied": aira_shell,
        "hdpe_shell": budget.shell_mass,
        "material_penalty": budget.shell_mass - aira_shell,
        "propulsion_mass": prop_mass,
        "aira_ballast": AIRA_22["ballast"],
        "our_ballast": budget.ballast_available,
        "ballast_delta": budget.ballast_available - AIRA_22["ballast"],
    }
