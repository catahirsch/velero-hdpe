# HDPE open daysailer

A 6.48 m open daysailer in high-density polyethylene, developed from two base
models: the **RS Aira 22** (dimensional envelope, 6-seat cockpit, rig concept) and
the **Flow 19** (retractable pivot keel plus water ballast, no-winch
2:1 purchase).

Requirements come from `notes.txt`.

---

## Headline results

| | |
|---|---|
| LOA / beam / draft | 6.48 m / 2.35 m / 0.22 m keel up, 1.29 m down |
| Displacement | 750 kg light, 1730 kg full load (6 crew + 500 L) |
| Ballast | 213 kg lead (28.4%) + 500 L water in the bench tanks |
| Sail area | 22.0 m² upwind, SA/D 15.5 full load |
| Structure | rotomoulded HDPE double skin, 5 mm skins / 50 mm gap, 9.5 kg/m² |
| Envelope compliance | **0 violations** |
| Cockpit self-drains | yes, +56 mm with 6 crew and 500 L aboard |
| Self-righting from 180° | **no — AVS 112°** light, ~105° tanks full. See below. |

### Three findings worth knowing up front

**1. HDPE costs essentially nothing in weight.** A rotomoulded double skin at
346 kg is within 12 kg of the GRP shell implied by the Aira's published figures.
The 46 kg of ballast lost against the Aira is bought by the **electric
auxiliary** (+58 kg), not the plastic. But single-skin HDPE is *not* viable —
deflection governs, requiring 23 mm and 710 kg of shell.

**2. The requirement envelope is the RS Aira's spec sheet.** LOA 6.50, DIS 750,
SQM 22.0 (14+8) are that boat's numbers, near-verbatim. Useful to know, because
they already encode GRP structure and no electric drive.

**3. True self-righting is a beam problem, not a ballast or open-cockpit
problem.** Sealing the cockpit entirely moves AVS by ~1°. Adding 800 kg of lead
gets to 149°, not 180°. What works is narrowing: 1.80 m beam and ~450 kg of
ballast self-rights, at ~990 kg displacement — which breaks the 6-abreast
cockpit and the 750 kg cap. **This requires a decision.**

The water ballast (`BAL <500` = 500 L) lives **inside the bench seats** (client
decision): one 250 kg tank filled to windward is worth about two crew on the
rail, and empty benches are the cockpit's sealed reserve buoyancy. The height
trade is real: at bench height, filling both tanks *costs* ~6° of AVS (under-sole
tanks would have gained ~4° via the RNLI righting-tank mechanism). Operating
rule: with a full crew sail tanks-empty; short-handed, fill the windward tank.

## Documents

| | |
|---|---|
| [`docs/01-requirements.md`](docs/01-requirements.md) | Conflict-resolved requirements, provenance of every figure, open items |
| [`docs/02-design-spec.md`](docs/02-design-spec.md) | Full design: hull form, HDPE structure, systems, build method, certification |
| [`docs/03-self-righting.md`](docs/03-self-righting.md) | Trade study and four costed options for the self-righting conflict |
| [`docs/04-build-spec.md`](docs/04-build-spec.md) | **Builder's package**: dimensions + tolerances, materials with grades, scantlings, hard points, foil/rig dimensions, water-ballast system, build sequence |
| [`docs/05-regulatory.md`](docs/05-regulatory.md) | **Argentina (PNA) + Chile (DIRECTEMAR)** path: approvals, registration, equipment by zone, the water-ballast friction point — from the primary ordinances |
| [`docs/06-compliance-notes.md`](docs/06-compliance-notes.md) | Line-by-line compliance matrix against the client's notes.txt — 30/33 met, the 3 that need a decision |
| [`docs/09-diseno-estilo.md`](docs/09-diseno-estilo.md) | Diseño: paletas de color para HDPE, terminaciones, detalles de confort, anti-ideas |
| [`docs/07-cost-analysis.md`](docs/07-cost-analysis.md) | Cost of building in Chile: welded one-off ~USD 64k mid vs rotomoulded series; parameterized model in `calc/costs.py` |
| [`autoadrizante/specs.md`](autoadrizante/specs.md) | **Self-righting variant (chosen resolution, 2026-08-07)**: same open 2.35 m boat + sealed mast + 60 L masthead float, *modelled in the GZ curves* — recovers unaided to 156°, turtle energy 2516 → 302 J. Full parallel of `out/`: specs, [changes vs baseline](autoadrizante/cambios.md), report, audit (22 checks), costs, 3DM + previews, STL, offsets, 8-sheet planos, water renders, physics GIF, presentation PDF — plus an **expanded options study** (section 4 of `presentacion.pdf`; raw run in `opciones.txt`): 8 righting options vs notes.txt, incl. an inflatable masthead bag that reaches literal 180° on the 2.35 m hull |

