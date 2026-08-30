#!/usr/bin/env python3
"""Pre-print verification for a betterportraitposter build.

Five checks, each catching a failure that is otherwise SILENT — the build exits 0
and the PDF looks plausible:

  size     wrong paper size, or a phantom blank second page
  words    prose over the #betterposter ceiling
  figures  a raster under 120 ppi at the size it is ACTUALLY placed
  fonts    the class's silent fallback to Latin Modern under XeTeX
  qr       a QR code that renders but does not decode

Everything is discovered from main.tex — paper size, font cuts, QR URLs, column
count — so this runs unmodified on any poster built with this class.

    python3 check_poster.py [--root DIR] [--only fonts,qr] [--ceiling 250]

Needs: poppler (pdfinfo, pdftoppm, pdffonts), zbar (zbarimg), Pillow.
    brew install poppler zbar && pip install Pillow
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PAPER_MM = {"a0paper": (841, 1189), "a1paper": (594, 841), "a2paper": (420, 594)}
INNER_FRAC = 0.9    # \titlebox / \centerbox / \bottombox inset
COLSEP_FRAC = 0.02  # \columnsep
FLOOR_PPI = 120     # NYU poster guideline
TARGET_PPI = 150    # comfortable margin

# Embedding any of these while a custom font was declared IS the silent fallback.
FALLBACK_MARKERS = ("LMSans", "LMRoman", "LMMono", "CMBright", "cmbr")

OK, WARN, FAIL, SKIP = "OK", "WARN", "FAIL", "SKIP"


# --------------------------------------------------------------------------- parsing
def strip_comments(s: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", s)


def inline_inputs(s: str, root: Path, depth: int = 0) -> str:
    if depth > 4:
        return s

    def sub(m):
        name = m.group(1)
        p = root / (name if name.endswith(".tex") else name + ".tex")
        if not p.exists():
            return " "
        return inline_inputs(strip_comments(p.read_text(encoding="utf-8")), root, depth + 1)

    return re.sub(r"\\input\{([^}]+)\}", sub, s)


def paper_size(src: str):
    """(name, W, H) in mm from the \\documentclass options, or (None, None, None)."""
    m = re.search(r"\\documentclass\s*(?:\[([^\]]*)\])?\s*\{[^}]*\}", src)
    if m and m.group(1):
        for opt in (o.strip() for o in m.group(1).split(",")):
            if opt in PAPER_MM:
                return (opt, *PAPER_MM[opt])
    return (None, None, None)


def column_mm(src: str, paper_w: float) -> float:
    """Width of one multicols column, from the class's own geometry."""
    m = re.search(r"\\begin\{multicols\}\{(\d+)\}", src)
    n = int(m.group(1)) if m else 1
    inner = INNER_FRAC * paper_w
    sep = COLSEP_FRAC * paper_w
    return (inner - (n - 1) * sep) / n


def declared_fonts(src: str) -> tuple[str | None, list[str]]:
    """(primary upright cut, all declared cuts) from fontspec declarations."""
    cuts: list[str] = []
    primary = None
    pattern = r"\\(?:setsansfont|setmainfont|setmonofont|newfontfamily\s*\\[a-zA-Z@]+)\s*\{([^}]+)\}\s*\[(.*?)\]"
    for i, m in enumerate(re.finditer(pattern, src, re.S)):
        family, opts = m.group(1).strip(), m.group(2)
        for key, suffix in re.findall(r"(\w*Font)\s*=\s*\*([-\w]+)", opts):
            cut = family + suffix
            cuts.append(cut)
            if key == "UprightFont" and primary is None:
                primary = cut
    return primary, sorted(set(cuts))


def qr_urls(src: str) -> list[str]:
    """URLs passed to any macro whose name contains 'qr' (\\qrcode, \\posterqr, ...)."""
    pat = r"\\[a-zA-Z@]*[qQ][rR][a-zA-Z@]*\s*(?:\[[^\]]*\])?\s*\{(https?://[^}\s]+)\}"
    return sorted(set(re.findall(pat, src)))


