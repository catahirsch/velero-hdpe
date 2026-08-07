"""HDPE panel scantlings.

The headline result: for HDPE at this size, **deflection governs, not stress**.
The material's allowable stress is low but its creep-derated modulus is lower
still relative to glass, so a panel sized to not break is still far too floppy.
That inverts the usual FRP intuition and it is why single-skin HDPE does not
work on a 6.5 m hull -- the required thickness comes out around 23 mm, which is
both unmouldable in one shot and ruinously heavy.

Design pressures follow the *form* of ISO 12215-5 so the numbers are recognisable
and defensible. They are indicative only: **ISO 12215-5 has no rotomoulded-PE
path.** Its scantling formulas cover FRP, aluminium, steel, plywood and wood.
Certifying a PE hull runs through physical testing instead -- see docs/02.
"""

from __future__ import annotations

from dataclasses import dataclass

from .params import Design, Material

# Clamped long-plate coefficients (aspect ratio >= 2), Poisson ratio 0.4 for PE.
BETA_STRESS = 0.5  # sigma = BETA * p * b^2 / t^2
NU = 0.4
ALPHA_DEFL = (1.0 - NU**2) / 32.0  # delta = ALPHA * p * b^4 / (E * t^3)

DEFLECTION_LIMIT = 0.015  # delta/b. Tighter than FRP practice: PE creeps.

# ISO 12215-5 design category factors.
K_DC = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4}


@dataclass
class PanelResult:
    name: str
    pressure: float  # Pa
    span: float  # m
    t_stress: float  # m, required for strength
    t_deflection: float  # m, required for stiffness
    governing: str

    @property
    def t_required(self) -> float:
        return max(self.t_stress, self.t_deflection)


@dataclass
class SandwichResult:
    skin_t: float
    core_depth: float
    t_equivalent: float  # equivalent solid thickness for bending stiffness
    face_stress: float  # Pa
    skin_t_required_local: float  # m, skin as a panel between kiss-offs
    mass_per_area: float  # kg/m^2
    passes_global: bool
    passes_local: bool
    passes_stress: bool


def design_pressures(design: Design, m_ldc: float) -> dict[str, float]:
    """Indicative ISO 12215-5-style design pressures, in pascals.

    ``m_ldc`` is loaded displacement mass in kg.
    """
    k_dc = K_DC[design.design_category]
    m33 = m_ldc**0.33
    bottom = (2.4 * m33 + 20.0) * k_dc
    side = (1.5 * m33 + 20.0) * k_dc
    deck = max(0.35 * (1.5 * m33 + 20.0) * k_dc, 5.0)
    # Cockpit sole carries crew as a live load, and is a watertight boundary
    # once the cockpit is self-draining.
    sole = max(deck, 6.0)
    return {
        "bottom": bottom * 1000.0,
        "side": side * 1000.0,
        "deck": deck * 1000.0,
        "cockpit_sole": sole * 1000.0,
    }


def single_skin(
    name: str, pressure: float, span: float, mat: Material
) -> PanelResult:
    """Required single-skin thickness for strength and for stiffness."""
    t_stress = span * (pressure / (2.0 * mat.sigma_allow)) ** 0.5
    t_defl = (
        ALPHA_DEFL * pressure * span**3 / (mat.E_long * DEFLECTION_LIMIT)
    ) ** (1.0 / 3.0)
    governing = "deflection" if t_defl > t_stress else "stress"
    return PanelResult(name, pressure, span, t_stress, t_defl, governing)


def sandwich(
    pressure: float,
    span: float,
    skin_t: float,
    core_depth: float,
    kiss_off_pitch: float,
    mat: Material,
    t_required: float,
) -> SandwichResult:
    """Evaluate a rotomoulded double skin against the single-skin requirement.

    Two skins separated by a gap act as the flanges of an I-beam. Bending
    stiffness per unit width is E*(2*t*(d/2)^2), so the equivalent solid
    thickness is (6*t*d^2)^(1/3) -- typically 4-5x the material actually used.
    That is the whole reason the weight budget closes.
    """
    t_eq = (6.0 * skin_t * core_depth**2) ** (1.0 / 3.0)

    # Face stress from the clamped-edge moment, carried as a couple over d.
    moment = pressure * span**2 / 12.0
    face_stress = moment / (skin_t * core_depth)

    # Each skin also spans locally between kiss-offs, deflection-governed again.
    local = single_skin("skin_local", pressure, kiss_off_pitch, mat)
    t_local_req = max(local.t_stress, local.t_deflection)

    return SandwichResult(
        skin_t=skin_t,
        core_depth=core_depth,
        t_equivalent=t_eq,
        face_stress=face_stress,
        skin_t_required_local=t_local_req,
        mass_per_area=2.0 * skin_t * mat.rho,
        passes_global=t_eq >= t_required,
        passes_local=skin_t >= t_local_req,
        passes_stress=face_stress <= mat.sigma_allow,
    )


def evaluate(design: Design, m_ldc: float) -> dict:
    """Full scantling evaluation for the design's structural mode."""
    mat = design.material
    st = design.structure
    p = design_pressures(design, m_ldc)

    spans = {
        "bottom": st.panel_span,
        "side": st.panel_span,
        "deck": st.panel_span * 1.15,
        "cockpit_sole": st.panel_span * 0.9,
    }

    panels = {
        k: single_skin(k, p[k], spans[k], mat) for k in ("bottom", "side", "deck", "cockpit_sole")
    }
    governing_t = max(max(r.t_stress, r.t_deflection) for r in panels.values())

    result: dict = {
        "pressures": p,
        "panels": panels,
        "single_skin_required_t": governing_t,
        "mode": st.mode,
    }

    if st.mode == "double":
        kiss_off = st.kiss_off_pitch
        sw = {}
        for key, r in panels.items():
            sw[key] = sandwich(
                pressure=r.pressure,
                span=spans[key],
                skin_t=st.skin_t,
                core_depth=st.core_depth,
                kiss_off_pitch=kiss_off,
                mat=mat,
                t_required=max(r.t_stress, r.t_deflection),
            )
        result["sandwich"] = sw
        result["mass_per_area"] = 2.0 * st.skin_t * mat.rho
        result["all_pass"] = all(
            s.passes_global and s.passes_local and s.passes_stress for s in sw.values()
        )
    else:
        result["mass_per_area"] = st.single_skin_t * mat.rho
        result["all_pass"] = st.single_skin_t >= governing_t

    # For the like-for-like comparison against the GRP Aira.
    from .params import GRP

    grp_panels = {
        k: single_skin(k, p[k], spans[k], GRP) for k in panels
    }
    grp_t = max(max(r.t_stress, r.t_deflection) for r in grp_panels.values())
    result["grp_equivalent_t"] = grp_t
    result["grp_mass_per_area"] = grp_t * GRP.rho
    result["stiffness_thickness_ratio"] = governing_t / grp_t if grp_t else float("nan")

    return result
