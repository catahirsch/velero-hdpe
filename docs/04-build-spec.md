# Build specification

Everything needed to build the boat: dimensions, materials with grades,
scantlings, construction details and a bill of materials. Geometry comes from
`out/offsets_baseline.txt` (table of offsets, 121 stations) and
`out/boat_baseline.3dm` (dimensioned 3D model, metres). Where a number is an
engineering assumption it is tagged; nothing here is decorative.

**Read first:** §9 of `02-design-spec.md` — this boat as specified does **not**
meet the true self-righting requirement. Building to this spec means accepting
the masthead-float resolution (Option A) or switching to the 1.80 m variant
(`offsets_selfrighting.txt`). Everything below describes the 2.35 m baseline.

---

## 1. Principal dimensions (as-built targets)

| | Value | Tolerance |
|---|---|---|
| LOA | 6.480 m | ±15 mm |
| LWL (light) | 6.30 m | — |
| Beam, sheer | 2.350 m | ±10 mm |
| Beam, chine | 1.880 m | ±10 mm |
| Canoe-body depth (baseline→sheer, min) | 0.755 m | ±8 mm |
| Deck crown above sheer | 0.055 m | — |
| Cockpit (L × W inside walls) | 3.200 × 1.720 m | ±10 mm |
| Cockpit sole above baseline | 0.385 m | +10/−0 mm — governs self-draining |
| Bench seats (top above baseline) | 0.800 m | ±10 mm |
| Bench width | 0.420 m | — |
| Footwell width between benches | 0.880 m | — |
| Draft, keel up / down | 0.30 / 1.29 m | — |
| Light displacement incl. keel | 750 kg | +0/−25 kg |
| Keel (fin + lead), total | 213 kg | ±2 kg, assembly VCG 0.86 m below baseline |

Full hull shape: `out/offsets_baseline.txt` — x from transom, half-breadths and
heights for keel, chine, sheer, crown at 54 mm station spacing. Loft from this
or section the 3DM directly.

## 2. Materials schedule

| Application | Material | Spec |
|---|---|---|
| Hull + deck shell (rotomoulded) | HDPE rotomoulding powder | MFI 3–6 g/10 min, density ≈ 940–950 kg/m³, UV8 stabilised (e.g. Matrix/ExxonMobil rotograde or regional equivalent). Colour compounded-in, not painted — HDPE takes no paint. |
| Hull + deck (welded-sheet prototype alternative) | PE300 (PE-HWU) or PE500 sheet | Extrusion-weldable, UV-stabilised black or through-coloured |
| Welding rod | Same resin family as sheet/moulding | 4–5 mm HDPE rod; hot-gas extrusion welding, DVS 2207-4 practice |
| Keel ballast | Lead, cast | Antimony-hardened (2–4% Sb) for casting; 213 kg |
| Keel fin structure | Steel S355, hot-dip galvanised | Plate 15 mm, chords 0.50/0.30 m, 6 mm root doublers both faces |
| Backing plates, mast spine, transverse beams | Aluminium 6082-T6 | Plate 6–10 mm |
| Keel pivot pin | Stainless 316, Ø25 mm | With PE-friendly polymer bushes (acetal) |
| Fasteners, all external | Stainless A4 (316) | M8–M12; **oversized washers ≥3× bolt Ø on every PE face** |
| Standing rigging | 1×19 stainless 316 wire, Ø5 mm | Forestay + 2 shrouds; no backstay by design |
| Running rigging | Polyester double-braid 8–10 mm | 2:1 purchases, no winches |
| Spars | Aluminium 6061-T6 or 6082-T6 extrusion | Mast Ø ~110×2.5 mm section or dinghy-class equivalent, boom 90×2 mm |
| Sails | Dacron 250–300 g/m² | Square-top main 14.0 m² **with 2 reef rows (≥40% luff reduction total — Chilean Circular A-41/014 II.M requires it for a non-furling main)**; furling jib 8.0 m² |
| Trampoline/nets, cuddy shelf | PVC mesh / canvas | `estante tela`, notes line 20 |
| Sealant at fastener penetrations | Butyl tape or MS polymer | Silicone and epoxies do not bond PE — use gaskets and compression, never adhesion |

**The one rule that governs every joint: nothing glues to HDPE.** Every
connection is a weld (PE to PE) or a bolted compression joint with load spread.
PE creeps: any bolt bearing on unreinforced PE will loosen. Every bolted joint
gets an aluminium backing plate on the PE side, torqued to compress a defined
gasket area, with slotted holes where the span exceeds ~0.5 m (PE expands
~200 µm/m per 10 °C — 10× aluminium).

## 3. Shell scantlings

### Production: rotomoulded double skin

| Parameter | Value |
|---|---|
| Skins | 2 × 5.0 mm nominal (−0/+1 mm) |
| Skin gap | 50 mm |
| Kiss-offs (tack-offs) | Ø ~60 mm at 75 mm pitch, both directions, bottom and topsides; 100 mm pitch deck |
| Areal mass | 9.5 kg/m² |
| Shell total (hull + deck + cockpit, 32.6 m²) | ≈ 346 kg incl. reinforcement |