## Client viewer

**Live:** https://catahirsch.github.io/velero-hdpe/

Everything — specs, options data, blueprints, PDFs, interactive 3D model,
design/colour studies, downloads — in one browser page. To run it locally
instead:

```bash
python3 -m http.server 8000     # from the project folder (or double-click visor.command)
# then open http://localhost:8000
```

`index.html` loads the options comparison live from `autoadrizante/opciones.json`,
renders `specs.md`/`cambios.md`, embeds `planos.pdf` and `presentacion.pdf`, and
shows the hull STL (variant with rig + masthead float, and the narrow Option D
reference) in an orbitable three.js viewer. Regenerating the model outputs
updates the page — nothing on it is hand-copied.

## Running it

```bash
python3 -m calc.report            # full calculation chain  (~10 s)
python3 -m calc.trade             # self-righting sweeps    (~4 min)
python3 -m calc.options           # costed resolution options (~5 min)
python3 -m geom.hull --both       # STL meshes + tables of offsets
python3 -m geom.export_3dm --both # Rhino .3dm visualization models
python3 -m calc.costs             # Chilean build cost model -> out/costs.txt
python3 -m geom.animate_righting  # self-righting animation -> out/selfrighting.gif
python3 -m calc.presentation      # client-facing PDF -> out/presentacion.pdf
python3 -m calc.audit             # buildability audit (15 physical checks)
python3 -m geom.drawings          # construction drawings -> out/planos.pdf
python3 -m geom.render_ideas      # design study: colorways + styling
python3 -m geom.render_scene      # 'photos': boat on the water, lit + reflections
```

Requires numpy, scipy, matplotlib; `rhino3dm` additionally for the .3dm export.
Polygon clipping and the STL writer are implemented directly.

### Outputs, in `out/`

| File | Contents |
|---|---|
| `report.txt` | Geometry, scantlings, weights, hydrostatics, stability, compliance |
| `trade_study.txt` | Ballast / beam / cockpit / depth sweeps and the frontier |
| `options.txt` | The four resolution options with costs |
| `gz_curves.png` | GZ curves, 0–180°, intact and flooded, light and loaded |
| `hull_lines.png` | Body plan, profile, plan |
| `trade_frontier.png` | Self-righting frontier and AVS vs ballast ratio |
| `hull_baseline.stl` | Baseline hull mesh, metres |
| `hull_selfrighting.stl` | 1.80 m beam variant that meets the requirement (452 kg keel) |
| `offsets_*.txt` | Tables of offsets for lofting or a builder |
| `boat_baseline.3dm` | Rhino model: hull with cockpit, keel, rudders, rig, tanks, waterlines — layered |
| `boat_selfrighting.3dm` | Same for the 1.80 m beam variant |
| `preview_3dm.png`, `preview_cockpit.png` | Quick renders of the .3dm contents |
| `foto_patagonia_navegando.png`, `foto_aira_fondeado.png` | El bote **en el agua**: renders iluminados con flotación y escora reales, velas izadas (`geom/render_scene.py`) |
| `diseno_colores.png`, `diseno_perfil.png` | Estudio de diseño: 4 paletas de color + elementos de estilo (`geom/render_ideas.py`) |
| `planos.pdf` | **7 láminas de construcción acotadas** (GA, formas, sección maestra, quilla, espejo/timón, plano vélico, lastre de agua) |
| `audit.txt` | Auditoría de constructibilidad — 15 verificaciones físicas, todas PASS |
| `presentacion.pdf` | **Resumen completo en castellano, listo para presentar** (12 páginas) |
| `selfrighting.gif` | **Animación**: ambos botes soltados invertidos — el base queda tortuga, la variante 1.80 m vuelve sola (`geom/animate_righting.py`) |

