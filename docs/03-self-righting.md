# Self-righting: the trade study

The brief asks for recovery from 180° unaided, in an open boat. This document
shows what that costs. Numbers come from `calc/trade.py` and `calc/options.py`;
raw output is in `out/trade_study.txt` and `out/options.txt`.

---

## 1. The test

A boat self-rights from fully inverted if and only if **GZ stays positive at
every angle up to 180°**. At exactly 180° the righting arm is zero by symmetry,
so the meaningful test is the sign just short of it: negative GZ approaching 180°
means there is a stable inverted equilibrium and the boat stays upside down.

The governing condition is **light ship with the cockpit flooded** — crew are in
the water, so their weight is not helping, and the cockpit is full.

## 2. Baseline result

| | |
|---|---|
| Ballast | 213 kg (28.4% ratio) |
| GZ max | 0.667 m at 46° |
| Downflooding angle | **37°** at full load (1730 kg) |
| AVS | **112°** |
| Stable inverted | **yes** |
| Energy holding it inverted | 0.32 m·rad |

**Not self-righting.** For reference: a Contessa 26 — the benchmark small
self-righting cruiser — has a ~43% ballast ratio, is fully decked, and reaches
AVS ~157°. It is *still* not self-righting from 180°. The RS Aira at 33% and
fully decked is not either.

### A note on which way the model errs

The flooded case removes the cockpit's buoyancy but does not add trapped water as
weight. That is right for a cockpit draining aft through an open transom at
moderate heel — the internal water level is the sea level. At large heel and
inverted, some water would sit above sea level and its weight would push GZ down
further.

Also visible in `out/gz_curves.png`: between roughly 60° and 110° the flooded
curve sits marginally *above* the intact one. That is real, not an error —
losing the cockpit's buoyancy makes the hull float deeper at the same heel, which
brings deck-edge volume on the low side into play and lengthens the righting arm
slightly. It reverses before the zero crossing, so flooded AVS still ends up
marginally below intact.

Both effects mean the model is **optimistic about self-righting**. The boat fails
the test anyway, so the conclusion below is robust in the direction that matters.

## 3. Which levers actually move it

### Ballast alone — no

At 2.35 m beam, adding lead barely helps:

| Ballast | Displacement | Ratio | AVS |
|---|---|---|---|
| 213 kg | 751 kg | 28% | 112° |
| 400 kg | 938 kg | 43% | 126° |
| 600 kg | 1138 kg | 53% | 136° |
| 1000 kg | 1538 kg | 65% | **149°** |

A tonne of lead on a 6.5 m hull, displacing ~1540 kg, still does not get there.
Ballast has strongly diminishing returns against inverted form stability.

### Sealing the cockpit — almost no effect

This is the counter-intuitive one. Fully decking the boat, so the cockpit is
watertight all the way round:

| Ballast | AVS flooded | AVS sealed |
|---|---|---|
| 213 kg | 112.2° | 112.4° |
| 300 kg | 119.6° | 119.9° |
| 400 kg | 126.3° | 126.2° |

**About one degree.** When inverted, light displacement against a large enclosed
volume means the boat floats very high — the cockpit is mostly above water
regardless of whether it is sealed. Narrowing the cockpit to convert floodable
volume into sealed side tanks does nothing measurable either (the cockpit-width sweep
moves AVS by ~1°).

So the common argument — *an open boat can't self-right because it floods* — is
not what is happening here. The boat would not self-right if it were decked.

### Water ballast — the answer depends on tank height

Where the tanks sit decides whether filling them helps or hurts at large heel.
Tanks **under the sole** (centroid z ≈ 0.26) are high above the water when
inverted, so full tanks destabilise the upside-down equilibrium — the RNLI
righting-tank mechanism — worth about +4° of AVS. But the client's decision to
build the tanks **into the bench seats** (centroid z ≈ 0.48, close to the roll
axis) inverts the trade: the upright VCG penalty now dominates.

With bench tanks, light ship + sealed-full tanks, flooded:

| Water aboard | Displacement | AVS |
|---|---|---|
| 0 | 750 kg | 111.0° |
| 250 kg | 1000 kg | 107.3° |
| **500 kg** | 1250 kg | **105.0°** |

So with seats-as-tanks there is **no heavy-weather argument for filling both
tanks** — symmetric fill costs ~6° of AVS and buys only damping. The tanks earn
their keep empty (reserve buoyancy, seats) or filled to windward (~two crew of
righting moment). Either way the effect is single-digit degrees against the ~70°
the requirement needs; it does not change the verdict.

### Beam — this is the constraint

Ballast held at the 213 kg the budget allows:

| Beam | GZ max | AVS | Energy holding inverted |
|---|---|---|---|
| 1.80 m | 0.441 m | **138°** | 0.035 m·rad |
| 1.95 m | 0.503 m | 123° | 0.110 m·rad |
| 2.10 m | 0.583 m | 117° | 0.189 m·rad |
| 2.35 m | 0.667 m | 112° | 0.317 m·rad |
| 2.50 m | 0.716 m | 110° | 0.384 m·rad |

Beam buys upright stiffness (GZ max rises with beam) and pays for it with
inverted stability. That is the same physics, read in both directions.

### The frontier

Minimum ballast for true self-righting, by beam:

