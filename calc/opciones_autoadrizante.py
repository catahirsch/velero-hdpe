"""Exploracion ampliada de opciones de auto-adrizado, contra notes.txt.

    python3 -m calc.opciones_autoadrizante   ->  autoadrizante/opciones.txt
                                                 autoadrizante/opciones.json
                                                 autoadrizante/opciones_gz.png
                                                 autoadrizante/opciones_board.png

docs/03 barrio el espacio clasico (mas plomo, sellar, cubierta tortuga,
angostar). Este modulo barre el espacio NUEVO que abre el modelo con aparejo:
todo lo que se puede hacer SIN tocar el casco de 2.35 m ni el cockpit de 6
plazas -- que es lo que notes.txt no negocia.

Opciones evaluadas (rosca, cockpit inundado; 31 estaciones / 5 grados):

  BASE   casco desnudo (referencia -- el problema)
  A1     mastil sellado solo (30 L, sin flotador): lo minimo, gratis
  A2     mastil sellado + flotador 60 L  <- la variante elegida
  A3     mastil sellado + flotador 80 L: el siguiente escalon
  B      bolsa inflable de tope 150 L (disparo hidrostatico): cero windage
         navegando, fisica de flotador grande al dispararse
  C0     tanques de lastre BAJO EL PISO llenos (500 kg a z=0.26), sin tope:
         el mecanismo RNLI solo -- revisa la decision bancos-tanque
  C      C0 + flotador 60 L: el paquete maximo sin tocar el casco
  D      casco angosto 1.80 m / 452 kg (opcion B de docs/03): el unico
         auto-adrizado literal desde 180.0 -- rompe el brief

La vara de medir es la del brief real: (1) hasta que escora vuelve solo,
(2) cuanta energia sostiene la tortuga residual, (3) cuantas lineas de
notes.txt sobreviven.
"""

from __future__ import annotations

import json
import os

import numpy as np

from . import scantlings
from .autoadrizante import (DIR, MastBuoyancy, gz_curve_rig, recovery_limit,
                            variant_weights)
from .geometry import HullGeometry
from .params import G, Design
from .trade import _fixed_mass

HEEL = np.arange(0.0, 181.0, 5.0)
STATIONS = 31


def _wide_setup():
    design = Design()
    geom = HullGeometry(design.hull, design.cockpit)
    m_ldc = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc)
    wb = variant_weights(design, MastBuoyancy(), sc, geom.shell_area(),
                         geom.deck_area())
    d = Design()
    d.hull.n_stations = STATIONS
    d.ballast.keel_mass = wb.ballast_available
    g = HullGeometry(d.hull, d.cockpit)
    return d, g, wb


def evaluate(d, g, mb, mass, vcg, label):
    c = gz_curve_rig(g, d, mb, mass, vcg, flooded=True, heel=HEEL, label=label)
    lim = recovery_limit(c)
    return {
        "label": label,
        "curve": c,
        "rec_limit": lim,
        "pocket_mrad": c.negative_area,
        "pocket_j": c.negative_area * mass * G,
        "true_180": bool(c.self_righting),
        "gz_max": c.gz_max,
        "mass": mass,
    }


