"""Costed resolution options for the self-righting conflict.

trade.py establishes that no single lever gets there. This evaluates specific
*combinations* and reports what each one costs against the stated brief, so the
choice is a decision rather than a guess.

The mechanism worth understanding: a genuinely self-righting open boat gets its
righting moment when inverted from sealed buoyancy that is HIGH when upright --
because high-when-upright is deep-when-inverted, and depth is what generates the
moment. That is exactly how an RNLI lifeboat works: the watertight wheelhouse is
the righting device. This boat has no cabin (bow cuddy only), so a strongly
crowned "turtle" deck is the closest equivalent available to it.

Run:  python3 -m calc.options
"""

from __future__ import annotations

import os

from .params import Design
from .trade import evaluate_case, min_ballast_for_self_righting

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

FIXED_MASS = 536.9  # kg, non-ballast weight from the budget (see report.py s.3)


def run() -> None:
    os.makedirs(OUT, exist_ok=True)
    base = Design()
    lines: list[str] = []

    def say(*parts: object) -> None:
        line = " ".join(str(p) for p in parts)
        print(line)
        lines.append(line)

    say("=" * 78)
    say("RESOLUTION OPTIONS FOR THE SELF-RIGHTING REQUIREMENT")
    say("=" * 78)
    say("")

    # Option B: narrow hull, true self-righting.
    say("-" * 78)
    say("OPTION B -- narrow the hull until it self-rights")
    say("-" * 78)
    for beam in (1.75, 1.80, 1.90):
        need = min_ballast_for_self_righting(base, beam)
        if need is None:
            say(f"  beam {beam:.2f} m : not achievable")
            continue
        disp = FIXED_MASS + need
        say(f"  beam {beam:.2f} m : ballast {need:.0f} kg, displacement {disp:.0f} kg"
            f" ({disp / 750 - 1:+.0%} vs cap), ratio {need / disp:.0%}")
    say("  Cost: loses the 6-abreast cockpit, and busts DIS 750.")

    # Option C: crowned turtle deck -- sealed volume high up.
    say("")
    say("-" * 78)
    say("OPTION C -- crowned 'turtle' deck: sealed buoyancy high when upright")
    say("-" * 78)
    say(f"  {'camber':>8}{'beam':>7}{'ballast needed':>16}{'displacement':>14}")
    for camber, beam in ((0.15, 2.35), (0.25, 2.35), (0.35, 2.35),
                         (0.25, 2.10), (0.35, 2.10)):
        need = min_ballast_for_self_righting(base, beam, deck_camber=camber)
        if need is None:
            say(f"  {camber:>8.2f}{beam:>7.2f}{'not achievable':>16}{'-':>14}")
        else:
            say(f"  {camber:>8.2f}{beam:>7.2f}{need:>16.0f}{FIXED_MASS + need:>14.0f}")
    say("  Cost: a domed deck fights the flat sunbathing foredeck (notes line 44)")
    say("  and the cockpit tent, and raises the boom further.")

    # Option D: deeper body + moderate narrowing.
    say("")
    say("-" * 78)
    say("OPTION D -- deeper canoe body plus moderate narrowing")
    say("-" * 78)
    for beam, ds in ((2.10, 1.30), (2.10, 1.45), (2.00, 1.30), (1.90, 1.20)):
        need = min_ballast_for_self_righting(base, beam, depth_scale=ds)
        sheer = 0.76 * ds
        if need is None:
            say(f"  beam {beam:.2f}, depth x{ds:.2f} (sheer {sheer:.2f} m):"
                f" not achievable below 1400 kg")
        else:
            say(f"  beam {beam:.2f}, depth x{ds:.2f} (sheer {sheer:.2f} m):"
                f" ballast {need:.0f} kg, disp {FIXED_MASS + need:.0f} kg")
    say("  Cost: freeboard grows, windage and trailer height with it.")

    # Option A: masthead buoyancy -- different mechanism, stated for contrast.
    say("")
    say("-" * 78)
    say("OPTION A -- masthead buoyancy (prevents inversion instead of curing it)")
    say("-" * 78)
    b = evaluate_case(base, 204.0, label="baseline")
    say(f"  Baseline as designed: AVS {b.avs:.0f} deg, inverted-stable,"
        f" energy holding it there {b.negative_area:.2f} m.rad")
    say("  A masthead float does not appear on a GZ curve -- it works by making")
    say("  180 degrees unreachable, so the boat stops at roughly the AVS angle")
    say(f"  ({b.avs:.0f} deg) and the crew right it from there with the floor straps")
    say("  already in the brief (notes line 46).")
    say("")
    say("  Sizing: to hold the rig up at ~110 deg the float must displace more")
    say("  than the rig's submerged weight plus a margin. For a 32 kg alloy rig")
    say("  a 45-60 litre masthead float is the usual answer: about 2.5 kg.")
    say("  Cost: 2.5 kg and some windage aloft. Nothing else in the brief moves.")

    say("")
    say("=" * 78)
    say("SUMMARY")
    say("=" * 78)
    say("  A  masthead float      2.5 kg   keeps every other requirement       ")
    say("     -> NOT true self-righting; recovers to ~110 deg, crew right it")
    say("  B  narrow to 1.80 m    +157 kg  loses 6-abreast cockpit, busts DIS")
    say("  C  turtle deck         varies   fights the sunbathing deck + tent")
    say("  D  deeper + narrower   varies   more freeboard, more windage")
    say("")
    say("  Only B, C and D deliver the requirement as literally stated.")
    say("  All three break something else in notes.txt. That is the decision.")

    path = os.path.join(OUT, "options.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWritten to {path}")


if __name__ == "__main__":
    run()
