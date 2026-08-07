"""Mesh generation and STL export for the parametric hull.

The hull is a two-panel-per-side hard chine form, which is what both viable HDPE
processes want: rotomoulding needs a shape that releases from a shell tool
without undercuts, and welded-sheet construction needs panels that develop flat.
Every surface here is a ruled surface between adjacent station polylines, so the
side and bottom panels are developable to within the small twist the plan taper
introduces -- flat sheet will take them with heat and no compound forming.

    python3 -m geom.hull                 # baseline, out/hull_baseline.stl
    python3 -m geom.hull --self-righting # 1.80 m beam variant

STL is written binary. Units are metres; scale by 1000 on import if your CAD
expects millimetres.
"""

from __future__ import annotations

import argparse
import copy
import os
import struct

import numpy as np

from calc.geometry import HullGeometry
from calc.params import Design

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

# Order around a closed station loop. Indices must be consistent station to
# station so the ruled surfaces between them are well defined.
LOOP_KEEL = 0
LOOP_CHINE_S = 1
LOOP_SHEER_S = 2
LOOP_CROWN = 3
LOOP_SHEER_P = 4
LOOP_CHINE_P = 5
LOOP_N = 6


def station_loop(geom: HullGeometry, i: int) -> np.ndarray:
    """The six ordered (x, y, z) points of station i, closed loop."""
    x = geom.x[i]
    ys, yc = geom.y_sheer[i], geom.y_chine[i]
    zk, zc, zs, zx = geom.z_keel[i], geom.z_chine[i], geom.z_sheer[i], geom.z_crown[i]
    return np.array(
        [
            [x, 0.0, zk],
            [x, yc, zc],
            [x, ys, zs],
            [x, 0.0, zx],
            [x, -ys, zs],
            [x, -yc, zc],
        ],
        dtype=float,
    )


def build_mesh(geom: HullGeometry) -> tuple[np.ndarray, np.ndarray]:
    """Return (vertices, triangles) for the closed hull shell."""
    loops = [station_loop(geom, i) for i in range(len(geom.x))]
    verts: list[np.ndarray] = []
    tris: list[tuple[int, int, int]] = []

    for loop in loops:
        verts.extend(loop)

    n_st = len(loops)
    for i in range(n_st - 1):
        a = i * LOOP_N
        b = (i + 1) * LOOP_N
        for k in range(LOOP_N):
            k2 = (k + 1) % LOOP_N
            v00, v01 = a + k, a + k2
            v10, v11 = b + k, b + k2
            # Two triangles per quad; degenerate ones are dropped on write.
            tris.append((v00, v10, v11))
            tris.append((v00, v11, v01))

    # Cap the transom (station 0) and the bow (last station) with fans.
    for base, flip in ((0, False), ((n_st - 1) * LOOP_N, True)):
        centre = len(verts)
        verts.append(np.mean(np.asarray([verts[base + k] for k in range(LOOP_N)]), axis=0))
        for k in range(LOOP_N):
            k2 = (k + 1) % LOOP_N
            tri = (centre, base + k, base + k2)
            tris.append(tri[::-1] if flip else tri)

    return np.asarray(verts, dtype=float), np.asarray(tris, dtype=np.int64)


def write_stl(path: str, verts: np.ndarray, tris: np.ndarray, name: str = "hull") -> int:
    """Write a binary STL, skipping degenerate triangles. Returns facet count."""
    facets: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    for i0, i1, i2 in tris:
        p0, p1, p2 = verts[i0], verts[i1], verts[i2]
        n = np.cross(p1 - p0, p2 - p0)
        mag = np.linalg.norm(n)
        if mag < 1e-12:
            continue  # collapsed at the bow or on centreline
        facets.append((n / mag, p0, p1, p2))

    with open(path, "wb") as f:
        f.write(struct.pack("<80s", name.encode()[:80]))
        f.write(struct.pack("<I", len(facets)))
        for n, p0, p1, p2 in facets:
            f.write(struct.pack("<12f", *n, *p0, *p1, *p2))
            f.write(struct.pack("<H", 0))
    return len(facets)


def write_offsets(path: str, geom: HullGeometry) -> None:
    """Table of offsets -- the form a builder or a lofting program wants."""
    with open(path, "w") as f:
        f.write("# Table of offsets. Units: metres.\n")
        f.write("# x from transom, y half-breadth from centreline, z above baseline.\n")
        f.write("# Baseline z=0 is the lowest point of the canoe body.\n")
        f.write(f"{'x':>8}{'y_chine':>10}{'z_chine':>10}"
                f"{'y_sheer':>10}{'z_sheer':>10}{'z_keel':>10}{'z_crown':>10}\n")
        for i in range(len(geom.x)):
            f.write(
                f"{geom.x[i]:>8.3f}{geom.y_chine[i]:>10.4f}{geom.z_chine[i]:>10.4f}"
                f"{geom.y_sheer[i]:>10.4f}{geom.z_sheer[i]:>10.4f}"
                f"{geom.z_keel[i]:>10.4f}{geom.z_crown[i]:>10.4f}\n"
            )