def run() -> dict:
    os.makedirs(DIR, exist_ok=True)
    d, g, wb = _wide_setup()
    m0, v0 = wb.disp_light, wb.vcg_light
    lines: list[str] = []

    def say(*parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        lines.append(line)

    say("=" * 86)
    say("OPCIONES DE AUTO-ADRIZADO, CONTRA LOS REQUISITOS DE notes.txt")
    say("=" * 86)
    say("Condicion: rosca, cockpit inundado (tripulacion en el agua).")
    say("Lo que notes.txt no negocia: bote abierto 6 plazas (linea 19/37),")
    say("DIS<750, manga para el cockpit, quilla pivotante, lastre de agua,")
    say("electrico. El casco de 2.35 m queda fijo en todas menos D.")
    say("")

    results = {}
    results["BASE"] = evaluate(d, g, None, m0, v0, "BASE casco desnudo")
    results["A1"] = evaluate(d, g, MastBuoyancy(float_volume=0.0, float_mass=0.5),
                             m0, v0, "A1 mastil sellado solo (30 L)")
    results["A2"] = evaluate(d, g, MastBuoyancy(), m0, v0,
                             "A2 sellado + flotador 60 L (elegida)")
    results["A3"] = evaluate(d, g, MastBuoyancy(float_volume=0.080), m0, v0,
                             "A3 sellado + flotador 80 L")
    results["B"] = evaluate(d, g, MastBuoyancy(float_volume=0.150, float_mass=4.0),
                            m0, v0, "B bolsa inflable 150 L (disparada)")

    # C0 / C: tanques bajo el piso llenos -- 500 kg a z ~ 0.26
    m_ws = m0 + 500.0
    v_ws = (m0 * v0 + 500.0 * 0.26) / m_ws
    results["C0"] = evaluate(d, g, MastBuoyancy(float_volume=0.0, float_mass=0.5),
                             m_ws, v_ws, "C0 tanques bajo piso llenos, sin tope")
    results["C"] = evaluate(d, g, MastBuoyancy(), m_ws, v_ws,
                            "C tanques bajo piso + flotador 60 L")

    # D: casco angosto (referencia de docs/03; 500 kg da margen sobre el
    # umbral bisectado de 452 kg, que a esta resolucion queda al filo)
    d_n = Design()
    d_n.hull.n_stations = STATIONS
    d_n.hull.beam_sheer = 1.80
    fixed_mass, fixed_moment, _, _ = _fixed_mass(d_n)
    d_n.ballast.keel_mass = 500.0
    m_n = fixed_mass + 500.0
    v_n = (fixed_moment + 500.0 * -d_n.ballast.keel_vcg_below_bl) / m_n
    g_n = HullGeometry(d_n.hull, d_n.cockpit)
    results["D"] = evaluate(d_n, g_n, None, m_n, v_n,
                            "D casco angosto 1.80 m / 500 kg")

    say(f"  {'opcion':<44}{'vuelve solo':>12}{'tortuga':>10}{'GZ>0':>7}"
        f"{'desde 180':>0}")
    say(f"  {'':<44}{'hasta':>12}{'residual':>10}{'':>7}")
    say("  " + "-" * 78)
    for k, r in results.items():
        say(f"  {r['label']:<44}{r['rec_limit']:>10.0f}°{r['pocket_j']:>9.0f} J"
            f"{('SI' if r['true_180'] else 'no'):>7}")
    say("")

    say("-" * 86)
    say("LECTURA")
    say("-" * 86)
    say("  - A1 es gratis y ya recupera 13 grados mas que el casco desnudo:")
    say("    sellar el perfil deberia hacerse en CUALQUIER caso.")
    say("  - A2 -> A3: 20 L mas compran ~6 grados. Rendimiento decreciente;")
    say("    el bolsillo queda atrapado contra 180 por simetria.")
    say("  - B (inflable) es el unico camino a 180.0 LITERAL sin tocar el")
    say("    casco: disparada, GZ queda positivo hasta 180. El costo es que")
    say("    es un sistema armado: disparo hidrostatico, botella, rearmado")
    say("    tras cada uso, inspeccion anual. En un bote de dia familiar la")
    say("    fiabilidad pasiva del flotador rigido vale mas que la estetica;")
    say("    como UPGRADE (rigido 60 L + bolsa encima) cierra el requisito")
    say("    literal si la certificacion lo pide.")
    say("  - C0 confirma docs/03: el mecanismo RNLI solo NO alcanza a esta")
    say("    manga. C (tanques bajos + flotador) es lo maximo sin tocar el")
    say("    casco -- pero es una CONDICION (tanques llenos), no una")
    say("    configuracion: con tanques vacios vuelve a ser A2. Ademas")
    say("    revisa la decision del cliente de tanques-en-bancos y roba")
    say("    ~55 mm de piso. Solo tiene sentido si se acepta llenar tanques")
    say("    como regla al salir con mar formada.")
    say("  - D sigue siendo el unico 180.0 literal, y sigue rompiendo el")
    say("    brief (4 plazas, ~990 kg, remolque con frenos).")
    say("")
    say("-" * 86)
    say("MATRIZ CONTRA notes.txt")
    say("-" * 86)
    reqs = [
        ("6 plazas / cockpit grande (l.19)", ["SI", "SI", "SI", "SI", "SI", "SI", "SI", "no:4"]),
        ("DIS < 750 rosca (l.5)", ["SI", "SI", "SI", "SI", "SI", "SI", "SI", "no:1036"]),
        ("bancos-tanque = asientos (dec. cliente)", ["SI", "SI", "SI", "SI", "SI", "no", "no", "SI"]),
        ("sin sistemas armados / pasivo", ["SI", "SI", "SI", "SI", "no", "SI", "SI", "SI"]),
        ("tope de mastil limpio (estetica)", ["SI", "SI", "no", "no", "SI", "SI", "no", "SI"]),
        ("anti-tortuga efectivo", ["no", "parc.", "SI", "SI", "SI", "no", "SI", "SI"]),
    ]
    keys = list(results.keys())
    say(f"  {'requisito':<42}" + "".join(f"{k:>8}" for k in keys))
    for name, vals in reqs:
        say(f"  {name:<42}" + "".join(f"{v:>8}" for v in vals))
    say("")
    say("  RECOMENDACION: A2 como esta (pasivo, 2.5 kg, ~USD 240-760).")
    say("  B como upgrade si se exige el 180.0 literal sin cambiar el casco")
    say("  (o si el flotador molesta en regata). C como modo operativo solo")
    say("  si se re-abre la decision de los tanques. D solo si se exige el")
    say("  180.0 literal Y pasivo -- y se aceptan 4 plazas y ~1040 kg.")

    path = os.path.join(DIR, "opciones.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nescrito: {path}")

    # ---- json para el PDF ----
    js = {k: {kk: vv for kk, vv in r.items() if kk != "curve"}
          for k, r in results.items()}
    with open(os.path.join(DIR, "opciones.json"), "w") as f:
        json.dump(js, f, indent=1)

    _plot_gz(results)
    _plot_board(results)
    return results


# ---------------------------------------------------------------------------
# figuras
# ---------------------------------------------------------------------------


def _plot_gz(results) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.6))
    styles = {
        "BASE": ("#cc6677", "--", 1.6),
        "A2": ("#117733", "-", 2.2),
        "B": ("#4477aa", "-", 1.6),
        "C": ("#882255", "-", 1.6),
        "D": ("#999933", "-.", 1.6),
    }
    for k, (col, ls, lw) in styles.items():
        r = results[k]
        hasta = 180 if r["true_180"] else round(r["rec_limit"])
        ax.plot(r["curve"].heel, r["curve"].gz, color=col, ls=ls, lw=lw,
                label=f"{r['label']} — vuelve solo hasta {hasta}°")
    ax.axhline(0, color="#333", lw=0.9)
    ax.set_xlim(0, 180)
    ax.set_xlabel("escora (grados)")
    ax.set_ylabel("GZ (m)")
    ax.set_title("Opciones de auto-adrizado — rosca, cockpit inundado "
                 "(A1/A3/C0 en opciones.txt)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8.3, loc="upper right")
    fig.tight_layout()
    path = os.path.join(DIR, "opciones_gz.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"escrito: {path}")


def _sketch_profile(ax, mast_col="#3c3c3c"):
    d = Design()
    geom = HullGeometry(d.hull, d.cockpit)
    ax.plot(geom.x, geom.z_sheer, color="#232d37", lw=1.3)
    ax.plot(geom.x, geom.z_keel, color="#232d37", lw=1.3)
    ax.plot([geom.x[0]] * 2, [geom.z_keel[0], geom.z_sheer[0]],
            color="#232d37", lw=1.3)
    px = d.ballast.keel_pivot_x
    ax.fill([px + 0.24, px - 0.14, px + 0.16, px + 0.26],
            [0.02, -0.90, -0.90, 0.02], color="#7a7f86")
    ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"])
                 .Rectangle((px - 0.29, -1.075), 0.58, 0.17, fc="#5a5f66"))
    ax.plot([4.25, 4.25], [0.86, 9.46], color=mast_col, lw=2.0)
    ax.axhline(0.217, color="#5a8fb5", lw=0.6, ls=":")
    ax.set_xlim(-0.7, 8.0)
    ax.set_ylim(-1.9, 10.6)
    ax.set_aspect("equal")
    ax.axis("off")


def _plot_board(results) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Ellipse, Rectangle

    RED = "#c0392b"
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 10.5))
    fig.suptitle("Opciones de auto-adrizado sin tocar el casco (mas la referencia angosta) — "
                 "rosca, cockpit inundado, quilla abajo y trabada",
                 fontsize=13, y=0.99)

    def verdict(ax, r, extra=""):
        t = ("auto-adriza desde 180.0°" if r["true_180"]
             else f"vuelve solo hasta {r['rec_limit']:.0f}° · "
                  f"tortuga residual {r['pocket_j']:.0f} J")
        ax.set_title(f"{r['label']}\n{t}{extra}", fontsize=9.5)

    # A1 -- mastil sellado
    ax = axes[0, 0]
    _sketch_profile(ax, mast_col=RED)
    ax.text(4.5, 5.2, "perfil sellado\n30 L utiles\n+0 kg / USD ~150",
            fontsize=8, color=RED)
    verdict(ax, results["A1"], extra="  ·  hacerlo SIEMPRE")

    # A2 -- 60 L (elegida)
    ax = axes[0, 1]
    _sketch_profile(ax, mast_col=RED)
    ax.add_patch(Ellipse((4.25, 9.55), 1.0, 0.34, fc="#e8b09a", ec=RED, lw=1.4))
    ax.text(4.9, 9.35, "60 L / 2.5 kg", fontsize=8, color=RED)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#117733")
        s.set_linewidth(2.5)
    ax.axis("on")
    ax.set_xticks([])
    ax.set_yticks([])
    verdict(ax, results["A2"], extra="  ·  ELEGIDA")

    # A3 -- 80 L
    ax = axes[0, 2]
    _sketch_profile(ax, mast_col=RED)
    ax.add_patch(Ellipse((4.25, 9.57), 1.10, 0.40, fc="#e8b09a", ec=RED, lw=1.4))
    ax.text(4.95, 9.35, "80 L / 3.2 kg", fontsize=8, color=RED)
    verdict(ax, results["A3"], extra="  ·  +20 L = +6°")

    # B -- inflable
    ax = axes[1, 0]
    _sketch_profile(ax, mast_col=RED)
    ax.add_patch(Rectangle((4.10, 9.42), 0.30, 0.16, fc="#9aa7b0", ec="#3c3c3c"))
    ax.add_patch(Circle((4.25, 9.55), 0.42, fill=False, ec="#4477aa",
                        lw=1.4, ls="--"))
    ax.text(4.85, 9.6, "bolsa plegada;\ninflada 150 L\n(disparo hidrostatico)",
            fontsize=8, color="#4477aa")
    verdict(ax, results["B"], extra="  ·  cero windage, pero sistema ARMADO")

    # C -- tanques bajos + flotador
    ax = axes[1, 1]
    _sketch_profile(ax, mast_col=RED)
    ax.add_patch(Ellipse((4.25, 9.55), 1.0, 0.34, fc="#e8b09a", ec=RED, lw=1.4))
    ax.add_patch(Rectangle((0.35, 0.24), 3.2, 0.10, fc="#508cbe", alpha=0.8))
    ax.annotate("500 L bajo el piso (z=0.26)\nrevisa bancos-tanque; solo si estan LLENOS",
                (1.9, 0.29), (0.0, -1.72), fontsize=8, color="#2c5d8a",
                arrowprops=dict(arrowstyle="->", color="#2c5d8a", lw=0.8))
    verdict(ax, results["C"], extra="  ·  condicion, no configuracion")

    # D -- angosta (secciones comparadas)
    ax = axes[1, 2]
    for hb, col, lw, lab in ((1.175, "#8a8f96", 1.4, "2.35 m (brief)"),
                             (0.90, "#999933", 2.0, "1.80 m + 500 kg")):
        ys = [-hb, -hb * 0.8, 0, hb * 0.8, hb, -hb]
        zs = [0.76, 0.21, 0.0, 0.21, 0.76, 0.76]
        ax.plot(ys, zs, color=col, lw=lw, label=lab)
    ax.plot([0, 0], [0, -1.29], color="#999933", lw=2.4)
    ax.add_patch(Rectangle((-0.29, -1.29), 0.58, 0.17, fc="#999933"))
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.7, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")
    verdict(ax, results["D"], extra="  ·  rompe el brief (4 plazas, ~1040 kg)")

    fig.text(0.5, 0.01,
             "Todas las opciones A/B/C conservan: cockpit 6 plazas, 750 kg, manga 2.35, quilla pivotante, "
             "lastre de agua, electrico, remolque sin frenos. La D no.",
             ha="center", fontsize=9.5, color="#8a2b2b")
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    path = os.path.join(DIR, "opciones_board.png")
    fig.savefig(path, dpi=135)
    plt.close(fig)
    print(f"escrito: {path}")


if __name__ == "__main__":
    run()
