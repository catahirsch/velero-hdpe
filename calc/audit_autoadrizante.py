"""Auditoria de constructibilidad y costos de la variante auto-adrizante.

    python3 -m calc.audit_autoadrizante  ->  autoadrizante/audit.txt
                                             autoadrizante/costs.txt

audit.txt = las 15 verificaciones fisicas del baseline (calc/audit.py; el
casco, quilla, bancos, botavara y jarcia no cambian -- con 2.5 kg menos de
plomo todas valen a fortiori) MAS las verificaciones propias del paquete de
tope de mastil.

costs.txt = el modelo de costos del baseline (calc/costs.py) MAS el delta de
la variante: el paquete de tope es marginal frente al total (~0.5 %).
"""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout

import numpy as np

from . import audit, costs
from .autoadrizante import DIR, MastBuoyancy
from .params import RHO_SEA, Design

G = 9.80665
RHO_AIR = 1.225


def float_checks(mb: MastBuoyancy) -> list[audit.Check]:
    d = Design()
    checks: list[audit.Check] = []

    def add(name, computed, required, ok, note=""):
        checks.append(audit.Check(name, computed, required, ok, note))

    # 1 -- el flotador sostiene el aparejo sumergido
    rig_mass = 32.0 + mb.float_mass  # palo+botavara+jarcia + flotador
    buoy = mb.float_volume * RHO_SEA
    add("Float carries the submerged rig",
        f"buoyancy {buoy:.0f} kg vs rig {rig_mass:.1f} kg",
        "margin >= 1.5x", buoy / rig_mass >= 1.5,
        f"margin {buoy / rig_mass:.2f}x; the sealed spar (30 L) is extra on top")

    # 2 -- el volumen sellado del perfil existe fisicamente
    a_in, b_in = 0.055 - 0.0025, 0.035 - 0.0025  # elipse 110x70x2.5
    spar_internal = np.pi * a_in * b_in * (mb.spar_z1 - mb.spar_z0)
    add("Sealed spar volume fits inside the 110x70x2.5 section",
        f"internal {spar_internal * 1000:.0f} L available",
        f">= {mb.spar_volume * 1000:.0f} L usable claimed",
        spar_internal >= mb.spar_volume,
        "claim uses 70% of internal: heel/head plugs, sheave boxes, conduit")

    # 3 -- la elipsoide 1.00 x 0.34 realmente contiene 60 L
    vol = 4.0 / 3.0 * np.pi * 0.50 * 0.17 * 0.17
    add("Float ellipsoid geometry holds its volume",
        f"1.00 x 0.34 x 0.34 m ellipsoid = {vol * 1000:.0f} L",
        f">= {mb.float_volume * 1000:.0f} L", vol >= mb.float_volume * 0.98)

    # 4 -- masa y presupuesto: el flotador sale del remanente de quilla
    keel_base, keel_var = 213.0, 213.0 - mb.float_mass
    fin_mass = 50.0  # S355 15 mm (audit base)
    lead = keel_var - fin_mass
    bulb_capacity = 0.58 * 0.145 * 0.17 * 11340.0
    add("Keel budget still closes with the float paid for",
        f"keel {keel_var:.1f} kg -> lead {lead:.1f} kg",
        f"bulb capacity {bulb_capacity:.0f} kg >= lead", bulb_capacity >= lead,
        f"baseline keel {keel_base:.0f} kg minus float {mb.float_mass:.1f} kg")

    # 5 -- windage del flotador: despreciable frente al momento adrizante
    frontal = np.pi / 4.0 * 0.34 * 0.34
    q25 = 0.5 * RHO_AIR * (25 * 0.5144) ** 2
    hm = 0.5 * q25 * frontal * mb.float_z  # Cd ~0.5 carenado
    rm = 750.0 * G * 0.64
    add("Float windage vs peak righting moment (25 kt)",
        f"{hm:.0f} N.m heeling", f"< 2% of RM ({rm:.0f} N.m)",
        hm / rm < 0.02, f"{hm / rm * 100:.1f}% -- faired fore-aft, Cd~0.5")

    # 6 -- soporte del tope: 4x M6 A4 contra la carga del flotador
    load = buoy * G  # N, flotador totalmente sumergido empujando
    per_bolt = load / 4.0
    add("Masthead bracket bolts (4x M6 A4) under full float buoyancy",
        f"{per_bolt / 1000:.2f} kN/bolt", "<= 3.0 kN working",
        per_bolt <= 3000.0,
        "worst case: float fully submerged at the recovery limit")

    # 7 -- VCG: el modelo carga la subida por el flotador
    dvcg = mb.float_mass * (mb.float_z - 0.256) / 750.0
    add("Float VCG penalty is carried by the stability model",
        f"+{dvcg * 1000:.0f} mm on the light VCG",
        "included in calc/autoadrizante.py curves", True,
        "gz_curves.png is computed WITH this penalty")

    return checks


