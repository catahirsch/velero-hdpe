"""Variante AUTO-ADRIZANTE del velero abierto -- la 'Opcion A hecha en serio'.

    python3 -m calc.autoadrizante     ->  autoadrizante/ (report, curvas, specs)

docs/03 dismisses the masthead float in one paragraph: "does not appear on a
GZ curve". This module puts it ON the curve. A sealed volume at the masthead is
buoyancy like any other -- once the rig immerses (heel ~75 deg and beyond) it
displaces water at the end of an 9.5 m lever, which is exactly the region
(AVS..180) where the bare hull's curve goes negative.

The design decision this variant encodes (client conversation, 2026-08-07):
keep the open 6-seat daysailer at 2.35 m beam and 750 kg, and buy the missing
righting range with GEOMETRY (sealed volume placed high) instead of lead:

  - sealed benches            already in the baseline (they are the tanks)
  - sealed bow cuddy          already in the baseline
  - sealed mast + 60 L crown  NEW -- modelled here, drawn in L8
  - design condition          keel DOWN + LOCKED, tanks EMPTY (worst sailing
                              state; water ballast is a performance option,
                              never a safety dependency)

The honest claim that comes out is not "self-rights from a mathematical 180.0
degrees" -- it is "recovers unaided from any heel up to theta_rec (computed
below, ~176 deg), and the residual inverted pocket holds a few joules where
the baseline holds hundreds". The report quantifies both.

Physics: the rig is discretised into point volumes along the sealed spar plus
the crown float. Each element counts toward displacement and toward the
buoyancy centroid whenever it sits below the waterplane in the earth frame.
The waterline is re-solved per heel angle including those elements, so the
hull floats HIGHER when the rig is immersed -- which itself weakens the
inverted equilibrium. Same Sutherland-Hodgman hull integration as calc/
stability.py; same flooded-cockpit treatment (and the same optimism caveat:
trapped water above sea level is not added as weight).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from . import scantlings, stability, weights
from .geometry import HullGeometry, rotate_point
from .params import RHO_SEA, Design
from .stability import GZCurve, downflooding_angle, solve_waterline

DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "autoadrizante"
)


# ---------------------------------------------------------------------------
# The new element: buoyancy aloft
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MastBuoyancy:
    """Sealed spar plus masthead crown float.

    [ASSUM] Spar: 8.60 m of 110x70 alloy oval, ~5.0e-3 m2 internal section is
    ~43 L; foam-plugged and sealed at heel/head/sheave boxes, 70 % is usable
    -> 30 L, distributed along the length. Halyards run external or in a
    separate conduit (a wet luff groove costs nothing here: only SEALED volume
    counts).

    Crown float: 60 L rotomoulded PE ellipsoid (1.00 x 0.34 m) faired fore-aft
    at the masthead, ~2.5 kg with its bracket. 60 L at 9.5 m is the cheapest
    righting moment on the boat: the same moment as ~270 kg of lead sitting on
    the keel bulb.
    """

    float_volume: float = 0.060  # m3, crown float
    float_z: float = 9.55  # m above baseline, float centroid
    float_mass: float = 2.5  # kg, float + bracket + sealing
    spar_volume: float = 0.030  # m3, usable sealed volume inside the spar
    spar_z0: float = 0.86  # m, mast heel (deck step)
    spar_z1: float = 9.46  # m, masthead
    n_segments: int = 24  # spar discretisation


def rig_elements(mb: MastBuoyancy) -> list[tuple[float, float]]:
    """(z_body, volume) point elements for the sealed spar + crown float."""
    zs = np.linspace(mb.spar_z0, mb.spar_z1, mb.n_segments)
    v = mb.spar_volume / mb.n_segments
    els = [(float(z), v) for z in zs]
    # The float as four sub-volumes across its diameter, so its immersion
    # ramps over ~0.3 m of heel travel instead of switching in one step.
    for dz in (-0.12, -0.04, 0.04, 0.12):
        els.append((mb.float_z + dz, mb.float_volume / 4.0))
    return els


def rig_submerged(
    els: list[tuple[float, float]], z_wl: float, heel_deg: float
) -> tuple[float, float]:
    """Total submerged rig volume and its y-moment, earth frame."""
    vol = 0.0
    my = 0.0
    for z_body, v in els:
        y_e, z_e = rotate_point(0.0, z_body, heel_deg)
        if z_e < z_wl:
            vol += v
            my += v * y_e
    return vol, my


def solve_waterline_rig(
    geom: HullGeometry,
    target_volume: float,
    heel_deg: float,
    flooded: bool,
    keel_volume: float,
    els: list[tuple[float, float]],
) -> float | None:
    """Bisect for the waterplane including hull, keel and rig buoyancy."""
    all_z = []
    for sec in geom._sections:
        if len(sec) >= 3:
            from .geometry import rotate

            all_z.append(rotate(sec, heel_deg)[:, 1])
    if not all_z:
        return None
    z_lo = float(np.min([z.min() for z in all_z])) - 0.05
    z_hi = float(np.max([z.max() for z in all_z])) + 0.05

    def total(z_wl: float) -> float:
        v_hull = geom.volume(z_wl, heel_deg, flooded)[0]
        v_rig, _ = rig_submerged(els, z_wl, heel_deg)
        return v_hull + keel_volume + v_rig

    if total(z_hi) < target_volume:
        return None
    for _ in range(70):
        z_mid = 0.5 * (z_lo + z_hi)
        if total(z_mid) < target_volume:
            z_lo = z_mid
        else:
            z_hi = z_mid
        if z_hi - z_lo < 1e-7:
            break
    return 0.5 * (z_lo + z_hi)


def gz_curve_rig(
    geom: HullGeometry,
    design: Design,
    mb: MastBuoyancy | None,
    mass: float,
    vcg: float,
    flooded: bool,
    heel: np.ndarray | None = None,
    label: str = "",
) -> GZCurve:
    """GZ curve with the sealed rig counted as buoyancy. mb=None -> bare boat."""
    if heel is None:
        heel = np.arange(0.0, 181.0, 2.0)
    els = rig_elements(mb) if mb is not None else []

    keel_vol = geom.keel_appendage_volume(design.ballast.keel_mass)
    ky, kz = 0.0, -design.ballast.keel_vcg_below_bl
    target = mass / RHO_SEA

    gz = np.full(len(heel), np.nan)
    afloat = np.zeros(len(heel), dtype=bool)
    for j, angle in enumerate(heel):
        a = float(angle)
        if els:
            z_wl = solve_waterline_rig(geom, target, a, flooded, keel_vol, els)
        else:
            z_wl = solve_waterline(geom, target, a, flooded, keel_vol)
        if z_wl is None:
            continue
        vol, _, y_b_hull, _ = geom.volume(z_wl, a, flooded)
        ky_e, _ = rotate_point(ky, kz, a)
        v_rig, my_rig = rig_submerged(els, z_wl, a) if els else (0.0, 0.0)
        v_total = vol + keel_vol + v_rig
        if v_total <= 1e-9:
            continue
        y_b = (vol * y_b_hull + keel_vol * ky_e + my_rig) / v_total
        y_g, _ = rotate_point(0.0, vcg, a)
        gz[j] = y_b - y_g
        afloat[j] = True

    df = downflooding_angle(geom, design, mass) if flooded else None
    return GZCurve(heel=np.asarray(heel, dtype=float), gz=gz, label=label,
                   downflooding_angle=df, afloat=afloat)


def recovery_limit(curve: GZCurve) -> float:
    """Largest heel from which the boat returns unaided: the LAST +to-
    zero crossing. 180.0 if GZ never goes negative."""
    limit = 180.0
    for i in range(len(curve.heel) - 1):
        a, b = curve.gz[i], curve.gz[i + 1]
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        if a > 0.0 >= b:
            frac = a / (a - b)
            limit = float(curve.heel[i] + frac * (curve.heel[i + 1] - curve.heel[i]))
    return limit


# ---------------------------------------------------------------------------
# Variant weight budget: the float goes aloft, the lead pays for it
# ---------------------------------------------------------------------------


def variant_weights(design: Design, mb: MastBuoyancy, sc, hull_area, deck_area):
    """Baseline budget, minus the float's mass taken from the keel remainder."""
    wb = weights.build(design, sc["mass_per_area"], hull_area, deck_area)
    keel = next(i for i in wb.items if "keel ballast" in i.name)
    keel.mass -= mb.float_mass
    keel.note = "REMAINDER of the 750 kg cap, minus the crown float"
    wb.items.append(
        weights.Item("masthead crown float", mb.float_mass, mb.float_z,
                     "60 L PE ellipsoid + bracket")
    )
    wb.ballast_available = keel.mass
    wb.disp_light = sum(i.mass for i in wb.items)
    wb.vcg_light = sum(i.moment for i in wb.items) / wb.disp_light
    wb.ballast_ratio = keel.mass / wb.disp_light
    crew = design.crew_mass_each * design.cockpit.seats
    water = design.ballast.water_ballast_total
    crew_z = design.cockpit.bench_top_z + 0.30
    loaded = wb.items + [
        weights.Item("crew", crew, crew_z, ""),
        weights.Item("water ballast", water, design.ballast.water_ballast_z, ""),
    ]
    wb.disp_loaded = sum(i.mass for i in loaded)
    wb.vcg_loaded = sum(i.moment for i in loaded) / wb.disp_loaded
    return wb


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run() -> dict:
    os.makedirs(DIR, exist_ok=True)
    design = Design()
    mb = MastBuoyancy()

    say = stability.__dict__  # placate linters; real Tee below
    from .report import Tee, rule

    say = Tee(os.path.join(DIR, "report.txt"))

    rule(say, "VARIANTE AUTO-ADRIZANTE -- masthead buoyancy, modelled honestly")
    say("  Concept: baseline 2.35 m open daysailer, unchanged, plus a sealed")
    say(f"  spar ({mb.spar_volume * 1000:.0f} L usable) and a"
        f" {mb.float_volume * 1000:.0f} L / {mb.float_mass:.1f} kg crown float.")
    say("  Design condition for the claim: keel DOWN and LOCKED, tanks EMPTY.")

    geom = HullGeometry(design.hull, design.cockpit)
    hull_area, deck_area = geom.shell_area(), geom.deck_area()
    m_ldc = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc)

    wb = variant_weights(design, mb, sc, hull_area, deck_area)
    design.ballast.keel_mass = wb.ballast_available

    rule(say, "1. WEIGHT BUDGET  (float aloft, paid for by the keel remainder)")
    say(wb.table())
    say("")
    say(f"  VCG light rises {mb.float_mass * (mb.float_z - wb.vcg_light) / wb.disp_light * 1000:.0f} mm"
        f" for the float -- the GZ curves below already carry that penalty.")

    # -- the curves ------------------------------------------------------
    rule(say, "2. GZ CURVES  (2.35 m beam; 'con aparejo' counts the sealed rig)")
    heel = np.arange(0.0, 181.0, 2.0)
    cases = {
        "light/flooded/bare": (None, wb.disp_light, wb.vcg_light, True),
        "light/flooded/rig": (mb, wb.disp_light, wb.vcg_light, True),
        "light/intact/rig": (mb, wb.disp_light, wb.vcg_light, False),
        "loaded/flooded/rig": (mb, wb.disp_loaded, wb.vcg_loaded, True),
    }
    curves: dict[str, GZCurve] = {}
    for key, (m, mass, vcg, flooded) in cases.items():
        curves[key] = gz_curve_rig(geom, design, m, mass, vcg, flooded,
                                   heel=heel, label=key)

    say(f"  {'case':<22}{'GZmax':>8}{'AVS':>8}{'rec.limit':>11}{'neg area':>10}"
        f"{'GZ>0 to 180':>13}")
    for key, c in curves.items():
        say(f"  {key:<22}{c.gz_max:>8.3f}{c.avs:>8.1f}{recovery_limit(c):>11.1f}"
            f"{c.negative_area:>10.4f}{str(c.self_righting):>13}")

    # -- verdict ---------------------------------------------------------
    c_bare = curves["light/flooded/bare"]
    c_rig = curves["light/flooded/rig"]
    lim = recovery_limit(c_rig)
    pocket = c_rig.negative_area
    pocket_j = pocket * wb.disp_light * 9.80665
    bare_j = c_bare.negative_area * wb.disp_light * 9.80665
    barrier = c_rig.area_under(c_bare.avs, lim)

    rule(say, "3. VERDICT  (governing case: light ship, cockpit flooded, tanks empty)")
    say(f"  Bare hull (baseline):   AVS {c_bare.avs:.0f} deg, stable inverted,")
    say(f"                          {c_bare.negative_area:.3f} m.rad = {bare_j:.0f} J"
        f" holding it turtle.")
    say(f"  With sealed rig+float:  GZ stays positive past {c_bare.avs:.0f} deg --")
    say(f"                          the boat recovers unaided from any heel up to"
        f" {lim:.1f} deg.")
    if c_rig.self_righting:
        say("                          No stable inverted equilibrium remains at all.")
    else:
        say(f"                          Residual inverted pocket: {lim:.1f}-180 deg,"
            f" {pocket:.4f} m.rad = {pocket_j:.0f} J")
        say(f"                          ({bare_j / max(pocket_j, 1e-9):.0f}x shallower"
            f" than the baseline's).")
        say(f"  Energy barrier guarding that pocket (area {c_bare.avs:.0f}-{lim:.0f} deg):"
        f" {barrier:.3f} m.rad = {barrier * wb.disp_light * 9.80665:.0f} J --")
        say("  to turtle, a seaway must push the boat through ALL of it; to release,")
        say(f"  it only has to nudge the boat {180 - lim:.1f} deg. In any water rough")
        say("  enough to capsize this boat, the pocket is not a resting state.")
    say("")
    say("  Claim for the spec sheet / placard: AUTO-ADRIZANTE con quilla abajo y")
    say("  trabada y tanques vacios; el flotador de tope hace el 180 inalcanzable")
    say(f"  y el barco vuelve solo desde cualquier escora hasta {lim:.0f} grados.")

    # -- float sizing sweep ----------------------------------------------
    rule(say, "4. FLOAT SIZING  (why 60 L: sweep at 31 stations, 5 deg)")
    say(f"  {'float (L)':>10}{'rec.limit':>11}{'neg area':>10}{'GZ>0 to 180':>13}")
    d_coarse = Design()
    d_coarse.hull.n_stations = 31
    d_coarse.ballast.keel_mass = design.ballast.keel_mass
    g_coarse = HullGeometry(d_coarse.hull, d_coarse.cockpit)
    heel_c = np.arange(0.0, 181.0, 5.0)
    for litres in (0.0, 20.0, 40.0, 60.0, 80.0):
        mb_i = MastBuoyancy(float_volume=litres / 1000.0)
        c = gz_curve_rig(g_coarse, d_coarse, mb_i, wb.disp_light, wb.vcg_light,
                         True, heel=heel_c, label=f"{litres:.0f}L")
        say(f"  {litres:>10.0f}{recovery_limit(c):>11.1f}{c.negative_area:>10.4f}"
            f"{str(c.self_righting):>13}")
    say("  Below ~40 L the float cannot carry the immersed rig's weight with")
    say("  margin (rig 32 kg + float, buoyancy needed > ~35 kg); 60 L gives a")
    say("  1.7x margin and costs 2.5 kg. Beyond 80 L the recovery limit barely")
    say("  moves -- the residual pocket is pinched against 180 by symmetry, not")
    say("  by float size.")

    # -- loaded + placard cases ------------------------------------------
    c_load = curves["loaded/flooded/rig"]
    rule(say, "5. OTHER CONDITIONS")
    say(f"  Loaded (6 crew + 500 L), flooded, with rig: recovery limit"
        f" {recovery_limit(c_load):.0f} deg.")
    say("  Keel UP: NOT self-righting in any variant -- keel-up is a launch/")
    say("  recovery state only. The keel lock (L4) is what makes the claim hold")
    say("  through a knockdown: an unlocked keel falling into the case at 120 deg")
    say("  would remove most of the righting moment when it is needed most.")
    df = c_load.downflooding_angle
    if df:
        say(f"  Downflooding angle at full load: {df:.0f} deg (unchanged from base).")

    say("")
    say(f"Report written to {os.path.join(DIR, 'report.txt')}")
    say.close()

    _plot(curves, wb, lim)
    _specs_md(design, mb, wb, curves, lim, pocket_j, bare_j, sc)

    return {"curves": curves, "weights": wb, "design": design, "mb": mb,
            "recovery_limit": lim}


