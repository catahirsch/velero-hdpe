# Design specification — HDPE open daysailer

6.48 m open daysailer in high-density polyethylene, based on the RS Aira 22
(envelope, cockpit, rig concept) and the Flow 19 (ballast strategy,
purchase system).

All figures from `calc/report.py`; raw output in `out/report.txt`.

---

## 1. Principal dimensions

| | Baseline | Limit | RS Aira 22 |
|---|---|---|---|
| LOA | 6.48 m | 6.50 | 6.50 m |
| LWL | 6.30 m | — | 6.45 m |
| Beam (sheer) | 2.35 m | 2.50 | 2.20 m |
| Beam (chine) | 1.88 m | — | — |
| Canoe-body depth | 0.755 m | — | — |
| Draft, keel up | 0.22 m light / 0.29 m loaded | — | — |
| Draft, keel down | 1.29 m | 1.30 | 1.20 m |
| Displacement, light | 750 kg | 750 | 750 kg |
| Displacement, full load (6 crew + 500 L) | 1730 kg | — | — |
| Keel ballast | 213 kg (28.4%) | — | 250 kg (33.3%) |
| Water ballast | 2 × 250 kg (488 L) | 500 L | none |
| Sail area, upwind | 22.0 m² | 22.0 | 22.0 m² |
| SA/D (full load) | 15.5 | — | — |
| VCG, light | 0.239 m above baseline | — | — |
| Design category | C (inshore) | — | — |

Baseline z = 0 is the lowest point of the canoe body. x = 0 at the transom.

## 2. Hull form

**Hard chine, two panels per side.** This is not stylistic. Both viable HDPE
processes want it: rotomoulding needs a shape that releases from a shell tool
without undercuts, and welded-sheet construction needs panels that develop flat.
A hard chine also gives more form stability than a round bilge of the same beam,
which matters when the ballast ratio is only 27%.

Plan form carries beam well aft to support the 6-seat cockpit and the semi-open
transom, with a fine entry forward to stop it pounding. Moderate rocker, flat run
aft.

### Developability

From `geom/hull.py`, using the standard test `det[t₁, t₂, (P₂−P₁)] = 0`:

| Panel | Mean twist | Peak | Location of peak |
|---|---|---|---|
| Bottom | 0.039 | 0.199 | x = 5.94 m |
| Side | 0.018 | 0.161 | x = 5.94 m |

**Sheet-formable from the transom to x = 4.10 m — 63% of LOA.** Forward of that
the entry twists too hard for flat PE sheet. Three ways out:

1. Rotomould the stem as a separate piece and butt-weld it on
2. Split the forward panels into narrower strakes
3. Straighten the entry (costs seakeeping)

If the whole hull is rotomoulded in one shot this is moot — a shell tool does not
care about developability.

## 3. Structure — the part that decides whether HDPE works

### Material design values

| Property | Value | Note |
|---|---|---|
| Density | 950 kg/m³ | rotomoulding grade |
| Flexural modulus, short-term | 1100 MPa | **not a design value** |
| Flexural modulus, creep-derated | **250 MPa** | 10 yr, 20 °C — use this |
| Allowable bending stress | 7.0 MPa | long-term |
| Weldable | yes | |
| Adhesively bondable | **no** | non-polar surface; weld or bolt |
| Thermal expansion | ~200 × 10⁻⁶ /K | ~10× steel — detail for it |

Designing to the short-term modulus is the single most common way plastic boat
structures end up floppy. Everything below uses 250 MPa.

### Deflection governs, not stress

For HDPE at this size the stiffness requirement is always the binding one:

| Panel | Pressure | Span | t for strength | t for stiffness | Governs |
|---|---|---|---|---|---|
| Bottom | 27.1 kPa | 0.40 m | 17.6 mm | **23.0 mm** | deflection |
| Side | 21.4 kPa | 0.40 m | 15.6 mm | **21.2 mm** | deflection |
| Deck | 7.5 kPa | 0.46 m | 10.6 mm | **17.2 mm** | deflection |
| Cockpit sole | 7.5 kPa | 0.36 m | 8.3 mm | **13.5 mm** | deflection |

Pressures follow the *form* of ISO 12215-5 (category C, m_LDC 1230 kg) so they are
recognisable, but see §6 — that standard does not actually cover PE.

**Single skin is not viable.** 23 mm of solid HDPE over 32.6 m² of shell is
**710 kg** — the whole displacement budget, before rig, keel or crew. The
HDPE/GRP thickness ratio for equal panel stiffness is 2.96×.

### Double skin is the answer

Two skins separated by a gap act as the flanges of an I-beam. Equivalent solid
thickness is `(6·t·d²)^(1/3)`, typically 4–5× the material actually used.

**Specification: 5.0 mm skins, 50 mm gap, kiss-offs at 75 mm pitch.**

