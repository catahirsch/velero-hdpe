"""Animacion de la variante: el flotador de tope contra la tortuga.

    python3 -m geom.animate_autoadrizante   ->  autoadrizante/selfrighting.gif
                                                + anim_inicio/medio/final.png

El MISMO casco de 2.35 m, soltado a 150 grados (tumbado mas alla de la
vertical, mastil bien hundido -- la peor escora de la que la variante debe
volver), en las dos configuraciones:

  IZQ  -- sin el paquete de tope (baseline): GZ ya es negativo a 150, el
          casco sigue rodando y se asienta tortuga a 180.
  DER  -- variante auto-adrizante: el mastil sellado + flotador de 60 L hacen
          GZ positivo hasta ~156, el aparejo empuja el barco de vuelta y
          termina adrizado.

Igual que geom/animate_righting.py: la trayectoria integra la ecuacion de
rolido 1-DOF sobre las curvas GZ REALES (rosca, cockpit inundado, tanques
vacios; la curva de la variante sale de calc/autoadrizante.py con el aparejo
sellado dentro de la hidrostatica). Inercia y amortiguamiento son didacticos:
el tiempo es aproximado, los equilibrios y el veredicto son exactos. El
encuadre es ancho a proposito: la fisica pasa en el tope del mastil.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Ellipse
from scipy.interpolate import interp1d

from calc.autoadrizante import (DIR, MastBuoyancy, gz_curve_rig, recovery_limit,
                                rig_elements, solve_waterline_rig, variant_weights)
from calc import scantlings
from calc.geometry import HullGeometry, rotate
from calc.params import G, Design
from calc.stability import solve_waterline

HEEL_GRID = np.arange(0.0, 181.0, 2.0)
STATIONS = 31
FPS = 12
T_END = 22.0
START_DEG = 150.0


def build_boat(with_float: bool, label: str) -> dict:
    d = Design()
    d.hull.n_stations = STATIONS
    mb = MastBuoyancy() if with_float else None

    d_full = Design()
    g_full = HullGeometry(d_full.hull, d_full.cockpit)
    m_ldc = d_full.envelope.disp_max + d_full.crew_mass_each * d_full.cockpit.seats
    sc = scantlings.evaluate(d_full, m_ldc)
    wb = variant_weights(d_full, MastBuoyancy(), sc, g_full.shell_area(),
                         g_full.deck_area())
    d.ballast.keel_mass = wb.ballast_available
    mass, vcg = wb.disp_light, wb.vcg_light

    geom = HullGeometry(d.hull, d.cockpit)
    curve = gz_curve_rig(geom, d, mb, mass, vcg, flooded=True, heel=HEEL_GRID,
                         label=label)

    gz = np.asarray(curve.gz, dtype=float)
    finite = np.isfinite(gz)
    gz[~finite] = np.interp(np.flatnonzero(~finite), np.flatnonzero(finite),
                            gz[finite])
    phi_ext = np.concatenate([-HEEL_GRID[::-1][:-1], HEEL_GRID,
                              360.0 - HEEL_GRID[::-1][:-1]])
    gz_ext = np.concatenate([-gz[::-1][:-1], gz, -gz[::-1][:-1]])
    f_gz = interp1d(phi_ext, gz_ext, bounds_error=False,
                    fill_value=(gz_ext[0], gz_ext[-1]))

    keel_vol = geom.keel_appendage_volume(d.ballast.keel_mass)
    els = rig_elements(mb) if mb else None
    zwl = []
    for a in HEEL_GRID:
        if els:
            z = solve_waterline_rig(geom, mass / 1025.0, float(a), True,
                                    keel_vol, els)
        else:
            z = solve_waterline(geom, mass / 1025.0, float(a), flooded=True,
                                keel_volume=keel_vol)
        zwl.append(z or 0.0)
    f_zwl = interp1d(HEEL_GRID, np.array(zwl), bounds_error=False,
                     fill_value=(zwl[0], zwl[-1]))

    i_mid = int(np.argmax(geom.y_sheer))
    return {
        "label": label, "mass": mass, "vcg": vcg, "with_float": with_float,
        "f_gz": f_gz, "f_zwl": f_zwl, "gz": gz,
        "section": geom._sections[i_mid], "bench": geom._voids[i_mid],
        "self_rights_from_start": float(f_gz(START_DEG)) > 0.0,
        "recovery_limit": recovery_limit(curve), "avs": curve.avs,
    }


def simulate(boat: dict) -> tuple[np.ndarray, np.ndarray]:
    m = boat["mass"]
    b = 2.35
    inertia = 1.6 * m * (0.40 * b) ** 2
    if boat["with_float"]:
        # el flotador y el aparejo lejos del eje suben inercia y amortiguan
        inertia *= 1.8
    c_damp = 0.9 * inertia

    dt = 1.0 / (FPS * 8)
    n = int(T_END / dt) + 1
    phi = np.zeros(n)
    omega = np.zeros(n)
    phi[0] = np.radians(START_DEG)
    for k in range(n - 1):
        gz_val = float(boat["f_gz"](np.degrees(phi[k])))
        alpha = (-m * G * gz_val - c_damp * omega[k]) / inertia
        omega[k + 1] = omega[k] + alpha * dt
        phi[k + 1] = phi[k] + omega[k + 1] * dt
    t = np.linspace(0.0, T_END, n)
    return t, np.degrees(phi)


MAST_HEEL_Z = 0.86
MAST_HEAD_Z = 9.46
FLOAT_Z = 9.55
LIM = 11.0


def _draw_boat(ax, boat: dict, heel_deg: float) -> None:
    ax.clear()
    z_wl = float(boat["f_zwl"](min(abs(heel_deg), 180.0)))
    sec = rotate(boat["section"], heel_deg)

    ax.fill_between([-LIM, LIM], -LIM, z_wl, color="#bcd6e8", zorder=0)
    ax.axhline(z_wl, color="#5a8fb5", lw=1.0, zorder=1)

    closed = np.vstack([sec, sec[:1]])
    ax.fill(closed[:, 0], closed[:, 1], color="#d7e1e8", ec="#3c5a6e",
            lw=1.4, zorder=3)
    if len(boat["bench"]) >= 3:
        bt = rotate(boat["bench"], heel_deg)
        ax.fill(np.append(bt[:, 0], bt[0, 0]), np.append(bt[:, 1], bt[0, 1]),
                color="#508cbe", alpha=0.35, zorder=4)

    phi = np.radians(heel_deg)
    c, s = np.cos(phi), np.sin(phi)

    def rot(y, z):
        return y * c + z * s, -y * s + z * c

    # quilla (abajo y trabada)
    ya, za = rot(0.0, 0.02)
    yb, zb = rot(0.0, -1.06)
    ax.plot([ya, yb], [za, zb], color="#2e2e38", lw=2.6, zorder=2)
    ax.plot(yb, zb, "o", color="#2e2e38", ms=7, zorder=2)

    # mastil
    y0, z0 = rot(0.0, MAST_HEEL_Z)
    y1, z1 = rot(0.0, MAST_HEAD_Z)
    col_mast = "#8a3324" if boat["with_float"] else "#3c3c3c"
    ax.plot([y0, y1], [z0, z1], color=col_mast, lw=1.8, zorder=2)

    # flotador de tope
    if boat["with_float"]:
        yf, zf = rot(0.0, FLOAT_Z)
        ax.add_patch(Ellipse((yf, zf), 1.0, 0.44, angle=-heel_deg,
                             fc="#e8622d", ec="#8a3324", lw=1.2, zorder=5))

    # G
    yg, zg = rot(0.0, boat["vcg"])
    ax.plot(yg, zg, "o", color="#cc3333", ms=5, zorder=6)

    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM * 0.55)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> None:
    os.makedirs(DIR, exist_ok=True)

    print("building bare (sin flotador)...")
    bare = build_boat(False, "SIN paquete de tope — queda tortuga")
    print(f"  bare: AVS {bare['avs']:.0f}, GZ(150) "
          f"{float(bare['f_gz'](START_DEG)):+.3f} m")
    print("building variante (mastil sellado + 60 L)...")
    vari = build_boat(True, "Variante auto-adrizante — vuelve sola")
    print(f"  variante: recupera hasta {vari['recovery_limit']:.0f} deg, GZ(150) "
          f"{float(vari['f_gz'](START_DEG)):+.3f} m")

    print("simulating...")
    t_b, phi_b = simulate(bare)
    t_v, phi_v = simulate(vari)
    print(f"  final: bare {phi_b[-1]:.0f} deg, variante {phi_v[-1]:.0f} deg")

    frames = int(T_END * FPS)
    idx = np.linspace(0, len(t_b) - 1, frames).astype(int)

    fig = plt.figure(figsize=(11, 7.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.5, 1.0], hspace=0.18)
    ax_b = fig.add_subplot(gs[0, 0])
    ax_v = fig.add_subplot(gs[0, 1])
    ax_g = fig.add_subplot(gs[1, :])

    ax_g.plot(HEEL_GRID, bare["gz"], color="#cc6677", lw=1.8,
              label="sin flotador — GZ negativo desde 110°: sigue hasta la tortuga")
    ax_g.plot(HEEL_GRID, vari["gz"], color="#117733", lw=1.8,
              label=f"con mastil sellado + 60 L — GZ positivo hasta "
                    f"{vari['recovery_limit']:.0f}°: vuelve sola")
    ax_g.axhline(0, color="#333", lw=0.8)
    ax_g.axvline(START_DEG, color="#888", lw=0.9, ls=":")
    ax_g.text(START_DEG + 2, 0.8, "soltado a 150°", fontsize=8, color="#555")
    ax_g.set_xlim(0, 180)
    ax_g.set_xlabel("escora (°)")
    ax_g.set_ylabel("GZ (m)")
    ax_g.legend(frameon=False, fontsize=8, loc="lower left")
    ax_g.grid(alpha=0.25)
    dot_b, = ax_g.plot([], [], "o", color="#cc6677", ms=8, zorder=5)
    dot_v, = ax_g.plot([], [], "o", color="#117733", ms=8, zorder=5)

    def fold(h: float) -> float:
        h = abs(h) % 360.0
        return h if h <= 180.0 else 360.0 - h

    def update(f: int):
        k = idx[f]
        hb, hv = float(phi_b[k]), float(phi_v[k])
        _draw_boat(ax_b, bare, hb)
        _draw_boat(ax_v, vari, hv)
        ax_b.set_title(f"{bare['label']}\nescora {fold(hb):5.0f}°  ·  t={t_b[k]:4.1f} s",
                       fontsize=10, color="#8b3a3a")
        ax_v.set_title(f"{vari['label']}\nescora {fold(hv):5.0f}°  ·  t={t_v[k]:4.1f} s",
                       fontsize=10, color="#1e5e3a")
        dot_b.set_data([fold(hb)], [float(bare["f_gz"](fold(hb)))])
        dot_v.set_data([fold(hv)], [float(vari["f_gz"](fold(hv)))])
        return []

    fig.suptitle("El mismo casco de 2.35 m soltado tumbado a 150°: sin el paquete de tope "
                 "sigue a la tortuga; con mastil sellado + 60 L vuelve solo",
                 fontsize=11)

    # frames fijos para la presentacion
    for name, tt in (("anim_inicio.png", 0.2), ("anim_medio.png", 7.4),
                     ("anim_final.png", T_END - 0.1)):
        f = min(int(tt * FPS), frames - 1)
        update(f)
        fig.savefig(os.path.join(DIR, name), dpi=110)
        print("escrito:", os.path.join(DIR, name))

    print(f"rendering {frames} frames...")
    anim = FuncAnimation(fig, update, frames=frames, blit=False)
    path = os.path.join(DIR, "selfrighting.gif")
    anim.save(path, writer=PillowWriter(fps=FPS))
    plt.close(fig)
    print(f"written: {path}")


if __name__ == "__main__":
    main()
