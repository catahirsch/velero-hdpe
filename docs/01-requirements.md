# Requirements — HDPE open daysailer

Derived from `notes.txt`, with every figure traced to a source. Nothing in this
document is invented; where a number had to be assumed it says so.

---

## 1. Where the envelope came from

The six dimensional limits in `notes.txt` are, to within rounding, the published
spec sheet of the **RS Aira 22**. That is worth stating plainly, because it means
the envelope is not an independent set of targets — it is one existing GRP boat's
achieved numbers, and it already encodes GRP's structural efficiency and the
absence of an electric drive.

| Note | Stated limit | RS Aira 22 (published) | Reading |
|---|---|---|---|
| `LOA <6.50` | 6.50 m | **6.50 m** | identical |
| `BEA <2.50` | 2.50 m | 2.20 m | rounded up to the EU road limit |
| `DIS <750` | 750 kg | **750 kg** | identical |
| `SQM <22` | 22 m² | **22.0 m²** (14.0 main + 8.0 jib) | identical |
| `BAL <500` | 500 **litres** of water ballast | — (Aira carries none) | see §2 |
| `CBD <1.30` | 1.30 m | 1.20 m | keel lowered |

Source: rssailing.com/project/rs-aira/, fetched 2026-08-06.

**Note on naming:** `notes.txt` line 17 reads *Aira 22* (RS Aira). The original
request said "Aria 22". The RS Aira is the boat.

The **Flow 19** figures on lines 26–33 could not be verified — the
carbonmade.com URL returns HTTP 403. They are used as recorded by the designer:
beam 2.30 m, draft 1.30 m, displacement 450 kg, 70 kg swing keel, 2 × 60 kg water
ballast, twin pivoting rudders, 2:1 purchase, no traveller, no backstay.

## 2. Resolved parameters

`CBD` (line 8) and `CND` (line 27) are the same parameter under two spellings.
Read as **keel depth, lowered** — not overall draft, which for a pivot-keel boat
is a different and much smaller number (canoe-body draft, computed at 0.22 m
light / 0.29 m loaded).

`DIS <750` is confirmed as **light/dry displacement including ballast**. Six crew
and the water ballast sit on top of it, so full-load displacement is ~1730 kg.
This is the definition the whole weight budget is built on.

`BAL <500` is confirmed (designer, 2026-08-06) as **500 litres of water
ballast** — not a cap on lead. The design carries 2 × 250 kg tanks (488 L of
seawater, inside the cap) built into the cockpit benches and double sole, so the
tanks are the sealed reserve buoyancy when empty and the ballast when full. The
keel ballast is a separate quantity, solved as the remainder of the 750 kg
budget (213 kg).

## 3. Intended use — settled

An open daysailer, not a cruiser:

- 6-seat cockpit, no cabin; bow cuddy with a fabric shelf (`estante tela`)
- Self-draining cockpit, draining aft through a semi-open transom
- Spray hood plus cockpit tent for shelter; flat foredeck for sunbathing
- Electric auxiliary
- Single centreline kick-up rudder with short tiller (client amendment 2026-08-06; notes line 39 said two)
- Pivoting keel
- Furling jib, centred high boom, short mast, square-top main
- No traveller, no backstay, no winches — 2:1 purchase throughout
- Double bow hatch (`doble tambucho proa`); removable righting straps on the
  sole; 1″×1″ foot-bracing battens

## 4. What each base model contributes

**RS Aira 22** — the dimensional envelope, the 6-adult cockpit, the general
rig concept (high centred boom, short mast, square-top main, furling headsail),
and the reference point for what 750 kg buys in a 6.5 m hull.

**Flow 19** — the ballast strategy (light pivoting keel plus symmetric water
ballast), the no-winch 2:1 purchase system (its twin rudders were later dropped by client amendment), and the
no-traveller/no-backstay rig simplification.

## 5. Requirements that conflict

### 5.1 True self-righting vs. everything else — **unresolved, decision needed**

The stated requirement (confirmed after the conflict was flagged) is recovery
from 180° unaided. The calculations say this is **not achievable within the rest
of the brief**, and the reason is not the one usually assumed.