| Panel | t equivalent | Required | Face stress | Skin needed locally | Verdict |
|---|---|---|---|---|---|
| Bottom | 42.2 mm | 23.0 mm | 1.44 MPa | 4.3 mm | **pass** |
| Side | 42.2 mm | 21.2 mm | 1.14 MPa | 4.0 mm | **pass** |
| Deck | 42.2 mm | 17.2 mm | 0.53 MPa | 2.8 mm | **pass** |
| Cockpit sole | 42.2 mm | 13.5 mm | 0.32 MPa | 2.8 mm | **pass** |

Areal mass **9.5 kg/m²** — 44% of the single-skin mass. Face stresses are an
order of magnitude below allowable; the kiss-off pitch is what sizes the skins,
not the global bending.

Shell mass: 32.6 m² × 9.5 kg/m² × 1.12 (reinforcement) = **346 kg**.

### The material is weight-neutral — the electric drive is not

Backing the Aira's shell mass out of its published figures (750 kg total, 250 kg
ballast, minus the same non-shell items this design carries, minus the electric
drive it does not have) gives an implied GRP shell of **358 kg**.

| | kg |
|---|---|
| RS Aira shell, implied (GRP) | 358 |
| This shell, HDPE double-skin | 346 |
| **Material penalty** | **−12** |
| Electric motor + battery | **+58** |
| **Ballast: Aira 250 → this boat 213** | **−37** |

**HDPE costs essentially nothing in weight.** A rotomoulded double skin is as
efficient as a stiffened glass laminate. The 46 kg of ballast lost against the
Aira is bought by the electric auxiliary, not the plastic.

If ballast ratio matters more than motoring range, a 1.5 kWh pack instead of
3.0 kWh returns ~16 kg to the keel.

## 4. Weight budget

Ballast is not an input — it is the remainder under the 750 kg cap.

| Item | kg | z (m) | Note |
|---|---|---|---|
| HDPE shell (hull + deck) | 346.3 | 0.420 | 9.5 kg/m² × 32.5 m² |
| Keel case + pivot structure | 22.0 | 0.350 | welded PE bosses, bolted |
| Rudder + tiller (single, kick-up) | 15.0 | 0.550 | client amendment 2026-08-06 |
| Mast + boom + standing rig | 32.0 | 3.100 | short mast, no backstay |
| Sails (main + jib + furler) | 16.0 | 2.200 | square-top, lazy bag |
| Deck hardware + 2:1 systems | 19.0 | 0.780 | no winches |
| Electric motor | 26.0 | 0.550 | ~4 kW outboard format |
| Battery | 31.6 | 0.220 | 3.0 kWh LiFePO₄ |
| Spray hood + cockpit tent | 11.0 | 0.950 | stowed |
| Anchor, lines, safety gear | 18.0 | 0.400 | |
| **Keel ballast (lead)** | **213.1** | **−0.860** | **remainder** |
| **Light, incl. ballast** | **750.0** | **0.239** | |
| **Full load (6 crew + 500 kg water)** | **1730.0** | **0.402** | |

## 5. Systems and layout

### Cockpit and freeboard — the open question, resolved

Cockpit 3.20 m × 1.72 m, sole at 0.385 m above baseline.

| Condition | Waterline | Sole freeboard | Drains? |
|---|---|---|---|
| Light ship | 0.217 m | **+168 mm** | yes |
| 6 crew + 500 kg water ballast (1730 kg) | 0.329 m | **+56 mm** | yes |

The self-draining cockpit works, draining aft through the semi-open transom, with
56 mm of margin in the worst case — tight but positive. If more margin is wanted,
each 10 mm of sole height buys 10 mm of margin at the cost of cockpit depth;
alternatively sail with one tank when fully crewed. Sheer freeboard 0.538 m light.

This closes `notes.txt` line 30.

### Ballast

- **Retractable pivoting keel, 213 kg total (163 lead + 50 fin)**, 1.29 m draft lowered, 0.30 m raised, pivot at
  x = 3.30 m. Ballast VCG 0.86 m below baseline when down.
- **Water ballast, 2 × 250 kg (488 L total, inside the 500 L cap)**, tanks built
  **into the cockpit bench seats**: sealed HDPE boxes, sole (0.385) to seat top
  (0.80), inboard face at y = 0.44, outboard face at the cockpit wall
  (y = 0.86). Water centroid when full: z ≈ 0.48, y ≈ ±0.65.

The bench-tanks do triple duty, and the three roles should be kept distinct:

1. **Empty and sealed** — they *are* the reserve buoyancy of the benches
   (`reserva flotabilidad`, line 38) and the seats. No separate foam or tankage.
2. **One tank filled to windward** — 250 kg at 0.65 m of lever ≈ 1.6 kN·m,
   about **two crew on the rail**. This is the payoff that earns the plumbing:
   sailing stiffness when short-handed. Heel at 16 kt drops from 10° to 5°.
3. **Both tanks filled** — adds 500 kg for damping and inertia only. At bench
   height this **costs ~6° of AVS** (111° → 105° light ship), unlike under-sole
   tanks which would gain ~4°. That is the price of seats-as-tanks; it was a
   deliberate trade for build simplicity, seating and reserve buoyancy.

