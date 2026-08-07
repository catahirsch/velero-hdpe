"""Geometria de la variante auto-adrizante.

    python3 -m geom.autoadrizante   ->  autoadrizante/
        hull_autoadrizante.stl        malla del casco (identica al baseline)
        offsets_autoadrizante.txt     tabla de puntos
        boat_autoadrizante.3dm        modelo Rhino por capas + flotador de tope
        planos.pdf                    8 laminas: L1-L7 constructivas + L8 flotador
        perfil_flotador.png           perfil con aparejo y flotador (presentacion)

El casco, cockpit, quilla y aparejo son los del baseline sin cambios: la
variante agrega el paquete de tope de mastil (mastil sellado + flotador 60 L)
y la condicion de diseno quilla-abajo-trabada / tanques-vacios. Ver
calc/autoadrizante.py para la fisica.
"""

from __future__ import annotations

import copy
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Ellipse, FancyArrowPatch

from calc.autoadrizante import DIR, MastBuoyancy, gz_curve_rig, recovery_limit
from calc.geometry import HullGeometry
from calc.params import Design
from geom import drawings, export_3dm
from geom.hull import build_mesh, write_offsets, write_stl

TAG = "autoadrizante"


# ---------------------------------------------------------------------------
# STL + offsets (hull is the baseline hull)
# ---------------------------------------------------------------------------


def export_hull(design: Design) -> None:
    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    verts, tris = build_mesh(geom)
    stl_path = os.path.join(DIR, f"hull_{TAG}.stl")
    n = write_stl(stl_path, verts, tris, name=f"hdpe-daysailer-{TAG}")
    off_path = os.path.join(DIR, f"offsets_{TAG}.txt")
    write_offsets(off_path, geom)
    print(f"[{TAG}] stl {n} facets -> {stl_path}")
    print(f"[{TAG}] offsets -> {off_path}")


# ---------------------------------------------------------------------------
# 3DM: baseline boat + capa 'flotador-tope'
# ---------------------------------------------------------------------------


def ellipsoid_mesh(cx, cy, cz, rx, ry, rz, nu=16, nv=10) -> tuple[list, list]:
    verts, faces = [], []
    for i in range(nv + 1):
        th = np.pi * i / nv
        for j in range(nu):
            ph = 2.0 * np.pi * j / nu
            verts.append((cx + rx * np.sin(th) * np.cos(ph),
                          cy + ry * np.sin(th) * np.sin(ph),
                          cz + rz * np.cos(th)))
    for i in range(nv):
        for j in range(nu):
            j2 = (j + 1) % nu
            a, b = i * nu + j, i * nu + j2
            c, d = (i + 1) * nu + j2, (i + 1) * nu + j
            faces += [(a, b, c), (a, c, d)]
    return verts, faces


def export_boat_3dm(design: Design, mb: MastBuoyancy) -> None:
    import rhino3dm as r3

    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    z_light, z_loaded = export_3dm.solve_waterlines(copy.deepcopy(d), geom)

    model, attrs = export_3dm.make_model()
    layer = r3.Layer()
    layer.Name = "flotador-tope"
    layer.Color = (200, 80, 60, 255)
    idx = model.Layers.Add(layer)
    a = r3.ObjectAttributes()
    a.LayerIndex = idx
    attrs["flotador-tope"] = a

    model.ApplicationName = "bote geom/autoadrizante.py"
    model.StartSectionComments = (
        f"Variante AUTO-ADRIZANTE. Casco = baseline (LOA {d.hull.loa:.2f} m, manga "
        f"{geom.max_beam:.2f} m) + mastil sellado ({mb.spar_volume * 1000:.0f} L) + "
        f"flotador de tope {mb.float_volume * 1000:.0f} L. Condicion de diseno: "
        f"quilla abajo y trabada, tanques vacios. Unidades: metros. "
        f"Flotaciones: rosca z={z_light:.3f}, plena carga z={z_loaded:.3f}."
    )

    export_3dm.add_mesh(model, attrs["hull"], *export_3dm.hull_mesh(geom))
    export_3dm.add_keel(model, attrs["keel"], d)
    export_3dm.add_rudders(model, attrs["rudders"], geom)
    export_3dm.add_rig(model, attrs, d, geom)
    export_3dm.add_tanks(model, attrs["bench-tanks"], d)
    export_3dm.add_waterlines(model, attrs["waterlines"], z_light, z_loaded, d.hull.loa)
    export_3dm.add_lines(model, attrs["lines"], geom)
    # El flotador: elipsoide 1.00 x 0.34 m carenado proa-popa en el tope.
    export_3dm.add_mesh(model, attrs["flotador-tope"],
                        *ellipsoid_mesh(4.25, 0.0, mb.float_z, 0.50, 0.17, 0.17))

    path = os.path.join(DIR, f"boat_{TAG}.3dm")
    ok = model.Write(path, 7)
    print(f"[{TAG}] {'written' if ok else 'WRITE FAILED'}: {path}")
    export_3dm.verify(path)


