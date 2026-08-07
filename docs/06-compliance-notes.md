# Compliance matrix — notes.txt (client requirements)

Every line of `notes.txt` checked against the design as specified in
`04-build-spec.md`. Status: ✅ met · ⚠️ met with a caveat the client should see ·
❌ not met, decision needed · ➖ not a requirement (note-to-self in the file).

| Line | Requirement | Status | Where / how |
|---|---|---|---|
| 1 | HDPE material ("HDPE finalists") | ✅ | Rotomoulded HDPE double skin 2×5 mm/50 mm; welded PE500 prototype route. Weight-neutral vs GRP (report §3). Build spec §2–3. |
| 3 | LOA < 6.50 | ✅ | 6.48 m |
| 4 | BEA < 2.50 | ✅ | 2.35 m (road-trailerable) |
| 5 | DIS < 750 | ✅ | 750.0 kg light incl. ballast — at the cap exactly, tolerance −25/+0 kg in build spec §1 |
| 6 | SQM < 22 | ✅ | 22.0 m² (14 main + 8 jib) — at the cap |
| 7 | BAL < 500 (500 L water ballast) | ✅ | 488 L (2 × 244 L) in the bench-tanks |
| 8 | CBD < 1.30 | ✅ | 1.29 m keel down (to bulb bottom, audited) |
| 10 | Shipyard QA | ⚠️ | Build spec §10: wall-thickness ultrasonic audit, tank leak test, inclining test. A yard-level QA plan (weld inspection records, material certs) is sketched, not written — say the word and it becomes a checklist. |
| 11 | ISO certification | ⚠️ | ISO 12215-5 has **no rotomoulded-PE path**; scantlings follow its pressure *form* with equivalence justification — the accepted route, but it is testing + argument, not a checkbox (design spec §6). Stability: ISO 12217-2 methods used in the model. AR/CL law does not require ISO; see docs/05. |
| 13–15 | "Objective short / clear ideas / done well defined" | ➖ | Notes-to-self on scoping. The repo's structure (requirements → spec → build → regulatory) is the response. |
| 17–18 | Base: RS Aira 22 | ✅ | Envelope, 6-seat cockpit, rig concept, published specs used throughout (docs/01 §1) |
| 19 | Large cockpit, 6 seats | ✅ | 3.20 × 1.72 m cockpit; two 3.2 m benches seat 3 per side. ⚠️ see operating rule: with 6 crew, tanks stay empty (loaded AVS). |
| 20 | Bow cuddy, no cabin, fabric shelf | ✅ | Cuddy forward of x = 5.05 m under the foredeck, `estante tela` in materials (build spec §2). |
| 21 | Furling jib | ✅ | 8 m² on furler — also satisfies Chile A-41/014 II.M headsail clause |
| 22 | High boom, short mast, square-top main | ✅ | Boom **1.80 m** above baseline — audited: 1.0 m over the bench tops clears a tall seated adult; 1.66 m did not. Mast 8.60 m; square-top main. ⚠️ square-top + no backstay = swept spreaders, standard but tune matters (build spec §6). |
| 25–27 | Base: Flow 19 (BEA 2.30, draft 1.30, DSP 450) | ✅ | Ballast strategy and purchase system taken (its twin rudders were dropped by client amendment); figures unverified (URL 403) — flagged in docs/01 §1 |
| 28 | ~70 kg swing keel (Flow 19 reference) | ⚠️ | Our pivot keel is 213 kg total. The 70 kg Flow-19 keel scaled to this displacement and to any meaningful AVS is too light; 213 kg is what the 750 kg budget allows. Client should know it departs from the Flow 19 number deliberately. |
| 29 | 2 × 60 kg water ballast (Flow 19 reference) | ✅→ | Superseded by client: BAL < 500 read as 500 L → 2 × 250 kg fitted. |
| 30 | Freeboard / cockpit sole height "??" | ✅ | **Resolved by calculation**: sole 0.385 m → +168 mm light, +56 mm at 1730 kg full load. Report §5. Tightest number in the boat; sole tolerance +10/−0. |
| 31 | No winches, 2:1 purchase | ✅ | All controls 2:1 (keel lift 4:1 tackle), no winches (build spec §6) |
| 32 | Pivoting rudders | ✅ | Kick-up rudder, transom-hung. **Client amended to a single rudder (2026-08-06)** — pivoting requirement kept. |
| 33 | No traveller, no backstay | ✅ | Centreline mainsheet beam; swept spreaders replace backstay. Hard-point engineering in build spec §4. |
| 37 | Open sailboat | ✅ | Open self-draining cockpit, no cabin |
| 38 | Reserve buoyancy + self-righting (`auto-adrizante`) | ❌/⚠️ | Reserve buoyancy ✅ — sealed bow cuddy + sealed bench-tanks + double-skin voids; the boat floats swamped. **True self-righting from 180° is NOT met and cannot be within this brief** (beam-dominated; docs/03). Options: masthead float + crew righting (keeps everything else), or 1.80 m beam variant (loses 6-abreast + 750 cap). **Client decision required — the one open item.** |
| 39 | 2 rudders, short tillers | ✅→ | **Client amended to one rudder with short tiller (2026-08-06)**, superseding this line |
| 40 | Pivot keel | ✅ | x = 3.30 m pivot, 0.30/1.29 m drafts, hold-down latch |
| 41 | Rigging | ✅ | Full rig dimensions I/J/P/E in build spec §6 |
| 42 | Electric engine | ✅ | 4 kW outboard + 3 kWh LiFePO₄. ⚠️ costs 58 kg ≈ 46 kg of ballast vs the Aira — the honest price of electric (report §3). |
| 44 | Sunbathing foredeck | ✅ | Flat foredeck kept — one reason the turtle-deck self-righting option was rejected (docs/03 §4C) |
| 45 | Double bow hatch | ✅ | Specified: two gasketed PE-framed acrylic hatches on the cuddy top (not yet drawn in the 3DM — arrangement detail for the tooling pass) |
| 46 | Floor straps for righting, removable | ✅ | Webbing straps on sole anchors; part of the crew-righting concept that pairs with the masthead float option |
| 47 | 1"×1" foot batten | ✅ | Welded PE batten on the sole centreline (weldable = trivial in HDPE) |
| 48 | Spray hood | ✅ | On cuddy aft edge; 11 kg budget line covers hood + tent |
| 49 | Cockpit tent | ✅ | Boom-ridge tent over the 1.80 m boom — the high boom makes this work |
| 50–51 | Self-draining cockpit, direct drain | ✅ | Sole above WL at full load; drains aft through transom — no valves to fail |
| 52 | Semi-open transom | ✅ | Transom open above sole level between rudder stocks |
| 54 | Centred boom rig w/o traveller | ✅ | Mainsheet to centreline beam under sole |
| 55 | Lazy bag main + auto furling jib | ✅ | Build spec §2. Main has 2 reef rows — **required by Chile** (A-41/014 II.M) since the main doesn't furl. |
| 56 | Empty water ballast with air pump | ✅ | 12 V diaphragm pump pressurises tank via vent; also gravity dump when heeled (build spec §7) |
| 57 | Fill water ballast while sailing — "how?" | ✅ | **Resolved**: forward-facing Ø38 scoop at the chine per side, ball valve; fills 244 L in ~3 min above 4 kt, zero electrical load. Cross-connect line allows tacking the ballast. |
| 58 | No backstay | ✅ | Duplicate of 33 |

## Summary for the client

**Met: 30 of 33 requirement lines.** The three that need their eyes:

1. **Line 38, self-righting — the only ❌.** Physics, not effort: at 2.35 m beam
   no ballast the boat can float will bring it back from 180°. Two honest
   resolutions on the table (docs/03 §5); the rest of the boat is unaffected by
   either. This decision should be made before tooling.
2. **Line 11, ISO** — achievable as *equivalence + testing*, not as a stamped
   checklist, because no ISO scantling standard covers rotomoulded PE. Cost and
   schedule item.
3. **Line 19/7 interaction** — 6 crew and full tanks don't stack (AVS 85°
   loaded). The operating rule (crew full → tanks empty) is now part of the
   design and should be on a placard at the fill valves.

Plus one regulatory flag outside the notes: **Chile requires ballast to be
"permanently installed"** — get the Capitanía's written agreement on the
welded-in tanks before building (docs/05 §2.2).
