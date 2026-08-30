# `betterportraitposter` — the twelve silent failures

Every one of these was found in a real compile. **None of them raises an error.**
Each produces a wrong PDF while the build reports success.

Read this before debugging any unexplained spacing, font, or layout behaviour.

---

## 1. A clean compile does NOT prove the fonts resolved

The class's load order breaks under XeTeX (i.e. under Tectonic):

```latex
\RequirePackage{cmbright}
\RequirePackage[default]{lato}     % pulls in fontspec => TU encoding
\RequirePackage[T1]{fontenc}       % then asks for T1 anyway
```

You get `LaTeX Font Warning: Font shape 'TU/cmbr/m/n' undefined` and a **silent
fallback**: neither Lato nor CM Bright is embedded, only Latin Modern Sans.
Exit code 0.

```latex
\usepackage{fontspec}
\setsansfont{Lato}[
  Extension = .ttf, UprightFont = *-Regular, ItalicFont = *-Italic,
  BoldFont  = *-Bold, BoldItalicFont = *-BoldItalic,
]
\renewcommand{\familydefault}{\sfdefault}
```

**The check is `pdffonts main.pdf`, not the exit code.** The signature of the
failure is any `LMSans*` in the output. Automated by `check_poster.py --only fonts`.

## 2. `\newfontfamily` does not inherit `Ligatures=TeX`

`\setsansfont` gets the tex-text mapping by default; `\newfontfamily` does not.
Without it, apostrophes print as straight typewriter quotes and `--` stays two
hyphens. Add it explicitly to **every** `\newfontfamily`:

```latex
\newfontfamily\displayfont{Lato}[
  Extension = .ttf, UprightFont = *-Light, BoldFont = *-Black,
  Ligatures = TeX,
]
```

## 3. `\fontsizemain` is 116/220 — a 190% leading

On a two-line display headline this leaves ~70 mm between the lines and pushes the
first line off the top of the page. At display size the correct ratio is ~1.14:

```latex
\renewcommand{\fontsizemain}{\fontsize{116}{132}\selectfont}
```

## 4. A font-size group must contain its own `\par`

`\baselineskip` is read **at `\par` time**. If the group closes first, the lines are
set on the outer leading — which, given trap 3, is enormous.

```latex
{\fontsize{48}{62}\selectfont ...text...\par}   % \par INSIDE — correct
{\fontsize{48}{62}\selectfont ...text...}\par   % outer leading applies — wrong
```

## 5. `\bottombox` injects space on both sides of its argument

Its definition wraps `#1` in newlines. At `\fontsizesection`'s 48 pt that is
**8.4 mm** per side. If the content uses `\hfill`, the slack is already spent and it
overflows the right margin. Wrap the content:

```latex
\bottombox{\begin{minipage}{0.97\linewidth}...\end{minipage}}
```

## 6. A full-width band belongs INSIDE `\centerbox`

Content after `\end{multicols}` but still inside `\centerbox` spans the full inner
width. Opening a second `\centerbox` is wrong — it draws a second horizontal rule.

```latex
\centerbox{%
  \begin{multicols}{3} ... \end{multicols}
  \section{Results}
  \begin{minipage}[b]{0.63\textwidth} ... \end{minipage}\hfill
  \begin{minipage}[b]{0.30\textwidth} ... \end{minipage}
}
```

## 7. `minipage[t]` aligns first BASELINES, not tops

If two minipages hold different content types (say a `tikzpicture` and an image),
their first baselines do not correspond and one drops tens of mm below the other.
The band's height becomes `top-of-highest → bottom-of-lowest`, not `max(content)`.

**Measured case:** 234 mm of content occupied 277 mm. Switching to `[b]`
(align last baselines) recovered 44 mm.

Use `[b]` when the visual intent is "sit these on a common floor".

## 8. `minipage[t]` is a `\vtop` — its first element must be a BOX

A `\vtop` takes its height from the first box in its vertical list. If the content
begins with a whatsit such as `\color`, the height is 0 and everything drops by one
line. This is the cause of mysterious one-line offsets between columns.