- The baseline reaches AVS **112°** with 213 kg of ballast (28% ratio) and has a
  **stable inverted equilibrium**.
- Ballast alone does not fix it. Even at 1000 kg of lead — displacement ~1540 kg
  on a 6.5 m hull — AVS only reaches 149°.
- **Sealing the cockpit barely helps** (AVS 112.4° sealed vs 112.2° flooded).
  When inverted the boat floats so high that the cockpit is mostly out of the
  water anyway. The "open boat loses its reserve buoyancy" argument is wrong here.
- The binding constraint is **beam-to-depth ratio**. 2.35 m of beam on 0.755 m of
  depth is a hull that is stable upside down, and that is the same form stability
  that makes it stiff upright and lets it carry 6 people and 22 m².

Cheapest configuration that genuinely self-rights: **1.75–1.80 m beam, 417–452 kg
ballast, ~954–988 kg displacement** — which breaks the 6-abreast cockpit and
exceeds `DIS 750` by 27–32%.

Full trade study and four costed options: [`03-self-righting.md`](03-self-righting.md).

### 5.2 Lead is scarce; water is not

The 750 kg budget leaves **213 kg** for the keel after structure, rig, foils,
hardware and the electric drive — 46 kg less than the Aira, bought by the
electric auxiliary. The 500 L of water ballast rides on top of the light-ship
budget and lives **inside the bench seats** (client decision): filled to
windward it is worth about two crew on the rail; empty, the benches are the
cockpit's reserve buoyancy. Filling both tanks symmetrically costs ~6° of AVS
at bench height and is only worth doing for motion damping in a seaway with a
small crew.

### 5.3 ISO certification vs. the material — cost and schedule risk

**ISO 12215-5 has no rotomoulded-PE path.** Its scantling formulas cover FRP,
aluminium, steel, plywood and wood. Certification of a PE hull runs through
physical testing instead.

At 6.50 m hull length the boat falls under **ISO 12217-2** (sailing boats,
hull length ≥ 6 m) — *not* 12217-3, which covers boats under 6 m. This is a
cliff edge, not a gradient: dropping hull length below 6.00 m would move the boat
into a materially simpler and cheaper stability-assessment path. At 6.50 m LOA
the boat sits just the wrong side of it, by 0.50 m.

## 6. Questions the notes left open

| # | Question | Status |
|---|---|---|
| 1 | Freeboard and cockpit sole height (line 30) | **Resolved by calculation.** Sole at 0.385 m above baseline drains with +168 mm margin light, **+56 mm** with 6 crew and 500 L of water ballast aboard (1730 kg). Tight but positive; raising the sole 30 mm would buy comfort at the cost of cockpit depth. |
| 2 | How to fill water ballast under way (line 57) | **Open.** Scoop/venturi intake vs. powered pump changes electrical load and thru-hull count. Emptying by air pump is already specified (line 56). |
| 3 | True self-righting | **Open — needs a decision.** See §5.1. |
| 4 | Flow 19 source data | **Blocked.** URL returns 403. |

## 7. Assumptions this model makes

All are tagged `[ASSUM]` in `calc/params.py` and can be changed in one place:

- Beam 2.35 m (between the Aira's 2.20 and the 2.50 road cap, for form stability)
- LOA 6.48 m, LWL 6.30 m
- Canoe-body depth 0.755 m; cockpit 3.20 m × 1.72 m; sole at 0.385 m
- Keel ballast VCG 0.86 m below baseline, lowered
- Water ballast tanks: 2 × 250 kg, centroid 0.26 m above baseline, 0.72 m off
  centreline, built into the benches and double sole
- Electric drive: ~4 kW outboard-format motor (26 kg) + 3.0 kWh LiFePO₄ (32 kg)
- Crew 80 kg each (ISO uses 75 kg; 80 is more honest)
- Design category C (inshore)
- HDPE: ρ 950 kg/m³, short-term flexural modulus 1100 MPa, **creep-derated
  design modulus 250 MPa**, allowable bending stress 7 MPa
