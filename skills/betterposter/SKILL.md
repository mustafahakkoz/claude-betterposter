---
name: betterposter
description: "Build or audit a print-ready A0/A1/A2 portrait scientific poster in LaTeX using the #betterposter format (betterportraitposter class). Covers scaffolding, layout budgeting, colour contrast, typography, figure resolution, QR codes, and pre-print verification. Use when the user is making a conference or scientific poster, mentions betterposter / betterportraitposter / 'big finding' poster design, wants an A0 poster built or reviewed, or needs to verify a poster PDF before sending it to print."
---

# #betterposter — A0/A1/A2 portrait

The format: one **main finding** readable at 3 metres, small supporting columns,
a QR code for detail. Nobody reads the wall at a poster session. The poster's job
is to *stop* someone walking past; depth comes from the presenter's mouth or from
behind the QR.

**Every number in this skill came from measuring a real compiled A0 render.**
When something disagrees with the `.cls` you have, the `.cls` wins — versions drift.
But the traps in `references/class-traps.md` are about the class's *behaviour*, and
if one of those bites, measure before you diagnose.

---

## Two entry points

This skill's bundled files (`references/`, `scripts/`, `assets/`) sit in the skill's
own directory, available as `${CLAUDE_SKILL_DIR}`. Paths below are relative to it —
copy `scripts/` and `assets/` into the poster project as noted.

**A. Building a new poster** → follow the workflow below.

**B. Auditing an existing poster** → jump straight to
`python3 scripts/check_poster.py --root <dir>`, then read
`references/class-traps.md` for anything it flags.

---

## Workflow

### 1. Scaffold

```
poster/
├── main.tex
├── betterportraitposter.cls   # vendored, committed
├── figures/                   # one .tex wrapper per figure
├── assets/                    # image files (PDF preferred, PNG accepted)
├── scripts/
├── Makefile
├── .gitignore
└── README.md
```

```bash
curl -sL https://raw.githubusercontent.com/machml/Better-Portrait-Scientific-Poster-Template/master/betterportraitposter.cls \
  -o poster/betterportraitposter.cls
curl -sL https://raw.githubusercontent.com/github/gitignore/main/TeX.gitignore > poster/.gitignore
printf '\nmain.pdf\n.DS_Store\n' >> poster/.gitignore
```

Copy `assets/Makefile` and `assets/main.tex` from this skill as the starting point —
the skeleton already has every trap in §3 pre-fixed. Copy `scripts/check_poster.py`
and `scripts/contrast.py` into the project's `scripts/`.

`git init` and commit the scaffold **before** writing content. Layout work is
experimental and you will want to revert cleanly.

**Why each figure gets its own `.tex`:** sizing and cropping decisions live in the
figure file, placement lives in `main.tex`. Diffs stay readable and you can re-size
one figure without touching the layout.

### 2. Toolchain

Default to **Tectonic**. It is a Homebrew *formula*, so it installs into
user-owned `/opt/homebrew` with **no sudo**:

```bash
brew install tectonic
brew install poppler zbar    # required by the checks — without them there is no verification
```

MacTeX and BasicTeX install a `.pkg` into `/Library/TeX` and need a root password.
**They cannot be installed from an agent session**: the attempt degrades to a dry run,
prints `==> Would install 1 cask`, exits 1, and installs nothing. If the user wants
BasicTeX, they must run it in their own terminal — see `references/setup.md`.

### 3. Write the preamble — the non-negotiables

These four are the ones that produce a *silently wrong* PDF. The full list of twelve
is in `references/class-traps.md`; read it before debugging any layout oddity.

**Fonts do not survive the class's load order under XeTeX.** The class does
`cmbright` → `lato[default]` (which pulls fontspec, giving TU encoding) → `[T1]{fontenc}`.
Result: `TU/cmbr` undefined, silent fallback to Latin Modern, exit code 0. Re-assert
the font explicitly:

```latex
\usepackage{fontspec}
\setsansfont{Lato}[
  Extension = .ttf, UprightFont = *-Regular, ItalicFont = *-Italic,
  BoldFont  = *-Bold, BoldItalicFont = *-BoldItalic,
]
\renewcommand{\familydefault}{\sfdefault}
```

> **A clean compile does not prove the fonts resolved. `pdffonts` does.**

**`\fontsizemain` ships as 116/220** — a 190% leading that pushes a two-line headline
off the top of the page. At display size the right ratio is ~1.14:

```latex
\renewcommand{\fontsizemain}{\fontsize{116}{132}\selectfont}
```

**A font-size group must contain its own `\par`.** `\baselineskip` is read at `\par`
time, so `{\fontsize{48}{62}\selectfont text}\par` sets the text on the *outer* leading.