```latex
\begin{minipage}[t]{...}\leavevmode\color{...}...
```

`\leavevmode` supplies the carrier box.

## 9. `\rlap` zeroes width, not height

To hang an image outside the line without disturbing line spacing you need both:

```latex
\rlap{\hspace{48mm}\raisebox{0pt}[0pt][0pt]{\includegraphics[...]{...}}}
```

With `\rlap` alone the image's height inflates the line box and TeX spreads the
lines apart to avoid a collision it thinks exists.

## 10. The phantom blank page

`margin=0in` makes `\textheight` the full paper height, and `\bottombox`'s `\vfill`
pins the footer to the edge. The page finishes ~1 mm short of full and the residual
glue spills onto a second, **inkless** page. `pdfinfo` reports 2 pages; page 2 is empty.

> **Never add negative space at the end.** Because `\bottombox` begins with `\vfill`,
> any negative space after it is absorbed by the `\vfill` stretching further: the
> footer is pushed below the page edge, its bottom strip is clipped, and correctly
> centred content inside it appears bottom-heavy.

**The correct fix is to shrink the box so the page never overflows:**

```latex
\setlength{\bottomboxheight}{0.085\paperheight}   % instead of 0.10
```

Multipliers inside the footer are relative to `\bottomboxheight`, so scale them
inversely if you want the QR and logo to keep their physical size.

## 11. `\section` prepends `\vspace{2em}` to every heading

At 48 pt that is **34 mm** each — 136 mm across four headings, which a figure-heavy
poster does not have.

```latex
\renewcommand{\section}[1]{%
  \vspace{0.7em}{\fontsizesection\selectfont\textbf{\leavevmode #1}}\\[0.25em]}
```

(`\leavevmode` here for the same reason as trap 8.)

## 12. `\qrcode` name clash

The class defines `\newcommand{\qrcode}[3]` (places ready-made images); the `qrcode`
package defines `\qrcode[opts]{text}` (draws from a URL at build time). Loading the
package after the class errors on the redefinition.

```latex
\let\qrcodebox\qrcode   % keep the class's version under a new name
\let\qrcode\relax       % free the name — \@ifdefinable permits redefining \relax
\usepackage{qrcode}
```

---

## Bonus: two more that are not the class's fault

**`\PassOptionsToPackage` before `\documentclass`.** The class does a bare
`\RequirePackage{xcolor}`, so `\usepackage[dvipsnames]{xcolor}` later is an option
clash. Pass options ahead of the class:

```latex
\PassOptionsToPackage{dvipsnames}{xcolor}
\documentclass[a0paper,fleqn]{betterportraitposter}
```

**`\marginvertical` is dead code.** The class defines it (`0.07\paperheight`) and
never uses it. Vertical rhythm comes from `\vspace` inside `\titlebox`/`\centerbox`
and the `\vfill` in `\bottombox`. Do not plan around it.

---

## Expected warnings — do NOT chase these

A **correct** build of this class still emits three overfull warnings. They were
present in a finished, verified, print-ready poster:

```
Overfull \hbox (11.12pt too wide)   -- \mainfinding's tabular cell
Overfull \hbox (22.384pt too wide)  -- \bottombox, twice
```

The 22.384 pt is exactly the two spaces `\bottombox` injects around its argument
(trap 5): 2 × 11.192 pt. The 11.12 pt is the equivalent in `\mainfinding`'s
`tabular` wrapper. Neither affects the rendered page.

Time spent trying to eliminate them is wasted. **The checks that matter are
`check_poster.py`'s five**, not the warning count.

What is *not* expected, and does mean something is wrong:

- `LaTeX Font Warning: Font shape 'TU/cmbr/...' undefined` → trap 1
- any `LMSans` / `LMMono` / `cmbr` font actually **embedded** in the PDF
  (`pdffonts`) → a fallback happened. On a poster the usual causes are math mode
  (`$...$` pulls cmbright's math fonts) and `\texttt` with no `\setmonofont`.
  Avoid both: equations do not survive being read at two metres anyway.
