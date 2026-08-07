"""Animation: why one hull self-rights and the other stays turtled.

    python3 -m geom.animate_righting        # writes out/selfrighting.gif

Two boats are released fully inverted (heel 178 deg) and left to the physics:

  LEFT  -- baseline as designed: 2.35 m beam, 213 kg keel. GZ is negative
           approaching 180, so the inverted position is a stable equilibrium:
           the boat settles upside down and stays.
  RIGHT -- self-righting variant: 1.80 m beam, 361 kg keel. GZ is positive at
           every angle, so from 178 deg the keel wins, the boat rolls all the
           way back and oscillates to upright.

The motion integrates the 1-DOF roll equation on the REAL righting curves from
calc/stability.py (light ship, cockpit flooded -- the honest post-capsize
condition). Roll inertia and damping are didactic estimates: the trajectory
timing is approximate, the equilibria and the verdict are exact.
"""

from __future__ import annotations

import copy
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from scipy.interpolate import interp1d

from calc.geometry import HullGeometry, rotate
from calc.params import G, Design
from calc.stability import gz_curve, solve_waterline
from calc.trade import _fixed_mass

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

HEEL_GRID = np.arange(0.0, 181.0, 2.0)
STATIONS = 31
FPS = 12
T_END = 22.0  # s of simulated (and shown) time
START_DEG = 178.0


def build_boat(beam: float, keel: float, cockpit_half_width: float,
               label: str) -> dict:
    d = Design()
    d.hull.n_stations = STATIONS
    d.hull.beam_sheer = beam
    d.cockpit.half_width = cockpit_half_width
    d.ballast.keel_mass = keel

    # Mass and VCG from the weight model itself -- no hand-typed numbers.
    fixed_mass, fixed_moment, _, _ = _fixed_mass(d)
    mass = fixed_mass + keel
    vcg = (fixed_moment + keel * -d.ballast.keel_vcg_below_bl) / mass

    geom = HullGeometry(d.hull, d.cockpit)
    curve = gz_curve(geom, d, mass, vcg, flooded=True, heel=HEEL_GRID, label=label)

    # Fill non-floating gaps by extending the last finite value (rare, edges).
    gz = np.asarray(curve.gz, dtype=float)
    finite = np.isfinite(gz)
    gz[~finite] = np.interp(np.flatnonzero(~finite), np.flatnonzero(finite), gz[finite])

    # Odd extension to negative heel (GZ(-phi) = -GZ(phi)) so the boat can
    # oscillate through upright, and mirror symmetry past 180
    # (GZ(360-phi) = -GZ(phi)) so it can oscillate about fully inverted.
    phi_ext = np.concatenate([-HEEL_GRID[::-1][:-1], HEEL_GRID,
                              360.0 - HEEL_GRID[::-1][:-1]])
    gz_ext = np.concatenate([-gz[::-1][:-1], gz, -gz[::-1][:-1]])
    f_gz = interp1d(phi_ext, gz_ext, bounds_error=False, fill_value=(gz_ext[0], gz_ext[-1]))

    # Waterline height per heel, for drawing sinkage correctly.
    keel_vol = geom.keel_appendage_volume(keel)
    zwl = np.array([
        solve_waterline(geom, mass / 1025.0, float(a), flooded=True, keel_volume=keel_vol)
        or 0.0
        for a in HEEL_GRID
    ])
    f_zwl = interp1d(HEEL_GRID, zwl, bounds_error=False, fill_value=(zwl[0], zwl[-1]))

    # Midship section polygon for drawing + keel fin line.
    i_mid = int(np.argmax(geom.y_sheer))
    section = geom._sections[i_mid]
    bench = geom._voids[i_mid]

    return {
        "label": label, "mass": mass, "vcg": vcg, "beam": beam, "keel": keel,
        "f_gz": f_gz, "f_zwl": f_zwl, "section": section, "bench": bench,
        "gz": gz, "keel_tip": -1.06 if beam > 2.0 else -1.06,
        "self_rights": bool(curve.self_righting), "avs": curve.avs,
    }


def simulate(boat: dict) -> tuple[np.ndarray, np.ndarray]:
    """Integrate I*phi'' = -m*g*GZ(phi) - c*phi' from the inverted release."""
    m = boat["mass"]
    b = boat["beam"]
    inertia = 1.6 * m * (0.40 * b) ** 2  # roll inertia + added mass [didactic]
    c_damp = 0.9 * inertia  # heavy damping: water everywhere after a capsize

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