| Beam | Ballast needed | Displacement | Ratio |
|---|---|---|---|
| 1.70 m | 383 kg | 920 kg | 42% |
| **1.75 m** | **417 kg** | **954 kg** | **44%** |
| **1.80 m** | **452 kg** | **988 kg** | **46%** |
| 1.90 m | 647 kg | 1184 kg | 55% |
| 2.00 m | 842 kg | 1379 kg | 61% |
| 2.10 m | 1059 kg | 1596 kg | 66% |
| 2.20 m | 1352 kg | 1889 kg | 72% |
| **2.35 m (as designed)** | **not achievable below 1400 kg** | — | — |

The curve is steep — roughly 200 kg of lead per 100 mm of beam above 1.80 m —
and past 2.10 m it runs away entirely. (These thresholds moved up ~90 kg when
the bench-tanks became sealed seats and the single rudder lightened the ends:
verdicts near 180° are sensitive to small changes, which is itself worth
knowing.)

## 4. Four ways to resolve it

### Option A — masthead buoyancy: prevent inversion rather than cure it

A 45–60 litre masthead float (≈2.5 kg) makes 180° unreachable. The boat stops at
roughly the AVS angle (~112°), floats on its side, and the crew right it from
there using the floor straps already in the brief (`notes.txt` line 46,
*cinturones piso xa adrizar quitapon*).

- **Cost: 2.5 kg and some windage aloft. Nothing else in the brief moves.**
- **Does not meet the requirement as literally stated.** It is not self-righting;
  it is inversion-proof plus crew-righted.

### Option B — narrow the hull

1.75–1.80 m beam, 417–452 kg ballast, ~954–988 kg displacement.

- Meets the requirement.
- **Loses the 6-abreast cockpit.** At 1.80 m beam the cockpit is ~1.25 m wide
  inside the side tanks: 4 seated comfortably, 6 only in line.
- **Exceeds `DIS 750` by 27–32%.** At ~990 kg the boat is also past the EU
  750 kg unbraked-trailer threshold, so the trailer needs brakes.
- Sail area needs rechecking: 22 m² on a 1.80 m beam hull with a 46% ballast
  ratio is a stiffer boat but a narrower one, so it will heel earlier.

### Option C — crowned "turtle" deck

Sealed buoyancy that is high when upright is deep when inverted, and depth is
what generates the moment. This is exactly how an RNLI lifeboat self-rights: the
watertight wheelhouse is the righting device. With no cabin, a strongly crowned
deck is the nearest equivalent available.

| Deck camber | Beam | Ballast needed | Displacement |
|---|---|---|---|
| 0.15 m | 2.35 m | not achievable | — |
| 0.25 m | 2.35 m | not achievable | — |
| 0.35 m | 2.35 m | not achievable | — |
| 0.25 m | 2.10 m | not achievable | — |
| 0.35 m | 2.10 m | not achievable | — |

- **It does not work at any camber tested, at 2.35 m or 2.10 m of beam.** A
  crowned deck alone cannot rescue this hull.
- Fights the flat sunbathing foredeck (line 44), the cockpit tent (line 49), and
  raises the boom further.
- **Not recommended.** Listed because it is the mechanism people reach for, and
  it is worth seeing it fail with numbers attached.

### Option D — deeper canoe body plus moderate narrowing

| Beam | Depth | Sheer height | Ballast needed | Displacement |
|---|---|---|---|---|
| 2.00 m | ×1.30 | 0.99 m | 615 kg | 1152 kg |
| 2.10 m | ×1.45 | 1.10 m | 771 kg | 1308 kg |
| 2.10 m | ×1.30 | 0.99 m | 835 kg | 1372 kg |
| 1.90 m | ×1.20 | 0.91 m | 1003 kg | 1540 kg |

- Works, but every configuration is heavier than Option B for the same result.
- Freeboard grows, and windage and trailer height with it. At 1.10 m of sheer
  height a 6.5 m open boat starts to look like a very different vessel.

## 5. Recommendation

**The requirement and the brief are mutually exclusive.** The choice is:

1. **Keep the boat, change the requirement** → Option A. A 2.5 kg masthead float
   gives a boat that cannot invert and that the crew can always right, keeping
   the 6-seat cockpit, 750 kg, 2.35 m beam and 22 m² intact. This is what the
   floor straps in `notes.txt` line 46 already imply, and it is what
   *auto-adrizante* most plausibly meant.

2. **Keep the requirement, change the boat** → Option B at 1.80 m beam. Accept a
   4-seat cockpit and ~990 kg, and get genuine 180° recovery.

Options C and D are dominated by B on every axis.

If the answer is B, the parametric model already carries it:

```
python3 -m geom.hull --self-righting     # 1.80 m beam hull, STL + offsets
```

and the baseline in `calc/params.py` needs `beam_sheer = 1.80` and
`envelope.disp_max = 990`.

## 6. What is *not* in question

Everything else in the brief checks out at the baseline:

- Cockpit self-drains: +56 mm of sole freeboard with 6 crew and 500 L aboard
- Sail area is carryable: 15° steady heel at 20 kt (11° with the windward tank),
  peak righting moment at 32 kt
- Envelope compliance: 0 violations, including 488 L ≤ 500 L water ballast
- Structure: all HDPE panels pass, double-skin, 9.5 kg/m²

The self-righting requirement is the only thing that does not close.
