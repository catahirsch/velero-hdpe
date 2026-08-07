"""Planos de construccion:  python3 -m geom.drawings  ->  out/planos.pdf

Siete laminas A3 apaisadas, acotadas en metros, generadas desde el modelo
parametrico (no dibujadas a mano: si cambia calc/params.py, cambian los
planos). Complementan la tabla de puntos (offsets_*.txt) y el 3DM.

  L1  Disposicion general (perfil + planta)
  L2  Plano de formas (secciones, perfil, planta)
  L3  Seccion maestra constructiva (doble piel, banco-tanque, piso)
  L4  Quilla pivotante-retractil (pala, bulbo, caja, herrajes)
  L5  Espejo: timon unico abatible, imbornales, motor
  L6  Plano velico y jarcia
  L7  Esquema del lastre de agua + placa operativa

Preliminar: para construir en Argentina el proyecto debe firmarlo un
ingeniero naval (CPIN); en Chile, presentar croquis ante la SCLINM.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, Rectangle

from calc.geometry import HullGeometry
from calc.params import Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

INK = "#232d37"
DIM = "#8a2b2b"
AUX = "#5a7d96"
LIGHT = "#b9c8d4"
WATER = "#dcebf5"

A3 = (16.54, 11.69)


def sheet(pp: PdfPages, title: str, num: str):
    fig = plt.figure(figsize=A3)
    fig.text(0.015, 0.975, "VELERO ABIERTO HDPE 6.48 m", fontsize=9, color=AUX,
             fontweight="bold")
    fig.text(0.015, 0.958, f"{num}  ·  {title}", fontsize=13, color=INK,
             fontweight="bold")
    fig.text(0.985, 0.975, "cotas en METROS  ·  agosto 2026", fontsize=8,
             color=AUX, ha="right")
    fig.text(0.985, 0.958,
             "PRELIMINAR - sujeto a revision de ingeniero naval",
             fontsize=8, color=DIM, ha="right")
    return fig


def dim_h(ax, x0, x1, y, text, offset=0.06, fs=7.5):
    """Cota horizontal."""
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="<->",
                                 mutation_scale=8, color=DIM, lw=0.8))
    ax.plot([x0, x0], [y - 0.02, y + 0.02], color=DIM, lw=0.6)
    ax.plot([x1, x1], [y - 0.02, y + 0.02], color=DIM, lw=0.6)
    ax.text((x0 + x1) / 2, y + offset * 0.4, text, ha="center", va="bottom",
            fontsize=fs, color=DIM)


def dim_v(ax, x, y0, y1, text, side=1, fs=7.5):
    """Cota vertical."""
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="<->",
                                 mutation_scale=8, color=DIM, lw=0.8))
    ax.text(x + 0.03 * side, (y0 + y1) / 2, text, ha="left" if side > 0 else "right",
            va="center", fontsize=fs, color=DIM, rotation=90)


def note(ax, x, y, text, fs=7.5, color=INK):
    ax.text(x, y, text, fontsize=fs, color=color, va="top")


# ---------------------------------------------------------------------------


def sheet_ga(pp, geom: HullGeometry, d: Design):
    fig = sheet(pp, "Disposicion general", "L1")
    cp = d.cockpit

    # ---- perfil ----
    ax = fig.add_axes([0.05, 0.52, 0.90, 0.40])
    ax.plot(geom.x, geom.z_sheer, color=INK, lw=1.6)
    ax.plot(geom.x, geom.z_keel, color=INK, lw=1.6)
    ax.plot(geom.x, geom.z_crown, color=AUX, lw=0.9, ls="--")
    ax.plot([geom.x[0], geom.x[0]], [geom.z_keel[0], geom.z_sheer[0]], color=INK, lw=1.6)
    # flotaciones
    ax.axhline(0.217, color=AUX, lw=0.8, ls=":")
    ax.axhline(0.329, color=AUX, lw=0.8, ls=":")
    note(ax, 6.55, 0.24, "WL rosca 0.217", fs=7, color=AUX)
    note(ax, 6.55, 0.35, "WL 1730 kg 0.329", fs=7, color=AUX)
    # cockpit / bancos / piso
    ax.plot([cp.x_aft, cp.x_fwd], [cp.sole_z] * 2, color=INK, lw=1.2)
    ax.add_patch(Rectangle((cp.x_aft, cp.sole_z), cp.x_fwd - cp.x_aft,
                           cp.bench_top_z - cp.sole_z, fc=WATER, ec=AUX, lw=0.9))
    note(ax, 1.6, 0.74, "bancos-tanque\n(lastre 2 x 250 kg)", fs=7, color=AUX)
    # quilla abajo / arriba
    px = d.ballast.keel_pivot_x
    ax.plot([px + 0.24, px - 0.14, px + 0.16, px + 0.26, px + 0.24],
            [0.02, -0.90, -0.90, 0.02, 0.02], color=INK, lw=1.1)
    ax.add_patch(Rectangle((px - 0.29, -1.075), 0.58, 0.17, fc="#666", ec=INK))
    ax.plot([px, px + 1.06], [0.05, 0.28], color=AUX, lw=0.9, ls="--")
    note(ax, px + 0.65, 0.20, "quilla arriba (calado 0.30)", fs=7, color=AUX)
    # timon
    ax.plot([0.02, 0.07, 0.30, 0.34, 0.02], [0.64, -0.58, -0.58, 0.64, 0.64],
            color=INK, lw=1.0)
    # mastil (cortado: aparejo completo en L6) + botavara
    ax.plot([4.25, 4.25], [0.86, 2.55], color=INK, lw=1.4)
    ax.plot([4.28, 4.22], [2.55, 2.70], color=INK, lw=1.0)  # marca de corte
    note(ax, 4.35, 2.62, "mastil (ver L6)", fs=7, color=AUX)
    ax.plot([4.23, 1.50], [1.80, 1.76], color=INK, lw=1.2)
    dim_v(ax, 6.9, 0, 1.80, "botavara 1.80", side=1)
    dim_v(ax, -0.35, -1.075, 0, "calado quilla 1.294", side=-1)
    dim_h(ax, 0, 6.48, -1.5, "LOA 6.480")
    dim_h(ax, cp.x_aft, cp.x_fwd, 1.05, "cockpit 3.200")
    ax.set_xlim(-0.9, 7.4)
    ax.set_ylim(-1.9, 3.0)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- planta ----
    ax = fig.add_axes([0.05, 0.05, 0.90, 0.44])
    ax.plot(geom.x, geom.y_sheer, color=INK, lw=1.6)
    ax.plot(geom.x, -geom.y_sheer, color=INK, lw=1.6)
    ax.plot([0, 0], [-geom.y_sheer[0], geom.y_sheer[0]], color=INK, lw=1.6)
    ax.plot(geom.x, geom.y_chine, color=AUX, lw=0.8, ls="--")
    ax.plot(geom.x, -geom.y_chine, color=AUX, lw=0.8, ls="--")
    # cockpit y bancos
    for s in (1, -1):
        ax.add_patch(Rectangle((cp.x_aft, s * cp.bench_inner_y),
                               cp.x_fwd - cp.x_aft,
                               s * (cp.half_width - cp.bench_inner_y),
                               fc=WATER, ec=AUX, lw=0.9))
    ax.add_patch(Rectangle((cp.x_aft, -cp.bench_inner_y), cp.x_fwd - cp.x_aft,
                           2 * cp.bench_inner_y, fc="none", ec=INK, lw=1.0))
    # cuddy + tambuchos
    ax.plot([cp.bow_cuddy_x] * 2, [-0.75, 0.75], color=INK, lw=1.0)
    for s in (1, -1):
        ax.add_patch(Rectangle((5.25, s * 0.12), 0.45, s * 0.35, fc="none",
                               ec=INK, lw=0.9))
    note(ax, 5.28, -0.62, "2 tambuchos", fs=7)
    # mastil, quilla, timon, motor
    ax.plot(4.25, 0, "o", color=INK, ms=6)
    note(ax, 4.32, 0.14, "mastil x=4.25", fs=7)
    ax.add_patch(Rectangle((px - 0.65, -0.09), 1.21, 0.18, fc="none", ec=INK, lw=1.0))
    note(ax, px - 0.62, -0.16, "caja de quilla 1.21 x 0.18", fs=7)
    ax.add_patch(Rectangle((0.02, -0.017), 0.32, 0.034, fc=INK))
    ax.add_patch(Rectangle((-0.12, 0.37), 0.14, 0.16, fc="none", ec=INK, lw=0.9))
    note(ax, -0.85, 0.62, "motor electrico\ny = +0.45", fs=7)
    dim_h(ax, 0, 6.48, -1.55, "LOA 6.480")
    dim_v(ax, 6.8, -1.175, 1.175, "manga 2.350")
    dim_v(ax, 2.0, -cp.bench_inner_y, cp.bench_inner_y, "pasillo 0.880")
    ax.set_xlim(-0.9, 7.4)
    ax.set_ylim(-1.9, 1.9)
    ax.set_aspect("equal")
    ax.axis("off")
    pp.savefig(fig)
    plt.close(fig)


def sheet_lines(pp, geom: HullGeometry, offsets_name: str = "offsets_baseline.txt"):
    fig = sheet(pp, f"Plano de formas  (tabla de puntos: {offsets_name}, 121 estaciones)", "L2")
    ax = fig.add_axes([0.07, 0.50, 0.40, 0.42])
    step = max(1, len(geom.x) // 12)
    for i in range(0, len(geom.x), step):
        s = geom._sections[i]
        if len(s) < 3:
            continue
        cl = np.vstack([s, s[:1]])
        ax.plot(cl[:, 0], cl[:, 1], color=AUX, lw=0.9)
    ax.axhline(0.217, color=DIM, lw=0.6, ls=":")
    ax.set_title("secciones (caja de cuadernas)", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=7)

    ax = fig.add_axes([0.55, 0.56, 0.40, 0.36])
    ax.plot(geom.x, geom.z_keel, color=INK, lw=1.2, label="quilla")
    ax.plot(geom.x, geom.z_chine, color=DIM, lw=1.0, label="codaste")
    ax.plot(geom.x, geom.z_sheer, color=AUX, lw=1.2, label="borda")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("perfil", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=7)

    ax = fig.add_axes([0.30, 0.07, 0.55, 0.34])
    ax.plot(geom.x, geom.y_sheer, color=AUX, lw=1.2)
    ax.plot(geom.x, -geom.y_sheer, color=AUX, lw=1.2)
    ax.plot(geom.x, geom.y_chine, color=DIM, lw=1.0)
    ax.plot(geom.x, -geom.y_chine, color=DIM, lw=1.0)
    ax.set_title("planta (borda y codaste)", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=7)

    fig.text(0.07, 0.40,
             "Construccion en chapa: paneles desarrollables desde el espejo hasta x = 4.10 m;\n"
             "a proa, termoformar la roda sobre plantilla macho o dividir en tracas.\n"
             "Rotomoldeo: la desarrollabilidad es irrelevante (herramienta hembra).\n\n"
             "Lofting: pasar splines por la tabla de puntos y alisar; las curvas de este\n"
             "plano son las del modelo de calculo (hidrostatica y estabilidad ya\n"
             "verificadas sobre esta geometria).", fontsize=8.5, color=INK, va="top")
    pp.savefig(fig)
    plt.close(fig)


def sheet_midship(pp, geom: HullGeometry, d: Design):
    fig = sheet(pp, "Seccion maestra constructiva  (x = 2.00 m)", "L3")
    cp = d.cockpit
    ax = fig.add_axes([0.06, 0.08, 0.60, 0.84])
    i = int(np.argmin(np.abs(geom.x - 2.0)))
    ys, yc = geom.y_sheer[i], geom.y_chine[i]
    zk, zc, zs = geom.z_keel[i], geom.z_chine[i], geom.z_sheer[i]

    # casco doble piel: piel exterior + piel interior desplazada 50 mm
    pts = np.array([[-ys, zs], [-yc, zc], [0.0, zk], [yc, zc], [ys, zs]])
    ax.plot(pts[:, 0], pts[:, 1], color=INK, lw=1.6)
    centre = np.array([0.0, (zk + zs) / 2.0])
    inner = []
    for p in pts:
        v = p - centre
        n = np.linalg.norm(v)
        inner.append(centre + v * (1 - 0.05 / max(n, 0.3)))
    inner = np.array(inner)
    ax.plot(inner[:, 0], inner[:, 1], color=INK, lw=0.9)
    note(ax, -1.0, -0.05, "doble piel 5+5 mm,\nseparacion 50 mm", fs=7, color=AUX)
    # kiss-offs
    for yy in np.arange(-yc + 0.1, yc, 0.075 * 3):
        ax.plot([yy, yy], [zk + 0.005, zk + 0.05], color=AUX, lw=0.7)
    note(ax, -0.25, zk + 0.115, "kiss-offs @ 75 mm", fs=7, color=AUX)

    # piso completo + cubierta lateral hasta la borda
    ax.plot([-cp.half_width, cp.half_width], [cp.sole_z] * 2, color=INK, lw=1.4)
    for sgn in (1, -1):
        yw = sgn * min(cp.half_width, ys * 0.95)
        zd = geom._deck_z_at(i, yw)
        ax.plot([yw, sgn * ys], [zd, zs], color=INK, lw=1.4)  # cubierta lateral
        ax.plot([yw, yw], [cp.sole_z, zd], color=INK, lw=1.2)  # pared cockpit
    for s in (1, -1):
        x0 = s * cp.bench_inner_y
        x1 = s * min(cp.half_width, ys * 0.95)
        ax.add_patch(Rectangle((min(x0, x1), cp.sole_z), abs(x1 - x0),
                               cp.bench_top_z - cp.sole_z, fc=WATER, ec=INK, lw=1.2))
        ax.plot([min(x0, x1), max(x0, x1)],
                [cp.sole_z + 0.186] * 2, color=AUX, lw=0.9, ls=":")
    note(ax, 0.47, 0.62, "nivel 250 kg\n(+186 mm)", fs=7, color=AUX)

    # cotas
    dim_v(ax, -1.45, 0, cp.sole_z, "piso 0.385", side=-1)
    dim_v(ax, 1.45, 0, cp.bench_top_z, "asiento 0.800")
    dim_h(ax, -cp.bench_inner_y, cp.bench_inner_y, 0.30, "pasillo 0.880")
    dim_h(ax, cp.bench_inner_y, 0.86, 0.90, "banco 0.420")
    dim_h(ax, -ys, ys, -0.28, f"manga en seccion {2 * ys:.3f}")
    ax.axhline(0.217, color=AUX, lw=0.7, ls=":")
    note(ax, -1.38, 0.26, "WL rosca", fs=7, color=AUX)
    ax.set_xlim(-1.7, 1.7)
    ax.set_ylim(-0.45, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.69, 0.90, "LAMINADO (rotomoldeo)", fontsize=10, color=INK, fontweight="bold")
    fig.text(0.69, 0.87,
             "- 2 pieles HDPE 5.0 mm (-0/+1)\n"
             "- separacion 50 mm\n"
             "- kiss-offs Ø60 @ 75 mm fondo/costado,\n  @ 100 mm cubierta\n"
             "- masa 9.5 kg/m2\n"
             "- equivalente rigidez: 42 mm solidos\n\n"
             "PROTOTIPO (chapa soldada)\n"
             "- PE500 12 mm fondo/costados,\n  10 mm cubierta\n"
             "- omegas PE 60x40x8 @ 200 mm\n"
             "- cordon extrusion int.+ext. en borda\n"
             "- (+40 kg vs rotomoldeo)\n\n"
             "REGLA DE ORO\n"
             "Nada se pega al HDPE: union = soldadura\n"
             "PE-PE o bulon A4 con placa 6082-T6 y\n"
             "tubo de compresion piel-a-piel.\n"
             "Dilatacion PE ~10x aluminio:\n"
             "agujeros ovalados en tramos > 0.5 m.\n\n"
             "Paredes de banco: PE 8 mm soldadas a\n"
             "piso y casco - son estructura (rigidizan\n"
             "el costado y portan el piso). Tapa\n"
             "registro con junta en cada banco.",
             fontsize=8, color=INK, va="top")
    pp.savefig(fig)
    plt.close(fig)


def sheet_keel(pp, d: Design):
    fig = sheet(pp, "Quilla pivotante-retractil  (auditada: calc/audit.py)", "L4")
    px = 0.0  # dibujo local, origen en el pivote
    ax = fig.add_axes([0.06, 0.08, 0.52, 0.84])
    # pala
    ax.plot([px - 0.24, px - 0.14, px + 0.16, px + 0.26, px - 0.24],
            [0.02, -0.90, -0.90, 0.02, 0.02], color=INK, lw=1.6)
    # bulbo
    ax.add_patch(Rectangle((px - 0.29, -1.075), 0.58, 0.17, fc="#8a8f96", ec=INK, lw=1.2))
    # pivote
    ax.plot(px, 0.05, "o", ms=10, mfc="none", mec=INK, mew=1.4)
    note(ax, px + 0.06, 0.10, "pivote Ø25 316\n(bujes acetal + engrasador)", fs=7.5)
    # doublers
    ax.plot([px - 0.22, px + 0.24], [-0.30, -0.30], color=AUX, lw=1.0, ls="--")
    note(ax, px + 0.28, -0.18, "doblers 6 mm ambas caras\nhasta z = -0.30", fs=7.5, color=AUX)
    # cotas
    dim_h(ax, px - 0.24, px + 0.26, 0.16, "cuerda raiz 0.50")
    dim_h(ax, px - 0.14, px + 0.16, -1.16, "cuerda punta 0.30")
    dim_v(ax, px - 0.55, -0.90, 0.02, "pala 0.92", side=-1)
    dim_v(ax, px + 0.62, -1.075, 0.05, "1.125 pivote-fondo bulbo")
    dim_h(ax, px - 0.29, px + 0.29, -1.30, "bulbo 0.580")
    ax.set_xlim(-1.0, 1.15)
    ax.set_ylim(-1.55, 0.45)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.62, 0.90, "DESPIECE Y MASAS", fontsize=10, color=INK, fontweight="bold")
    fig.text(0.62, 0.87,
             "Pala: S355 15 mm, perfilada NACA 0012,\n"
             "  galvanizada en caliente ............ 50 kg\n"
             "Bulbo: plomo fundido (2-4% Sb)\n"
             "  0.58 x 0.145 x 0.17 m (14.3 L) .... 163 kg\n"
             "  centroide bulbo z = -0.99\n"
             "CONJUNTO ............................ 213 kg\n"
             "  VCG conjunto z = -0.86 (el que usa\n"
             "  el modelo de estabilidad)\n"
             "Calado bajada: 1.294 m (tope CBD 1.30)\n"
             "Calado subida: 0.30 m\n\n"
             "TENSIONES\n"
             "Flexion raiz a RM max (4.9 kN.m):\n"
             "  157 MPa -> SF 2.3 sobre fluencia\n\n"
             "CAJA\n"
             "Ranura casco 1.21 x 0.18 m; caja PE 12 mm\n"
             "con placas laterales 6082-T6 8 mm,\n"
             "8x M12 A4 pasantes con tubos.\n"
             "Izado: aparejo 4:1 al cockpit.\n"
             "TRABA de posicion bajada (obligatoria:\n"
             "una orzada no debe retraerla).\n\n"
             "Fundicion del bulbo: molde de arena\n"
             "alrededor de la punta de la pala\n"
             "(taladros Ø20 x3 en la punta para llave\n"
             "mecanica plomo-acero).",
             fontsize=8, color=INK, va="top")
    pp.savefig(fig)
    plt.close(fig)


def sheet_transom(pp, geom: HullGeometry, d: Design):
    fig = sheet(pp, "Espejo: timon unico abatible, imbornales y motor", "L5")
    ax = fig.add_axes([0.06, 0.08, 0.55, 0.84])
    ys0 = geom.y_sheer[0]
    zs0, zk0 = geom.z_sheer[0], geom.z_keel[0]
    yc0, zc0 = geom.y_chine[0], geom.z_chine[0]
    # espejo
    ax.plot([-ys0, -yc0, 0, yc0, ys0, -ys0][0:5] + [-ys0],
            [zs0, zc0, zk0, zc0, zs0, zs0][0:5] + [zs0], color=INK, lw=1.6)
    ax.plot([-ys0, ys0], [zs0, zs0], color=INK, lw=1.6)
    # abertura semi-abierta (sobre el piso) partida por la mecha
    for s in (1, -1):
        ax.add_patch(Rectangle((s * 0.09, d.cockpit.sole_z),
                               s * (d.cockpit.bench_inner_y - 0.09), 0.22,
                               fc="white", ec=AUX, lw=1.1, hatch="///"))
    note(ax, -0.42, 0.68, "imbornales espejo\n(2) 0.35 x 0.22", fs=7.5, color=AUX)
    # timon
    ax.add_patch(Rectangle((-0.017, -0.58), 0.034, 1.22, fc="#8a8f96", ec=INK, lw=1.2))
    note(ax, 0.05, -0.30, "pala PE500 20 mm\ncuerda 0.26, abatible", fs=7.5)
    # herrajes
    for z in (0.55, 0.20):
        ax.plot(0, z, "s", ms=7, mfc="none", mec=INK)
    note(ax, 0.07, 0.42, "2 pinzotes con placas\n150x100x6 + 4x M8 c/u", fs=7.5)
    # motor
    ax.add_patch(Rectangle((0.38, 0.55), 0.16, 0.28, fc="none", ec=INK, lw=1.2))
    note(ax, 0.38, 0.92, "soporte motor 4 kW\ny = +0.45 (libre del timon)", fs=7.5)
    ax.axhline(0.217, color=AUX, lw=0.7, ls=":")
    dim_v(ax, -1.35, 0, d.cockpit.sole_z, "piso 0.385", side=-1)
    dim_v(ax, 1.30, -0.58, 0.64, "timon 1.22 total")
    dim_h(ax, -ys0, ys0, 0.95, f"manga espejo {2 * ys0:.3f}")
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-0.85, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.65, 0.90, "TIMON (enmienda del cliente: UNO)", fontsize=10,
             color=INK, fontweight="bold")
    fig.text(0.65, 0.87,
             "- Central, colgado del espejo, abatible\n"
             "  (kick-up) con retencion por gomas o\n"
             "  fusible; cana corta.\n"
             "- Pala NACA 0010, cuerda media 0.26 m,\n"
             "  inmersa 0.85 m (mas profunda que las\n"
             "  gemelas que reemplaza: agarre a 20-25°\n"
             "  de escora).\n"
             "- Mecha 6082-T6; pinzotes pasantes con\n"
             "  placas de respaldo (nunca roscar al PE).\n\n"
             "ESPEJO SEMI-ABIERTO\n"
             "- Drena el cockpit por gravedad; abertura\n"
             "  partida a ambos lados de la mecha.\n"
             "- El piso (0.385) queda +56 mm sobre la\n"
             "  flotacion a plena carga: verifica el\n"
             "  autoachique en la peor condicion.\n\n"
             "MOTOR\n"
             "- Electrico ~4 kW en soporte a y=+0.45\n"
             "  (estribor), placa de respaldo 6082-T6;\n"
             "  bateria 48 V bajo el piso en caja\n"
             "  ventilada y trincada.",
             fontsize=8, color=INK, va="top")
    pp.savefig(fig)
    plt.close(fig)


def sheet_sailplan(pp, geom: HullGeometry, d: Design):
    fig = sheet(pp, "Plano velico y jarcia", "L6")
    ax = fig.add_axes([0.05, 0.06, 0.58, 0.88])
    # casco perfil simplificado
    ax.plot(geom.x, geom.z_sheer, color=INK, lw=1.2)
    ax.plot(geom.x, geom.z_keel, color=INK, lw=1.2)
    ax.plot([geom.x[0]] * 2, [geom.z_keel[0], geom.z_sheer[0]], color=INK, lw=1.2)
    mast_x, deck_z, head_z = 4.25, 0.86, 9.46
    boom_z = d.rig.boom_height
    hounds = deck_z + 0.82 * 8.60
    # mastil, botavara, estay
    ax.plot([mast_x, mast_x], [deck_z, head_z], color=INK, lw=1.8)
    ax.plot([mast_x, 1.50], [boom_z, boom_z - 0.04], color=INK, lw=1.5)
    ax.plot([6.45, mast_x], [1.03, hounds], color=INK, lw=0.9)
    # mayor square-top
    main = [(mast_x - 0.02, boom_z + 0.05), (1.55, boom_z),
            (3.35, head_z - 0.35), (mast_x - 0.02, head_z - 0.10)]
    ax.fill(*zip(*(main + [main[0]])), fc="#eef2f5", ec=AUX, lw=1.1)
    # foque
    jib = [(6.42, 1.06), (mast_x + 0.02, hounds - 0.05), (3.62, boom_z - 0.15)]
    ax.fill(*zip(*(jib + [jib[0]])), fc="#f5f2ea", ec=AUX, lw=1.1)
    note(ax, 2.9, 5.4, "MAYOR 14.0 m2\nsquare-top, 2 rizos\n(-40% gratil: exigencia CL)", fs=8)
    note(ax, 4.9, 3.6, "FOQUE 8.0 m2\nenrollador", fs=8)
    # cotas
    dim_v(ax, 7.15, 1.03, hounds, "I 7.05")
    dim_h(ax, mast_x, 6.45, 0.55, "J 2.20")
    dim_v(ax, 3.30, boom_z, head_z - 0.10, "P 7.55", side=-1)
    dim_h(ax, 1.55, mast_x, boom_z - 0.42, "E 2.75")
    dim_v(ax, 0.60, 0, boom_z, "botavara 1.80", side=-1)
    ax.set_xlim(-0.4, 8.1)
    ax.set_ylim(-1.0, 10.2)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.66, 0.90, "JARCIA", fontsize=10, color=INK, fontweight="bold")
    fig.text(0.66, 0.87,
             "Mastil 8.60 m, 6082-T6 ~110x2.5,\n"
             "  pisado en cubierta sobre larguero\n"
             "  120x60x8 (3 mamparos PE).\n"
             "Sin backstay ni traveller: crucetas\n"
             "  retrasadas ~20°, pretension con\n"
             "  ~20 mm de prebend.\n"
             "Obenques + estay: 1x19 316 Ø5,\n"
             "  cadenotes 50x8 a y=±1.10, x=4.05.\n"
             "Escota mayor 2:1 a punto fijo central\n"
             "  (viga 80x40x4 bajo el piso, x=1.55,\n"
             "  apoyada en paredes de bancos).\n"
             "Sin winches: todo 2:1; izado quilla 4:1.\n\n"
             "BOTAVARA A 1.80 m\n"
             "= 1.0 m sobre el asiento: pasa sobre\n"
             "cabezas sentadas (auditado; a 1.66 no\n"
             "pasaba). Sosten de carpa-toldo.\n\n"
             "VELERIA\n"
             "Dacron 250-300 g/m2; mayor con lazy\n"
             "bag; numeral por Federacion de Vela\n"
             "(CL) / PNA (AR).",
             fontsize=8, color=INK, va="top")
    pp.savefig(fig)
    plt.close(fig)


def sheet_ballast(pp, d: Design):
    fig = sheet(pp, "Sistema de lastre de agua (bancos-tanque) + placa operativa", "L7")
    ax = fig.add_axes([0.05, 0.30, 0.90, 0.60])
    cp = d.cockpit
    # planta esquematica
    for s, lbl in ((1, "ER"), (-1, "BR")):
        ax.add_patch(Rectangle((cp.x_aft, s * cp.bench_inner_y),
                               cp.x_fwd - cp.x_aft,
                               s * (cp.half_width - cp.bench_inner_y),
                               fc=WATER, ec=INK, lw=1.4))
        ax.text(1.9, s * 0.65, f"TANQUE {lbl}  250 kg / 244 L",
                ha="center", va="center", fontsize=9, color=INK)
        # cuchara + valvula
        ax.plot(3.35, s * 0.88, "v", ms=9, color=INK)
        ax.text(3.35, s * 1.02, "cuchara Ø38 + valvula bola\n(orientada a proa, en codaste)",
                ha="center", fontsize=7, color=INK)
        # venteo
        ax.plot(0.55, s * 0.88, "^", ms=8, color=AUX)
        ax.text(0.55, s * 1.06, "venteo Ø25\n(cuello de cisne)", ha="center",
                fontsize=7, color=AUX)
        # sight tube
        ax.plot([0.9, 0.9], [s * cp.bench_inner_y, s * (cp.bench_inner_y + 0.1)],
                color=DIM, lw=2)
    # cross connect
    ax.plot([1.4, 1.4], [-cp.bench_inner_y, cp.bench_inner_y], color=INK, lw=2.2)
    ax.plot(1.4, 0, "s", ms=8, mfc="white", mec=INK)
    ax.text(1.52, 0.02, "trasvase Ø51 + valvula\n(bajo el piso: cambiar de banda)",
            fontsize=7.5, va="center")
    # bomba aire
    ax.add_patch(Rectangle((-0.25, -0.14), 0.42, 0.28, fc="none", ec=INK, lw=1.2))
    ax.text(-0.04, 0.0, "bomba\naire 12V", ha="center", va="center", fontsize=7)
    ax.plot([0.17, 0.55, 0.55], [0.0, 0.0, cp.bench_inner_y], color=AUX, lw=1.2, ls="--")
    ax.plot([0.17, 0.55], [0.0, 0.0], color=AUX, lw=1.2, ls="--")
    ax.plot([0.55, 0.55], [0.0, -cp.bench_inner_y], color=AUX, lw=1.2, ls="--")
    ax.set_xlim(-0.6, 4.3)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.06, 0.26, "OPERACION", fontsize=10, color=INK, fontweight="bold")
    fig.text(0.06, 0.23,
             "LLENAR (navegando > 4 kt): abrir valvula de cuchara de sotavento ~3 min; trasvasar a barlovento en la virada.\n"
             "VACIAR: bomba de aire presuriza por el venteo y expulsa por la cuchara; o descarga por gravedad escorado.\n"
             "SELLADO: tanques estancos probados a 0.15 bar (son la reserva de flotabilidad ademas del lastre).",
             fontsize=8.5, color=INK, va="top")
    fig.text(0.06, 0.135, "PLACA JUNTO A LAS VALVULAS (grabar):", fontsize=10,
             color=DIM, fontweight="bold")
    fig.text(0.06, 0.105,
             "TRIPULACION 5-6: TANQUES VACIOS   ·   TRIPULACION 1-3: SOLO BARLOVENTO   ·   "
             "AMBOS LLENOS: SOLO A MOTOR / CON POCA GENTE",
             fontsize=9.5, color=DIM, va="top")
    pp.savefig(fig)
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    d = Design()
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    path = os.path.join(OUT, "planos.pdf")
    with PdfPages(path) as pp:
        sheet_ga(pp, geom, d)
        sheet_lines(pp, geom)
        sheet_midship(pp, geom, d)
        sheet_keel(pp, d)
        sheet_transom(pp, geom, d)
        sheet_sailplan(pp, geom, d)
        sheet_ballast(pp, d)
    print(f"escrito: {path}")


if __name__ == "__main__":
    main()