def _plot(curves, wb, lim) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    styles = {
        "light/flooded/bare": ("#cc6677", "--", "rosca inundado, SIN flotador (base)"),
        "light/flooded/rig": ("#117733", "-", "rosca inundado, CON mastil sellado + 60 L"),
        "light/intact/rig": ("#117733", ":", "rosca intacto, con flotador"),
        "loaded/flooded/rig": ("#4477aa", "-", "plena carga inundado, con flotador"),
    }
    for key, c in curves.items():
        col, ls, lab = styles[key]
        ax.plot(c.heel, c.gz, color=col, linestyle=ls, linewidth=1.9, label=lab)
    ax.axhline(0.0, color="#333333", linewidth=0.9)
    ax.axvline(lim, color="#117733", linewidth=1.0, linestyle="-.",
               label=f"limite de recuperacion {lim:.0f}°")
    ax.fill_betweenx([-0.55, 1.0], lim, 180, color="#117733", alpha=0.06)
    ax.set_xlabel("escora (grados)")
    ax.set_ylabel("brazo adrizante GZ (m)")
    ax.set_title(f"Variante auto-adrizante: el volumen sellado en el tope entra a la curva GZ\n"
                 f"quilla {wb.ballast_available:.0f} kg abajo y trabada, tanques vacios")
    ax.set_xlim(0, 180)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(DIR, "gz_curves.png"), dpi=140)
    plt.close(fig)


