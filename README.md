# betterposter

A [Claude Code](https://claude.com/claude-code) skill for building and verifying
print-ready **A0/A1/A2 scientific posters** in LaTeX, using the
[#betterposter](https://osf.io/ef53g/) format — one main finding readable at three
metres, small supporting columns, a QR code for detail.

It targets the `betterportraitposter` class, which is capable but **fails silently**:
a build can exit 0 while embedding the wrong fonts, blanking your QR codes, or
spilling onto an invisible second page. This skill documents twelve of those failure
modes and ships tested scripts that catch them.

Every number in it came from measuring a compiled A0 render, not from a spec sheet.

## Install

**As a plugin** (recommended — one command, and you get updates):

```
/plugin marketplace add mustafahakkoz/claude-betterposter
/plugin install betterposter@mustafahakkoz
```

**Or manually**, as a personal skill:

```bash
git clone https://github.com/mustafahakkoz/claude-betterposter.git
ln -s "$PWD/claude-betterposter/skills/betterposter" ~/.claude/skills/betterposter
```

Then just describe what you want — "help me build an A0 poster for my paper", or
"check this poster before I print it". You can also invoke it directly with
`/betterposter`.

## What's inside

| | |
|---|---|
| `SKILL.md` | workflow, and the four traps that silently corrupt a build |
| `references/class-traps.md` | twelve silent failures, with the fix for each |
| `references/design.md` | contrast, typography, content rules, figures, vertical budget |
| `references/class-reference.md` | class API and the geometry arithmetic for A0/A1/A2 |
| `references/setup.md` | template choice, licence, toolchain, QR codes |
| `scripts/check_poster.py` | five pre-print checks, all auto-discovered from `main.tex` |
| `scripts/contrast.py` | WCAG ratios, xcolor mix arithmetic, colour ramps, PDF sampling |
| `assets/main.tex` | a starter that compiles, with every trap pre-fixed |
| `assets/Makefile` | build, watch, clean, check |

### The checks

```
$ python3 scripts/check_poster.py

[OK  ] size      841.0 x 1189.0 mm, 1 page(s)
[OK  ] words     233 prose words (ceiling 250)
[OK  ] figures   worst: 168 ppi (floor 120)
[OK  ] fonts     embedded Lato-Regular, Lato-Bold, Lato-Light, Lato-Black
[OK  ] qr        both codes decode to the right URLs
```

Each one catches something that is otherwise invisible: a phantom blank page, a
raster that is under-resolution *at the size it is actually placed*, the silent
fallback to Latin Modern, and a QR code that renders but will not scan.

Paper size, column width, font cuts and QR URLs are all read out of your `main.tex`,
so the checker runs unmodified on any poster built with this class.

## Requirements

```bash
brew install tectonic poppler zbar
python3 -m pip install Pillow
```

Tectonic is a Homebrew *formula*, so it installs without `sudo`. A local TeX Live
works too: `make pdf TEX=latexmk`.

## Credits

**The #betterposter format is Mike Morrison's.** The idea — one main finding readable
at three metres, supporting detail demoted to a sidebar and a QR code — is his, along
with the original PowerPoint template and the [talk that started it](https://osf.io/ef53g/).
Nothing here improves on that design; this repository only automates building and
checking one.

The LaTeX lineage, all of it other people's work:

| | |
|---|---|
| **Mike Morrison** ([@mikemorrison](https://twitter.com/mikemorrison)) | the #betterposter design and the original PowerPoint template |
| **Rafael Bailo** ([betterposter-latex-template](https://github.com/rafaelbailo/betterposter-latex-template)) | the landscape LaTeX port, `betterposter.cls`, GPL-3.0 |
| **Daniel Bradford** ([Overleaf](https://www.overleaf.com/latex/templates/better-portrait-poster-template/rnfzsnvbhxgr)) | the portrait adaptation this skill targets, `betterportraitposter.cls` |

The `.cls` header names all three. Keep it intact when you vendor the file.

This repository contributes only the layer around them: the measurements, the twelve
documented failure modes, the verification scripts and the Claude Code automation.
The class itself is neither bundled nor modified here.

## Licence

This skill — the starter `main.tex`, both scripts, the Makefile and all the prose — is
**MIT**. See [LICENSE](LICENSE). None of it is derived from the poster class.

**The `betterportraitposter` class is not bundled**, deliberately. The skill tells you
to `curl` it into your own project instead. Line 2 of the `.cls` header says
**GNU GPL-3.0**, as does Bailo's landscape class that it is built on; the Overleaf
listing for the same template records CC BY 4.0. The two disagree. The header travels
with the file you actually vendor, so treat the class as GPL-3.0 and say so in your
poster's README.

Bradford has no public GitHub repository, so the skill fetches the class from
[machml/Better-Portrait-Scientific-Poster-Template](https://github.com/machml/Better-Portrait-Scientific-Poster-Template),
a third-party re-upload carrying no `LICENSE` file. The
[Overleaf template page](https://www.overleaf.com/latex/templates/better-portrait-poster-template/rnfzsnvbhxgr)
is the canonical source.

## Contributing

Corrections are welcome, especially measured ones. If you find a claim here that your
own render contradicts, please open an issue with the measurement — that is how every
number in this skill got here.
