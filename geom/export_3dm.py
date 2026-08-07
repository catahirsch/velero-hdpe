"""Export the boat as a Rhino .3dm file for visualization.

Unlike the STL (which is the closed analysis shell), this model is built to be
looked at: the cockpit is cut into the deck, and the keel, rudders, rig, water
ballast tanks and both waterlines are included on their own layers so each can
be toggled in Rhino.

    python3 -m geom.export_3dm             # out/boat_baseline.3dm
    python3 -m geom.export_3dm --self-righting
    python3 -m geom.export_3dm --both

Units are metres (set in the file header). Layers:

    hull          shell with cockpit recess, transom and bow capped
    keel          pivoting keel shown LOWERED, with the lead bulb at its VCG
    rudders       single centreline kick-up rudder
    rig           mast, boom (cylinder meshes) and forestay
    sails         outline curves of the square-top main and jib
    bench-tanks   the 2 x 250 kg bench-seat water ballast tanks
    waterlines    light (750 kg) and full load (1730 kg) planes as rectangles
    lines         station sections + keel/chine/sheer longitudinals
"""

from __future__ import annotations

import argparse
import copy
import os

import numpy as np
import rhino3dm as r3

from calc import scantlings, stability, weights
from calc.geometry import HullGeometry
from calc.params import Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

LAYERS = {
    "hull": (176, 196, 210, 255),
    "keel": (90, 90, 100, 255),
    "rudders": (120, 110, 90, 255),
    "rig": (60, 60, 60, 255),
    "sails": (200, 200, 210, 255),
    "bench-tanks": (80, 140, 190, 255),
    "waterlines": (60, 120, 200, 255),
    "lines": (150, 60, 60, 255),
}


# ---------------------------------------------------------------------------
# rhino3dm helpers
# ---------------------------------------------------------------------------


def make_model() -> tuple[r3.File3dm, dict[str, r3.ObjectAttributes]]:
    model = r3.File3dm()
    model.Settings.ModelUnitSystem = r3.UnitSystem.Meters
    attrs = {}
    for name, color in LAYERS.items():
        layer = r3.Layer()
        layer.Name = name
        layer.Color = color
        idx = model.Layers.Add(layer)
        a = r3.ObjectAttributes()
        a.LayerIndex = idx
        attrs[name] = a
    return model, attrs


def add_mesh(model: r3.File3dm, attr: r3.ObjectAttributes,
             verts: list, faces: list) -> None:
    """Add a triangle mesh, dropping degenerate faces."""
    m = r3.Mesh()
    for v in verts:
        m.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    v = np.asarray(verts, dtype=float)
    for i, j, k in faces:
        area = 0.5 * np.linalg.norm(np.cross(v[j] - v[i], v[k] - v[i]))
        if area > 1e-10:
            m.Faces.AddFace(i, j, k)
    m.Normals.ComputeNormals()
    m.Compact()
    model.Objects.AddMesh(m, attr)


def add_polyline(model: r3.File3dm, attr: r3.ObjectAttributes,
                 pts: list, closed: bool = False) -> None:
    points = [r3.Point3d(float(p[0]), float(p[1]), float(p[2])) for p in pts]
    if closed:
        points.append(points[0])
    model.Objects.AddCurve(r3.PolylineCurve(points), attr)


