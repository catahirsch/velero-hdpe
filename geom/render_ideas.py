"""Estudio de diseno: colores y estilo.  python3 -m geom.render_ideas

Escribe:
  out/diseno_colores.png   4 combinaciones de color renderizadas del 3DM
  out/diseno_perfil.png    perfil con los elementos de estilo numerados

En HDPE el color VA EN LA RESINA (masterbatch al moldear): no hay pintura ni
gelcoat, el rayon no se nota (color pasante) y la decision es previa al molde.
Regla tecnica que ordena las paletas: cubierta y bancos SIEMPRE claros (el PE
oscuro al sol toma 20-30 C mas -> mas fluencia y dilatacion); los costados
pueden ser oscuros; el negro/carbono es el PE mas estable al UV.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rhino3dm as r3
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from calc.geometry import HullGeometry
from calc.params import Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

WL = 0.217  # flotacion rosca
BOOT_TOP = 0.34  # tope de la franja de flotacion


# paleta: nombre, topsides, franja, fondo, cubierta, bancos, nota
PALETTES = [
    ("PATAGONIA", "#3a3f45", "#e8622d", "#22262a", "#ccd2d6", "#e8622d",
     "grafito + naranja: maxima estabilidad UV (carbono),\n"
     "no muestra el uso, alta visibilidad SAR en los acentos"),
    ("CHILOE", "#1f4e5f", "#e8e2d4", "#16333d", "#e8e2d4", "#b98a54",
     "petroleo + crema + bancos 'madera' (pads EVA teca):\n"
     "clasico, esconde algas en la franja baja"),
    ("AIRA", "#eceeec", "#2c5d8a", "#7c8b94", "#d8dcdf", "#2c5d8a",
     "blanco + azul: el mas fresco al sol (menor dilatacion),\n"
     "look de astillero; el PE pasante no muestra rayones"),
    ("ARENA", "#d5c69e", "#5c6b4a", "#4a4438", "#efe9da", "#5c6b4a",
     "arena + oliva: discreto en fondeaderos australes,\n"
     "cubierta muy clara = la mas comoda descalzo"),
]


def load_boat():
    f = r3.File3dm.Read(os.path.join(OUT, "boat_baseline.3dm"))
    layers = {i: l.Name for i, l in enumerate(f.Layers)}
    parts = []
    for obj in f.Objects:
        g = obj.Geometry
        if isinstance(g, r3.Mesh):
            v = np.array([[p.X, p.Y, p.Z] for p in g.Vertices])
            tris = np.array([[g.Faces[k][0], g.Faces[k][1], g.Faces[k][2]]
                             for k in range(g.Faces.Count)])
            parts.append((layers[obj.Attributes.LayerIndex], v, tris))
    return parts


def classify_hull_faces(v, tris):
    """Separa el mesh del casco en fondo / franja / costado / cubierta."""
    cats = {"fondo": [], "franja": [], "costado": [], "cubierta": []}
    for t in tris:
        p = v[t]
        zc = p[:, 2].mean()
        n = np.cross(p[1] - p[0], p[2] - p[0])
        nz = n[2] / (np.linalg.norm(n) + 1e-12)
        if abs(nz) > 0.55 and zc > 0.35:
            cats["cubierta"].append(p)
        elif zc < WL:
            cats["fondo"].append(p)
        elif zc < BOOT_TOP:
            cats["franja"].append(p)
        else:
            cats["costado"].append(p)
    return cats


def render_palette(ax, parts, pal):
    name, tops, boot, bottom, deck, bench, _ = pal
    fixed = {"keel": "#4a4e55", "rudders": "#4a4e55", "rig": "#3c3c3c",
             "bench-tanks": bench, "sails": None, "waterlines": None,
             "lines": None}
    for lay, v, tris in parts:
        if lay == "hull":
            cats = classify_hull_faces(v, tris)
            for cat, col in (("fondo", bottom), ("franja", boot),
                             ("costado", tops), ("cubierta", deck)):
                if cats[cat]:
                    ax.add_collection3d(Poly3DCollection(
                        cats[cat], facecolor=col, edgecolor="none"))
        else:
            col = fixed.get(lay)
            if col is None:
                continue
            polys = [[v[a], v[b], v[c]] for a, b, c in tris]
            ax.add_collection3d(Poly3DCollection(polys, facecolor=col,
                                                 edgecolor="none"))
    ax.set_xlim(0.1, 6.4)
    ax.set_ylim(-3.15, 3.15)
    ax.set_zlim(-2.1, 4.2)
    ax.set_box_aspect((6.3, 6.3, 6.3))
    ax.view_init(elev=34, azim=-58)
    ax.axis("off")


def board_colorways():
    parts = load_boat()
    fig = plt.figure(figsize=(15, 9.5))
    fig.suptitle("Estudio de color — HDPE pasante (el color se decide al moldear; no se pinta)",
                 fontsize=13, y=0.98)
    for k, pal in enumerate(PALETTES):
        ax = fig.add_subplot(2, 2, k + 1, projection="3d")
        render_palette(ax, parts, pal)
        ax.set_title(f"{pal[0]}", fontsize=12, fontweight="bold", pad=0)
        ax.text2D(0.5, -0.02, pal[6] if len(pal) > 6 else pal[5],
                  transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
                  color="#445")
    for k, pal in enumerate(PALETTES):
        pass
    fig.text(0.5, 0.015,
             "Regla tecnica: cubierta y bancos siempre CLAROS (PE oscuro al sol: +20-30 °C -> fluencia y dilatacion). "
             "Costados libres. Negro/carbono = maxima vida UV.",
             ha="center", fontsize=9, color="#8a2b2b")
    path = os.path.join(OUT, "diseno_colores.png")
    fig.savefig(path, dpi=135, bbox_inches="tight")
    plt.close(fig)
    print("escrito:", path)


def profile_styling():
    d = Design()
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    pal = PALETTES[0]  # Patagonia como ejemplo
    _, tops, boot, bottom, deck, bench, _ = pal

    fig, ax = plt.subplots(figsize=(15, 6.4))
    x, zs, zk = geom.x, geom.z_sheer, geom.z_keel
    # casco por bandas de color
    ax.fill_between(x, zk, np.minimum(zs, WL), color=bottom, zorder=2)
    ax.fill_between(x, np.clip(zk, WL, None), np.minimum(zs, BOOT_TOP),
                    color=boot, zorder=3)
    ax.fill_between(x, np.clip(zk, BOOT_TOP, None), zs, color=tops, zorder=4)
    ax.plot(x, zs, color="#1a1e22", lw=2)
    ax.plot(x, zk, color="#1a1e22", lw=2)
    ax.plot([x[0]] * 2, [zk[0], zs[0]], color="#1a1e22", lw=2)
    # linea de borda: perfil de defensa PE soldado
    ax.plot(x, zs + 0.015, color=boot, lw=4, solid_capstyle="round", zorder=6)
    # nombre grabado
    ax.text(1.15, 0.52, "AUSTRAL 21", fontsize=17,  # nombre de ejemplo color="#e9edf0",
            fontweight="bold", style="italic", zorder=7)
    ax.text(5.9, 0.83, "PM-1234", fontsize=9, color="#e9edf0", zorder=7)
    # quilla y timon
    px = d.ballast.keel_pivot_x
    ax.fill([px + 0.24, px - 0.14, px + 0.16, px + 0.26],
            [0.02, -0.90, -0.90, 0.02], color="#4a4e55", zorder=1)
    ax.add_patch(plt.Rectangle((px - 0.29, -1.075), 0.58, 0.17, fc="#3a3e44",
                               zorder=1))
    ax.fill([0.02, 0.07, 0.30, 0.34], [0.64, -0.58, -0.58, 0.64],
            color="#4a4e55", zorder=1)
    ax.axhline(WL, color="#5a8fb5", lw=0.8, ls=":")

    # callouts
    def call(n, xx, yy, text, tx, ty):
        ax.annotate(f"{n}", (xx, yy), xytext=(tx, ty), fontsize=10,
                    fontweight="bold", color="#8a2b2b",
                    arrowprops=dict(arrowstyle="-", color="#8a2b2b", lw=0.8),
                    bbox=dict(boxstyle="circle,pad=0.18", fc="white",
                              ec="#8a2b2b"))
        ax.text(tx + 0.14, ty - 0.015, text, fontsize=8.6, color="#232d37",
                va="center")

    call(1, 3.4, 0.90, "defensa perimetral PE soldada (protege el cordon de borda)", 0.9, 1.60)
    call(2, 1.15, 0.60, "nombre (ejemplo): bajorrelieve ruteado + inlay de soldadura en contraste", 0.1, 1.95)
    call(3, 5.2, 0.42, "franja de flotacion en acento (esconde la zona sucia)", 5.05, 1.60)
    call(4, 5.9, 0.86, "matricula grabada en amuras (exigencia CL/AR)", 5.6, 1.95)
    call(5, px, -0.5, "apendices en gris oscuro: no delatan algas ni golpes", 4.9, -1.35)
    call(6, 2.0, 0.79, "antideslizante moldeado (textura guijarro) en cubierta,\nbancos y piso — sin pinturas antideslizantes", 0.1, -1.35)

    ax.set_xlim(-0.6, 7.3)
    ax.set_ylim(-1.75, 2.25)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Elementos de estilo sobre el perfil (paleta PATAGONIA de ejemplo) — todo resuelto en el molde o soldado, nunca pintado",
                 fontsize=11)
    path = os.path.join(OUT, "diseno_perfil.png")
    fig.savefig(path, dpi=135, bbox_inches="tight")
    plt.close(fig)
    print("escrito:", path)


if __name__ == "__main__":
    board_colorways()
    profile_styling()
