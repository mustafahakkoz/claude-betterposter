# Design rules — colour, type, content, figures, space

---

## 1. Colour and contrast

**Measure the contrast of your main colour against white text before committing.**
A colour's *name* guarantees nothing: `PineGreen` is `cmyk(0.92,0,0.59,0.25)`, a
bright green, **2.47:1** against white — below even the 3:1 large-text floor. Do not
assume a name that sounds dark is dark.

Darkening preserves the hue identity: `PineGreen!65!black` → **5.39:1** nominal.

**Thresholds:** body text **4.5:1** · large text (≥18 pt, or ≥14 pt bold) **3:1**.
Poster labels are nearly always large text, but clearing 3:1 by a hair is a real
legibility loss — measure it and say what you measured.

```bash
python3 scripts/contrast.py --mix 'PineGreen!65!black'   # ratio vs white and black
python3 scripts/contrast.py --ratio '#007C1B' --on white
```

The maths, if you need it inline:

```python
def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
def L(r, g, b):   return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)
def ratio(fg, bg):
    a, b = L(*fg), L(*bg)
    if a < b: a, b = b, a
    return (a + 0.05) / (b + 0.05)
```

> **Careful:** contrast against white is `1.05/(L+0.05)`; against black it is
> `(L+0.05)/0.05`. Swapping them inverts every conclusion in the table.

### Nominal is not rendered — measure the PDF

**Sample the pixel out of the compiled PDF. The computed value can be wrong by a lot.**

Measured on a real build: `PineGreen!65!black` is nominally `#007C1B` (5.39:1) by the
naive `R = 1 − min(1, c+k)` conversion — but it **renders as `#396E5D`** (5.89:1).
A cmyk-defined colour is stored as `DeviceCMYK` in the PDF and the renderer applies a
proper conversion, not the naive one. Same build, as a control: colours declared with
`\definecolor{x}{RGB}{...}` render **exactly** as declared.

So:

- **cmyk-derived colours** (most `dvipsnames`, including `PineGreen`) shift between
  what you compute and what prints. Always confirm with `--sample`.
- **RGB-declared colours** do not shift. If you want the number you computed to be the
  number that prints, declare in RGB.

```bash
python3 scripts/contrast.py --sample main.pdf     # what actually printed
```

The print shop's CMYK conversion moves it again. Neither shift broke the 4.5:1 floor
in the measured case, but neither was predictable from the arithmetic either.

### Colour ramps (stage sequences, timelines, ordered categories)

- **Make the steps perceptually even.** A constant step in the green channel is a
  good approximation (e.g. 204 · 180 · 155 · 130 · 110 · 94 · 77). Between `!92` and
  `!100` there are 12 units of difference and they read as the same colour.
- **Push the last step past the pure colour** — `base!80!black` — or the final two
  stages will not separate.
- **Choose label colour by measured contrast, not by which half of the ramp it is in.**
  White on a mid-tone can measure 2.4:1; that is an unreadable label, not a preference.
- White text needs background `L ≤ 0.183` to reach 4.5:1. On a mid-tone hue that is
  nearly the darkest step — so **if you want white to start earlier, darken the whole
  ramp**; recolouring one node does not fix it.

```bash
python3 scripts/contrast.py --ramp 'PineGreen!65!black' --steps 7
```

### Categorical colours (comparing methods or conditions)

If one figure's colours come from a raster you cannot regenerate, **reuse the same
hues** in the figure next to it — otherwise the reader cannot connect them. But pure
RGB (`255,0,0`) is garish in large fills and contrasts badly. **Keep the hue, drop the
saturation.** The class palette is built for this: `methods` (140,22,22) and
`imperialblue` (0,62,116) give 9.4:1 and 10.8:1 against white text.

---

## 2. Typography

- **Body 32 pt** (the class default) is the *upper* end of standard advice. Do not
  shrink it.
- **Weight contrast is cheaper than size contrast.** Lato ships nine weights; Light
  (300) against Black (900) is a three-step jump. Do not settle for Bold/Regular.
- **Emphasis rule:** someone who reads *only the bold words* must get the finding.
  "What would you stress reading aloud" is a prosody test, not a poster test. If you
  are drawing a contrast, **bold both sides** — one-sided contrast does not read at
  a glance.
- **Hanging punctuation.** To keep two centred lines optically aligned, put the
  terminal punctuation in `\rlap`; otherwise the longer line shifts left.
- **Open up the leading in centred text.** With no fixed left edge for the eye to
  return to, 1.25× is not enough — use ~1.45×.
- **`\centering` also fixes justification.** A justified 80 pt title gets ugly word
  spaces; `\centering` sets `\leftskip`/`\rightskip` to `\fill`, which both centres
  and stops the stretching.
- **Keep the byline below the title hierarchy.** `\fontsizeauthor` defaults to 48 pt
  = `\fontsizesection`, so author names carry section-heading weight. Drop to ~42 pt.
- **Underline the presenting author.** It is the conference convention, so it carries
  *meaning*, not just emphasis. An icon has to be interpreted and drags an icon font
  into the PDF for one glyph.

---

## 3. Content

Two rule sets; the tighter one binds.

