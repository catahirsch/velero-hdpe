"""Exporta el bote por capas a JSON para el visor web (three.js).

    python3 -m geom.export_web   ->  autoadrizante/boat_web.json

Lee boat_autoadrizante.3dm y convierte cada objeto por capa:
  - mallas   -> {v: [x,y,z,...], f: [a,b,c,...]}
  - polilineas -> {pts: [x,y,z,...]}   (lineas del plano, flotaciones)
  - las velas (polilineas cerradas) se triangulan en abanico para poder
    dibujarlas como superficie translucida ademas del contorno.

El visor (index.html) arma un grupo three.js por capa con su color del 3DM y
un checkbox por capa. Regenerar el 3DM y correr este modulo actualiza el
visor publicado.
"""

from __future__ import annotations

import json
import os

import rhino3dm as r3

from calc.autoadrizante import DIR


def _mesh_json(g: r3.Mesh) -> dict:
    v = []
    for p in g.Vertices:
        v += [round(p.X, 4), round(p.Y, 4), round(p.Z, 4)]
    f = []
    for k in range(g.Faces.Count):
        face = g.Faces[k]
        f += [face[0], face[1], face[2]]
        if len(face) == 4 and face[2] != face[3]:
            f += [face[0], face[2], face[3]]
    return {"v": v, "f": f}


def _polyline_pts(g) -> list[float]:
    pts = []
    if isinstance(g, r3.PolylineCurve):
        for i in range(g.PointCount):
            p = g.Point(i)
            pts += [round(p.X, 4), round(p.Y, 4), round(p.Z, 4)]
    return pts


def _fan_mesh(pts: list[float]) -> dict:
    """Triangulacion en abanico de una polilinea cerrada (velas)."""
    n = len(pts) // 3
    f = []
    for k in range(1, n - 1):
        f += [0, k, k + 1]
    return {"v": pts, "f": f}


def main() -> None:
    path3dm = os.path.join(DIR, "boat_autoadrizante.3dm")
    f3 = r3.File3dm.Read(path3dm)
    layers = {}
    layer_names = {}
    for i, lay in enumerate(f3.Layers):
        layer_names[i] = lay.Name
        c = lay.Color
        layers[lay.Name] = {"color": [c[0], c[1], c[2]], "meshes": [], "lines": []}

    for obj in f3.Objects:
        name = layer_names.get(obj.Attributes.LayerIndex, "?")
        g = obj.Geometry
        if isinstance(g, r3.Mesh):
            layers[name]["meshes"].append(_mesh_json(g))
        else:
            pts = _polyline_pts(g)
            if pts:
                layers[name]["lines"].append(pts)
                if name == "sails" and len(pts) >= 12:
                    layers[name]["meshes"].append(_fan_mesh(pts))

    out = {
        "meta": f3.StartSectionComments,
        "order": ["hull", "bench-tanks", "keel", "rudders", "rig", "sails",
                  "flotador-tope", "waterlines", "lines"],
        "layers": layers,
    }
    path = os.path.join(DIR, "boat_web.json")
    with open(path, "w") as fp:
        json.dump(out, fp, separators=(",", ":"))
    kb = os.path.getsize(path) / 1024
    counts = {k: f"{len(v['meshes'])}m/{len(v['lines'])}l" for k, v in layers.items()}
    print(f"escrito: {path} ({kb:.0f} kB) — {counts}")


if __name__ == "__main__":
    main()