# ---------------------------------------------------------------------------
# L8 + perfil
# ---------------------------------------------------------------------------


def _draw_profile(ax, geom: HullGeometry, d: Design, mb: MastBuoyancy) -> None:
    """Perfil completo con aparejo y flotador, para L8 y la presentacion."""
    mast_x, deck_z, head_z = 4.25, 0.86, 9.46
    boom_z = d.rig.boom_height
    hounds = deck_z + 0.82 * 8.60
    ax.plot(geom.x, geom.z_sheer, color=drawings.INK, lw=1.4)
    ax.plot(geom.x, geom.z_keel, color=drawings.INK, lw=1.4)
    ax.plot([geom.x[0]] * 2, [geom.z_keel[0], geom.z_sheer[0]],
            color=drawings.INK, lw=1.4)
    # quilla abajo
    px = d.ballast.keel_pivot_x
    ax.plot([px + 0.24, px - 0.14, px + 0.16, px + 0.26, px + 0.24],
            [0.02, -0.90, -0.90, 0.02, 0.02], color=drawings.INK, lw=1.0)
    ax.add_patch(plt.Rectangle((px - 0.29, -1.075), 0.58, 0.17,
                               fc="#8a8f96", ec=drawings.INK))
    ax.text(px + 0.5, -1.02, "quilla TRABADA abajo", fontsize=7,
            color=drawings.DIM)
    # aparejo
    ax.plot([mast_x, mast_x], [deck_z, head_z], color=drawings.INK, lw=1.6)
    ax.plot([mast_x, 1.50], [boom_z, boom_z - 0.04], color=drawings.INK, lw=1.2)
    ax.plot([6.45, mast_x], [1.03, hounds], color=drawings.INK, lw=0.8)
    main = [(mast_x - 0.02, boom_z + 0.05), (1.55, boom_z),
            (3.35, head_z - 0.35), (mast_x - 0.02, head_z - 0.10)]
    ax.fill(*zip(*(main + [main[0]])), fc="#eef2f5", ec=drawings.AUX, lw=0.9)
    jib = [(6.42, 1.06), (mast_x + 0.02, hounds - 0.05), (3.62, boom_z - 0.15)]
    ax.fill(*zip(*(jib + [jib[0]])), fc="#f5f2ea", ec=drawings.AUX, lw=0.9)
    # mastil sellado (sombreado) + flotador
    ax.plot([mast_x, mast_x], [deck_z, head_z], color="#c0392b", lw=3.2, alpha=0.35)
    ax.add_patch(Ellipse((mast_x, mb.float_z), 1.00, 0.34, fc="#e8b09a",
                         ec="#c0392b", lw=1.6))
    ax.axhline(0.217, color=drawings.AUX, lw=0.7, ls=":")
    ax.text(6.6, 0.26, "WL rosca", fontsize=6.5, color=drawings.AUX)