def _draw_boat(ax, boat: dict, heel_deg: float) -> None:
    ax.clear()
    sec = rotate(boat["section"], heel_deg)
    z_wl = float(boat["f_zwl"](abs(heel_deg)))

    # water
    ax.fill_between([-2.6, 2.6], -2.6, z_wl, color="#bcd6e8", zorder=0)
    ax.axhline(z_wl, color="#5a8fb5", lw=1.0, zorder=1)

    # hull section
    closed = np.vstack([sec, sec[:1]])
    ax.fill(closed[:, 0], closed[:, 1], color="#d7e1e8", ec="#3c5a6e", lw=1.6, zorder=3)

    # bench tanks
    if len(boat["bench"]) >= 3:
        bt = rotate(boat["bench"], heel_deg)
        ax.fill(np.append(bt[:, 0], bt[0, 0]), np.append(bt[:, 1], bt[0, 1]),
                color="#508cbe", alpha=0.35, zorder=4)

    # keel fin + bulb (drawn from body-frame keel line)
    phi = np.radians(heel_deg)
    c, s = np.cos(phi), np.sin(phi)
    for y0, z0, y1, z1, lw in [(0.0, 0.02, 0.0, boat["keel_tip"], 3.0)]:
        ya, za = y0 * c + z0 * s, -y0 * s + z0 * c
        yb, zb = y1 * c + z1 * s, -y1 * s + z1 * c
        ax.plot([ya, yb], [za, zb], color="#2e2e38", lw=lw, zorder=2)
        ax.plot(yb, zb, "o", color="#2e2e38", ms=9, zorder=2)

    # mast
    zm = 0.80 + 8.6
    ym, zmr = zm * s, zm * c  # rotate (0, zm)
    y0m, z0m = 0.80 * s, 0.80 * c
    ax.plot([y0m, ym], [z0m, zmr], color="#3c3c3c", lw=1.4, zorder=2)

    # G and B markers: G at (0, vcg) body frame
    yg, zg = boat["vcg"] * s, boat["vcg"] * c
    ax.plot(yg, zg, "o", color="#cc3333", ms=6, zorder=5)
    ax.annotate("G", (yg, zg), textcoords="offset points", xytext=(6, 4),
                fontsize=9, color="#cc3333")

    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-2.6, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    print("building baseline (2.35 m)...")
    base = build_boat(beam=2.35, keel=213.0, cockpit_half_width=0.86,
                      label="Base 2.35 m / 213 kg — NO auto-adrizante")
    print("building variant (1.80 m)...")
    vari = build_boat(beam=1.80, keel=500.0, cockpit_half_width=0.86,
                      label="Variante 1.80 m / 500 kg — auto-adrizante")
    print(f"  base self-rights: {base['self_rights']} (AVS {base['avs']:.0f})")
    print(f"  variant self-rights: {vari['self_rights']} (AVS {vari['avs']:.0f})")

    print("simulating...")
    t_b, phi_b = simulate(base)
    t_v, phi_v = simulate(vari)

    frames = int(T_END * FPS)
    idx = np.linspace(0, len(t_b) - 1, frames).astype(int)

    fig = plt.figure(figsize=(11, 6.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.6, 1.0], hspace=0.16)
    ax_b = fig.add_subplot(gs[0, 0])
    ax_v = fig.add_subplot(gs[0, 1])
    ax_g = fig.add_subplot(gs[1, :])

    # static GZ curves below
    ax_g.plot(HEEL_GRID, base["gz"], color="#cc6677", lw=1.8,
              label="Base 2.35 m / 213 kg — GZ negativo cerca de 180°: equilibrio invertido")
    ax_g.plot(HEEL_GRID, vari["gz"], color="#117733", lw=1.8,
              label="Variante 1.80 m / 500 kg — GZ positivo hasta 180°: siempre vuelve")
    ax_g.axhline(0, color="#333", lw=0.8)
    ax_g.set_xlim(0, 180)
    ax_g.set_xlabel("escora (°)")
    ax_g.set_ylabel("GZ (m)")
    ax_g.legend(frameon=False, fontsize=8, loc="lower left")
    ax_g.grid(alpha=0.25)
    dot_b, = ax_g.plot([], [], "o", color="#cc6677", ms=8, zorder=5)
    dot_v, = ax_g.plot([], [], "o", color="#117733", ms=8, zorder=5)

    def update(f: int):
        k = idx[f]
        hb, hv = float(phi_b[k]), float(phi_v[k])
        _draw_boat(ax_b, base, hb)
        _draw_boat(ax_v, vari, hv)
        ax_b.set_title(f"{base['label']}\nescora {hb:5.0f}°  ·  t={t_b[k]:4.1f} s",
                       fontsize=10, color="#8b3a3a")
        ax_v.set_title(f"{vari['label']}\nescora {hv:5.0f}°  ·  t={t_v[k]:4.1f} s",
                       fontsize=10, color="#1e5e3a")
        dot_b.set_data([abs(hb) if abs(hb) <= 180 else 360 - abs(hb)],
                       [float(base['f_gz'](abs(hb)))])
        dot_v.set_data([abs(hv) if abs(hv) <= 180 else 360 - abs(hv)],
                       [float(vari['f_gz'](abs(hv)))])
        return []

    fig.suptitle("Soltados invertidos (178°): la quilla de la variante angosta gana; "
                 "la manga del base lo mantiene tortuga", fontsize=11)

    print(f"rendering {frames} frames...")
    anim = FuncAnimation(fig, update, frames=frames, blit=False)
    path = os.path.join(OUT, "selfrighting.gif")
    anim.save(path, writer=PillowWriter(fps=FPS))
    plt.close(fig)
    print(f"written: {path}")


if __name__ == "__main__":
    main()