**QR codes need `\color{black}` and a light background.** `\bottombox` sets
`\color{\maincolumnfontcolor}` (white), so the package draws white-on-white while the
log still reports success. Use the `\posterqr` wrapper in `assets/main.tex`.

### 4. Content

Two rule sets; the tighter one wins.

- **NYU Libraries**: 300–800 words, readable at 3 m, name + affiliation +
  acknowledgments required, images ≥120 ppi at print size.
- **betterposter** (binding): **150–250 words**, main finding is **one sentence**,
  jargon-free, key terms emphasised, 3 short supporting blocks, **2–3 figures**, QR.

Poster copy is written from scratch — paper text never transfers. Cutting a section
entirely beats shortening it.

**Validate every claim against your own table.** An abstract's phrasing is often
stronger than the data supports; on a poster that sentence stands alone in front of
someone who just read your table. A countable framing ("best in 4 of the 5 conditions tested") is almost
always more defensible than an average-improvement claim.

**Leave no dangling reference.** "As reported in the paper" has no antecedent on a
poster — the reader has not read it. State the criterion directly.

### 5. Colour

**Measure the contrast; never trust the name.** `PineGreen` is a *bright* green —
2.47:1 against white, below even the 3:1 large-text floor. Darkening preserves the
hue identity: `PineGreen!65!black` → 5.39:1.

```bash
python3 scripts/contrast.py --mix 'PineGreen!65!black'
python3 scripts/contrast.py --ramp 'PineGreen!65!black' --steps 7
```

Thresholds: body text **4.5:1**, large text (≥18pt, or ≥14pt bold) **3:1**.
Details, ramp construction, and categorical palettes: `references/design.md`.

### 6. Figures

Rasters must be ≥120 ppi **at the size they are actually placed** — not at nominal
column width, because a height-driven figure is not column-width. Best practice is
to sidestep resolution entirely: export plots as PDF (`savefig('x.pdf')`), where ppi
does not exist.

Give every figure wrapper the **same** opening vertical space, or inter-column
spacing will not match. `\begin{center}` is a trivlist and adds `\topsep` twice;
a bare `tikzpicture` adds nothing. Normalise:

```latex
{\centering\includegraphics[...]{...}\par}
\newcommand{\figgap}{\par\vspace{\baselineskip}}
```

### 7. Verify before printing

```bash
make check      # or: python3 scripts/check_poster.py
```

Five checks, each catching a failure that is **silent**:

| check | catches |
|---|---|
| `size` | wrong paper size, or a phantom second page |
| `words` | prose over the 250-word ceiling |
| `figures` | a raster under 120 ppi at its real placed size |
| `fonts` | the silent Latin Modern fallback |
| `qr` | a QR that exists but does not scan |

Then the checklist in `references/design.md` §Checklist — including the items only a
human can close: logo permissions, licences, and scanning the QR from **printed**
output with a real phone.

---

## Reference files

Read these on demand; do not preload them.

| file | when |
|---|---|
| `references/class-traps.md` | **any** unexplained layout, spacing, or font behaviour — 12 silent failures |
| `references/class-reference.md` | class API: macros, lengths, colours, and the geometry arithmetic |
| `references/design.md` | contrast, typography, content rules, figures, vertical budget, final checklist |
| `references/setup.md` | template choice and licence, toolchain install, verified package list |

## Bundled scripts

| script | use |
|---|---|
| `scripts/check_poster.py` | all five pre-print checks; auto-discovers paper size, fonts and QR URLs from `main.tex` |
| `scripts/contrast.py` | WCAG ratios, xcolor mix arithmetic, and perceptually even colour ramps |

## Bundled assets

| file | use |
|---|---|
| `assets/main.tex` | starter preamble + layout with all known traps pre-fixed |
| `assets/Makefile` | build, watch, clean, and the check targets |

---

## Measurement discipline

When a layout question comes up, measure the render — do not reason about it.

```python
from PIL import Image
import numpy as np
a = np.asarray(Image.open('page.png').convert('RGB'))
H, W, _ = a.shape
mmy = lambda p: p / H * 1189      # A0 portrait
mmx = lambda p: p / W * 841
ink = a.min(axis=2) < 248
```

- **Check the measurement window.** A crop in the wrong place silently measures
  something else. If a number will not move, you are probably looking at the wrong region.
- **Colour masks over-capture.** Bound the band before hunting for a hue.
- **When a measurement refutes a hypothesis, change the diagnosis — not the fix.**
  One symptom can have several causes, and fixing the wrong one changes nothing.
  If a change does nothing, revert it.
