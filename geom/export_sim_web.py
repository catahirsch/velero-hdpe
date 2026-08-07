"""Exporta la simulacion de adrizado para el visor web 3D.

    python3 -m geom.export_sim_web   ->  autoadrizante/righting_sim.json

Corre la MISMA fisica que selfrighting.gif (rolido 1-DOF sobre las curvas GZ
reales, rosca, cockpit inundado, tanques vacios) y guarda las trayectorias
phi(t) de las dos configuraciones mas la altura de flotacion resuelta por
angulo, para que el visor three.js mueva el bote completo en 3D con la
flotacion correcta en cada instante.
"""

from __future__ import annotations

import json
import os

import numpy as np

from calc.autoadrizante import DIR
from geom.animate_autoadrizante import FPS, START_DEG, T_END, build_boat, simulate

ZWL_STEP = 5.0


def main() -> None:
    out = {"fps": FPS, "t_end": T_END, "start_deg": START_DEG,
           "zwl_step": ZWL_STEP, "boats": {}}
    grid = np.arange(0.0, 180.0 + ZWL_STEP, ZWL_STEP)
    for key, with_float, label in (
        ("con", True, "con mastil sellado + flotador 60 L"),
        ("sin", False, "sin paquete de tope"),
    ):
        print(f"building {key} ({label})...")
        boat = build_boat(with_float, label)
        t, phi = simulate(boat)
        n = int(T_END * FPS)
        idx = np.linspace(0, len(t) - 1, n).astype(int)
        out["boats"][key] = {
            "label": label,
            "phi": [round(float(p), 2) for p in phi[idx]],
            "zwl": [round(float(boat["f_zwl"](a)), 4) for a in grid],
            "final": round(float(phi[-1]), 1),
        }
        print(f"  final {phi[-1]:.0f} deg")
    path = os.path.join(DIR, "righting_sim.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"escrito: {path} ({os.path.getsize(path) / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
