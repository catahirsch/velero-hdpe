# Regulatory path — Argentina and Chile

What it takes to build, register and operate this boat legally in each country.
Grounded in the primary documents fetched 2026-08-06 (cited at the end); **this
is engineering research, not legal advice — confirm with the Prefectura /
Capitanía before cutting material**, because ordinances get amended and local
jurisdictions add requirements.

The two systems are structured differently and it changes what you build first:
**Argentina regulates the construction** (approval before and during the build,
signed by a registered professional); **Chile regulates the finished boat**
(local inspection, roll test, equipment). If the boat will live in both
countries, design the paperwork for Argentina and the equipment for Chile and
you satisfy both.

---

## 1. Argentina — Prefectura Naval Argentina (PNA)

Framework: Ley 20.094 (Navigation), REGINAVE (Decree 4516/73), Tomo 4
Ordenanza 1-18 (DPSN) "Régimen de las Actividades Náutico-Deportivas".

### 1.1 Construction approval

- Any individual construction gets a **Certificado de Aprobación de
  Construcción** from PNA; a repeatable design gets a **Certificado de
  Aprobación de Prototipo** (both defined in Ord. 1-18 §1). If you intend to
  build more than one boat for clients, do the prototype approval once — every
  later hull rides on it.
- The project must be signed by a professional (naval engineer / licenciado /
  técnico constructor naval) under a **Certificado de Encomienda** — the
  contract of technical representation (Ord. 1-18 §1, definitions). The
  designer and the construction supervisor must be registered with the
  professional council (CPIN) and with PNA (REGINAVE Título 1, art. 101.0302).
- Submission: plans (general arrangement, lines, structure/midship section,
  electrical, bilge), calculation memory (weights, stability), materials. This
  repo *is* most of the technical annex: offsets, 3DM, scantlings with method,
  weight/VCG budget, GZ curves, equipment schedule.
- **HDPE note:** PNA's technical rules, like ISO 12215, have no rotomoulded-PE
  scantling table. Expect the Agrupación Técnica to ask for equivalence
  justification — the plate-theory + creep-derated-modulus method in
  `calc/scantlings.py` plus panel test coupons is the standard argument. Budget
  time for this conversation; have the ingeniero naval lead it.

### 1.2 Registration and zone

- Registration in **REJU** (Registro Jurisdiccional — typical for a 6.5 m open
  daysailer) or **REY** (Registro Especial de Yates).
- The boat's permitted **navigation zone** is set in its construction
  certificate (Ord. 1-18 §4.1): Aguas Protegidas / Costera Restringida /
  Costera Marítima / Oceánica. **Target: Costera Restringida** (protected +
  limited coastal) — consistent with design category C assumptions in the
  stability work. Oceánica is off the table for an open boat and was never the
  brief.
- Skipper licence: a 6.48 m auxiliary-sail yacht needs **Timonel de Yate a
  Vela** minimum (Ord. 1-18 §7.2.4); Conductor Náutico only covers motor boats
  to 7 m. Tell the client — it affects who they can sell/lend the boat to.

### 1.3 Equipment (Ord. 1-18 Anexo A, VELA column, Costera Restringida / Aguas Protegidas)

| Item | Costera Restringida | Aguas Protegidas |
|---|---|---|
| Lifejackets (all aboard) | ✔ | ✔ |
| Anchor + line — **6.0–8.9 m boat: 7 kg anchor, 12 mm nylon, 6 mm chain** (§4.7) | ✔ | ✔ |
| Compás magnético | ✔ | ✔ (vela) |
| VHF (portable OK; cell phone w/ GPS acceptable in these zones) | ✔ | ✔ |
| Hand sonda / lead line | ✔ | ✔ |
| Manual bilge pump (§4.6) + bailer | ✔ | bailer |
| Fire extinguisher (tri-class, sized to boat) | ✔ | ✔ |
| Nav lights per RIPA | ✔ | ✔ |
| Bell or hand bell (≤12 m), horn/whistle | ✔ | ✔ |
| Red hand flares ×2, parachute ×2 (hand-only on large lakes) | ✔ | flares ×2 |
| Lifebuoy w/ 27.5 m floating line | ✔ | ✔ |
| First-aid kit (Anexo A **) | ✔ | ✔ |
| Signal mirror, distress-signal table, RIPA text | ✔ | ✔ |
| Harnesses (per boat size) | ✔ | — |
| Cizalla (rigging cutter) — **sail specific** | ✔ | ✔ |

(EPIRB, raft, AIS, HF, sextant: Oceánica only — not applicable.)

### 1.4 Design consequences already absorbed

- Manual bilge pump is in the spec (§8 of the build spec) even though the
  cockpit is self-draining.
- Anchor spec fixed at 7 kg / 12 mm / 6 mm chain per the §4.7 table.
- Rigging cutter (cizalla) added to inventory — a dismasted rig with no
  backstay still needs cutting free.

## 2. Chile — DIRECTEMAR / Autoridad Marítima

Framework: D.L. 2.222 (Ley de Navegación), D.S. 87/97 + D.S.(M) 214/2015
(Deportes Náuticos), **Circular O-71/010** (construction/inspection of naves
menores), **Circular A-41/014** (equipment for embarcaciones deportivas).

### 2.1 Construction and plan approval — lighter than Argentina

- Registration of naves menores deportivas is at the **Capitanía de Puerto**;
  boats under 5 m sail-only are exempt — at 6.48 m this boat **must register**
  (A-41/014 II.C).
- For an **open (undecked) boat**, O-71/010 Anexo A(C) requires only a **croquis
  with the principal hull data and measurements** plus 4 photos showing name
  and registration on the hull; project review, where sought, is done locally
  by the **SCLINM** (local minor-vessel inspection commission). Formal plan
  sets are for ≥12 m or decked vessels.