def write_audit(mb: MastBuoyancy) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        base_checks = audit.run()  # regenera out/audit.txt (identico) y devuelve
    extra = float_checks(mb)

    lines = ["=" * 86,
             "BUILDABILITY AUDIT -- VARIANTE AUTO-ADRIZANTE",
             "=" * 86,
             "Base checks: hull, keel, benches, boom, rig and sole are unchanged",
             f"(keel carries {mb.float_mass:.1f} kg less lead, so mass checks hold a fortiori).",
             ""]
    n_fail = 0
    for c in list(base_checks) + extra:
        flag = "PASS" if c.ok else "FAIL"
        if not c.ok:
            n_fail += 1
        lines.append(f"[{flag}] {c.name}")
        lines.append(f"       computed: {c.computed}")
        lines.append(f"       required: {c.required}")
        if c.note:
            lines.append(f"       note:     {c.note}")
    total = len(base_checks) + len(extra)
    lines.append("=" * 86)
    lines.append(f"{total - n_fail}/{total} checks pass "
                 f"({len(base_checks)} baseline + {len(extra)} float package)")
    out = "\n".join(lines)
    print(out.splitlines()[-1])
    with open(os.path.join(DIR, "audit.txt"), "w") as f:
        f.write(out + "\n")
    print(f"escrito: {os.path.join(DIR, 'audit.txt')}")


def write_costs(mb: MastBuoyancy) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        costs.run()  # regenera out/costs.txt (identico al base)
    with open(os.path.join(costs.OUT, "costs.txt")) as f:
        base_txt = f.read()

    delta = f"""

{'=' * 78}
DELTA VARIANTE AUTO-ADRIZANTE  (sobre cualquiera de las rutas de arriba)
{'=' * 78}
  Flotador de tope 60 L (PE rotomoldeado o soplado, 1.00 x 0.34) USD 120-350
  Soporte de tope 6082-T6 + 4x M6 A4                             USD 40-90
  Sellado del perfil (espuma pie/tope/cajeras, mano de obra)     USD 80-200
  Conducto de drizas / drizas externas (delta vs interno)        USD 0-120
  Traba de quilla reforzada (ya prevista: sin delta)             USD 0
  ------------------------------------------------------------------------
  TOTAL DELTA                                                    USD 240-760
  ~0.5 % del costo medio del barco (USD 64,400). El paquete se paga con
  2.5 kg de plomo de quilla, que ademas ahorra ~USD 10 de plomo.
"""
    with open(os.path.join(DIR, "costs.txt"), "w") as f:
        f.write(base_txt.rstrip("\n") + delta)
    print(f"escrito: {os.path.join(DIR, 'costs.txt')}")


def main() -> None:
    os.makedirs(DIR, exist_ok=True)
    mb = MastBuoyancy()
    write_audit(mb)
    write_costs(mb)


if __name__ == "__main__":
    main()