# --------------------------------------------------------------------------- prose
ARG_EATERS = ("includegraphics", "colorbox", "definecolor", "colorlet", "setlength",
              "input", "usetikzlibrary", "hspace", "vspace", "raisebox", "qrcode")


def prose_words(src: str, root: Path) -> list[str]:
    """What a reader reads as text. Excludes preamble, figure internals, machinery."""
    s = strip_comments(src)
    body = re.search(r"\\begin\{document\}(.*)\\end\{document\}", s, re.S)
    if body:
        s = body.group(1)
    s = inline_inputs(s, root)
    # figure internals are part of the figure, not body text
    s = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", s, flags=re.S)
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"\\(begin|end)\{[^}]*\}(\{[^}]*\})?", " ", s)
    for cmd in ARG_EATERS:
        s = re.sub(rf"\\{cmd}\*?(\s*\[[^\]]*\])?(\s*\{{[^}}]*\}})*", " ", s)
    s = re.sub(r"\\textcolor\s*\{[^}]*\}", " ", s)     # keep the prose, drop the colour
    s = re.sub(r"\\\\\s*\[[^\]]*\]", " ", s)           # \\[1.5em]
    s = re.sub(r"\\[a-zA-Z@]+\*?(\s*\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\[^a-zA-Z]", " ", s)
    s = re.sub(r"[{}$&~^_]", " ", s)
    s = re.sub(r"(?<![A-Za-z])(mm|cm|pt|em|ex|in|bp|sp)(?![A-Za-z])", " ", s)
    return [w for w in re.split(r"[^A-Za-z\u00C0-\u024F'\-]+", s) if len(w) > 1]


# --------------------------------------------------------------------------- helpers
def need(tool: str, brew: str, allow_missing: bool):
    if shutil.which(tool):
        return None
    msg = f"{tool} not found — install with: brew install {brew}"
    return (SKIP, [msg]) if allow_missing else (FAIL, [msg])


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout


# --------------------------------------------------------------------------- checks
def check_size(ctx):
    if (m := need("pdfinfo", "poppler", ctx["allow_missing"])):
        return m
    out = run(["pdfinfo", str(ctx["pdf"])])
    pages = re.search(r"^Pages:\s+(\d+)", out, re.M)
    dims = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+)", out, re.M)
    if not (pages and dims):
        return FAIL, ["could not read page size from pdfinfo"]

    n = int(pages.group(1))
    w_mm = float(dims.group(1)) * 25.4 / 72
    h_mm = float(dims.group(2)) * 25.4 / 72
    lines = [f"{w_mm:.1f} x {h_mm:.1f} mm, {n} page(s)"]
    status = OK

    name, exp_w, exp_h = ctx["paper"]
    if exp_w and not (abs(w_mm - exp_w) < 1.5 and abs(h_mm - exp_h) < 1.5):
        status = FAIL
        lines.append(f"expected {name} portrait = {exp_w} x {exp_h} mm")
    elif not exp_w:
        lines.append("no a0paper/a1paper/a2paper option found — size not asserted")

    if n != 1:
        status = FAIL
        lines.append("more than one page — check for the phantom blank page "
                     "(class-traps.md #10); page 2 is usually inkless")
    return status, lines


def check_words(ctx):
    words = prose_words(ctx["raw"], ctx["root"])
    n, ceiling = len(words), ctx["ceiling"]
    lines = [f"{n} prose words (ceiling {ceiling})"]
    if n > ceiling:
        lines.append(f"over by {n - ceiling} — cut captions before column copy")
        if ctx["verbose"]:
            lines.append(" ".join(words))
        return FAIL, lines
    if ctx["verbose"]:
        lines.append(" ".join(words))
    return OK, lines