def _edge_curves(geom: HullGeometry) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """The pairs of space curves bounding each panel, starboard side."""
    keel = np.column_stack([geom.x, np.zeros_like(geom.x), geom.z_keel])
    chine = np.column_stack([geom.x, geom.y_chine, geom.z_chine])
    sheer = np.column_stack([geom.x, geom.y_sheer, geom.z_sheer])
    return {"bottom": (keel, chine), "side": (chine, sheer)}


def panel_development_check(geom: HullGeometry) -> dict:
    """How far each panel is from being developable to flat sheet.

    The correct test is not whether the mesh quads are planar -- a developable
    surface is generally ruled along lines that are *not* transverse, so
    station-to-station quads are non-planar even on a perfectly developable
    panel. The standard condition is that for corresponding points on the two
    bounding curves, the two tangents and the connecting chord are coplanar:

        det[ t1, t2, (P2 - P1) ] = 0

    With all three vectors normalised this is a dimensionless twist measure in
    [-1, 1]. Zero means the panel rolls onto flat sheet exactly. Below ~0.05 is
    comfortably formable in HDPE sheet with heat; above ~0.15 needs compound
    forming, which sheet PE will not do -- that region has to be rotomoulded,
    split into narrower strakes, or reshaped.
    """
    out: dict = {}
    for name, (c1, c2) in _edge_curves(geom).items():
        t1 = np.gradient(c1, geom.x, axis=0)
        t2 = np.gradient(c2, geom.x, axis=0)
        chord = c2 - c1

        def unit(v: np.ndarray) -> np.ndarray:
            n = np.linalg.norm(v, axis=1, keepdims=True)
            return np.divide(v, n, out=np.zeros_like(v), where=n > 1e-12)

        t1u, t2u, du = unit(t1), unit(t2), unit(chord)
        twist = np.abs(np.einsum("ij,ij->i", np.cross(t1u, t2u), du))

        # The stem is a genuine singularity (chord length goes to zero); report
        # the body of the panel separately from the last 8 % of length.
        body = geom.x <= 0.92 * geom.x.max()
        # Where does the panel stop being sheet-formable? Walk aft from the bow.
        formable_limit = float(geom.x.max())
        over = np.where(twist[body] > 0.05)[0]
        if over.size:
            formable_limit = float(geom.x[body][over.min()])
        out[name] = {
            "max_body": float(twist[body].max()),
            "mean_body": float(twist[body].mean()),
            "max_overall": float(twist.max()),
            "x_at_max_body": float(geom.x[body][int(np.argmax(twist[body]))]),
            "sheet_formable_aft_of": formable_limit,
        }
    return out


def export(design: Design, tag: str) -> dict:
    os.makedirs(OUT, exist_ok=True)
    # Denser stations for a smoother mesh than the hydrostatics needs.
    d = copy.deepcopy(design)
    d.hull.n_stations = 121
    geom = HullGeometry(d.hull, d.cockpit)

    verts, tris = build_mesh(geom)
    stl_path = os.path.join(OUT, f"hull_{tag}.stl")
    n_facets = write_stl(stl_path, verts, tris, name=f"hdpe-daysailer-{tag}")

    off_path = os.path.join(OUT, f"offsets_{tag}.txt")
    write_offsets(off_path, geom)

    dev = panel_development_check(geom)

    print(f"[{tag}]")
    print(f"  LOA {d.hull.loa:.3f} m   beam {geom.max_beam:.3f} m"
          f"   depth {float(geom.z_sheer.min() - geom.z_keel.min()):.3f} m")
    print(f"  shell area {geom.shell_area():.2f} m2"
          f"   deck+cockpit {geom.deck_area():.2f} m2")
    print(f"  mesh: {len(verts)} vertices, {n_facets} facets -> {stl_path}")
    print(f"  offsets -> {off_path}")
    print("  developability (0 = rolls onto flat sheet exactly):")
    for name, dv in dev.items():
        print(f"    {name:<7} mean {dv['mean_body']:.4f}, peak {dv['max_body']:.4f}"
              f" at x={dv['x_at_max_body']:.2f} m")
    limit = min(dv["sheet_formable_aft_of"] for dv in dev.values())
    pct = limit / d.hull.loa
    print(f"    sheet-formable from the transom to x = {limit:.2f} m"
          f" ({pct:.0%} of LOA)")
    print(f"    forward of that the entry twists too hard for flat PE sheet:")
    print(f"    rotomould the stem as a separate welded-on piece, split the")
    print(f"    forward panels into narrower strakes, or straighten the entry.")
    return {"stl": stl_path, "offsets": off_path, "dev": dev, "facets": n_facets}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-righting", action="store_true",
                    help="export the 1.80 m beam variant that meets the "
                         "true self-righting requirement")
    ap.add_argument("--both", action="store_true", help="export both variants")
    args = ap.parse_args()

    if args.both or not args.self_righting:
        export(Design(), "baseline")
    if args.both or args.self_righting:
        d = Design()
        d.hull.beam_sheer = 1.80
        d.ballast.keel_mass = 452.0
        export(d, "selfrighting")


if __name__ == "__main__":
    main()