Verification (from `calc/scantlings.py`, ISO 12215-5-form pressures, category C,
creep-derated E = 250 MPa):

| Panel | Design pressure | Required equiv. t | Provided | Margin |
|---|---|---|---|---|
| Bottom | 27.1 kPa | 23.0 mm | 42.2 mm | 1.8× |
| Topsides | 21.4 kPa | 21.2 mm | 42.2 mm | 2.0× |
| Deck | 7.5 kPa | 17.2 mm | 42.2 mm | 2.5× |
| Cockpit sole | 7.5 kPa | 13.5 mm | 42.2 mm | 3.1× |

Face stresses ≤1.5 MPa against 7 MPa allowable. The kiss-off pitch, not global
bending, sizes the skins — do not stretch the pitch past 90 mm on the bottom.

### Prototype: welded PE500 sheet

12 mm single skin on welded top-hat stiffeners (PE, 60×40×8 mm section) at
200 mm pitch, bottom and sides; 10 mm deck on 250 mm pitch. Weight penalty
≈ +40 kg over the rotomoulded shell — take it out of the keel and accept 165 kg
of ballast, or accept 790 kg light. Sheet development: panels are flat-formable
from the transom to x = 4.10 m; forward of that, either strake-split the panels
or thermoform the stem over a simple male plug.

## 4. Structure and hard points

The internal skeleton is aluminium, because rig and keel loads cannot terminate
in creeping plastic.

| Item | Specification |
|---|---|
| Mast spine | 6082-T6 channel 120×60×8 mm, under-deck, spanning stations at x = 3.55 → 5.05 m, through-bolted to 3 PE bulkhead webs (audited: 138 MPa at 11 kN rig compression) |
| Mast step | Cast/machined alloy base on the spine; compression post to keel-case top not required (deck-stepped, loads into spine) |
| Chainplates (×2) | 6082-T6 strap 50×8 mm, outside face; backing plate 300×150×8 mm inside, 6× M10 A4 through both skins with compression tubes so bolts do not crush the double skin |
| Forestay fitting | Stem head alloy weldment, 4× M10 through the (solid at stem) bow moulding |
| Mainsheet anchor | Transverse 6082 beam 80×40×4 box under the sole at x = 1.55 m, bearing on both bench-tank inner walls; single centreline padeye — no traveller by design |
| Keel case | Rotomoulded/welded PE box, wall 12 mm, capped by 8 mm alloy cheek plates each side; pivot pin Ø25 316 at x = 3.30 m, z = 0.05 m |
| Keel bolts / pivot bearing area | Cheek plates through-bolted 8× M12; acetal bushes; grease nipple |
| Rudder gudgeons (×2) | Alloy, through-transom on 150×100×6 backing plates, 4× M8 each |
| Bench-tank walls | Structural: they carry the sole and stiffen the topsides. 8 mm PE inboard wall, welded to sole and hull; tops removable gasketed hatches for inspection |
| Compression tubes | At EVERY bolt through double skin: PE or alloy tube, skin-to-skin, so torque does not crush the sandwich |

## 5. Keel and rudders (foil dimensions)

**Pivoting keel** — NACA 0012-faired plate fin (audited in `calc/audit.py`):

| | |
|---|---|
| Root chord / tip chord | 0.50 / 0.30 m |
| Span below hull (down) | 1.06 m |
| Fin | S355 plate **15 mm** + 6 mm root doublers, profiled, HDG — 50 kg (bending 157 MPa at max RM, SF 2.3 on yield) |
| Ballast | **163 kg lead bulb 0.58 × 0.145 × 0.17 m (14.3 L)** cast around the fin tip, centroid z = −0.99 → **assembly VCG −0.86** |
| Draft, down | 1.294 m to bulb bottom (inside CBD 1.30) |
| Pivot | x = 3.30 m, Ø25 pin; raised draft 0.30 m; case slot ~1.21 × 0.18 m |
| Lift | 4:1 tackle to cockpit; hold-down latch (keel is buoyancy-negative, but a knockdown must not retract it) |

**Rudder (single, centreline)** — NACA 0010, kick-up blade:

| | |
|---|---|
| Chord (mean) | 0.26 m |
| Immersed span | 0.85 m |
| Blade | HDPE-skinned foam or solid PE500 20 mm, alloy stock |
| Position | Transom-hung on centreline, kick-up pivot, short tiller. Transom drain scuppers split either side of the stock. |

## 6. Rig dimensions

| | |
|---|---|
| Mast length / height above deck | 8.60 m, deck-stepped at x = 4.25 m |
| I (foretriangle height) | 7.05 m (hounds at 82% — fractional) |
| J (stem to mast) | 2.20 m |
| P (main luff) | 7.55 m |
| E (main foot) | 2.75 m |
| Boom height above baseline | **1.80 m** — 1.0 m over the bench tops, so a tall seated adult (pan + 0.95 m) clears it. Audited; 1.66 m did not clear. |
| Main | 14.0 m² square-top, 2 reef rows, lazy bag |
| Jib | 8.0 m² on furler |
| Shroud base | Chainplates at x = 4.05 m, y = ±1.10 m; swept spreaders ~20° aft replace the backstay |
| Purchases | Main 2:1, jib sheets 2:1, keel lift 4:1 — no winches |

