"""Escenas 'en el agua':  python3 -m geom.render_scene

Escribe:
  out/foto_patagonia_navegando.png   escorado 14°, velas llenas, paleta PATAGONIA
  out/foto_aira_fondeado.png         fondeado en calma, paleta AIRA

Render estilizado desde el modelo real (no es fotografia generada): proyeccion
ortografica + sombreado lambertiano + recorte en la flotacion de calculo +
reflejo especular en el agua. El casco flota donde dice la hidrostatica.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rhino3dm as r3
from matplotlib.collections import PolyCollection

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

WL_CALM = 0.217  # flotacion rosca (hidrostatica)
WL_SAIL = 0.245  # ~2 tripulantes + tanque de barlovento

PAL = {
    "PATAGONIA": dict(tops="#3a3f45", boot="#e8622d", bottom="#22262a",
                      deck="#ccd2d6", bench="#e8622d", sail="#f2f1ec",
                      sky_hi="#dfeaf2", sky_lo="#b9cede",
                      sea_hi="#6f8ea6", sea_lo="#2e4356"),
    "AIRA": dict(tops="#eceeec", boot="#2c5d8a", bottom="#7c8b94",
                 deck="#d8dcdf", bench="#2c5d8a", sail="#f6f5f0",
                 sky_hi="#eaf3fa", sky_lo="#c8dff0",
                 sea_hi="#8fb4cd", sea_lo="#3f6785"),
}

SUN = np.array([0.45, -0.35, 0.82])
SUN = SUN / np.linalg.norm(SUN)


# ---------------------------------------------------------------------------
# geometria
# ---------------------------------------------------------------------------


def load_parts() -> list[tuple[str, np.ndarray]]:
    """Triangulos (N,3,3) por capa, del 3DM base."""
    f = r3.File3dm.Read(os.path.join(OUT, "boat_baseline.3dm"))
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


def sail_mesh(luff0, luff1, cl0, cl1, camber=0.30, n=14, side=1.0):
    """Superficie de vela triangulada entre gratil (luff0->luff1) y baluma."""
    tris = []
    for i in range(n):
        for j in range(6):
            def pt(si, tj):
                s, t = si / n, tj / 6
                a = np.asarray(luff0) + (np.asarray(luff1) - np.asarray(luff0)) * s
                b = np.asarray(cl0) + (np.asarray(cl1) - np.asarray(cl0)) * s
                p = a + (b - a) * t
                chord = np.linalg.norm(b - a)
                p = p.astype(float)
                p[1] += side * camber * chord * np.sin(np.pi * t) * 0.32
                return p
            p00, p10 = pt(i, j), pt(i + 1, j)
            p01, p11 = pt(i, j + 1), pt(i + 1, j + 1)
            tris += [[p00, p10, p11], [p00, p11, p01]]
    return np.array(tris)


def make_sails():
    main = sail_mesh((4.23, 0, 1.86), (4.21, 0, 9.34),
                     (1.55, 0, 1.80), (3.35, 0, 9.10))
    jib = sail_mesh((6.42, 0, 1.06), (4.27, 0, 7.90),
                    (6.42, 0, 1.06), (3.64, 0, 1.62), camber=0.26)
    return main, jib


# ---------------------------------------------------------------------------
# transformaciones y recorte
# ---------------------------------------------------------------------------


def heel_tris(tris: np.ndarray, deg: float) -> np.ndarray:
    phi = np.radians(deg)
    c, s = np.cos(phi), np.sin(phi)
    out = tris.copy()
    y, z = tris[..., 1], tris[..., 2]
    out[..., 1] = y * c + z * s
    out[..., 2] = -y * s + z * c
    return out


def clip_above(tris: np.ndarray, z0: float) -> np.ndarray:
    """Recorta triangulos al semiespacio z >= z0 (lo de abajo lo tapa el agua)."""
    out = []
    for tri in tris:
        poly = list(tri)
        res = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            ain, bin_ = a[2] >= z0, b[2] >= z0
            if ain:
                res.append(a)
            if ain != bin_:
                t = (z0 - a[2]) / (b[2] - a[2])
                res.append(a + t * (b - a))
        if len(res) >= 3:
            for k in range(1, len(res) - 1):
                out.append([res[0], res[k], res[k + 1]])
    return np.array(out) if out else np.empty((0, 3, 3))


def camera(az_deg: float, el_deg: float):
    az, el = np.radians(az_deg), np.radians(el_deg)
    f = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    up = np.array([0.0, 0.0, 1.0])
    u = np.cross(up, f)
    u /= np.linalg.norm(u)
    v = np.cross(f, u)
    return u, v, f


def shade(tris: np.ndarray, base_rgb, f) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Proyeccion + sombreado; devuelve (poly2d, colores, profundidad)."""
    base = np.array(matplotlib.colors.to_rgb(base_rgb))
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    lam = np.abs(nn @ SUN)
    k = (0.42 + 0.58 * lam)[:, None]
    cols = np.clip(base[None, :] * k, 0, 1)
    return cols


