#!/usr/bin/env python3
"""WCAG contrast, xcolor mix arithmetic, and perceptually even colour ramps.

A colour's NAME guarantees nothing about its contrast. This resolves the actual
sRGB value, measures it, and — for a stage ramp — tells you at which step white
text becomes legal instead of leaving you to guess.

    contrast.py --ratio '#007C1B'                  # vs white and black
    contrast.py --ratio '#007C1B' --on '#FFFFFF'
    contrast.py --mix 'PineGreen!65!black'         # resolve an xcolor expression
    contrast.py --ramp 'PineGreen!65!black' --steps 7
    contrast.py --sample main.pdf                  # measure the REAL rendered colours
    contrast.py --selftest

Thresholds: body text 4.5:1 · large text (>=18pt, or >=14pt bold) 3:1.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Only colours whose values are certain: the five defined in betterportraitposter.cls
# (read out of the class) plus PineGreen, whose cmyk is confirmed by the RGB it
# renders to. For any other xcolor name, pass hex or use --sample.
NAMED_RGB = {
    "white": (255, 255, 255), "black": (0, 0, 0),
    "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
    "imperialblue": (0, 62, 116),      # class
    "empirical": (0, 77, 64),          # class default main colour
    "theory": (26, 35, 126),           # class
    "methods": (140, 22, 22),          # class
    "intervention": (255, 213, 79),    # class
}
NAMED_CMYK = {
    "pinegreen": (0.92, 0.0, 0.59, 0.25),
}


# ------------------------------------------------------------------ colour maths
def cmyk_to_rgb(c, m, y, k):
    """xcolor's subtractive conversion: R = 1 - min(1, c+k)."""
    return tuple(round(255 * (1 - min(1.0, v + k))) for v in (c, m, y))


def parse_color(s: str):
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    if re.fullmatch(r"\d+\s*,\s*\d+\s*,\s*\d+", s):
        return tuple(int(v) for v in s.split(","))
    key = s.lower()
    if key in NAMED_RGB:
        return NAMED_RGB[key]
    if key in NAMED_CMYK:
        return cmyk_to_rgb(*NAMED_CMYK[key])
    raise SystemExit(
        f"unknown colour '{s}'. Known names: {', '.join(sorted(set(NAMED_RGB) | set(NAMED_CMYK)))}.\n"
        "For any other xcolor name pass hex (#RRGGBB), or measure the real one "
        "with --sample <pdf>."
    )


def mix(expr: str):
    """Resolve an xcolor expression: A!p!B, A!p (= A!p!white), or a longer chain."""
    parts = [p.strip() for p in expr.split("!")]
    cur = parse_color(parts[0])
    i = 1
    while i < len(parts):
        pct = float(parts[i])
        other = parse_color(parts[i + 1]) if i + 1 < len(parts) else (255, 255, 255)
        f = pct / 100.0
        cur = tuple(round(f * a + (1 - f) * b) for a, b in zip(cur, other))
        i += 2
    return cur


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    if a < b:
        a, b = b, a
    return (a + 0.05) / (b + 0.05)


def hexs(rgb):
    return "#%02X%02X%02X" % rgb


def uses_cmyk(expr: str) -> bool:
    """True if any term is a cmyk-defined name, whose RENDERED value will differ."""
    return any(t.strip().lower() in NAMED_CMYK for t in expr.split("!"))


CMYK_WARNING = (
    "\n  !! This is the NOMINAL value from the naive cmyk->rgb formula.\n"
    "     A cmyk colour is stored as DeviceCMYK in the PDF and the renderer applies a\n"
    "     proper conversion, so the printed colour differs -- measured on a real build,\n"
    "     PineGreen!65!black is nominally #007C1B (5.39:1) but RENDERS as #396E5D\n"
    "     (5.89:1). Confirm with:  contrast.py --sample <pdf>\n"
    "     RGB-defined colours (\\definecolor{x}{RGB}{...}) are not shifted."
)


def verdict(r):
    if r >= 4.5:
        return "body + large"
    if r >= 3.0:
        return "large only"
    return "FAILS"


# ------------------------------------------------------------------ commands
def show(rgb, label=""):
    w = ratio(rgb, (255, 255, 255))
    k = ratio(rgb, (0, 0, 0))
    print(f"{label}{hexs(rgb)}  rgb{rgb}  L={luminance(rgb):.4f}")
    print(f"    vs white text : {w:5.2f}:1   {verdict(w)}")
    print(f"    vs black text : {k:5.2f}:1   {verdict(k)}")
    print(f"    -> use {'white' if w >= k else 'black'} text on this background")