- Stability for <12 m: **initial stability only, by rolling-period test** on
  the finished boat (O-71/010 Anexo B.2, per the fishermen's-code Annex III
  method). This is the §10.9 test in the build spec. No paper GZ submission is
  demanded — but ours exists and makes the inspection conversation short.
- **Certificado de Navegabilidad** after inspection; 6-year validity for
  deportivas menores (A-41/014 II.D) with the owner responsible for keeping
  equipment current.

### 2.2 Classification and the two flags to manage

- Likely classification: **Bahía (vela)** or **Costera 12 MN** depending on
  where the client sails. Equipment differs sharply (below).
- **Ballast must be permanently installed** (A-41/014 II.K.1). A pivoting keel
  bolted through cheek plates qualifies; **pumpable water ballast is arguably
  not "permanent"** — this is the one genuine regulatory friction point in the
  design. Position it to the Capitanía as trimming/ballast *tanks* integral to
  the structure (they are welded-in bench tanks, not portable weights), with
  the operating rule documented. Get this agreed **before** the build, in
  writing. Fallback if refused: the boat floats on its lines with tanks empty;
  ballast function is then windward trim only, or tanks get filled and sealed
  permanently at a reduced 120 kg (which restores the original Flow-19 spec).
- **Sails**: no furling main → main must reef ≥40% of luff (A-41/014 II.M) —
  the 2 reef rows in the build spec §2 satisfy this. Furling jib satisfies the
  headsail clause.
- Sail-powered costeras must carry an **auxiliary motor** (II.H) — the electric
  outboard satisfies it; note II.H.2: if the motor is inoperative, coastal
  boats are limited to 12 MN.

### 2.3 Equipment (A-41/014 Anexo A)

**Bahía Vela** (protected-water sailing): lifejackets for all (ISO 12402-4,
100 N), cell phone in waterproof case, alternative bailing system, compass (R),
anchor per design, lifejackets worn **at all times** in bahía class (II.L.8).

**Costera 12 MN** adds: VHF with DSC (portable acceptable), GPS, 150 N
lifejackets (ISO 12402-3), harnesses, 2+2 flares, extinguisher, manual bilge
pump, charts, lifebuoy with light, first-aid kit per Anexo B, compass and
corredera mandatory, EPIRB replaceable by satellite tracker (II.G.2).

Life raft: only required for costeras **outside bay limits** (II.L.1) — for
12 MN operation plan on carrying one or staying classified Bahía.

### 2.4 Registration papers

Owner must be Chilean (or per Ley de Navegación art. 11 conditions); sail
number certificate from the **Federación de Vela de Chile**; title documents;
name + registration painted per II.E (amuras: port abbreviation + number,
aletas: name, espejo: home port) — the 4 photos for the croquis file show
exactly this.

## 3. The cross-border summary

| | Argentina | Chile |
|---|---|---|
| Before building | **Yes** — project + Encomienda + CPIN professional, PNA approval | No (open boat <12 m: croquis + local SCLINM at most) |
| During building | Supervision by registered professional | Optional SCLINM supervision on request |
| After building | Construction certificate → REJU/REY registration | Roll test + inspection → matrícula + Cert. de Navegabilidad |
| Stability proof | Calculation memory in the project | **Roll-period test on the water** |
| Water ballast | Part of the approved project | **Negotiate "permanent installation" reading first** |
| Skipper | Timonel de Yate a Vela | Licencia deportiva per class |
| Sail detail | — | Main: ≥40% reefable ✔ (2 reefs) |
| Equipment driver | Ord. 1-18 Anexo A by zone | Circular A-41/014 Anexo A by class |

**Actionable order:** (1) engage the ingeniero naval in Argentina and submit
the project; (2) in parallel, put the water-ballast question to the Chilean
Capitanía in writing; (3) build; (4) roll test — it serves both the Chilean
certificate and the model validation.

## Sources

- [PNA Ordenanza 1-18 (DPSN), Tomo 4 — Régimen de las Actividades Náutico-Deportivas](https://www.ingsa.com.ar/pdf/3a30f2463c14fe25d5865cc30845e51038b6a3d0.pdf) (definitions §1; zones §4.1.2; bilge §4.6; anchor table §4.7; equipment Anexo A; licences §7.2)
- [PNA Ordenanza 4-09 (DPSN)](https://www.argentina.gob.ar/sites/default/files/4-2009-4.pdf) (use authorizations — context only)
- [PNA — Preguntas frecuentes deportes náuticos](https://www.argentina.gob.ar/prefecturanaval/deportesnauticos/preguntas-frecuentes)
- [DIRECTEMAR Circular A-41/014 (2019)](https://www.directemar.cl/directemar/site/docs/20170328/20170328153044/circular_a_41_014_publicada.pdf) (construction reference II.B; inscription II.C; navegabilidad II.D; ballast II.K; sails II.M; equipment Anexo A/B)
- [DIRECTEMAR Circular O-71/010](https://www.directemar.cl/directemar/site/docs/20170130/20170130125617/o71_010_publ.pdf) (plan requirements Anexo A; arqueo/estabilidad Anexo B — roll test for <12 m; open-boat croquis clause)
- [DIRECTEMAR — Inscripción de naves menores deportivas](https://www.directemar.cl/directemar/tramites/inscripcion-de-naves-menores-deportivas)
- [DIRECTEMAR TM-078 — Manual de inscripción de naves](https://www.directemar.cl/directemar/site/docs/20170829/20170829144922/tm_078_actualizado_11_abr_2024.pdf)