def check_figures(ctx):
    try:
        from PIL import Image
    except ImportError:
        m = "Pillow not installed — pip install Pillow"
        return (SKIP, [m]) if ctx["allow_missing"] else (FAIL, [m])

    root, col_mm = ctx["root"], ctx["col_mm"]
    inner = INNER_FRAC * ctx["paper"][1] if ctx["paper"][1] else None
    sources = [root / "main.tex"] + sorted((root / "figures").glob("*.tex"))
    placed: dict[str, tuple[float, bool]] = {}

    for tex in sources:
        if not tex.exists():
            continue
        src = strip_comments(tex.read_text(encoding="utf-8"))
        for m in re.finditer(r"\\includegraphics\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}", src):
            opts, path = (m.group(1) or ""), m.group(2)
            img = root / path
            if not img.exists() or img.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
                continue
            w_px, h_px = Image.open(img).size
            approx = False
            if (mm := re.search(r"height\s*=\s*([\d.]+)\s*mm", opts)):
                w_mm = float(mm.group(1)) * (w_px / h_px)   # height-driven: derive width
            elif (mm := re.search(r"width\s*=\s*([\d.]+)\s*mm", opts)):
                w_mm = float(mm.group(1))
            elif re.search(r"width\s*=\s*\\(columnwidth|linewidth)", opts):
                w_mm = col_mm
            elif (fr := re.search(r"width\s*=\s*([\d.]+)\s*\\textwidth", opts)) and inner:
                w_mm, approx = float(fr.group(1)) * inner, True
            else:
                continue
            placed[path] = (w_mm, approx)

    if not placed:
        return SKIP, ["no sized raster \\includegraphics found (vector-only is ideal)"]

    lines = [f"{'file':38s}{'px':>7s}{'placed':>10s}{'ppi':>7s}"]
    worst = 1e9
    for path, (mm, approx) in sorted(placed.items()):
        w_px = Image.open(root / path).size[0]
        ppi = w_px / (mm / 25.4)
        worst = min(worst, ppi)
        note = "FAIL" if ppi < FLOOR_PPI else ("thin" if ppi < TARGET_PPI else "")
        if approx:
            note = (note + " ~approx").strip()
        lines.append(f"{path:38s}{w_px:7d}{mm:9.0f}mm{ppi:7.0f}   {note}")
    lines.append(f"worst: {worst:.0f} ppi (floor {FLOOR_PPI})")
    return (OK if worst >= FLOOR_PPI else FAIL), lines


def check_fonts(ctx):
    if (m := need("pdffonts", "poppler", ctx["allow_missing"])):
        return m
    primary, cuts = declared_fonts(ctx["raw"])
    if not cuts:
        return SKIP, ["no fontspec font declared in main.tex — "
                      "the class's own load order is unreliable under XeTeX "
                      "(class-traps.md #1)"]

    out = run(["pdffonts", str(ctx["pdf"])])
    embedded = out
    lines, status = [], OK

    fell_back = [f for f in FALLBACK_MARKERS if f in embedded]
    if fell_back:
        status = FAIL
        lines.append(f"SILENT FALLBACK: {', '.join(fell_back)} embedded although "
                     f"{primary or cuts[0]} was declared")
        lines.append("causes, in order of likelihood: (a) the class's font load "
                     "order under XeTeX (class-traps.md #1); (b) math mode, which "
                     "pulls cmbright math fonts -- avoid $...$ on a poster; "
                     "(c) \\texttt without \\setmonofont")

    missing = [c for c in cuts if c not in embedded]
    present = [c for c in cuts if c in embedded]
    for c in present:
        lines.append(f"embedded  {c}")
    if primary and primary in missing:
        status = FAIL
        lines.append(f"MISSING primary upright cut {primary}")
    for c in missing:
        if c != primary:
            if status != FAIL:
                status = WARN
            lines.append(f"declared but not embedded: {c} "
                         "(unused, or the weight silently downgraded)")
    return status, lines