**Operating rule that falls out of the numbers:** water ballast substitutes for
crew weight, it does not stack with it. With 5–6 crew aboard, sail tanks-empty
(the crew *is* the ballast; full tanks put the loaded AVS at ~85°). With 1–3
crew, fill the windward tank. Symmetric fill is for motoring or running in a
seaway, short-handed.

Only the keel does real work at large heel in every condition.

**Filling under way remains open** (`notes.txt` line 57). Scoop/venturi intake is
passive and free but only works above ~3 kt and adds two thru-hulls; a powered
pump adds ~180 W and a load on the same battery as the motor. Recommend the
scoop, with the air pump already specified for emptying (line 56).

### Rig

Centred high boom (1.80 m above baseline — audited to clear seated heads), short mast (8.60 m), square-top main 14.0 m²,
furling jib 8.0 m², no traveller, no backstay, no winches, 2:1 purchase.

Sail-carrying, 6 crew aboard:

| True wind | Tanks symmetric | Windward tank only |
|---|---|---|
| 8 kt | 2° | 0° |
| 12 kt | 5° | 1° |
| 16 kt | 10° | 5° |
| 20 kt | 17° | 12° |
| 25 kt | 28° | 25° |

Peak righting moment at **28 kt steady** — gusts reach it sooner, so first reef
goes in around 18 kt. SA/D 15.5 at full load (18.3 without the water ballast) is
moderate; the boat is stiff for its sail area.

Downflooding angle is **37°** at full load. For an open boat that is the number
to design the crew drill around.

### Foils and steering

Single centreline kick-up rudder with a short tiller (client amendment
2026-08-06 — the notes and Flow 19 had two). Kick-up keeps beaching and trailer
recovery. The lone blade is drawn deeper (0.85 m immersed) than each of the
former twins so it keeps grip at the 20–30° heel this boat sails at; expect
some rudder emergence in the worst gusts — ease the main first.

### Propulsion

~4 kW outboard-format electric, 3.0 kWh LiFePO₄ mounted low (z = 0.22 m) under
the sole. At 4 kt cruise the pack gives roughly 1.5–2 h of motoring.

## 6. Build method and certification

### Which process

| | Rotomoulding | Welded sheet |
|---|---|---|
| Tooling | High — shell tool for a 6.5 m hull | Low |
| Double skin | Natural, with kiss-offs | Must be fabricated |
| Developability | Irrelevant | Only 63% of LOA works as-drawn |
| Unit cost at volume | Low | Flat |
| Viable at 1–5 boats | No | Yes |

**Rotomoulding for production, welded sheet for a prototype.** The scantlings
above assume the rotomoulded double skin; a welded prototype needs an equivalent
stiffened structure — 12 mm sheet on 200 mm-pitch welded top-hat stiffeners gets
close at a weight penalty of roughly 40 kg.

### Hard points — the main structural risk

HDPE **cannot be adhesively bonded**. Every load path is welded or mechanically
fastened, and PE creeps under sustained load, so bolts pull through over time
unless the load is spread.

The rig makes this worse than usual: no traveller and a centred boom put the
entire mainsheet load into one centreline point, and with no backstay the
forestay is reacted by shroud geometry alone.

| Hard point | Detail |
|---|---|
| Mast step | Welded PE box, through-bolted to an aluminium spine spanning ≥3 station frames. Do not rely on the shell. |
| Chainplates | Full-depth aluminium backing plates through both skins, load spread over ≥0.15 m². |
| Mainsheet anchor | Centreline welded PE boss, through-bolted to a transverse alloy beam bearing on the keel case. |
| Keel pivot | Machined alloy trunnion in a welded PE case, bolted to a full-height bulkhead. Highest cyclic load on the boat. |
| Rudder gudgeons | Bolted through alloy backing plates, not tapped into PE. |
| Thermal | ~200 × 10⁻⁶ /K expansion: every alloy-to-PE joint needs slotted holes or compliant bushes, or it will yield through a season. |

### Certification path

**ISO 12215-5 has no rotomoulded-PE path** — it covers FRP, aluminium, steel,
plywood and wood. The scantling numbers in §3 are indicative, not a compliance
route. CE certification of a PE hull runs through **physical testing**:
instrumented panel tests to demonstrate equivalence, plus ISO 12217-2 stability
trials.

At 6.50 m hull length the boat falls under **ISO 12217-2** (sailing boats,
hull length ≥ 6 m). Below 6.00 m it would fall under 12217-3, which is a
materially cheaper and simpler path. **The boat is 0.50 m the wrong side of that
line.** If certification cost is a driver, shortening to under 6.00 m hull length
is the single highest-leverage change available — and it is worth pricing before
committing to 6.48 m.

Treat certification as a cost and schedule item with real risk attached, not a
checkbox. Budget for a test programme.

## 7. Open items

1. **Self-righting** — requirement conflicts with the brief. Decision needed.
   See [`03-self-righting.md`](03-self-righting.md).
2. **Water ballast filling under way** — scoop vs pump. Recommend scoop.
3. **Flow 19 source data** — unverified, URL returns 403.
4. **Certification strategy** — test programme scope and cost; whether to drop
   below 6.00 m hull length.