def cmd_ramp(expr: str, steps: int, lightest: float, darkest: float):
    base = mix(expr)
    # candidates: base!p!white (light half) then base!q!black (dark half)
    cands = []
    for p in range(int(lightest), 101, 1):
        c = tuple(round(p / 100 * a + (1 - p / 100) * 255) for a in base)
        cands.append((f"{expr}!{p}" if p < 100 else expr, c))
    for q in range(99, int(darkest) - 1, -1):
        c = tuple(round(q / 100 * a) for a in base)
        cands.append((f"{expr}!{q}!black", c))

    lums = [luminance(c) for _, c in cands]
    hi, lo = max(lums), min(lums)
    targets = [hi - (hi - lo) * i / (steps - 1) for i in range(steps)]

    print(f"base {expr} = {hexs(base)}")
    if uses_cmyk(expr):
        print(CMYK_WARNING)
    print()
    print(f"{'step':5}{'xcolor':28}{'hex':10}{'white':>8}{'black':>8}   label")
    used = set()
    for i, t in enumerate(targets, 1):
        name, c = min((x for x in cands if x[0] not in used),
                      key=lambda x: abs(luminance(x[1]) - t))
        used.add(name)
        w, k = ratio(c, (255, 255, 255)), ratio(c, (0, 0, 0))
        pick = "white" if w >= k else "black"
        flag = "" if max(w, k) >= 4.5 else "  <- under 4.5:1"
        print(f"S{i:<4}{name:28}{hexs(c):10}{w:8.2f}{k:8.2f}   {pick}{flag}")
    print("\nWhite text needs the background at L <= 0.183 to reach 4.5:1.")
    print("If white should start earlier, darken the WHOLE ramp — recolouring one")
    print("node breaks the even spacing and does not fix the contrast.")


def cmd_sample(pdf: Path, dpi: int, top: int):
    for tool in ("pdftoppm",):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found — brew install poppler")
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow not installed — pip install Pillow")

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", "1", "-l", "1",
                        str(pdf), f"{td}/p"], capture_output=True)
        pngs = sorted(Path(td).glob("p*.png"))
        if not pngs:
            raise SystemExit("pdftoppm produced no render")
        im = Image.open(pngs[0]).convert("RGB")
        counts = im.getcolors(maxcolors=1 << 24) or []

    total = sum(n for n, _ in counts)
    counts.sort(key=lambda t: -t[0])
    print(f"{pdf.name} at {dpi} dpi — colours by area "
          f"(this is what actually printed, not what you computed)\n")
    shown = 0
    for n, rgb in counts:
        if shown >= top:
            break
        if max(rgb) > 247 and min(rgb) > 247:      # page white
            continue
        pct = 100 * n / total
        if pct < 0.05:
            break
        w, k = ratio(rgb, (255, 255, 255)), ratio(rgb, (0, 0, 0))
        print(f"  {hexs(rgb)}  rgb{str(rgb):18} {pct:5.2f}% of page   "
              f"white {w:5.2f}:1  black {k:5.2f}:1")
        shown += 1


def cmd_selftest():
    """Verified against a measured render, so the arithmetic cannot drift silently."""
    cases = [
        ("PineGreen", (0, 191, 41)),
        ("PineGreen!65!black", (0, 124, 27)),
        ("empirical", (0, 77, 64)),
    ]
    bad = 0
    for expr, want in cases:
        got = mix(expr)
        ok = got == want
        bad += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} {expr:22} -> {got}  expected {want}")
    r = ratio(mix("PineGreen!65!black"), (255, 255, 255))
    ok = abs(r - 5.39) < 0.02
    bad += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} contrast PineGreen!65!black vs white = "
          f"{r:.2f}:1  expected 5.39")
    print("  NOTE nominal != rendered for cmyk colours: PineGreen!65!black is")
    print("       nominally #007C1B but renders #396E5D (5.89:1) -- measured, not derived.")
    r2 = ratio(mix("PineGreen"), (255, 255, 255))
    ok2 = abs(r2 - 2.47) < 0.02
    bad += not ok2
    print(f"  {'OK  ' if ok2 else 'FAIL'} contrast PineGreen vs white = "
          f"{r2:.2f}:1  expected 2.47  (the name promised dark; it is not)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ratio", help="colour to measure (#hex, r,g,b, or a known name)")
    ap.add_argument("--on", help="background to measure against (default: white and black)")
    ap.add_argument("--mix", help="resolve an xcolor expression, e.g. 'PineGreen!65!black'")
    ap.add_argument("--ramp", help="base colour for a ramp")
    ap.add_argument("--steps", type=int, default=7)
    ap.add_argument("--lightest", type=float, default=30, help="lightest mix %% (default 30)")
    ap.add_argument("--darkest", type=float, default=60, help="darkest mix %% toward black")
    ap.add_argument("--sample", help="PDF to sample the real rendered colours from")
    ap.add_argument("--dpi", type=int, default=50)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return cmd_selftest()
    if a.sample:
        cmd_sample(Path(a.sample), a.dpi, a.top)
        return 0
    if a.ramp:
        cmd_ramp(a.ramp, a.steps, a.lightest, a.darkest)
        return 0
    if a.mix:
        show(mix(a.mix), f"{a.mix} = ")
        if uses_cmyk(a.mix):
            print(CMYK_WARNING)
        return 0
    if a.ratio:
        fg = mix(a.ratio) if "!" in a.ratio else parse_color(a.ratio)
        if a.on:
            bg = mix(a.on) if "!" in a.on else parse_color(a.on)
            r = ratio(fg, bg)
            print(f"{hexs(fg)} on {hexs(bg)} = {r:.2f}:1   {verdict(r)}")
        else:
            show(fg)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