def render_scene(name: str, palette: str, heel: float, z_wl: float,
                 sails_on: bool, az: float, el: float, fname: str):
    pal = PAL[palette]
    parts = load_parts()

    # ensamblar (capa, tris, color)
    items = []
    hull = next(t for lay, t in parts if lay == "hull")
    # clasificar caras del casco
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
    if sails_on:
        main, jib = make_sails()
        items.append((main, pal["sail"]))
        items.append((jib, pal["sail"]))

    # escorar + poner la flotacion en z=0
    world = []
    for tris, col in items:
        t = heel_tris(tris, heel)
        t[..., 2] -= z_wl
        world.append((t, col))

    u, v, f = camera(az, el)
    fig, ax = plt.subplots(figsize=(13.5, 8.2))

    # cielo + mar (gradientes)
    grad = np.linspace(0, 1, 256)[:, None]
    sky = (1 - grad) * np.array(matplotlib.colors.to_rgb(pal["sky_hi"])) + \
        grad * np.array(matplotlib.colors.to_rgb(pal["sky_lo"]))
    sea = (1 - grad) * np.array(matplotlib.colors.to_rgb(pal["sea_hi"])) + \
        grad * np.array(matplotlib.colors.to_rgb(pal["sea_lo"]))
    XL, XR, YB, YT = -6.5, 7.5, -4.2, 8.6
    ax.imshow(sky[None, :, 0, :] if False else np.tile(sky[:, None, :], (1, 8, 1)),
              extent=[XL, XR, 0, YT], aspect="auto", zorder=0, origin="lower")
    ax.imshow(np.tile(sea[:, None, :], (1, 8, 1)),
              extent=[XL, XR, YB, 0], aspect="auto", zorder=0, origin="upper")

    # reflejo (espejo z -> -z, mas oscuro, alfa)
    polys_r, cols_r, depth_r = [], [], []
    for tris, col in world:
        t = clip_above(tris, 0.0)
        if not len(t):
            continue
        # el reflejo se atenua: solo los primeros ~2.2 m sobre el agua
        keep = t[:, :, 2].mean(axis=1) < 2.2
        t = t[keep]
        if not len(t):
            continue
        m = t.copy()
        m[..., 2] *= -1
        cols = shade(m, col, f) * 0.55
        for k in range(len(m)):
            p = m[k]
            polys_r.append(np.column_stack([p @ u, p @ v]))
            cols_r.append(cols[k])
            depth_r.append((p @ f).mean())
    order = np.argsort(depth_r)
    pc = PolyCollection([polys_r[i] for i in order],
                        facecolors=[cols_r[i] for i in order],
                        edgecolors="none", alpha=0.30, zorder=1)
    ax.add_collection(pc)

    # bote (recortado en la flotacion)
    polys, cols_l, depth = [], [], []
    for tris, col in world:
        t = clip_above(tris, 0.0)
        if not len(t):
            continue
        cc = shade(t, col, f)
        for k in range(len(t)):
            p = t[k]
            polys.append(np.column_stack([p @ u, p @ v]))
            cols_l.append(cc[k])
            depth.append((p @ f).mean())
    order = np.argsort(depth)
    pc = PolyCollection([polys[i] for i in order],
                        facecolors=[cols_l[i] for i in order],
                        edgecolors="none", zorder=3)
    ax.add_collection(pc)

    # linea de agua del casco + estela
    hull_h = heel_tris(hull, heel)
    hull_h[..., 2] -= z_wl
    pts = hull_h.reshape(-1, 3)
    near = pts[np.abs(pts[:, 2]) < 0.03]
    if len(near):
        s2d = np.column_stack([near @ u, near @ v])
        ax.scatter(s2d[:, 0], s2d[:, 1], s=3.5, color="white", alpha=0.75,
                   zorder=4, linewidths=0)
        x0, x1 = s2d[:, 0].min(), s2d[:, 0].max()
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
    path = os.path.join(OUT, fname)
    fig.savefig(path, dpi=135, facecolor="white")
    plt.close(fig)
    print("escrito:", path)


def main():
    render_scene(
        "PATAGONIA — navegando, tanque de barlovento lleno (escora 14°)",
        "PATAGONIA", heel=14.0, z_wl=WL_SAIL, sails_on=True,
        az=-38, el=13, fname="foto_patagonia_navegando.png")
    render_scene(
        "AIRA — fondeado en calma (flotacion rosca de calculo, 0.217 m)",
        "AIRA", heel=0.0, z_wl=WL_CALM, sails_on=False,
        az=-142, el=9, fname="foto_aira_fondeado.png")


if __name__ == "__main__":
    main()
