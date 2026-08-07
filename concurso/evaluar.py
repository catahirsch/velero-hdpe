"""Evaluador oficial del concurso.

    python3 -m concurso.evaluar concurso/entregas/<equipo>.json

Convierte el JSON del equipo en un barco real sobre la MISMA cadena de calculo
del proyecto (hidrostatica exacta por estaciones, curvas GZ 0-180 con cockpit
inundado, modelo de pesos con el plomo como remanente del tope de 750 kg) y
puntua los rubros automaticos. Escribe:

    concurso/resultados/<equipo>/resultado.json   tarjeta completa
    concurso/resultados/<equipo>/gz.png           curvas del diseno

Despues correr `python3 -m concurso.leaderboard` para regenerar el ranking.
Resolucion: 31 estaciones / 5 grados (la misma del estudio de opciones; las
cifras finas difieren <0.2 grados).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

from calc import scantlings
from calc.autoadrizante import MastBuoyancy, gz_curve_rig, recovery_limit, variant_weights
from calc.geometry import HullGeometry
from calc.params import RHO_SEA, Design
from calc.stability import downflooding_angle, upright_hydrostatics

BASE = os.path.dirname(os.path.abspath(__file__))
STATIONS = 31
HEEL = np.arange(0.0, 181.0, 5.0)

RANGOS = {
    "beam_sheer": (1.70, 2.50), "sole_z": (0.30, 0.50),
    "bench_inner_y": (0.35, 0.60), "bench_top_z": (0.60, 0.90),
    "keel_draft": (0.80, 1.30), "keel_vcg_below_bl": (0.50, 1.05),
    "mast_height": (7.0, 10.0), "main_area": (8.0, 16.0),
    "jib_area": (4.0, 10.0), "float_volume_l": (0.0, 120.0),
    "spar_volume_l": (0.0, 40.0), "water_ballast_each_kg": (0.0, 250.0),
    "water_ballast_z": (0.20, 0.60), "battery_z": (0.15, 0.60),
}


def validar(p: dict) -> list[str]:
    errores = []
    for k, (lo, hi) in RANGOS.items():
        if k not in p:
            errores.append(f"falta el parametro '{k}'")
        elif not (lo <= float(p[k]) <= hi):
            errores.append(f"'{k}' = {p[k]} fuera de rango [{lo}, {hi}]")
    if not errores and float(p["keel_vcg_below_bl"]) > float(p["keel_draft"]) - 0.20:
        errores.append("keel_vcg_below_bl > keel_draft - 0.20: el bulbo no cabe")
    return errores


def construir(p: dict) -> tuple[Design, MastBuoyancy]:
    d = Design()
    d.hull.n_stations = STATIONS
    d.hull.beam_sheer = float(p["beam_sheer"])
    d.cockpit.sole_z = float(p["sole_z"])
    d.cockpit.bench_inner_y = float(p["bench_inner_y"])
    d.cockpit.bench_top_z = float(p["bench_top_z"])
    d.ballast.keel_draft = float(p["keel_draft"])
    d.ballast.keel_vcg_below_bl = float(p["keel_vcg_below_bl"])
    d.ballast.water_ballast_each = float(p["water_ballast_each_kg"])
    d.ballast.water_ballast_z = float(p["water_ballast_z"])
    d.rig.mast_height = float(p["mast_height"])
    d.rig.main_area = float(p["main_area"])
    d.rig.jib_area = float(p["jib_area"])
    d.propulsion.battery_z = float(p["battery_z"])

    fv = float(p["float_volume_l"]) / 1000.0
    sv = float(p["spar_volume_l"]) / 1000.0
    z1 = 0.86 + d.rig.mast_height
    mb = MastBuoyancy(
        float_volume=fv,
        float_z=z1 + 0.09,
        float_mass=max(0.5, 2.5 * fv / 0.060) if fv > 0 else 0.3,
        spar_volume=sv, spar_z0=0.86, spar_z1=z1,
    )
    return d, mb


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def evaluar(path: str) -> dict:
    with open(path) as f:
        entrega = json.load(f)
    equipo = entrega.get("equipo", "sin-nombre").strip().lower().replace(" ", "-")
    p = entrega["parametros"]

    errores = validar(p)
    if errores:
        return {"equipo": equipo, "valido": False, "errores": errores}

    d, mb = construir(p)
    geom = HullGeometry(d.hull, d.cockpit)
    m_ldc = d.envelope.disp_max + d.crew_mass_each * d.cockpit.seats
    sc = scantlings.evaluate(d, m_ldc)
    wb = variant_weights(d, mb, sc, geom.shell_area(), geom.deck_area())
    d.ballast.keel_mass = max(wb.ballast_available, 0.0)

    # --- sobre dimensional --------------------------------------------------
    water_l = d.ballast.water_ballast_total / (RHO_SEA / 1000.0)
    violaciones = d.envelope.check(
        loa=d.hull.loa, beam=geom.max_beam, disp=wb.disp_light,
        sail_area=d.rig.sail_area_upwind, water_ballast_l=water_l,
        draft=d.ballast.keel_draft)
    if wb.ballast_available <= 0:
        violaciones.append("el peso fijo excede 750 kg: no queda plomo de quilla")

    # --- curvas -------------------------------------------------------------
    mb_o = mb if (mb.float_volume > 0 or mb.spar_volume > 0) else None
    c_light = gz_curve_rig(geom, d, mb_o, wb.disp_light, wb.vcg_light,
                           flooded=True, heel=HEEL, label="rosca inundado")
    c_bare = gz_curve_rig(geom, d, None, wb.disp_light, wb.vcg_light,
                          flooded=True, heel=HEEL, label="sin aparejo")
    rec = recovery_limit(c_light)
    hs_loaded = upright_hydrostatics(geom, d, wb.disp_loaded)
    fb_sole = (d.cockpit.sole_z - hs_loaded.z_wl) * 1000 if hs_loaded else -999
    # angulo de inundacion en la condicion honesta: plena carga
    df = downflooding_angle(geom, d, wb.disp_loaded) or 0.0
    sad = d.rig.sail_area_upwind / (wb.disp_loaded / RHO_SEA) ** (2.0 / 3.0)

    # --- puntaje ------------------------------------------------------------
    pts = {}
    pts["sobre (20)"] = round(max(0.0, 20.0 - 10.0 * len(violaciones)), 1)
    pts["auto-adrizado (35)"] = round(_clamp((rec - 110.0) / 70.0, 0, 1) * 35, 1)
    pts["autoachique (10)"] = round(_clamp(fb_sole / 80.0, 0, 1) * 10, 1)
    pts["inundacion (10)"] = round(_clamp((df - 25.0) / 20.0, 0, 1) * 10, 1)
    if 15.0 <= sad <= 18.0:
        s_sad = 1.0
    else:
        s_sad = _clamp(1.0 - abs(sad - (15.0 if sad < 15 else 18.0)) / 6.0, 0, 1)
    pts["porte de vela (15)"] = round(s_sad * 15, 1)
    pts["lastre (10)"] = round(_clamp((wb.ballast_ratio - 0.10) / 0.20, 0, 1) * 10, 1)
    total = round(sum(pts.values()), 1)

    res = {
        "equipo": equipo,
        "valido": True,
        "categoria": entrega.get("categoria", ""),
        "comentario": entrega.get("comentario", ""),
        "parametros": p,
        "metricas": {
            "desplazamiento_rosca_kg": round(wb.disp_light, 1),
            "plomo_quilla_kg": round(wb.ballast_available, 1),
            "relacion_lastre_pct": round(wb.ballast_ratio * 100, 1),
            "vcg_rosca_m": round(wb.vcg_light, 3),
            "limite_recuperacion_deg": round(rec, 1),
            "tortuga_residual_J": round(c_light.negative_area * wb.disp_light * 9.80665, 0),
            "gz_max_m": round(c_light.gz_max, 3),
            "francobordo_piso_carga_mm": round(fb_sole, 0),
            "angulo_inundacion_deg": round(df, 1),
            "sa_d_carga": round(sad, 2),
            "violaciones_sobre": violaciones,
        },
        "puntaje": pts,
        "total_auto": total,
    }

    outdir = os.path.join(BASE, "resultados", equipo)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "resultado.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    _plot(outdir, equipo, c_light, c_bare, rec, total)
    return res


def _plot(outdir, equipo, c_rig, c_bare, rec, total) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(c_bare.heel, c_bare.gz, color="#cc6677", ls="--", lw=1.5,
            label="casco desnudo")
    ax.plot(c_rig.heel, c_rig.gz, color="#117733", lw=2.0,
            label="con aparejo sellado")
    ax.axhline(0, color="#333", lw=0.8)
    ax.axvline(rec, color="#117733", ls="-.", lw=1.0)
    ax.set_xlim(0, 180)
    ax.set_xlabel("escora (°)")
    ax.set_ylabel("GZ (m)")
    ax.set_title(f"{equipo} — recupera hasta {rec:.0f}° · {total} pts automaticos")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "gz.png"), dpi=130)
    plt.close(fig)


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    res = evaluar(sys.argv[1])
    if not res["valido"]:
        print(f"ENTREGA INVALIDA ({res['equipo']}):")
        for e in res["errores"]:
            print(f"  - {e}")
        sys.exit(2)
    print(f"\n=== {res['equipo']} — {res['total_auto']} / 100 pts automaticos ===")
    for k, v in res["puntaje"].items():
        print(f"  {k:<22} {v}")
    print("\nmetricas:")
    for k, v in res["metricas"].items():
        print(f"  {k:<28} {v}")
    print(f"\ntarjeta: concurso/resultados/{res['equipo']}/resultado.json (+ gz.png)")


if __name__ == "__main__":
    main()