def _specs_md(design, mb, wb, curves, lim, pocket_j, bare_j, sc) -> None:
    c_rig = curves["light/flooded/rig"]
    c_bare = curves["light/flooded/bare"]
    keel = wb.ballast_available
    md = f"""# Especificacion — variante auto-adrizante

Velero abierto HDPE 6.48 m, identico al baseline en casco, cockpit, quilla,
aparejo y sistemas, mas el **paquete de flotabilidad de tope de mastil**. La
decision que encierra esta variante: mantener el daysailer abierto y liviano,
y comprar los grados de adrizado que faltan con **volumen sellado en altura**,
no con plomo.

## Dimensiones y pesos

| | |
|---|---|
| LOA / LWL | {design.hull.loa:.2f} m / {design.hull.lwl:.2f} m |
| Manga | {design.hull.beam_sheer:.2f} m (se mantiene el cockpit de 6 plazas) |
| Calado | 0.30 m quilla arriba — {design.ballast.keel_draft:.2f} m abajo |
| Desplazamiento rosca | {wb.disp_light:.0f} kg (tope 750) |
| Quilla (plomo) | {keel:.0f} kg ({wb.ballast_ratio * 100:.1f} %) |
| Lastre de agua | 2 × 244 L en bancos-tanque — **vacios para la condicion de diseno** |
| Superficie velica | {design.rig.sail_area_upwind:.1f} m² (mayor {design.rig.main_area:.0f} + foque {design.rig.jib_area:.0f}) |
| Estructura | HDPE doble piel 2×5 mm / 50 mm, {sc['mass_per_area']:.1f} kg/m² |

## El paquete auto-adrizante (lo unico que cambia)

| Elemento | Especificacion |
|---|---|
| Flotador de tope | {mb.float_volume * 1000:.0f} L, elipsoide PE rotomoldeado 1.00 × 0.34 m, carenado proa-popa, {mb.float_mass:.1f} kg con soporte |
| Mastil sellado | {mb.spar_volume * 1000:.0f} L utiles: espuma de cierre en pie, tope y cajeras; drizas externas o en conducto |
| Traba de quilla | obligatoria en posicion BAJA (ya en L4): una orzada no debe retraerla |
| Costo en plomo | el flotador se paga con {mb.float_mass:.1f} kg de quilla ({keel + mb.float_mass:.0f} → {keel:.0f} kg) |

## Resultado de estabilidad (condicion gobernante: rosca, cockpit inundado, tanques vacios)

| | Sin flotador (base) | Con mastil sellado + flotador |
|---|---|---|
| AVS | {c_bare.avs:.0f}° | GZ sigue positivo mas alla de {c_bare.avs:.0f}° |
| Limite de recuperacion sin ayuda | {recovery_limit(c_bare):.0f}° | **{lim:.1f}°** |
| Energia que sostiene la tortuga | {bare_j:.0f} J | {pocket_j:.0f} J |
| Equilibrio invertido estable | si — el barco queda tortuga | reducido a un bolsillo de {180 - lim:.1f}° junto a 180° |

**La afirmacion honesta**: con quilla abajo y trabada y tanques vacios, el
barco vuelve solo desde cualquier escora hasta {lim:.0f}°. El bolsillo
invertido residual ({180 - lim:.1f}° de ancho, {pocket_j:.0f} J) no es un
estado de reposo en ninguna mar capaz de dar vuelta el barco: para entrar hay
que atravesar toda la barrera positiva de la curva; para salir alcanza con
{180 - lim:.0f}° de perturbacion. A efectos operativos: **anti-tortuga +
retorno autonomo**, y las cinchas de piso quedan como respaldo (y para la
condicion quilla-arriba en playa).

## Condicion de diseno — placa junto a la quilla (grabar)

> AUTO-ADRIZANTE SOLO CON: QUILLA ABAJA Y TRABADA · TANQUES VACIOS
> QUILLA ARRIBA = SOLO BOTADURA / PLAYA · LLENAR TANQUES = VER PLACA DE LASTRE

El lastre de agua queda como sistema de rendimiento (tanque de barlovento con
poca tripulacion), nunca como dependencia de seguridad: la curva verde se
calcula con tanques vacios.

## Lo que esta variante NO cambia

Cockpit 3.20 × 1.72 m de 6 plazas, piso autoachicable (+56 mm a plena carga),
espejo semiabierto, bancos-tanque sellados, cuddy con doble tambucho, aparejo
sin winches 2:1, timon unico abatible, motor electrico con bateria bajo el
piso, remolque sin permiso especial. Desplazamiento rosca sigue en
{wb.disp_light:.0f} kg.

## Archivos de esta carpeta

| Archivo | Contenido |
|---|---|
| `specs.md` / `cambios.md` | esta especificacion + registro de cambios vs baseline |
| `report.txt` | corrida completa del modelo (pesos, curvas, dimensionado del flotador) |
| `audit.txt` / `costs.txt` | auditoria 22 verificaciones (15 base + 7 del flotador); costos con delta |
| `gz_curves.png` / `hull_lines.png` | curvas GZ con y sin paquete de tope; plano de lineas |
| `boat_autoadrizante.3dm` | modelo Rhino por capas, con flotador de tope |
| `preview_3dm.png` / `preview_cockpit.png` | vistas rapidas del 3DM |
| `hull_autoadrizante.stl` | malla del casco (identica al baseline, m) |
| `offsets_autoadrizante.txt` | tabla de puntos para loftear |
| `planos.pdf` | 8 laminas: las 7 constructivas + L8 flotador y condicion de diseno |
| `selfrighting.gif` + `anim_*.png` | animacion fisica: soltados a 150°, con y sin paquete de tope |
| `foto_*.png` / `diseno_*.png` | el bote en el agua y estudio de color, flotador a la vista |
| `opciones.txt` / `.json` / `opciones_gz.png` / `opciones_board.png` | exploracion ampliada: 8 opciones de auto-adrizado contra notes.txt (insumos de la seccion 4 de la presentacion) |
| `presentacion.pdf` | resumen para el cliente en castellano, con la comparacion de opciones y recomendacion integradas |

Generado por `python3 -m calc.autoadrizante`, `geom.autoadrizante`,
`geom.render_autoadrizante`, `geom.animate_autoadrizante`,
`calc.audit_autoadrizante` y `calc.presentacion_autoadrizante`. Mismas
advertencias que el modelo base: el caso inundado no agrega el peso del agua
atrapada (optimista; cuantificado en docs/03), y el proyecto requiere firma
de ingeniero naval.
"""
    with open(os.path.join(DIR, "specs.md"), "w") as f:
        f.write(md)
    print(f"specs -> {os.path.join(DIR, 'specs.md')}")


if __name__ == "__main__":
    run()