def check_qr(ctx):
    if (m := need("pdftoppm", "poppler", ctx["allow_missing"])):
        return m
    if (m := need("zbarimg", "zbar", ctx["allow_missing"])):
        return m
    want = qr_urls(ctx["raw"])
    if not want:
        return SKIP, ["no literal URL passed to a *qr* macro in main.tex — "
                      "if the URLs come from a macro, scan the print by hand"]

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(ctx["dpi"]), "-png", "-f", "1", "-l", "1",
                        str(ctx["pdf"]), f"{td}/page"], capture_output=True)
        pngs = sorted(Path(td).glob("page*.png"))
        if not pngs:
            return FAIL, ["pdftoppm produced no render"]
        got = sorted(set(filter(None, run(
            ["zbarimg", "--quiet", "--raw", str(pngs[0])]).splitlines())))

    lines = []
    missing = [u for u in want if u not in got]
    extra = [u for u in got if u not in want]
    for u in want:
        lines.append(("decoded  " if u in got else "NOT FOUND  ") + u)
    for u in extra:
        lines.append("unexpected code decoded: " + u)
    if missing:
        lines.append(f"a code that does not decode at {ctx['dpi']} dpi will not scan "
                     "in print — check \\color{black} and a light background "
                     "(class-traps.md #12)")
        return FAIL, lines
    return (WARN if extra else OK), lines


CHECKS = {"size": check_size, "words": check_words, "figures": check_figures,
          "fonts": check_fonts, "qr": check_qr}


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="project directory (default: cwd)")
    ap.add_argument("--tex", default="main.tex")
    ap.add_argument("--pdf", default=None, help="default: <tex> with .pdf")
    ap.add_argument("--only", default="", help="comma-separated subset of "
                    + ",".join(CHECKS))
    ap.add_argument("--ceiling", type=int, default=250, help="prose word ceiling")
    ap.add_argument("--dpi", type=int, default=150, help="render dpi for the QR check")
    ap.add_argument("--allow-missing-tools", action="store_true",
                    help="downgrade a missing poppler/zbar/Pillow to SKIP instead of FAIL")
    ap.add_argument("-v", "--verbose", action="store_true", help="dump counted words")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    tex = root / a.tex
    pdf = root / (a.pdf or Path(a.tex).with_suffix(".pdf").name)
    if not tex.exists():
        print(f"no {tex}", file=sys.stderr)
        return 2

    raw = strip_comments(tex.read_text(encoding="utf-8"))
    name, w, h = paper_size(raw)
    ctx = {"root": root, "pdf": pdf, "raw": raw, "paper": (name, w, h),
           "col_mm": column_mm(raw, w) if w else 241.1, "ceiling": a.ceiling,
           "dpi": a.dpi, "verbose": a.verbose,
           "allow_missing": a.allow_missing_tools}

    selected = [c.strip() for c in a.only.split(",") if c.strip()] or list(CHECKS)
    unknown = [c for c in selected if c not in CHECKS]
    if unknown:
        print(f"unknown check(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    pdf_needed = {"size", "figures", "fonts", "qr"} & set(selected)
    if pdf_needed and not pdf.exists():
        print(f"no {pdf} — run the build first", file=sys.stderr)
        return 2

    print(f"{tex.name} -> {pdf.name}"
          + (f"   [{name}, column {ctx['col_mm']:.0f} mm]" if name else ""))
    print()

    worst = OK
    rank = {OK: 0, SKIP: 1, WARN: 2, FAIL: 3}
    for key in selected:
        status, lines = CHECKS[key](ctx)
        print(f"[{status:4s}] {key}")
        for ln in lines:
            print(f"        {ln}")
        print()
        if rank[status] > rank[worst]:
            worst = status

    print(f"result: {worst}")
    return 1 if worst == FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