**NYU Libraries** (<https://guides.nyu.edu/posters>): 300–800 words · readable at
3 m · name + affiliation + acknowledgments required · images ≥120 ppi at print size.

**betterposter** (binding): **150–250 words** · main finding is **one sentence**,
jargon-free, key terms emphasised · **3 short blocks** in the side columns ·
**2–3 figures** · **QR code** at the bottom.

Paper text never transfers. Poster copy is written from scratch, and removing a
section entirely is almost always better than compressing it.

### Claim discipline

**Check the poster's wording against your own table.** An abstract often phrases a
result more strongly than the data supports. On a poster that sentence stands alone
in front of someone who has just read your table. A countable framing — "best in 4 of the 5 conditions
tested" — is nearly always more defensible than a claim about average improvement.

**Leave no dangling reference.** Phrases like "as reported in the paper" have no
antecedent on a poster; the reader has not read it, and the phrase only invites the
question. State the criterion itself.

### Caption discipline

A caption must not restate the column text beside it. It should give what the reader
can get from *neither* the figure nor the text alone. For a method figure, the best
caption is usually an analogy that connects it to something the viewer already knows.

---

## 4. Figures

### Resolution

**Rule: ≥120 ppi at printed size** (150 for comfort).

| target width | @120 ppi | @150 ppi |
|---|---|---|
| A0 single column (241 mm) | ~1140 px | ~1420 px |
| A0 two columns (499 mm) | ~2360 px | ~2950 px |
| A0 full width (757 mm) | ~3580 px | ~4470 px |

**Check the REAL placed size, not the nominal column width.** A figure sized by
`height=` does not occupy the column width, and checking against the column silently
reports a number the poster never uses. `check_poster.py --only figures` derives the
placed width from each wrapper.

**Best practice is to avoid the problem: export plots as PDF** (`savefig('x.pdf')`).
Vector output has no ppi.

### Wrapper uniformity

Figure files must open with the **same** vertical space or inter-column spacing will
not match. `\begin{center}` is a trivlist and adds `\topsep` **both** above and below;
a bare `tikzpicture` adds nothing. Normalise every wrapper to one form:

```latex
{\centering\includegraphics[...]{...}\par}     % no trivlist
```

then control spacing from a single place:

```latex
\newcommand{\figgap}{\par\vspace{\baselineskip}}
```

If an image carries its own white margin, zero the caption's top space — otherwise
two gaps stack. Give `\figcap` an optional top-space argument.

### Sourced and derived artwork

- **Never use watermarked stock art**, and do not trace it closely either. Search
  CC0 / public domain (Wikimedia Commons is a good start) and record licence and
  source in the README.
- **Derive assets with a script, not by hand.** Keep the source URL, the removed
  elements and any colour flattening in the script; commit the output so the build
  never needs the network.
- **Verify a derived PDF is pure vector:** an `/XObject` under `/Resources` means
  something rasterised.
- SVG → PDF: `rsvg-convert` (`brew install librsvg`).
- **Logos usually arrive centred on a large canvas.** Uncropped, `\includegraphics`
  scales the empty space and the logo comes out tiny. Measure the ink bounds from the
  accompanying PNG and pass `trim=…, clip`. If left = right and top = bottom, the
  artwork is centred and the measurement transfers safely to the PDF.
- **A dark logo disappears on a dark band.** Put logos on a white panel — which also
  matches the light background the QR codes already need.

---

## 5. Vertical budget

When the page fills up, the relationships are not linear. **Do not estimate — run a
ladder test:**

```bash
for h in 220 210 200 190; do
  perl -pi -e "s/height=\d+mm\]\{assets\/X\.png\}/height=${h}mm]{assets\/X.png}/" figures/X.tex
  tectonic -X compile main.tex >/dev/null 2>&1
  echo "$h -> $(pdfinfo main.pdf | awk '/^Pages:/{print $2}') page(s)"
done
```

Things worth knowing before you start moving figures:

- **The white space above the footer is not usable space.** `\bottomboxheight` can
  exceed the visible coloured band; the difference is the box's own padding, and TeX
  wants the rest to avoid breaking the page.
- **A band's height is set by its tallest element.** Growing the shorter one is free;
  growing the taller one costs page height one-for-one. Which element is tallest can
  change — and when it does, an earlier compression becomes **unnecessary** and can be
  reverted. Check for that, so you are not still paying a price you no longer owe.
- **Width is a ceiling too.** A square figure cannot grow past the minipage width even
  when vertical space exists.
- **Adding words costs figure space**, and word choice changes the price: one word can
  push a line over and take 12 mm from a figure.

### The 3-metre test

```python
import math
mm  = pt * 25.4 / 72
deg = math.degrees(2 * math.atan(mm / 2 / 3000))   # 3 m viewing distance
# >=0.30 comfortable · >=0.15 legible
```

Reference: 116 pt → 0.78° · 80 pt → 0.54° · 48 pt → 0.32° · 32 pt → 0.22° ·
26 pt → 0.18°. So body text and captions are **not** readable at 3 m — that is a
property of the format, not a defect.

Simulate it: viewing A0 from 3 m subtends the same angle as a 74 mm image at 30 cm.
Downscale the render to ~320 px wide and see what survives. What must survive: the
main finding, the section headings, and the shape of the results figure.

---

## 6. Pre-print checklist

- [ ] `make check` — all five checks pass
- [ ] Main colour **measured** ≥4.5:1 against white text (sample the pixel from the PDF)
- [ ] Main finding is one jargon-free sentence; the bold words alone convey it
- [ ] Every claim on the poster verified against the data
- [ ] Name, affiliation, acknowledgments present; presenting author marked
- [ ] Licence and source of any third-party artwork recorded in the README
- [ ] Logos are current, approved marks — **only the author can confirm this**
- [ ] Anything inferred from a figure (region names, labels) cross-checked with the source
- [ ] QR codes scanned from **printed** output with a real phone
- [ ] PDF opened at 100% and judged from 3 m back
- [ ] Print shop told: **A0, no scaling, 100%**