def prism_mesh(p0: np.ndarray, p1: np.ndarray, radius: float,
               sides: int = 10) -> tuple[list, list]:
    """Cylinder-ish prism between two points, for spars."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    axis = p1 - p0
    axis /= np.linalg.norm(axis)
    ref = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(axis, ref)
    u /= np.linalg.norm(u)
    w = np.cross(axis, u)
    verts, faces = [], []
    for centre in (p0, p1):
        for s in range(sides):
            ang = 2.0 * np.pi * s / sides
            verts.append(centre + radius * (np.cos(ang) * u + np.sin(ang) * w))
    for s in range(sides):
        s2 = (s + 1) % sides
        a, b, c, d = s, s2, sides + s2, sides + s
        faces += [(a, b, c), (a, c, d)]
    verts += [p0, p1]
    for s in range(sides):
        s2 = (s + 1) % sides
        faces.append((2 * sides, s2, s))
        faces.append((2 * sides + 1, sides + s, sides + s2))
    return verts, faces


def box_mesh(x0, x1, y0, y1, z0, z1) -> tuple[list, list]:
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    faces = []
    for a, b, c, d in quads:
        faces += [(a, b, c), (a, c, d)]
    return verts, faces


def loft8_mesh(root: list, tip: list) -> tuple[list, list]:
    """Hexahedron between two 4-point rectangles (root/tip of a foil)."""
    verts = list(root) + list(tip)
    quads = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    faces = []
    for a, b, c, d in quads:
        faces += [(a, b, c), (a, c, d)]
    return verts, faces


# ---------------------------------------------------------------------------
# Hull with cockpit recess
# ---------------------------------------------------------------------------

EPS = 1.5e-3  # collapsed cockpit half-width outside the cockpit


def station_loop9(geom: HullGeometry, i: int) -> np.ndarray:
    """Nine-point closed section, same topology at every station.

    keel, chine_s, sheer_s, deckedge_s, soleedge_s, soleedge_p, deckedge_p,
    sheer_p, chine_p. Outside the cockpit the deckedge/soleedge points collapse
    onto the deck crown, so the ruled faces between them are degenerate and get
    dropped -- which is what lets one topology carry the cockpit cutout.
    """
    cp = geom.cockpit
    x = geom.x[i]
    ys, yc = geom.y_sheer[i], geom.y_chine[i]
    zk, zc, zs = geom.z_keel[i], geom.z_chine[i], geom.z_sheer[i]
    zx = geom.z_crown[i]

    in_cockpit = cp.x_aft <= x <= cp.x_fwd
    yw = min(cp.half_width, ys * 0.95) if in_cockpit else 0.0
    if in_cockpit and yw > EPS and cp.sole_z < geom._deck_z_at(i, yw) - 1e-6:
        zd = geom._deck_z_at(i, yw)
        z_sole = cp.sole_z
    else:
        yw, zd, z_sole = EPS, zx, zx  # collapsed: solid deck crown

    return np.array(
        [
            [x, 0.0, zk],
            [x, yc, zc],
            [x, ys, zs],
            [x, yw, zd],
            [x, yw, z_sole],
            [x, -yw, z_sole],
            [x, -yw, zd],
            [x, -ys, zs],
            [x, -yc, zc],
        ],
        dtype=float,
    )


def hull_mesh(geom: HullGeometry) -> tuple[list, list]:
    n_pts = 9
    loops = [station_loop9(geom, i) for i in range(len(geom.x))]
    verts: list = []
    for lp in loops:
        verts.extend(lp)
    faces: list = []
    n_st = len(loops)
    for i in range(n_st - 1):
        a, b = i * n_pts, (i + 1) * n_pts
        for k in range(n_pts):
            k2 = (k + 1) % n_pts
            faces += [(a + k, b + k, b + k2), (a + k, b + k2, a + k2)]
    # transom and bow caps
    for base, flip in ((0, False), ((n_st - 1) * n_pts, True)):
        centre = len(verts)
        verts.append(np.mean(np.asarray(verts[base:base + n_pts]), axis=0))
        for k in range(n_pts):
            k2 = (k + 1) % n_pts
            tri = (centre, base + k, base + k2)
            faces.append(tri[::-1] if flip else tri)
    return verts, faces


# ---------------------------------------------------------------------------
# The rest of the boat
# ---------------------------------------------------------------------------


def add_keel(model, attr, design: Design) -> None:
    px = design.ballast.keel_pivot_x
    # Audited keel (calc/audit.py): 15 mm fin, chords 0.50/0.30, lead bulb
    # 0.58 x 0.145 x 0.17 centred at z = -0.99 so the ASSEMBLY VCG is -0.86.
    t = 0.0075
    root = [(px - 0.24, -t, 0.02), (px + 0.26, -t, 0.02),
            (px + 0.26, t, 0.02), (px - 0.24, t, 0.02)]
    tip = [(px - 0.14, -t, -0.90), (px + 0.16, -t, -0.90),
           (px + 0.16, t, -0.90), (px - 0.14, t, -0.90)]
    add_mesh(model, attr, *loft8_mesh(root, tip))
    zb = -0.99
    add_mesh(model, attr, *box_mesh(px - 0.29, px + 0.29, -0.0725, 0.0725,
                                    zb - 0.085, zb + 0.085))


def add_rudders(model, attr, geom: HullGeometry) -> None:
    """Single centreline kick-up rudder (client amendment 2026-08-06).

    Deeper than each of the former twins: a lone blade must keep grip at
    20-25 deg of heel on a 2.35 m beam hull. Transom scuppers split around
    the stock.
    """
    z_top = float(geom.z_sheer[0]) - 0.12
    root = [(0.02, -0.017, z_top), (0.34, -0.017, z_top),
            (0.34, 0.017, z_top), (0.02, 0.017, z_top)]
    tip = [(0.07, -0.011, -0.58), (0.30, -0.011, -0.58),
           (0.30, 0.011, -0.58), (0.07, 0.011, -0.58)]
    add_mesh(model, attr, *loft8_mesh(root, tip))


def add_rig(model, attrs, design: Design, geom: HullGeometry) -> None:
    mast_x, deck_z = 4.25, 0.86
    head_z = deck_z + design.rig.mast_height
    boom_z = 1.66  # [NOTES] "botavara alta" -- clears seated heads on the sole
    add_mesh(model, attrs["rig"],
             *prism_mesh((mast_x, 0, deck_z), (mast_x, 0, head_z), 0.045))
    add_mesh(model, attrs["rig"],
             *prism_mesh((mast_x - 0.02, 0, boom_z), (1.30, 0, boom_z - 0.04), 0.035))
    bow = (float(geom.x[-1]) - 0.03, 0.0, float(geom.z_sheer[-1]))
    hounds = (mast_x, 0.0, deck_z + 0.82 * design.rig.mast_height)
    add_polyline(model, attrs["rig"], [bow, hounds])
    # sail outlines
    add_polyline(model, attrs["sails"],
                 [(mast_x, 0, boom_z + 0.04), (1.38, 0, boom_z),
                  (3.45, 0, head_z - 0.25), (mast_x, 0, head_z - 0.05)],
                 closed=True)
    add_polyline(model, attrs["sails"],
                 [bow, hounds, (3.55, 0, boom_z - 0.15)], closed=True)


def bench_mesh(geom: HullGeometry, design: Design, side: int) -> tuple[list, list]:
    """Bench-tank solid lofted station a station, DENTRO del casco.

    La caja constante anterior atravesaba la geometria: con francobordo bajo a
    popa, un asiento a z=0.80 sobresale de la cubierta lateral local (~0.77) y
    la cara exterior coincidia exactamente con la pared del cockpit
    (z-fighting en los renders). Aqui la cara exterior queda 8 mm adentro de
    la pared y la tapa se limita a 15 mm bajo el borde de cubierta local, asi
    el banco sigue la linea de la cubierta hacia popa.
    """
    cp = design.cockpit
    secs: list[tuple[float, np.ndarray]] = []
    for i, x in enumerate(geom.x):
        if not (cp.x_aft <= x <= cp.x_fwd):
            continue
        yw = min(cp.half_width, geom.y_sheer[i] * 0.95)
        yo = yw - 0.008  # cara exterior: 8 mm adentro de la pared
        yi = cp.bench_inner_y
        if yo - yi < 0.05:
            continue
        top = min(cp.bench_top_z, geom._deck_z_at(i, yw) - 0.015)
        if top - cp.sole_z < 0.05:
            continue
        quad = np.array([[x, side * yi, cp.sole_z],
                         [x, side * yo, cp.sole_z],
                         [x, side * yo, top],
                         [x, side * yi, top]], dtype=float)
        secs.append((x, quad))
    verts: list = []
    faces: list = []
    for _, q in secs:
        verts.extend(q)
    n = len(secs)
    for i in range(n - 1):
        a, b = 4 * i, 4 * (i + 1)
        for k in range(4):
            k2 = (k + 1) % 4
            faces += [(a + k, b + k, b + k2), (a + k, b + k2, a + k2)]
    # tapas de proa y popa
    if n:
        faces += [(0, 1, 2), (0, 2, 3)]
        m = 4 * (n - 1)
        faces += [(m, m + 2, m + 1), (m, m + 3, m + 2)]
    return verts, faces


def add_tanks(model, attr, design: Design, geom: HullGeometry) -> None:
    """Bench seats = water ballast tanks, lofted to the hull (see bench_mesh)."""
    for s in (-1, 1):
        v, f = bench_mesh(geom, design, s)
        if v:
            add_mesh(model, attr, v, f)


def add_waterlines(model, attr, z_light: float, z_loaded: float, loa: float) -> None:
    for z, tag in ((z_light, "light"), (z_loaded, "loaded")):
        add_polyline(model, attr,
                     [(-0.25, -1.35, z), (loa + 0.25, -1.35, z),
                      (loa + 0.25, 1.35, z), (-0.25, 1.35, z)],
                     closed=True)


def add_lines(model, attr, geom: HullGeometry) -> None:
    step = max(1, len(geom.x) // 15)
    for i in range(0, len(geom.x), step):
        lp = station_loop9(geom, i)
        add_polyline(model, attr, lp, closed=True)
    for ys, zs in (("y_sheer", "z_sheer"), ("y_chine", "z_chine")):
        y, z = getattr(geom, ys), getattr(geom, zs)
        for sgn in (1.0, -1.0):
            add_polyline(model, attr, np.column_stack([geom.x, sgn * y, z]))
    add_polyline(model, attr, np.column_stack(
        [geom.x, np.zeros_like(geom.x), geom.z_keel]))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def solve_waterlines(design: Design, geom: HullGeometry) -> tuple[float, float]:
    """Actual floating waterlines for the light and full-load conditions."""
    m_ldc = design.envelope.disp_max + design.crew_mass_each * design.cockpit.seats
    sc = scantlings.evaluate(design, m_ldc)
    wb = weights.build(design, sc["mass_per_area"], geom.shell_area(), geom.deck_area())
    design.ballast.keel_mass = max(wb.ballast_available, 0.0)
    hs_l = stability.upright_hydrostatics(geom, design, wb.disp_light)
    hs_f = stability.upright_hydrostatics(geom, design, wb.disp_loaded)
    return (hs_l.z_wl if hs_l else 0.22), (hs_f.z_wl if hs_f else 0.33)


def export(design: Design, tag: str) -> str:
    os.makedirs(OUT, exist_ok=True)
    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)
    z_light, z_loaded = solve_waterlines(d, geom)

    model, attrs = make_model()
    model.ApplicationName = "bote geom/export_3dm.py"
    model.StartSectionComments = (
        f"HDPE open daysailer -- {tag}. LOA {d.hull.loa:.2f} m, beam "
        f"{geom.max_beam:.2f} m. Base models RS Aira 22 / Flow 19. Units metres. "
        f"Waterlines: light z={z_light:.3f}, full load z={z_loaded:.3f}."
    )

    add_mesh(model, attrs["hull"], *hull_mesh(geom))
    add_keel(model, attrs["keel"], d)
    add_rudders(model, attrs["rudders"], geom)
    add_rig(model, attrs, d, geom)
    add_tanks(model, attrs["bench-tanks"], d, geom)
    add_waterlines(model, attrs["waterlines"], z_light, z_loaded, d.hull.loa)
    add_lines(model, attrs["lines"], geom)

    path = os.path.join(OUT, f"boat_{tag}.3dm")
    ok = model.Write(path, 7)  # Rhino 7 format, opens in 7 and 8
    print(f"[{tag}] {'written' if ok else 'WRITE FAILED'}: {path}")
    print(f"  waterlines: light z={z_light:.3f} m, full load z={z_loaded:.3f} m")
    return path


def verify(path: str) -> None:
    f = r3.File3dm.Read(path)
    by_layer: dict[str, int] = {}
    layers = {i: lay.Name for i, lay in enumerate(f.Layers)}
    for obj in f.Objects:
        name = layers.get(obj.Attributes.LayerIndex, "?")
        by_layer[name] = by_layer.get(name, 0) + 1
    total = sum(by_layer.values())
    print(f"  verify: {total} objects -- " +
          ", ".join(f"{k}:{v}" for k, v in sorted(by_layer.items())))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-righting", action="store_true")
    ap.add_argument("--both", action="store_true")
    args = ap.parse_args()

    if args.both or not args.self_righting:
        verify(export(Design(), "baseline"))
    if args.both or args.self_righting:
        import dataclasses
        d = Design()
        d.hull.beam_sheer = 1.80
        # Self-righting variant floats at ~988 kg with a 452 kg keel: raise the
        # budget cap so solve_waterlines lands on the variant's real ballast.
        d.envelope = dataclasses.replace(d.envelope, disp_max=934.0)
        verify(export(d, "selfrighting"))


if __name__ == "__main__":
    main()
