# `betterportraitposter` — class API and geometry

Everything here was read out of the `.cls` and confirmed against a compiled render.
If your copy disagrees, your copy wins.

---

## Class options

```latex
\documentclass[a0paper,fleqn]{betterportraitposter}
```

Paper: `a0paper` · `a1paper` · `a2paper`. All portrait — this class has no landscape
mode, and `\leftbarwidth` / `\rightbarwidth` belong to the landscape template, not
this one.

---

## Geometry — where every number comes from

The class sets `\geometry{margin=0in}`, so **`\textwidth` is the full paper width**.
`\titlebox`, `\centerbox` and `\bottombox` each inset their content to
`0.9\textwidth`, and `\columnsep` is `0.02\textwidth`.

For `multicols{n}`, column width = `(0.9W − (n−1)·0.02W) / n`:

| paper | W × H (mm) | inner (0.9W) | colsep | 2 col | 3 col | 4 col |
|---|---|---|---|---|---|---|
| A0 | 841 × 1189 | 756.9 | 16.82 | 370.0 | **241.1** | 176.6 |
| A1 | 594 × 841 | 534.6 | 11.88 | 261.4 | **170.3** | 124.7 |
| A2 | 420 × 594 | 378.0 | 8.40 | 184.8 | **120.4** | 88.2 |

> Inside a minipage, LaTeX rebinds `\textwidth` to the minipage width. Nested
> fractions are relative to the enclosing box, not to the paper.

## Lengths

| length | default | notes |
|---|---|---|
| `\mainfindingheight` | `0.35\paperheight` | A0 416 mm · A1 294 mm · A2 208 mm |
| `\bottomboxheight` | `0.1\paperheight` | A0 119 mm · A1 84 mm · A2 59 mm |
| `\columnsep` | `0.02\textwidth` | |
| `\marginvertical` | `0.07\paperheight` | **dead code** — the class never uses it |

## Font sizes

| macro | default |
|---|---|
| `\fontsizemain` | 116 pt / **220 leading** — see trap 3 |
| `\fontsizetitle` | 80 pt |
| `\fontsizeauthor` | 48 pt |
| `\fontsizesection` | 48 pt |
| `\fontsizestandard` | 32 pt |

## Colours

Predefined — reusing these keeps a custom palette coherent with the template:

```latex
\definecolor{imperialblue}{RGB}{0,62,116}
\definecolor{empirical}{RGB}{0,77,64}      % the class's DEFAULT main colour
\definecolor{theory}{RGB}{26,35,126}
\definecolor{methods}{RGB}{140,22,22}
\definecolor{intervention}{RGB}{255,213,79}
```

Colour macros — **all take `\renewcommand`** (the class already defined them with
`\newcommand`, so `\newcommand` errors):

| macro | default |
|---|---|
| `\maincolumnbackgroundcolor` | `empirical` |
| `\maincolumnfontcolor` | `white` |
| `\columnbackgroundcolor` | `white` |
| `\columnfontcolor` | `black` |
| `\titlebackgroundcolor` / `\titlefontcolor` | `white` / `black` |
| `\authorfontcolor` / `\institutefontcolor` | `gray` / `gray` |

## Layout macros

`\mainfinding` · `\titlebox` · `\centerbox` · `\bottombox` · `\bottomboxlogo` ·
`\qrcode` · `\compactqrcode` · `\title` · `\author` · `\institution` · `\section`

### `\mainfinding{...}`

Wraps content in `minipage[c][\mainfindingheight][c]` → `\centering` →
`\fontsizemain` → `tabular{p{0.9\textwidth}}`.

**Consequence: inside `\mainfinding`, `\\` is a tabular row break, not a line break.**
Nesting your own `minipage` inside it gives normal paragraph behaviour and is usually
easier to control.

### `\centerbox{...}`

Draws `\hrulefill`, then insets to `0.9\textwidth` with `\vspace{2em}` top and bottom
and a `\vfill` around the content.

A full-width band goes **inside** this same `\centerbox`, after `\end{multicols}` —
see trap 6. A second `\centerbox` draws a second rule.

### `\bottombox{...}`

Begins with `\vfill`, then a `colorbox` in `\maincolumnbackgroundcolor`, insets to
`0.9\textwidth`, sets `\fontsizesection` and `\color{\maincolumnfontcolor}`.

Three consequences, each its own trap: the leading `\vfill` (trap 10), the injected
space around the argument (trap 5), and the white text colour that silently blanks
QR codes (trap 12 / `\posterqr`).

### `\qrcode` / `\compactqrcode` / `\bottomboxlogo`

Class widths: `\qrcode` is 0.12 + 0.12 + 0.36 = **0.60`\textwidth`**, and
`\bottomboxlogo` is **0.30**. That budget fits exactly one QR and one logo.
For two QRs plus logos, build the footer manually — see `assets/main.tex`.

Note `\qrcode` here **places two ready-made images**; it does not generate a code.
To generate from a URL at build time you need the `qrcode` package, which collides
on the name (trap 12).

---

## Verified package list

What is actually loaded, and nothing more.

By the class: `multicol` · `setspace` · `geometry` · `cmbright` · `lato` ·
`fontenc` · `enumitem` · `xcolor` · `graphicx`
(`amsmath` / `amsfonts` / `amssymb` are present but commented out.)

Typically added by `main.tex`: `fontspec` · `hyphenat` · `tikz` · `qrcode`

TeX Live install names — all 14 verified to resolve in the tlnet archive:

```bash
sudo tlmgr install latexmk tools graphics geometry enumitem setspace xcolor \
                   cmbright lato fontaxes qrcode pgf hyphenat fontspec
```

> **`tlmgr install multicol` fails — `multicol` is not a TeX Live package name.**
> `multicol.sty` ships inside `tools`. Likewise `tikz` installs as `pgf` and
> `graphicx` as `graphics`.

Bulk alternative, also verified:

```bash
sudo tlmgr install collection-latexrecommended collection-fontsrecommended \
                   collection-pictures
```

~1 GB, against MacTeX's 6.4 GB.

None of this applies to Tectonic, which resolves and caches packages itself.