def sheet_flotador(pp, geom: HullGeometry, d: Design, mb: MastBuoyancy,
                   res: dict) -> None:
    fig = drawings.sheet(
        pp, "Auto-adrizado: flotador de tope, mastil sellado y condicion de diseno", "L8")

    # ---- perfil con flotador ----
    ax = fig.add_axes([0.03, 0.30, 0.46, 0.62])
    _draw_profile(ax, geom, d, mb)
    ax.annotate("flotador 60 L\n1.00 x Ø0.34, 2.5 kg", (4.78, mb.float_z),
                (5.7, 8.6), fontsize=8, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
    ax.annotate("mastil SELLADO\n(30 L utiles)", (4.25, 5.6), (2.0, 6.7),
                fontsize=8, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
    ax.set_xlim(-0.6, 8.2)
    ax.set_ylim(-1.7, 10.3)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- mini curva GZ ----
    ax = fig.add_axes([0.52, 0.42, 0.30, 0.46])
    c_bare, c_rig = res["c_bare"], res["c_rig"]
    ax.plot(c_bare.heel, c_bare.gz, color="#cc6677", ls="--", lw=1.4,
            label="sin flotador")
    ax.plot(c_rig.heel, c_rig.gz, color="#117733", lw=1.7,
            label="mastil sellado + 60 L")
    ax.axhline(0, color="#333", lw=0.8)
    lim = res["lim"]
    ax.axvline(lim, color="#117733", ls="-.", lw=0.9)
    ax.text(lim - 4, 0.75, f"recupera solo\nhasta {lim:.0f}°", fontsize=7.5,
            color="#117733", ha="right")
    ax.set_xlim(0, 180)
    ax.set_xlabel("escora (°)", fontsize=8)
    ax.set_ylabel("GZ (m)", fontsize=8)
    ax.set_title("rosca, cockpit inundado, tanques vacios", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, frameon=False, loc="upper right")

    # ---- notas ----
    fig.text(0.845, 0.88, "FLOTADOR DE TOPE", fontsize=10, color=drawings.INK,
             fontweight="bold")
    fig.text(0.845, 0.855,
             "Elipsoide PE rotomoldeado\n"
             "1.00 x 0.34 m = 60 L, ~2.5 kg\n"
             "carenado proa-popa (menos\n"
             "windage que una bola).\n"
             "Soporte: placa 6082-T6 en el\n"
             "tope, 4x M6 A4; desmontable\n"
             "para regata/remolque bajo.\n\n"
             "MASTIL SELLADO\n"
             "Espuma de cierre en pie, tope\n"
             "y cajeras de roldana; drizas\n"
             "externas o en conducto. 30 L\n"
             "utiles que tambien cuentan.\n\n"
             "TRABA DE QUILLA (ver L4)\n"
             "Obligatoria navegando: la\n"
             "curva verde supone la quilla\n"
             "abajo Y trabada a 120° de\n"
             "escora.",
             fontsize=8, color=drawings.INK, va="top")

    fig.text(0.03, 0.24, "COMO FUNCIONA (calc/autoadrizante.py -- el flotador SI entra a la curva GZ)",
             fontsize=10, color=drawings.INK, fontweight="bold")
    fig.text(0.03, 0.21,
             f"El volumen sellado en el tope es flotabilidad como cualquier otra: al sumergirse el aparejo (escora ~75°+) desplaza agua al final de una\n"
             f"palanca de 9.5 m, exactamente en el rango donde la curva del casco desnudo se hace negativa. Resultado (rosca, inundado, tanques vacios):\n"
             f"recuperacion autonoma desde cualquier escora hasta {res['lim']:.0f}° (casco desnudo: {res['avs_bare']:.0f}°); la energia que sostiene la tortuga cae de "
             f"{res['bare_j']:.0f} J a {res['pocket_j']:.0f} J,\n"
             f"detras de una barrera de {res['barrier_j']:.0f} J. 60 L en el tope = el momento adrizante de ~270 kg de plomo en el bulbo, por 2.5 kg.",
             fontsize=8.5, color=drawings.INK, va="top")

    fig.text(0.03, 0.115, "PLACA JUNTO A LA CAJA DE QUILLA (grabar):",
             fontsize=10, color=drawings.DIM, fontweight="bold")
    fig.text(0.03, 0.085,
             "AUTO-ADRIZANTE SOLO CON: QUILLA ABAJO Y TRABADA  ·  TANQUES VACIOS\n"
             "QUILLA ARRIBA = SOLO BOTADURA / PLAYA   ·   LASTRE DE AGUA: VER PLACA L7 (rendimiento, nunca seguridad)",
             fontsize=9.5, color=drawings.DIM, va="top")
    fig.text(0.03, 0.035,
             "Cinchas de piso y liston de pie (notes.txt 46-47): se mantienen como respaldo y para la condicion quilla-arriba.",
             fontsize=8, color=drawings.AUX, va="top")
    pp.savefig(fig)
    plt.close(fig)


def export_planos(design: Design, mb: MastBuoyancy, res: dict) -> None:
    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    path = os.path.join(DIR, "planos.pdf")
    with PdfPages(path) as pp:
        drawings.sheet_ga(pp, geom, d)
        drawings.sheet_lines(pp, geom, offsets_name=f"offsets_{TAG}.txt")
        drawings.sheet_midship(pp, geom, d)
        drawings.sheet_keel(pp, d)
        drawings.sheet_transom(pp, geom, d)
        drawings.sheet_sailplan(pp, geom, d)
        drawings.sheet_ballast(pp, d)
        sheet_flotador(pp, geom, d, mb, res)
    print(f"[{TAG}] planos -> {path}")


def export_perfil_png(design: Design, mb: MastBuoyancy) -> None:
    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    fig, ax = plt.subplots(figsize=(8.5, 10))
    _draw_profile(ax, geom, d, mb)
    ax.annotate("flotador de tope 60 L / 2.5 kg", (4.78, mb.float_z), (5.4, 8.5),
                fontsize=10, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    ax.annotate("mastil sellado (30 L)", (4.25, 5.4), (1.6, 6.6), fontsize=10,
                color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    ax.set_xlim(-0.6, 8.2)
    ax.set_ylim(-1.8, 10.4)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(DIR, "perfil_flotador.png"), dpi=140,
                bbox_inches="tight")
    plt.close(fig)
    print(f"[{TAG}] perfil -> {os.path.join(DIR, 'perfil_flotador.png')}")


# ---------------------------------------------------------------------------


def main() -> None:
    os.makedirs(DIR, exist_ok=True)
    design = Design()
    mb = MastBuoyancy()

    # Curvas para la lamina L8 (31 estaciones / 5 grados: los numeros del
    # report fino difieren en <0.2 grados).
    from calc import scantlings, weights as w

    d31 = Design()
    d31.hull.n_stations = 31
    g31 = HullGeometry(d31.hull, d31.cockpit)
    geom = HullGeometry(design.hull, design.cockpit)
    m_ldc = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc)
    from calc.autoadrizante import variant_weights

    wb = variant_weights(design, mb, sc, geom.shell_area(), geom.deck_area())
    design.ballast.keel_mass = wb.ballast_available
    d31.ballast.keel_mass = wb.ballast_available
    heel = np.arange(0.0, 181.0, 5.0)
    c_bare = gz_curve_rig(g31, d31, None, wb.disp_light, wb.vcg_light, True,
                          heel=heel, label="bare")
    c_rig = gz_curve_rig(g31, d31, mb, wb.disp_light, wb.vcg_light, True,
                         heel=heel, label="rig")
    lim = recovery_limit(c_rig)
    G = 9.80665
    res = {
        "c_bare": c_bare,
        "c_rig": c_rig,
        "lim": lim,
        "avs_bare": c_bare.avs,
        "bare_j": c_bare.negative_area * wb.disp_light * G,
        "pocket_j": c_rig.negative_area * wb.disp_light * G,
        "barrier_j": c_rig.area_under(c_bare.avs, lim) * wb.disp_light * G,
    }

    export_hull(design)
    export_boat_3dm(design, mb)
    export_planos(design, mb, res)
    export_perfil_png(design, mb)


if __name__ == "__main__":
    main()
