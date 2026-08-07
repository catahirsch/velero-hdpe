"""Single source of truth for the design parameters.

Every number here is either (a) taken from a published source, (b) recorded in
notes.txt by the designer, or (c) an assumption. Provenance is tagged in the
comment on each line:

    [AIRA]  published RS Aira 22 spec (rssailing.com, fetched 2026-08-06)
    [FLOW]  Flow 19 figure as recorded in notes.txt (source URL returns 403)
    [NOTES] stated in notes.txt
    [ASSUM] assumption made by this model -- change freely
    [MAT]   published HDPE material property

Baseline z = 0 is the lowest point of the canoe body (keel line, keel raised).
x = 0 at the transom, positive forward. y = 0 on centreline, positive starboard.
All SI: metres, kilograms, newtons, pascals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RHO_SEA = 1025.0  # kg/m^3, seawater
G = 9.80665  # m/s^2


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Material:
    """Structural material properties.

    The HDPE numbers that matter most are ``E_long`` and ``sigma_allow``. HDPE
    creeps, so its short-term flexural modulus (~1100 MPa) is not a design
    value: under sustained load the effective modulus falls to roughly a
    quarter of it. Designing to the short-term number is the single most common
    way plastic boat structures end up floppy.
    """

    name: str
    rho: float  # kg/m^3
    E_short: float  # Pa, short-term flexural modulus
    E_long: float  # Pa, creep-derated modulus for sustained load
    sigma_allow: float  # Pa, long-term allowable bending stress
    weldable: bool
    bondable: bool


# [MAT] Rotomoulding-grade HDPE. E_long ~ E_short/4.4 at 10 yr, 20 C.
HDPE = Material(
    name="HDPE (rotomoulding grade)",
    rho=950.0,
    E_short=1_100e6,
    E_long=250e6,
    sigma_allow=7.0e6,
    weldable=True,
    bondable=False,  # non-polar surface: adhesives do not work, weld or bolt
)

# [MAT] Reference only, for the like-for-like comparison against the Aira.
GRP = Material(
    name="GRP (hand-laid E-glass/polyester)",
    rho=1600.0,
    E_short=8_000e6,
    E_long=6_500e6,
    sigma_allow=90.0e6,
    weldable=False,
    bondable=True,
)


# ---------------------------------------------------------------------------
# Requirement envelope (from notes.txt -- these are the RS Aira's numbers)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Envelope:
    """The stated design limits. All are maxima."""

    loa_max: float = 6.50  # [NOTES] LOA < 6.50; [AIRA] Aira is exactly 6.50
    beam_max: float = 2.50  # [NOTES] BEA < 2.50 (EU road limit, no permit)
    disp_max: float = 750.0  # [NOTES] DIS < 750, light/dry incl. ballast
    sail_area_max: float = 22.0  # [NOTES] SQM < 22; [AIRA] 14.0 main + 8.0 jib
    water_ballast_max_l: float = 500.0  # [NOTES] BAL < 500 = litres of water
    # ballast (designer confirmed 2026-08-06), NOT a lead cap
    draft_max: float = 1.30  # [NOTES] CBD < 1.30, keel lowered

    def check(self, **actual: float) -> list[str]:
        """Return a list of human-readable violations."""
        limits = {
            "loa": self.loa_max,
            "beam": self.beam_max,
            "disp": self.disp_max,
            "sail_area": self.sail_area_max,
            "water_ballast_l": self.water_ballast_max_l,
            "draft": self.draft_max,
        }
        out = []
        for key, value in actual.items():
            limit = limits.get(key)
            if limit is not None and value > limit:
                out.append(f"{key} = {value:.3g} exceeds limit {limit:.3g}")
        return out


# ---------------------------------------------------------------------------
# Hull form
# ---------------------------------------------------------------------------


def _sheer_halfbeam_fractions() -> list[tuple[float, float]]:
    """(t, fraction of max sheer half-beam), t = x/LWL, 0 = transom, 1 = bow.

    [ASSUM] Wide, carried-aft plan form. The brief wants a 6-seat cockpit and a
    semi-open transom, both of which want beam kept aft; the fine entry forward
    is what keeps it from pounding.
    """
    return [
        (0.00, 0.88),
        (0.15, 0.96),
        (0.30, 1.00),
        (0.45, 1.00),
        (0.60, 0.95),
        (0.75, 0.81),
        (0.90, 0.52),
        (1.00, 0.03),
    ]


def _chine_halfbeam_fractions() -> list[tuple[float, float]]:
    """[ASSUM] Chine follows the sheer but with a finer entry."""
    return [
        (0.00, 0.86),
        (0.15, 0.95),
        (0.30, 1.00),
        (0.45, 0.99),
        (0.60, 0.90),
        (0.75, 0.70),
        (0.90, 0.38),
        (1.00, 0.02),
    ]


def _keel_rocker() -> list[tuple[float, float]]:
    """(t, z of keel line above baseline). [ASSUM] Modest rocker, flat run aft."""
    return [
        (0.00, 0.055),
        (0.15, 0.010),
        (0.30, 0.000),
        (0.45, 0.004),
        (0.60, 0.030),
        (0.75, 0.105),
        (0.90, 0.295),
        (1.00, 0.560),
    ]


def _sheer_height() -> list[tuple[float, float]]:
    """(t, z of sheer above baseline). [ASSUM] Sheer spring rising to the bow."""
    return [
        (0.00, 0.760),
        (0.15, 0.755),
        (0.30, 0.765),
        (0.45, 0.790),
        (0.60, 0.830),
        (0.75, 0.890),
        (0.90, 0.965),
        (1.00, 1.030),
    ]


@dataclass
class Hull:
    """Parametric hard-chine hull.

    Hard chine is not a stylistic choice here: rotomoulding and welded-sheet PE
    both want developable or near-developable surfaces, and a two-panel-per-side
    hull is the cheapest form to tool and the easiest to weld. It also happens
    to give more form stability than a round bilge of the same beam.
    """

    loa: float = 6.48  # [ASSUM] just inside the 6.50 cap
    lwl: float = 6.30  # [ASSUM]
    beam_sheer: float = 2.35  # [ASSUM] inside 2.50 road cap, wider than Aira's 2.20
    beam_chine_frac: float = 0.80  # [ASSUM] chine beam as fraction of sheer beam
    deadrise_frac: float = 0.30  # [ASSUM] chine height as fraction of local depth
    deck_camber: float = 0.055  # [ASSUM] crown at centreline above sheer
    transom_immersion: float = 0.055  # [ASSUM] keel z at transom

    n_stations: int = 61  # odd, for Simpson integration

    sheer_beam_curve: list[tuple[float, float]] = field(
        default_factory=_sheer_halfbeam_fractions
    )
    chine_beam_curve: list[tuple[float, float]] = field(
        default_factory=_chine_halfbeam_fractions
    )
    keel_curve: list[tuple[float, float]] = field(default_factory=_keel_rocker)
    sheer_curve: list[tuple[float, float]] = field(default_factory=_sheer_height)


@dataclass
class Cockpit:
    """The open cockpit -- and the reason self-righting is hard.

    Everything above ``sole_z`` and inboard of ``half_width`` is floodable. When
    the boat is inverted this volume is lost buoyancy, which is what kills the
    righting moment at large heel. ``sole_z`` is the parameter the brief leaves
    open (notes.txt line 30) and it is the one that decides whether the cockpit
    can self-drain at all.
    """

    x_aft: float = 0.35  # [NOTES] semi-open transom, drains aft
    x_fwd: float = 3.55  # [ASSUM] 3.2 m long cockpit, 6 seats
    half_width: float = 0.86  # [ASSUM]
    sole_z: float = 0.385  # [ASSUM] the open question -- see freeboard study
    seats: int = 6  # [NOTES] / [AIRA] "up to 6 adults"

    # The bench seats ARE the water ballast tanks (client, 2026-08-06): sealed
    # HDPE boxes along each cockpit side. Empty they are reserve buoyancy,
    # full they are ballast, and their tops are the seats.
    bench_inner_y: float = 0.44  # inboard face; footwell is 0.88 m wide
    bench_top_z: float = 0.80  # seat height = sole + 0.415, ergonomic
    # bench outboard face is the cockpit wall at half_width

    # Sealed reserve buoyancy. This is the only thing standing between an open
    # boat and a stable inverted equilibrium.
    bow_cuddy_x: float = 5.05  # [NOTES] bow cuddy, no cabin
    side_tank_half_width_frac: float = 1.0  # sealed out to the hull side
    sealed_under_sole: bool = True  # [NOTES] "reserva flotabilidad"


@dataclass
class Ballast:
    """Retractable (pivoting) keel plus water ballast in the bench tanks.

    "Quilla retractil" (client, 2026-08-06): the pivoting keel IS the
    retractable keel -- draft 1.28 m down, 0.30 m up, pivoting aft into the
    case. Chosen over a vertical daggerboard lift because a vertical trunk
    would stand ~1 m tall in the middle of the 6-seat cockpit and a pivot
    absorbs groundings by kicking up instead of jamming.

    The tanks are the cockpit bench seats (client decision, 2026-08-06), and
    the three roles want to be understood separately:

    - EMPTY and sealed, they are the reserve buoyancy of the cockpit benches
      ("reserva flotabilidad", notes line 38).
    - FULL on the windward side only, one tank is 250 kg at 0.65 m of lever:
      about 1.6 kN.m of righting moment, roughly two crew sitting to weather.
      This is the mode that earns the plumbing.
    - FULL and symmetric, they add 500 kg of displacement for damping and
      inertia. NOTE the height trade: tanks under the sole (z~0.26) would be
      high when inverted and actively destabilise the upside-down equilibrium
      (AVS +4 deg when full). At bench height (z~0.48) that benefit inverts:
      filling both tanks now COSTS ~6 deg of AVS (111 -> 105). Seats-as-tanks
      buys build simplicity and reserve buoyancy, and gives this up.
    """

    keel_mass: float = 250.0  # [AIRA] 250 kg; solved for in the weight budget
    keel_draft: float = 1.29  # [NOTES] CBD < 1.30; audited to bulb bottom
    keel_vcg_below_bl: float = 0.86  # [ASSUM] ballast VCG below baseline, lowered
    keel_pivot_x: float = 3.30  # [ASSUM]
    keel_up_draft: float = 0.30  # [ASSUM] canoe-body draft, keel raised

    water_ballast_each: float = 250.0  # [NOTES] BAL < 500 = 500 L total, 2 tanks
    water_ballast_tanks: int = 2  # [FLOW] port + starboard
    # Tanks live inside the cockpit benches (client, 2026-08-06). 250 L in a
    # 3.2 m x 0.42 m bench floods it 0.19 m deep from the sole: centroid 0.48.
    water_ballast_z: float = 0.48
    water_ballast_y: float = 0.65  # bench centreline off boat centreline

    @property
    def water_ballast_total(self) -> float:
        return self.water_ballast_each * self.water_ballast_tanks


@dataclass
class Rig:
    """Centred boom, short mast, square-top main, furling jib, no backstay.

    No traveller and no backstay means mainsheet load lands in one place on the
    centreline, and forestay tension is reacted by shroud geometry alone. Both
    are hard-point problems in a material that cannot be bonded.
    """

    main_area: float = 14.0  # [AIRA]
    jib_area: float = 8.0  # [AIRA]
    mast_height: float = 8.60  # [ASSUM] short mast per [NOTES] "mastil corto"
    boom_height: float = 1.80  # [NOTES] "botavara alta": 1.0 m above the
    # bench tops so a tall seated adult (pan + 0.95 m) clears it -- audited
    ce_height_above_sheer: float = 3.05  # [ASSUM] centre of effort
    square_top: bool = True  # [NOTES] "vela cuadrada"
    traveller: bool = False  # [NOTES] "no traveler"
    backstay: bool = False  # [NOTES] "no backstay"
    purchase: str = "2:1"  # [NOTES] "sin molinetes 2:1"

    @property
    def sail_area_upwind(self) -> float:
        return self.main_area + self.jib_area


@dataclass
class Propulsion:
    """Electric auxiliary. [NOTES] "electric engine"."""

    motor_mass: float = 26.0  # [ASSUM] ~4 kW outboard-format electric
    battery_kwh: float = 3.0  # [ASSUM]
    battery_wh_per_kg: float = 95.0  # [ASSUM] LiFePO4 pack level
    motor_z: float = 0.55  # [ASSUM]
    battery_z: float = 0.22  # [ASSUM] low, under the sole

    @property
    def battery_mass(self) -> float:
        return self.battery_kwh * 1000.0 / self.battery_wh_per_kg


@dataclass
class Structure:
    """How the shell is built.

    ``mode`` drives the scantling calculation:
      "single"  -- single-skin PE with internal stiffeners
      "double"  -- rotomoulded double skin (two skins separated by a gap)

    Single skin is the intuitive choice and it does not work at this size: see
    scantlings.py. Double skin is the reason the weight budget closes.
    """

    mode: str = "double"
    skin_t: float = 0.0050  # m, each skin in double-skin mode
    core_depth: float = 0.050  # m, gap between skins
    panel_span: float = 0.40  # m, short span between supports
    kiss_off_pitch: float = 0.075  # m, tack-off spacing; sets local skin span
    single_skin_t: float = 0.024  # m, if mode == "single"

    # Areas [ASSUM], refined from the geometry once it is built.
    hull_area: float = 19.5  # m^2 wetted+topsides shell
    deck_area: float = 8.2  # m^2 deck, cuddy, cockpit sole and sides
    reinforcement_factor: float = 1.12  # keel case, hard points, stiffeners


@dataclass
class Design:
    """The complete design."""

    envelope: Envelope = field(default_factory=Envelope)
    hull: Hull = field(default_factory=Hull)
    cockpit: Cockpit = field(default_factory=Cockpit)
    ballast: Ballast = field(default_factory=Ballast)
    rig: Rig = field(default_factory=Rig)
    propulsion: Propulsion = field(default_factory=Propulsion)
    structure: Structure = field(default_factory=Structure)
    material: Material = HDPE

    crew_mass_each: float = 80.0  # [ASSUM] ISO uses 75 kg; 80 is honest
    design_category: str = "C"  # [ASSUM] inshore; see ISO 12217-2 discussion


# The reference boat, for like-for-like comparison.
AIRA_22 = {
    "loa": 6.50,
    "hull_length": 6.50,
    "lwl": 6.45,
    "beam": 2.20,
    "draft_keel_down": 1.20,
    "draft_shallow_keel": 1.00,
    "disp": 750.0,
    "ballast": 250.0,
    "main": 14.0,
    "jib": 8.0,
    "gennaker": 28.0,
    "material": "GRP",
    "crew": 6,
}

# Flow 19, as recorded in notes.txt. The source URL 403s, so these are the
# designer's own notes and have not been independently verified.
FLOW_19 = {
    "beam": 2.30,
    "draft": 1.30,
    "disp": 450.0,
    "swing_keel": 70.0,
    "water_ballast_each": 60.0,
    "water_ballast_tanks": 2,
    "rudders": 2,
    "purchase": "2:1",
    "traveller": False,
    "backstay": False,
}