## Code layout

```
calc/
  params.py       all design parameters, provenance-tagged  <- start here
  geometry.py     stations, polygon clipping, heeled hydrostatics
  scantlings.py   HDPE panel sizing, creep-derated
  weights.py      weight and VCG budget; ballast as the remainder
  stability.py    GZ curves 0-180 deg, intact and flooded; sail carrying
  trade.py        parameter sweeps for the self-righting study
  options.py      costed resolution options
  report.py       driver -- runs everything, writes report and plots
geom/
  hull.py         mesh generation, STL export, developability check
  export_3dm.py   Rhino .3dm export: full boat on layers, for visualization
  animate_righting.py  physics animation of the self-righting comparison
calc/
  presentation.py the client-facing PDF builder (Spanish)
  audit.py        buildability audit: 15 physical consistency checks
geom/
  drawings.py     dimensioned construction drawings (7 sheets, Spanish)
```

Every parameter lives in `calc/params.py`, tagged with its source:
`[AIRA]` published spec, `[FLOW]` from `notes.txt`, `[NOTES]` stated in the brief,
`[ASSUM]` an assumption, `[MAT]` a material property. Change an assumption there
and the whole chain follows.

## Method notes

- **Stability** is computed from real geometry, not coefficients: each station is
  rotated into the earth frame and clipped against the waterplane with
  Sutherland-Hodgman, then integrated. Clipping a simple polygon against one
  half-plane leaves degenerate edges lying exactly along the clip line, where
  they contribute nothing to the shoelace area — so areas and centroids are exact
  without a geometry library.
- **Two GZ curves** are produced for every case. *Intact* treats the cockpit as
  watertight and is valid only up to the downflooding angle (44°). *Flooded* lets
  the cockpit fill once its opening immerses, and is the physically meaningful
  curve beyond that. The difference between them is small, which is itself the
  key result in the trade study.
- **Displacement is not held constant** in the trade sweeps. Ballast is added on
  top of the fixed weight, so each figure shows the displacement it implies.
- **ISO 12215-5 has no rotomoulded-PE path.** Pressures follow its form so the
  numbers are recognisable, but they are indicative, not a compliance route. At
  6.50 m the boat falls under ISO 12217-2, not 12217-3 — 0.50 m the wrong side of
  a cliff edge in certification cost.

## Caveats

- Flow 19 figures are unverified — its source URL returns HTTP 403.
- The flooded-cockpit model **removes buoyancy but does not add trapped water as
  weight**. That is correct for a cockpit draining aft through an open transom at
  moderate heel, where the internal water level equals the sea. At large heel and
  inverted, some water would be trapped above sea level, and its weight would
  reduce GZ further. So the model is **optimistic about self-righting** — and the
  boat still fails the test. The conclusion in `docs/03` is robust in the
  direction that matters.
- Aerodynamic heeling uses a single effective coefficient (1.05); it is sizing-
  grade, not VPP-grade.
- Panel formulas assume clamped long plates. Real corners and openings need
  detailed checks.
- No structural FEA. The hard points in `docs/02` §6 are where that effort
  belongs.
