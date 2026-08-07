"""Cost model -- building in Chile.

    python3 -m calc.costs          # writes out/costs.txt

Every unit price is a (low, mid, high) band in USD, marked with its basis:

    [QUOTE]  needs a real Chilean quote -- band is the expected quote range
    [MKT]    international market price, stable enough to plan with
    [EST]    engineering estimate

The point of the script is that the client replaces bands with quotes and
re-runs; the arithmetic, tax treatment and totals stay consistent. Bands are
2026 planning numbers, not offers.

Chilean treatment:
    IVA 19 % applies to everything bought in Chile (and to imports, on CIF+duty).
    Duty: 6 % general, but 0 % under Chile's FTAs (EU, US, China) -- most marine
    gear enters duty-free; the model charges freight+insurance instead.
    FX assumption printed in the header; totals are given in USD and CLP.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

CLP_PER_USD = 950.0  # [EST] mid-2026 planning rate -- update at purchase time
IVA = 0.19
FREIGHT_IMPORT = 0.15  # [EST] CIF freight+insurance on imported gear, fraction


@dataclass
class Line:
    item: str
    qty: float
    unit: str
    usd_low: float
    usd_mid: float
    usd_high: float
    basis: str  # QUOTE / MKT / EST
    imported: bool  # True -> freight applied; IVA applies to all
    note: str = ""

    def totals(self) -> tuple[float, float, float]:
        f = (1.0 + FREIGHT_IMPORT) if self.imported else 1.0
        return (
            self.qty * self.usd_low * f * (1 + IVA),
            self.qty * self.usd_mid * f * (1 + IVA),
            self.qty * self.usd_high * f * (1 + IVA),
        )


# ---------------------------------------------------------------------------
# Quantities come from docs/04-build-spec.md
# ---------------------------------------------------------------------------

# Route A: welded PE500 sheet, one-off prototype in a Chilean shop.
# PE mass: hull 17.41 m2 x 12 mm + deck/cockpit 15.14 m2 x 10 mm + benches,
# sole, keel case, stiffeners ~60 kg = ~420 kg net, +15 % offcut waste.
SHEET_ROUTE = [
    Line("PE500 sheet (net 420 kg + 15% waste)", 483, "kg", 3.5, 4.5, 6.0, "QUOTE", False,
         "Plastigen / Polymerland / Plastisan / Siplas -- quote cut-to-size"),
    Line("HDPE welding rod 4-5 mm", 16, "kg", 8.0, 10.0, 13.0, "QUOTE", False, ""),
    Line("PE consumables (tips, tacks, test coupons)", 1, "lot", 150, 250, 400, "EST", False, ""),
]

# Route B: rotomoulded double-skin shell. The honest problem is not resin
# price, it is that a 6.5 m single-piece moulding exceeds the swing of almost
# every rotomoulding machine in Chile (big water tanks are the usual ceiling).
# The realistic version is a two-piece tool (hull + deck) and a machine of
# >= 4 m swing for each half, or importing the moulded shell.
ROTO_TOOLING_USD = (60_000, 90_000, 130_000)  # [EST] two-piece steel tool
ROTO_UNITS_AMORTISED = 20
ROTO_ROUTE = [
    Line("Rotomoulding powder (380 kg incl. yield)", 380, "kg", 1.6, 1.9, 2.3, "QUOTE", False,
         "UV8 rotograde, compounded colour"),
    Line("Moulding service, 2 shots (hull + deck)", 1, "lot", 1_800, 3_000, 5_000, "QUOTE", False,
         "machine >= 4 m swing -- capability to be confirmed in Chile"),
    Line("Tooling amortisation (1/%d of tool)" % ROTO_UNITS_AMORTISED, 1, "boat",
         ROTO_TOOLING_USD[0] / ROTO_UNITS_AMORTISED,
         ROTO_TOOLING_USD[1] / ROTO_UNITS_AMORTISED,
         ROTO_TOOLING_USD[2] / ROTO_UNITS_AMORTISED, "EST", False,
         "series production only; a one-off carries the whole tool"),
    Line("PE welding (bench walls, keel case, details)", 8, "kg", 8.0, 10.0, 13.0, "QUOTE", False, ""),
]

# Common to both routes.
COMMON = [
    # -- ballast & foils --
    Line("Lead, cast bulb (delivered, cast)", 170, "kg", 2.8, 3.4, 4.2, "QUOTE", False,
         "LME ~2.1 + casting; Chilean foundry"),
    Line("Keel fin S355 25 mm, profiled + HDG", 40, "kg", 4.0, 5.5, 7.5, "QUOTE", False,
         "plasma-cut + galvanised, local maestranza"),
    Line("Keel pivot pin 316 + acetal bushes + cheeks", 1, "lot", 350, 550, 850, "EST", False, ""),
    Line("Rudder blade PE500 20 mm + alloy stock (single)", 1, "lot", 300, 450, 650, "EST", False, ""),
    Line("Gudgeons + tiller fittings", 1, "lot", 200, 320, 500, "EST", True, ""),
    # -- aluminium skeleton --
    Line("6082-T6 plate & sections (spine, beams, backers)", 38, "kg", 7.0, 8.5, 11.0, "QUOTE", False, ""),
    Line("Machining/fabrication of alloy parts", 1, "lot", 600, 1_000, 1_600, "QUOTE", False, ""),
    # -- rig --
    Line("Mast section 8.6 m + fittings", 1, "lot", 2_000, 2_700, 3_600, "QUOTE", True,
         "dinghy/sportboat extrusion; Selden/AG+ class"),
    Line("Boom + gooseneck + outhaul", 1, "lot", 600, 850, 1_200, "QUOTE", True, ""),
    Line("Standing rigging 5 mm 1x19 + terminals", 1, "lot", 300, 450, 650, "MKT", True, ""),
    Line("Running rigging (2:1 systems, halyards)", 1, "lot", 350, 500, 750, "MKT", True, ""),
    Line("Deck hardware: blocks, clutches, cleats, padeyes", 1, "lot", 1_400, 1_900, 2_600, "MKT", True,
         "no winches -- this is the saving that pays for it"),
    # -- sails --
    Line("Square-top main 14 m2, 2 reefs", 1, "lot", 1_800, 2_300, 3_000, "QUOTE", True,
         "Chilean loft (e.g. local) or imported"),
    Line("Furling jib 8 m2", 1, "lot", 900, 1_200, 1_600, "QUOTE", True, ""),
    Line("Furler (small-boat, e.g. CDI FF2 class)", 1, "lot", 700, 950, 1_300, "MKT", True, ""),
    Line("Lazy bag + cover", 1, "lot", 250, 350, 500, "QUOTE", False, "local lonería"),
    # -- propulsion & electrical --
    Line("Electric outboard ~4 kW (Navy/Cruise class)", 1, "lot", 4_200, 5_500, 7_000, "MKT", True,
         "incl. throttle/cables"),
    Line("LiFePO4 48 V ~3 kWh + BMS + box", 1, "lot", 1_100, 1_700, 2_600, "MKT", True, ""),
    Line("DC-DC 48>12, panel, wiring, nav lights (LED)", 1, "lot", 500, 750, 1_100, "MKT", True, ""),
    Line("Bilge: electric pump + manual pump + bailer", 1, "lot", 250, 380, 550, "MKT", True,
         "manual pump required (PNA 1-18 4.6)"),
    # -- water ballast system --
    Line("Scoops, ball valves, cross-connect, vents, hoses", 1, "lot", 450, 650, 950, "EST", True, ""),
    Line("12 V diaphragm air pump (tank empty)", 1, "lot", 150, 220, 350, "MKT", True, ""),
    Line("Sight tubes, placards, sole strap anchors", 1, "lot", 120, 180, 280, "EST", False, ""),
    # -- fittings & finish --
    Line("A4 (316) fasteners, oversize washers, comp. tubes", 1, "lot", 450, 650, 950, "MKT", True, ""),
    Line("Acrylic bow hatches x2, PE-framed", 1, "lot", 300, 450, 650, "EST", True, ""),
    Line("Butyl tape, gaskets, sealants (PE-compatible)", 1, "lot", 150, 220, 350, "MKT", True, ""),
    Line("Spray hood + cockpit tent (lonería)", 1, "lot", 900, 1_300, 1_900, "QUOTE", False, ""),
    Line("Cuddy fabric shelf, nets, misc canvas", 1, "lot", 150, 250, 400, "QUOTE", False, ""),
    # -- safety (Chile, Bahia Vela -> Costera 12 MN band) --
    Line("Safety equipment per A-41/014 (bahia..12 MN)", 1, "lot", 600, 900, 1_400, "MKT", True,
         "lifejackets ISO 12402, flares, extinguisher, anchor 7 kg + line"),
]

# Labour is not a material, but a cost analysis that hides it misleads.
LABOUR_HOURS = {"sheet": (650, 800, 1_000), "roto": (350, 450, 600)}
SHOP_RATE_USD = (14, 18, 25)  # [QUOTE] Chilean boatyard/plastics shop, w/ overhead

# Regulatory & registration, Chile (nominal fees + inspection day)
REGULATORY = Line("Matricula, roll test day, cert fees, photos", 1, "lot",
                  250, 450, 800, "EST", False, "Capitania de Puerto")


def _sum(lines: list[Line]) -> tuple[float, float, float]:
    lo = sum(line.totals()[0] for line in lines)
    mid = sum(line.totals()[1] for line in lines)
    hi = sum(line.totals()[2] for line in lines)
    return lo, mid, hi


def run() -> None:
    os.makedirs(OUT, exist_ok=True)
    out_lines: list[str] = []

    def say(s: str = "") -> None:
        print(s)
        out_lines.append(s)

    say("=" * 96)
    say("COST ANALYSIS -- BUILDING IN CHILE")
    say(f"Assumptions: {CLP_PER_USD:.0f} CLP/USD | IVA {IVA * 100:.0f}% included in all totals |"
        f" imports +{FREIGHT_IMPORT * 100:.0f}% freight, 0% duty (FTA)")
    say("Bands are LOW / MID / HIGH planning prices, 2026. [QUOTE] lines need real quotes.")
    say("=" * 96)

    def table(title: str, lines: list[Line]) -> None:
        say("")
        say(f"--- {title} " + "-" * (91 - len(title)))
        say(f"{'item':<52}{'qty':>6} {'unit':<5}{'LOW':>9}{'MID':>9}{'HIGH':>10}  basis")
        for line in lines:
            lo, mid, hi = line.totals()
            say(f"{line.item:<52}{line.qty:>6.0f} {line.unit:<5}"
                f"{lo:>9,.0f}{mid:>9,.0f}{hi:>10,.0f}  [{line.basis}]"
                + (f"  {line.note}" if line.note else ""))
        lo, mid, hi = _sum(lines)
        say(f"{'SUBTOTAL (USD, IVA incl.)':<52}{'':>12}{lo:>9,.0f}{mid:>9,.0f}{hi:>10,.0f}")

    table("SHELL -- ROUTE A: WELDED PE500 SHEET (one-off / prototype)", SHEET_ROUTE)
    table("SHELL -- ROUTE B: ROTOMOULDED (series of %d)" % ROTO_UNITS_AMORTISED, ROTO_ROUTE)
    table("COMMON: BALLAST, FOILS, STRUCTURE, RIG, SAILS, SYSTEMS, SAFETY", COMMON)
    table("REGULATORY (Chile)", [REGULATORY])

    say("")
    say("=" * 96)
    say("TOTALS (USD, IVA included)")
    say("=" * 96)
    common = _sum(COMMON)
    reg = REGULATORY.totals()

    for name, shell_lines, hours_key in (
        ("ROUTE A -- welded sheet one-off", SHEET_ROUTE, "sheet"),
        ("ROUTE B -- rotomoulded, per boat in a series of %d" % ROTO_UNITS_AMORTISED,
         ROTO_ROUTE, "roto"),
    ):
        shell = _sum(shell_lines)
        mat = tuple(shell[i] + common[i] + reg[i] for i in range(3))
        say(f"\n{name}")
        say(f"  Materials + components:{mat[0]:>12,.0f}{mat[1]:>12,.0f}{mat[2]:>13,.0f}")
        hrs = LABOUR_HOURS[hours_key]
        lab = tuple(hrs[i] * SHOP_RATE_USD[i] * (1 + IVA) for i in range(3))
        say(f"  Labour ({hrs[0]}-{hrs[2]} h @ {SHOP_RATE_USD[0]}-{SHOP_RATE_USD[2]} USD/h):"
            f"{lab[0]:>10,.0f}{lab[1]:>12,.0f}{lab[2]:>13,.0f}")
        cont = tuple(0.10 * (mat[i] + lab[i]) for i in range(3))
        tot = tuple(mat[i] + lab[i] + cont[i] for i in range(3))
        say(f"  Contingency 10%:      {cont[0]:>12,.0f}{cont[1]:>12,.0f}{cont[2]:>13,.0f}")
        say(f"  TOTAL USD:            {tot[0]:>12,.0f}{tot[1]:>12,.0f}{tot[2]:>13,.0f}")
        say(f"  TOTAL CLP (millions): {tot[0] * CLP_PER_USD / 1e6:>12.1f}"
            f"{tot[1] * CLP_PER_USD / 1e6:>12.1f}{tot[2] * CLP_PER_USD / 1e6:>13.1f}")

    say("")
    say("Route B one-off (whole tool on one boat): add USD %s-%s tooling."
        % (f"{ROTO_TOOLING_USD[0]:,}", f"{ROTO_TOOLING_USD[2]:,}"))
    say("")
    say("NOT included: trailer, mooring, Argentine project/engineering fees")
    say("(ingeniero naval -- quote in Argentina, typ. USD 2,500-6,000 for a boat")
    say("this size incl. Encomienda), sail-number cert, delivery.")

    path = os.path.join(OUT, "costs.txt")
    with open(path, "w") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"\nWritten to {path}")


if __name__ == "__main__":
    run()
