"""Renders de la variante auto-adrizante.  python3 -m geom.render_autoadrizante

Escribe en autoadrizante/ los equivalentes de las imagenes de out/:

  hull_lines.png                 plano de lineas (secciones, perfil, planta)
  preview_3dm.png                render rapido del 3DM completo (con flotador)
  preview_cockpit.png            vista alta del cockpit y bancos-tanque
  foto_patagonia_navegando.png   'foto' navegando escorado, flotador a la vista
  foto_aira_fondeado.png         'foto' fondeado en calma
  diseno_colores.png             4 paletas de color sobre el 3DM
  diseno_perfil.png              elementos de estilo sobre el perfil

Las escenas reutilizan la maquinaria de geom/render_scene.py y
geom/render_ideas.py, cargando boat_autoadrizante.3dm (que agrega la capa
flotador-tope) y ampliando el encuadre para que el tope del mastil -- que es
la novedad de esta variante -- entre en el cuadro. El flotador se pinta con el
color de acento de cada paleta (alta visibilidad, como corresponde a un
elemento de seguridad).
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
import rhino3dm as r3
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import geom.render_ideas as ri
import geom.render_scene as rs
from calc.autoadrizante import DIR
from calc.geometry import HullGeometry
from calc.params import Design

WL_CALM = 0.217
WL_SAIL = 0.245


def load_parts() -> list[tuple[str, np.ndarray]]:
    """Triangulos por capa del 3DM de la variante."""
    f = r3.File3dm.Read(os.path.join(DIR, "boat_autoadrizante.3dm"))
    layers = {i: l.Name for i, l in enumerate(f.Layers)}
    parts = []
    for obj in f.Objects:
        g = obj.Geometry
        if not isinstance(g, r3.Mesh):
            continue
        v = np.array([[p.X, p.Y, p.Z] for p in g.Vertices])
        tris = np.array([v[[g.Faces[k][0], g.Faces[k][1], g.Faces[k][2]]]
                         for k in range(g.Faces.Count)])
        parts.append((layers[obj.Attributes.LayerIndex], tris))
    return parts


# ---------------------------------------------------------------------------
# hull_lines.png (identico en forma al baseline: el casco no cambia)
# ---------------------------------------------------------------------------


def hull_lines() -> None:
    d = Design()
    geom = HullGeometry(d.hull, d.cockpit)
    fig, axes = plt.subplots(3, 1, figsize=(9, 9))
    ax = axes[0]
    for i in range(0, len(geom.x), max(1, len(geom.x) // 14)):
        sec = geom._sections[i]
        if len(sec) < 3:
            continue
        closed = np.vstack([sec, sec[:1]])
        ax.plot(closed[:, 0], closed[:, 1], color="#4477aa", linewidth=1.0)
    ax.set_aspect("equal")
    ax.set_title("body plan  (variante auto-adrizante: casco identico al baseline)")
    ax.set_xlabel("y (m)")
    ax.set_ylabel("z (m)")
    ax.grid(alpha=0.2)

    ax = axes[1]
    ax.plot(geom.x, geom.z_keel, color="#333333", label="keel")
    ax.plot(geom.x, geom.z_chine, color="#cc6677", label="chine")
    ax.plot(geom.x, geom.z_sheer, color="#4477aa", label="sheer")
    ax.axhline(d.cockpit.sole_z, color="#999933", linestyle=":", label="cockpit sole")
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
    path = os.path.join(DIR, "hull_lines.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print("escrito:", path)


# ---------------------------------------------------------------------------
# previews del 3DM
# ---------------------------------------------------------------------------

NEUTRAL_PAL = ("PREVIEW", "#8fa3b0", "#40566a", "#5d6d79", "#d8dcdf",
               "#4a80b0", "")


def _load_boat_ri(include_float: bool) -> list:
    """Partes en el formato de render_ideas (capa, vertices, indices)."""
    f = r3.File3dm.Read(os.path.join(DIR, "boat_autoadrizante.3dm"))
    layers = {i: l.Name for i, l in enumerate(f.Layers)}
    parts = []
    for obj in f.Objects:
        g = obj.Geometry
        if isinstance(g, r3.Mesh):
            lay = layers[obj.Attributes.LayerIndex]
            if lay == "flotador-tope" and not include_float:
                continue
            v = np.array([[p.X, p.Y, p.Z] for p in g.Vertices])
            tris = np.array([[g.Faces[k][0], g.Faces[k][1], g.Faces[k][2]]
                             for k in range(g.Faces.Count)])
            parts.append((lay, v, tris))
    return parts


def previews() -> None:
    # vista general, con el flotador en cuadro. render_palette clasifica las
    # caras del casco en fondo/franja/costado/cubierta -- eso es lo que hace
    # visible el cockpit (una sola malla pierde el ordenado por profundidad).
    parts = _load_boat_ri(include_float=True)
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    ri.render_palette(ax, [p for p in parts if p[0] != "flotador-tope"],
                      NEUTRAL_PAL)
    for lay, v, tris in parts:
        if lay == "flotador-tope":
            polys = [[v[a], v[b], v[c]] for a, b, c in tris]
            ax.add_collection3d(Poly3DCollection(polys, facecolor="#c0392b",
                                                 edgecolor="none"))
    ax.set_xlim(-0.2, 6.8)
    ax.set_ylim(-3.5, 3.5)
    ax.set_zlim(-1.4, 10.2)
    ax.set_box_aspect((7.0, 7.0, 11.6))
    ax.view_init(elev=22, azim=-58)
    ax.axis("off")
    ax.set_title("boat_autoadrizante.3dm — casco, quilla, timon, aparejo, "
                 "bancos-tanque y flotador de tope (capa nueva)", fontsize=11)
    path = os.path.join(DIR, "preview_3dm.png")
    fig.savefig(path, dpi=135, bbox_inches="tight")
    plt.close(fig)
    print("escrito:", path)

    # vista alta del cockpit (sin aparejo: el mastil saldria del encuadre)
    parts_cp = [p for p in _load_boat_ri(include_float=False)
                if p[0] != "rig"]
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    ri.render_palette(ax, parts_cp, NEUTRAL_PAL)
    ax.set_xlim(0.2, 5.2)
    ax.set_ylim(-2.5, 2.5)
    ax.set_zlim(-0.9, 4.1)
    ax.set_box_aspect((5.0, 5.0, 5.0))
    ax.view_init(elev=38, azim=-62)
    ax.axis("off")
    ax.set_title("vista alta: cockpit 6 plazas, bancos-tanque (azul) y timon "
                 "central — sin cambios en la variante", fontsize=11)
    path = os.path.join(DIR, "preview_cockpit.png")
    fig.savefig(path, dpi=135, bbox_inches="tight")
    plt.close(fig)
    print("escrito:", path)


# ---------------------------------------------------------------------------
# 'fotos' en el agua (adaptacion de render_scene con encuadre alto y flotador)
# ---------------------------------------------------------------------------


def render_foto(name: str, palette: str, heel: float, z_wl: float,
                sails_on: bool, az: float, el: float, fname: str) -> None:
    pal = rs.PAL[palette]
    parts = load_parts()

    items = []
    hull = next(t for lay, t in parts if lay == "hull")
    zc = hull[:, :, 2].mean(axis=1)
    normals = np.cross(hull[:, 1] - hull[:, 0], hull[:, 2] - hull[:, 0])
    nz = normals[:, 2] / np.linalg.norm(normals, axis=1).clip(1e-12)
    deck_mask = (np.abs(nz) > 0.55) & (zc > 0.35)
    boot_mask = (~deck_mask) & (zc < 0.34)
    tops_mask = (~deck_mask) & (~boot_mask)
    items.append((hull[deck_mask], pal["deck"]))
    items.append((hull[boot_mask], pal["boot"]))
    items.append((hull[tops_mask], pal["tops"]))
    for lay, t in parts:
        if lay == "bench-tanks":
            items.append((t, pal["bench"]))
        elif lay == "rig":
            items.append((t, "#3c3c3c"))
        elif lay in ("keel", "rudders"):
            items.append((t, "#4a4e55"))
        elif lay == "flotador-tope":
            items.append((t, pal["bench"]))  # acento: elemento de seguridad
    if sails_on:
        main, jib = rs.make_sails()
        items.append((main, pal["sail"]))
        items.append((jib, pal["sail"]))

    world = []
    for tris, col in items:
        t = rs.heel_tris(tris, heel)
        t[..., 2] -= z_wl
        world.append((t, col))

    u, v, f = rs.camera(az, el)
    fig, ax = plt.subplots(figsize=(12.5, 9.6))

    grad = np.linspace(0, 1, 256)[:, None]
    sky = (1 - grad) * np.array(matplotlib.colors.to_rgb(pal["sky_hi"])) + \
        grad * np.array(matplotlib.colors.to_rgb(pal["sky_lo"]))
    sea = (1 - grad) * np.array(matplotlib.colors.to_rgb(pal["sea_hi"])) + \
        grad * np.array(matplotlib.colors.to_rgb(pal["sea_lo"]))
    XL, XR, YB, YT = -6.5, 7.5, -4.2, 10.6  # techo alto: el flotador en cuadro
    ax.imshow(np.tile(sky[:, None, :], (1, 8, 1)),
              extent=[XL, XR, 0, YT], aspect="auto", zorder=0, origin="lower")
    ax.imshow(np.tile(sea[:, None, :], (1, 8, 1)),
              extent=[XL, XR, YB, 0], aspect="auto", zorder=0, origin="upper")

    # reflejo
    polys_r, cols_r, depth_r = [], [], []
    for tris, col in world:
        t = rs.clip_above(tris, 0.0)
        if not len(t):
            continue
        keep = t[:, :, 2].mean(axis=1) < 2.2
        t = t[keep]
        if not len(t):
            continue
        m = t.copy()
        m[..., 2] *= -1
        cols = rs.shade(m, col, f) * 0.55
        for k in range(len(m)):
            p = m[k]
            polys_r.append(np.column_stack([p @ u, p @ v]))
            cols_r.append(cols[k])
            depth_r.append((p @ f).mean())
    if polys_r:
        order = np.argsort(depth_r)
        ax.add_collection(PolyCollection(
            [polys_r[i] for i in order], facecolors=[cols_r[i] for i in order],
            edgecolors="none", alpha=0.30, zorder=1))

    # bote
    polys, cols_l, depth = [], [], []
    for tris, col in world:
        t = rs.clip_above(tris, 0.0)
        if not len(t):
            continue
        cc = rs.shade(t, col, f)
        for k in range(len(t)):
            p = t[k]
            polys.append(np.column_stack([p @ u, p @ v]))
            cols_l.append(cc[k])
            depth.append((p @ f).mean())
    order = np.argsort(depth)
    ax.add_collection(PolyCollection(
        [polys[i] for i in order], facecolors=[cols_l[i] for i in order],
        edgecolors="none", zorder=3))

    # linea de agua + estela
    hull_h = rs.heel_tris(hull, heel)
    hull_h[..., 2] -= z_wl
    pts = hull_h.reshape(-1, 3)
    near = pts[np.abs(pts[:, 2]) < 0.03]
    if len(near):
        s2d = np.column_stack([near @ u, near @ v])
        ax.scatter(s2d[:, 0], s2d[:, 1], s=3.5, color="white", alpha=0.75,
                   zorder=4, linewidths=0)
        x0 = s2d[:, 0].min()
        y0 = s2d[:, 1].mean()
        for k in range(7):
            xx = x0 - 0.35 - 0.75 * k
            ax.plot([xx, xx + 0.55], [y0 - 0.05 - 0.05 * k] * 2, color="white",
                    lw=1.6, alpha=0.35 - 0.04 * k, zorder=2)
        for k in range(14):
            xx = XL + 0.6 + (XR - XL - 1.2) * (k / 13.0)
            ax.plot([xx, xx + 0.5], [-1.6 - 0.14 * (k % 5)] * 2, color="white",
                    lw=1.0, alpha=0.10, zorder=2)

    ax.set_xlim(XL, XR)
    ax.set_ylim(YB, YT)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(name, fontsize=12, loc="left", color="#233")
    fig.text(0.01, 0.012,
             "Render estilizado desde el modelo de calculo (flotacion e inclinacion reales). No es fotografia.",
             fontsize=7.5, color="#667")
    fig.tight_layout()
    path = os.path.join(DIR, fname)
    fig.savefig(path, dpi=135, facecolor="white")
    plt.close(fig)
    print("escrito:", path)


def fotos() -> None:
    render_foto(
        "PATAGONIA — navegando con flotador de tope (escora 14°, tanque de barlovento)",
        "PATAGONIA", heel=14.0, z_wl=WL_SAIL, sails_on=True,
        az=-38, el=13, fname="foto_patagonia_navegando.png")
    render_foto(
        "AIRA — fondeado en calma; el flotador de 60 L en el tope (flotacion rosca 0.217 m)",
        "AIRA", heel=0.0, z_wl=WL_CALM, sails_on=False,
        az=-142, el=9, fname="foto_aira_fondeado.png")


# ---------------------------------------------------------------------------
# estudio de diseno (paletas + perfil), sobre el 3DM de la variante
# ---------------------------------------------------------------------------


def diseno() -> None:
    def load_boat_variant():
        f = r3.File3dm.Read(os.path.join(DIR, "boat_autoadrizante.3dm"))
        layers = {i: l.Name for i, l in enumerate(f.Layers)}
        parts = []
        for obj in f.Objects:
            g = obj.Geometry
            if isinstance(g, r3.Mesh):
                lay = layers[obj.Attributes.LayerIndex]
                if lay == "flotador-tope":
                    continue  # fuera del encuadre del tablero (zlim 4.2)
                v = np.array([[p.X, p.Y, p.Z] for p in g.Vertices])
                tris = np.array([[g.Faces[k][0], g.Faces[k][1], g.Faces[k][2]]
                                 for k in range(g.Faces.Count)])
                parts.append((lay, v, tris))
        return parts

    old_load, old_out = ri.load_boat, ri.OUT
    ri.load_boat, ri.OUT = load_boat_variant, DIR
    try:
        ri.board_colorways()
        ri.profile_styling()
    finally:
        ri.load_boat, ri.OUT = old_load, old_out


def main() -> None:
    os.makedirs(DIR, exist_ok=True)
    hull_lines()
    previews()
    fotos()
    diseno()


if __name__ == "__main__":
    main()
