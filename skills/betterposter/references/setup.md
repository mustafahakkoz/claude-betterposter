# Template choice, licence, and toolchain

---

## 1. Which template — and which one to refuse

Use **`betterportraitposter`** (Bradford / Bailo / Morrison). The reason is specific:
`\documentclass[a0paper]` produces **native A0**.

There is a second LaTeX port of #betterposter — Lana Sinapayen's `better_poster.sty`
(`a4paper` plus 4× enlargement at print time). **Evaluated and rejected:** it upscales
raster images 4× and softens them, and it introduces a "print at 400%" step that is
easy to forget at the print shop. Do not recommend it, do not switch to `a4paper`,
and do not design a scaling workaround.

### Licence

**GNU GPL-3.0.** Line 2 of the `.cls` header states it; the upstream repo has no
`LICENSE` file (404). Some sources say CC BY 4.0 — that is **wrong**. Put GPL-3.0 in
your README.

The template has not been updated in years. Expect no upstream fixes; the class is
self-sufficient but you will be patching its behaviour yourself (`class-traps.md`).

### Vendoring

`betterportraitposter.cls` is **not** a CTAN package. Commit it to the repo so the
build does not depend on the TeX distribution:

```bash
curl -sL https://raw.githubusercontent.com/machml/Better-Portrait-Scientific-Poster-Template/master/betterportraitposter.cls \
  -o poster/betterportraitposter.cls
```

---

## 2. Toolchain

### Default: Tectonic

```bash
brew install tectonic          # single binary, NO SUDO
brew install poppler zbar      # required by the checks
tectonic -X compile main.tex
```

**Why Tectonic is the default:** it is a Homebrew *formula*, so it lands in
user-owned `/opt/homebrew` and needs no root. It also resolves and caches LaTeX
packages on demand, so there is no package list to maintain.

### Why MacTeX / BasicTeX cannot be installed from an agent session

They install a `.pkg` into `/Library/TeX`, which requires a root password. With no
passwordless sudo path the attempt **degrades to a dry run**: it prints
`==> Would install 1 cask: basictex`, exits 1, and installs nothing. The failure is
easy to misread as success — `/Library/TeX/Distributions/` will still contain only
empty shells and `brew list --cask` will show no TeX cask.

If the user wants BasicTeX, they run it themselves in their own terminal:

```bash
brew install --cask basictex
export PATH="/Library/TeX/texbin:$PATH"
sudo tlmgr update --self
sudo tlmgr install latexmk tools graphics geometry enumitem setspace xcolor \
                   cmbright lato fontaxes qrcode pgf hyphenat fontspec
```

All 14 names verified to resolve in the tlnet archive. Note the name traps:
`multicol` is **not** a package (it is in `tools`), `tikz` installs as `pgf`, and
`graphicx` as `graphics`.

The Makefile supports both: `make pdf` uses Tectonic, `make pdf TEX=latexmk` uses a
local TeX Live.

---

## 3. QR codes

Generate at build time rather than embedding an image — when the URL changes you fix
one line and recompile.

```latex
\let\qrcodebox\qrcode   % park the class's version
\let\qrcode\relax       % free the name
\usepackage{qrcode}

\newcommand{\posterqr}[2]{%
  \begin{minipage}[c]{0.13\textwidth}%
    {\setlength{\fboxsep}{5mm}\colorbox{white}{%
       \color{black}\qrcode[height=0.5\bottomboxheight]{#1}}}%
  \end{minipage}%
  \begin{minipage}[c]{0.16\textwidth}%
    \fontsize{34}{40}\selectfont\raggedright #2%
  \end{minipage}%
}
```

> ⚠️ **`\color{black}` and the white background are not decoration** — they are the
> difference between a working code and an empty rectangle. `\bottombox` sets
> `\color{\maincolumnfontcolor}` (white), so the package draws white modules on a
> white box while the log still reports
> `Error-correction level increased from M to Q at no cost`. It fails **silently**.
> Black modules on a dark background will not scan either; QR needs a light ground.

- **Keep the URL short.** A long URL makes a denser code with smaller modules.
- `texdoc qrcode` for options — do not guess them.
- **Test from printed output with a real phone.** Scanning off a screen does not
  predict scanning off paper.

---

## 4. Repository hygiene

```bash
curl -sL https://raw.githubusercontent.com/github/gitignore/main/TeX.gitignore > .gitignore
printf '\nmain.pdf\n.DS_Store\n' >> .gitignore
```

Commit the scaffold before writing content — layout work is experimental and you will
want clean reverts. Keep sizing decisions in `figures/*.tex` and placement in
`main.tex` so diffs stay readable.

README should record: the class licence (GPL-3.0), the licence and source of every
third-party asset, and the build command.