## 7. Water ballast system (bench-tanks)

| | |
|---|---|
| Tanks | 2, inside the bench seats: x 0.35–3.55 m, y 0.44–0.86 m, sole to 0.62 m fill level (seat top 0.80) |
| Capacity | 250 kg (244 L) each; 488 L total — inside the 500 L cap |
| Fill | Ø38 mm scoop thru-hull per side at the chine, forward-facing, ball valve — fills in ~3 min above 4 kt. No pump load. |
| Vent | Ø25 mm to cockpit wall, goose-necked |
| Empty | 12 V diaphragm air pump (notes line 56) pressurising the tank through the vent line, water forced back out the scoop; plus gravity dump when heeled |
| Cross-connect | Ø51 mm valved transfer line under the sole for tacking the ballast |
| Level | Clear sight tube on each inboard bench wall |

Operating rule (from the stability model): **crew full → tanks empty; crew 1–3 →
windward tank; symmetric fill only for motoring/damping.** One tank to windward
≈ righting moment of two crew.

## 8. Electrical / propulsion

| | |
|---|---|
| Motor | 4 kW electric outboard (e.g. class of Torqeedo Cruise 4.0 / ePropulsion Navy 6), transom bracket on backing plate |
| Battery | 3.0 kWh LiFePO₄, 48 V, in a ventilated sealed box under the sole at x ≈ 2.0 m (z = 0.22) — strapped per Chilean Circular A-41/014 II.K (heavy items secured) |
| Nav lights | Per COLREG/RIPA; ≥10 W or LED equivalent (A-41/014 II.J) — masthead tricolour + steaming |
| Bilge | 12 V electric pump in the footwell sump **plus manual pump** (PNA 1-18 §4.6 requires the manual pump for coastal zones) + bucket/bailer |
| Panel | 6-way, main isolator, 48→12 V DC-DC for lights/pumps/VHF |

## 9. Weights as specified

| Item | kg |
|---|---|
| Shell (rotomoulded, incl. reinforcement) | 346 |
| Keel case + pivot hardware | 22 |
| Keel fin + lead | 213 total — see note |
| Rudder + tiller (single) | 15 |
| Spars + standing rigging | 32 |
| Sails + furler + lazy bag | 16 |
| Deck hardware + purchases | 19 |
| Motor + battery | 58 |
| Spray hood + cockpit tent | 11 |
| Anchor, lines, safety | 18 |
| **Light ship** | **750** |

Note: the 213 kg "keel ballast" line in the budget is total keel mass allowance:
**163 kg lead + 50 kg fin steel** (audited — a 25 mm fin would have weighed
~100 kg and made the assembly VCG unreachable).
VCG of the combination held at −0.86 m by bulb placement.

## 10. Build sequence (rotomoulded route)

1. CNC-cut station moulds from the offsets → fabricate the two-piece shell tool
   (hull half, deck/cockpit half) in welded steel sheet.
2. Rotomould hull and deck halves; kiss-offs formed by tool bosses. Wall
   thickness audit: ultrasonic, 9 points/m², reject <4.5 mm.
3. Weld hull/deck flange (extrusion weld inside + outside beads at the sheer).
4. Weld in bench-tank inboard walls, keel case, sole (if not moulded in).
5. Fit aluminium skeleton: mast spine, mainsheet beam, chainplate backers —
   all on compression tubes and butyl gaskets.
6. Hang keel (pivot + cheek plates), rudders, deck hardware.
7. **Leak-test the bench tanks** (air, 0.15 bar, soap) — they are both ballast
   tanks and the reserve buoyancy; a leaking tank is a safety failure, not a
   nuisance.
8. Step rig, tune (swept spreaders pre-bend ~20 mm).
9. **Inclining/roll-period test** — required for the Chilean paperwork (O-71/010
   Anexo B) and it validates the stability model: measured light ship must be
   750 ±25 kg, VCG 0.24 ±0.03 m. If it isn't, the model and the operating
   rules get re-run before the boat carries six people.

## 11. What this spec does not include

- **Class-A fair NURBS surfaces for the production tool.** The offsets and 3DM
  are dimensionally complete but mesh-faceted; the toolmaker lofts fair splines
  through the offsets (standard practice) or a naval CAD pass does it first.
- **FEA of the four hard points.** The sizes above are engineering estimates
  with generous load spreading; a professional check of chainplate, mast spine,
  keel case and gudgeons is cheap insurance and — in Argentina — will be done
  anyway by the *ingeniero naval* who signs the project (see `05-regulatory.md`).
- **Certified stability documentation.** The GZ curves here are calculation,
  not certification; the roll test in §10.9 is where paper meets water.
