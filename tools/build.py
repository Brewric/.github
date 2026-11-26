#!/usr/bin/env python3
"""Draws every image in profile/assets, each in a light and a dark version.

    python3 tools/build.py --fonts DIR

DIR holds the fonts brewric.com uses, from Google Fonts (SIL Open Font License): DM Sans
(`DMSans[opsz,wght].ttf`, or the same file renamed `DMSans-VF.ttf`). Needs fontTools
(`pip install fonttools`).

Text is drawn as outlines, because GitHub shows these SVGs as images and an image can't load a font.
Colours, type sizes, radii and shadows are brewric.com's tokens. The mark is Brewric's hexagon with
a signal cut through it, in its 48 x 48 box. The pixel wave is the one at the foot of brewric.com,
drawn here as one still frame.
"""
import argparse
import glob
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'profile', 'assets'))

# brewric.com's colour tokens.
WHITE, PAPER, LINE, LINE_2 = '#ffffff', '#faf7f2', '#e9e2d8', '#d8cec1'
INK, TEXT, MUTED = '#1b1410', '#43382f', '#74685d'
DARK, DARK_2, DARK_3 = '#17110d', '#211812', '#2d211a'
ON_DARK, ON_DARK_2 = '#f4eee4', '#b8ab9d'
ACCENT, ACCENT_INK, BRIGHT, MARK = '#d4380b', '#bf3209', '#ff6a36', '#e8501d'
WAVE = ('#17110d', '#3a1c10', '#863419', '#e85d27')  # the band's own ground, then three tones up to ember
INK_RGB, PAPER_RGB, ACCENT_RGB = '27,20,16', '244,238,228', '255,96,44'

# The mark: a solid hexagon standing on a point, 44 tall in a 48 x 48 box, with a two-pulse signal cut through it.
MARK_PATH = (
    'M43.05 26.65L37.7 26.64L37.54 26.36L37.38 26L37.22 25.53L37.07 24.97L36.83 23.87L36.3 21.14L36.13 20.38'
    'L35.96 19.74L35.79 19.21L35.61 18.69L35.39 18.17L35.18 17.77L34.88 17.27L34.51 16.79L34.05 16.34'
    'L33.62 16.03L33.13 15.77L32.6 15.58L32.17 15.49L31.6 15.45L31.03 15.49L30.6 15.58L30.07 15.77L29.58 16.03'
    'L29.15 16.34L28.69 16.79L28.32 17.27L28.02 17.77L27.81 18.17L27.59 18.69L27.41 19.21L27.24 19.74'
    'L27.07 20.38L26.9 21.14L26.37 23.87L26.13 24.97L25.98 25.53L25.82 26L25.66 26.36L25.5 26.64L22.5 26.64'
    'L22.34 26.36L22.18 26L22.02 25.53L21.87 24.97L21.63 23.87L21.1 21.14L20.93 20.38L20.76 19.74L20.59 19.21'
    'L20.41 18.69L20.19 18.17L19.98 17.77L19.68 17.27L19.31 16.79L18.85 16.34L18.42 16.03L17.93 15.77'
    'L17.4 15.58L16.97 15.49L16.4 15.45L15.83 15.49L15.4 15.58L14.87 15.77L14.38 16.03L13.95 16.34L13.49 16.79'
    'L13.12 17.27L12.82 17.77L12.61 18.17L12.39 18.69L12.21 19.21L12.04 19.74L11.87 20.38L11.7 21.14'
    'L11.17 23.87L10.93 24.97L10.78 25.53L10.62 26L10.46 26.36L10.3 26.64L4.95 26.65V13L24 2L43.05 13Z'
    'M4.95 30.55L10.4 30.55L10.83 30.53L11.4 30.41L11.93 30.22L12.41 29.94L12.63 29.79L12.93 29.53L13.35 29.07'
    'L13.74 28.49L14.1 27.79L14.38 27.07L14.6 26.34L14.84 25.38L15.48 22.14L15.73 21.05L15.89 20.5L16.05 20.04'
    'L16.22 19.68L16.39 19.4L16.41 19.4L16.52 19.56L16.7 19.92L16.87 20.36L17.03 20.89L17.3 22.05L17.8 24.63'
    'L18.04 25.71L18.32 26.76L18.5 27.28L18.66 27.69L18.89 28.19L19.12 28.59L19.38 28.98L19.61 29.26'
    'L19.97 29.62L20.28 29.87L20.62 30.09L21 30.27L21.54 30.45L21.83 30.51L22.26 30.55L25.6 30.55L26.03 30.53'
    'L26.6 30.41L26.87 30.33L27.26 30.15L27.72 29.87L27.93 29.7L28.22 29.44L28.62 28.98L29 28.39L29.3 27.79'
    'L29.58 27.07L29.8 26.34L30.04 25.38L30.68 22.14L30.93 21.05L31.11 20.43L31.28 19.98L31.46 19.6L31.59 19.4'
    'L31.61 19.4L31.78 19.68L31.95 20.04L32.11 20.5L32.27 21.05L32.52 22.14L33.16 25.38L33.4 26.34L33.62 27.07'
    'L33.9 27.79L34.26 28.49L34.65 29.07L35.07 29.53L35.37 29.79L35.59 29.94L36.07 30.22L36.6 30.41L37.17 30.53'
    'L37.6 30.55L43.05 30.55V35L24 46L4.95 35Z'
)

# brewric.com's arrow icons, in a 16 x 16 box with a 1.6 stroke.
ARROW = 'M3 8h10M9 4l4 4-4 4'
OUT_ARROW = 'M4.5 11.5l7-7M5.5 4.5h6v6'


def num(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


# ---------- Type ----------

class Face:
    """One static instance of a font: kerned runs of text, measured and drawn as SVG outlines."""

    def __init__(self, path, **axes):
        font = TTFont(path)
        if 'fvar' in font:
            font = instancer.instantiateVariableFont(font, axes)
        self.upm = font['head'].unitsPerEm
        self.cmap = font.getBestCmap()
        self.glyphs = font.getGlyphSet()
        self.advance = {g: m[0] for g, m in font['hmtx'].metrics.items()}
        self.kern = self._kern(font)

    @staticmethod
    def _kern(font):
        """The pair adjustments of the `kern` feature, lookup by lookup, as dicts that are quick to search."""
        if 'GPOS' not in font:
            return []
        gpos = font['GPOS'].table
        wanted = sorted({i for r in gpos.FeatureList.FeatureRecord if r.FeatureTag == 'kern' for i in r.Feature.LookupListIndex})
        lookups = []
        for i in wanted:
            lookup = gpos.LookupList.Lookup[i]
            subtables = []
            for st in lookup.SubTable:
                if lookup.LookupType == 9:
                    if st.ExtensionLookupType != 2:
                        continue
                    st = st.ExtSubTable
                elif lookup.LookupType != 2:
                    continue
                covered = {g: n for n, g in enumerate(st.Coverage.glyphs)}
                if st.Format == 1:
                    pairs = {}
                    for g, n in covered.items():
                        for rec in st.PairSet[n].PairValueRecord:
                            pairs[(g, rec.SecondGlyph)] = (getattr(rec.Value1, 'XAdvance', 0) or 0) if rec.Value1 else 0
                    subtables.append((covered, pairs, None))
                else:
                    first = st.ClassDef1.classDefs if st.ClassDef1 else {}
                    second = st.ClassDef2.classDefs if st.ClassDef2 else {}
                    subtables.append((covered, None, (first, second, st.Class1Record)))
            lookups.append(subtables)
        return lookups

    def pair(self, a, b):
        total = 0
        for subtables in self.kern:
            for covered, pairs, classes in subtables:
                if a not in covered:
                    continue
                if pairs is not None:
                    if (a, b) not in pairs:
                        continue
                    total += pairs[(a, b)]
                else:
                    first, second, records = classes
                    rec = records[first.get(a, 0)].Class2Record[second.get(b, 0)]
                    total += (getattr(rec.Value1, 'XAdvance', 0) or 0) if rec.Value1 else 0
                break
        return total

    def run(self, text, size, track=0.0):
        """Glyphs, their offsets in font units, and the run's width in px (without the last letter's tracking)."""
        names = [self.cmap[ord(c)] for c in text]
        offsets, x = [], 0.0
        for i, g in enumerate(names):
            offsets.append(x)
            x += self.advance[g] + track * self.upm
            if i + 1 < len(names):
                x += self.pair(g, names[i + 1])
        return names, offsets, (x - track * self.upm) * size / self.upm

    def width(self, text, size, track=0.0):
        return self.run(text, size, track)[2]

    def path(self, text, x, y, size, track=0.0):
        """The outlines of `text`, its baseline starting at (x, y)."""
        names, offsets, _ = self.run(text, size, track)
        k = size / self.upm
        out = []
        for g, gx in zip(names, offsets):
            pen = SVGPathPen(self.glyphs, ntos=num)
            self.glyphs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + gx * k, y)))
            out.append(pen.getCommands())
        return ''.join(out)

    def wrap(self, text, size, width, track=0.0):
        """Lines no wider than `width`, as even in length as they can be (CSS's text-wrap: balance)."""
        words = text.split()
        greedy, line = [], ''
        for word in words:
            trial = f'{line} {word}'.strip()
            if line and self.width(trial, size, track) > width:
                greedy.append(line)
                line = word
            else:
                line = trial
        greedy.append(line)
        if len(greedy) != 2:
            return greedy
        splits = [(' '.join(words[:i]), ' '.join(words[i:])) for i in range(1, len(words))]
        fits = [s for s in splits if max(self.width(p, size, track) for p in s) <= width]
        return list(min(fits, key=lambda s: max(self.width(p, size, track) for p in s)))


class Type:
    """The faces these images use, at the optical size each is set in (DM Sans' opsz axis follows the px size)."""

    def __init__(self, fonts):
        sans = (glob.glob(os.path.join(fonts, 'DMSans*opsz*wght*.ttf')) + glob.glob(os.path.join(fonts, 'DMSans-VF.ttf')))[0]
        self.brand = Face(sans, wght=700, opsz=20)    # the wordmark
        self.title = Face(sans, wght=500, opsz=40)    # headings, 40 px and up
        self.lede = Face(sans, wght=400, opsz=16)     # running text
        self.chip = Face(sans, wght=400, opsz=14)     # chips
        self.button = Face(sans, wght=500, opsz=14)   # buttons


# ---------- Parts ----------

def svg(width, height, body, title, defs=''):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(width)}" height="{num(height)}" '
        f'viewBox="0 0 {num(width)} {num(height)}">\n'
        f'<title>{title}</title>\n'
        + (f'<defs>{defs}</defs>\n' if defs else '')
        + body
        + '</svg>\n'
    )


def shadow(name, far=None, near=None, rgb=INK_RGB):
    """A box shadow as an SVG filter on the shape that casts it: `far` is (y offset, blur, spread pulled in, opacity),
    `near` is (y offset, blur, opacity). Blur is CSS's: twice the Gaussian's deviation. Mixed in sRGB, as CSS does."""
    parts, merge = [], []
    if far:
        dy, blur, inset, alpha = far
        parts.append(f'<feMorphology in="SourceAlpha" operator="erode" radius="{inset}"/>'
                     f'<feGaussianBlur stdDeviation="{num(blur / 2)}"/><feOffset dy="{dy}" result="farb"/>'
                     f'<feFlood flood-color="rgb({rgb})" flood-opacity="{alpha}"/><feComposite in2="farb" operator="in" result="far"/>')
        merge.append('<feMergeNode in="far"/>')
    if near:
        dy, blur, alpha = near
        parts.append(f'<feGaussianBlur in="SourceAlpha" stdDeviation="{num(blur / 2)}"/><feOffset dy="{dy}" result="nearb"/>'
                     f'<feFlood flood-color="rgb({rgb})" flood-opacity="{alpha}"/><feComposite in2="nearb" operator="in" result="near"/>')
        merge.append('<feMergeNode in="near"/>')
    return (f'<filter id="{name}" x="-50%" y="-50%" width="200%" height="220%" color-interpolation-filters="sRGB">'
            + ''.join(parts) + '<feMerge>' + ''.join(merge) + '</feMerge></filter>')


def mark(x, y, size, fill):
    """The mark's 48 x 48 box, `size` px wide, with its top left at (x, y)."""
    return f'<path transform="translate({num(x)} {num(y)}) scale({num(size / 48)})" d="{MARK_PATH}" fill="{fill}"/>\n'


def lockup(t, x, top, size, mark_fill, text_fill):
    """brewric.com's logo lockup (.brand): the mark 1.25em square, .3em before the 700 wordmark, centred on its capitals."""
    box = 1.25 * size
    baseline = top + 0.125 * size + 0.841 * size  # a 1em line box centred on the mark; DM Sans' baseline sits .841em down it
    word = t.brand.path('Brewric', x + box + 0.3 * size, baseline, size, -0.025)
    return mark(x, top - 0.06 * size, box, mark_fill) + f'<path d="{word}" fill="{text_fill}"/>\n'


def chip(t, x, y, label, theme):
    """brewric.com's chip: 14 px text, 4 x 10 padding, a 1 px edge and the 6 px radius. Returns the markup and width."""
    w = t.chip.width(label, 14) + 2 * 10 + 2
    if theme == 'light':
        frame = f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="29" rx="5.5" fill="{WHITE}" stroke="{LINE}"/>\n'
        color = TEXT
    else:
        frame = f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="29" rx="5.5" fill="{DARK_3}" stroke="rgb({PAPER_RGB})" stroke-opacity=".1"/>\n'
        color = ON_DARK_2
    # A 20 px line box inside the 1 px edge and 4 px padding; DM Sans' baseline sits 15.4 px down a 14/20 line.
    text = t.chip.path(label, x + 11, y + 5 + 15.4, 14)
    return frame + f'<path d="{text}" fill="{color}"/>\n', w


# ---------- The pixel wave ----------

BAYER = (
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
    3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
)


def _fract(v):
    return v - math.floor(v)


def _hash(n):
    return _fract(math.sin(n) * 43758.5453)


def _wobble(v):
    i = math.floor(v)
    f = v - i
    s = f * f * (3 - 2 * f)
    return (_hash(i) * (1 - s) + _hash(i + 1) * s) * 2 - 1


def wave(width, height, first, step, amplitude, time, cell=3):
    """brewric.com's pixel wave (js/wave.js) as one still frame: four ridgelines rising from the foot of a
    width x height stage, lit at the crest and dithered into 3 px dots in four tones by an 8 x 8 Bayer matrix.
    Returns one path per lit tone (the first tone is the stage's own ground), in the stage's coordinates."""
    cols, rows = math.ceil(width / cell), math.ceil(height / cell)
    unit = max(140, min(420, width / 3.4))
    runs = {1: [], 2: [], 3: []}
    for cy in range(rows):  # rows count up from the foot, as in WebGL
        y = (cy + 0.5) * cell
        row = []
        for cx in range(cols):
            x = (cx + 0.5) * cell / unit
            light = 0.0
            for k in (3, 2, 1, 0):  # the back ridge first; each nearer one paints over it
                crest = first + k * step + amplitude * (
                    0.62 * math.sin(x * (2.9 + k * 0.45) + time * (0.36 + k * 0.07) + k * 1.9)
                    + 0.30 * math.sin(x * (6.3 - k * 0.70) - time * (0.27 + k * 0.05) + k * 4.3)
                    + 0.14 * _wobble(x * 3.4 + k * 11.0 + time * 0.12))
                depth = crest - y
                if depth > 0:
                    light = (1 - 0.17 * k) * math.exp(-depth * 1.9 / step)
            threshold = (BAYER[(cy & 7) * 8 + (cx & 7)] + 0.5) / 64
            row.append(int(min(3, max(0, math.floor(light * 3 + threshold)))))
        top = height - (cy + 1) * cell
        cx = 0
        while cx < cols:
            tone, start = row[cx], cx
            while cx < cols and row[cx] == tone:
                cx += 1
            if tone:
                runs[tone].append(f'M{num(start * cell)} {num(top)}h{num((cx - start) * cell)}v{cell}h-{num((cx - start) * cell)}z')
    return {tone: ''.join(parts) for tone, parts in runs.items()}


# ---------- The hero ----------

def hero(t, theme):
    W, H, R = 846, 340, 16
    light = theme == 'light'
    left = 40
    # The wave card: inset 28 px on three sides, as wide as the copy leaves room for.
    cx, cy, cw, ch = 470, 28, 348, 284

    defs = [
        f'<clipPath id="hero"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
        f'<clipPath id="card"><rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="12"/></clipPath>',
        # brewric.com's hero ground and dot grid; the dots fade out in an ellipse around the product.
        (f'<linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset=".4" stop-color="{WHITE}"/><stop offset="1" stop-color="{PAPER}"/></linearGradient>'
         if light else
         f'<linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{DARK_2}"/><stop offset="1" stop-color="{DARK}"/></linearGradient>'),
        f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r="1.15" '
        f'fill="rgb({INK_RGB if light else PAPER_RGB})" fill-opacity="{".16" if light else ".09"}"/></pattern>',
        f'<radialGradient id="fade" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" '
        f'gradientTransform="translate(630 156) scale(335 245)"><stop offset=".25" stop-color="#fff"/><stop offset=".8" stop-color="#fff" stop-opacity="0"/></radialGradient>',
        f'<mask id="dotmask"><rect x="305" width="{W - 305}" height="{H}" fill="url(#fade)"/></mask>',
        # The warm glow up to the right, in the accent's wash.
        f'<radialGradient id="glow" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" '
        f'gradientTransform="translate(635 119) scale(279 221)"><stop offset="0" stop-color="rgb({ACCENT_RGB})" stop-opacity="{".12" if light else ".14"}"/>'
        f'<stop offset=".72" stop-color="rgb({ACCENT_RGB})" stop-opacity="0"/></radialGradient>',
        # --sh-3, the shadow of floating things: 0 2px 4px, and 0 36px 72px pulled in by 28 px (CSS's negative spread).
        shadow('sh3', far=(36, 36, 28, '.34' if light else '.55'), near=(2, 2, '.05' if light else '.3'), rgb=INK_RGB if light else '0,0,0'),
    ]

    body = [f'<g clip-path="url(#hero)">\n',
            f'<rect width="{W}" height="{H}" fill="url(#ground)"/>\n',
            f'<rect x="305" width="{W - 305}" height="{H}" fill="url(#dots)" mask="url(#dotmask)"/>\n',
            f'<rect x="356" y="-102" width="558" height="442" fill="url(#glow)"/>\n',
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="12" filter="url(#sh3)"/>\n',
            '</g>\n']
    edge = f'stroke="{LINE}"' if light else f'stroke="rgb({PAPER_RGB})" stroke-opacity=".1"'
    body.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{R - .5}" fill="none" {edge}/>\n')

    # The copy: the lockup, the promise in two lines (the first in the accent), the lede and the formats.
    body.append(lockup(t, left, 40, 20, MARK if light else BRIGHT, INK if light else ON_DARK))
    title = 44
    body.append(f'<path d="{t.title.path("Observability", left - 1, 138, title, -0.035)}" fill="{ACCENT_INK if light else BRIGHT}"/>\n')
    body.append(f'<path d="{t.title.path("for Physical AI", left - 1, 184, title, -0.035)}" fill="{INK if light else ON_DARK}"/>\n')
    lede = 'The telemetry and real-time analytics stack for robot fleets.'
    for i, line in enumerate(t.lede.wrap(lede, 16, 360)):
        body.append(f'<path d="{t.lede.path(line, left, 224 + i * 25, 16)}" fill="{TEXT if light else ON_DARK_2}"/>\n')
    x = left
    for label in ('ROS 2', 'MCAP', 'OpenTelemetry', 'SQL'):
        part, w = chip(t, x, 274, label, theme)
        body.append(part)
        x += w + 8

    # The wave card: the mark above, the ridges at its foot.
    body.append(f'<g clip-path="url(#card)">\n<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="{WAVE[0]}"/>\n')
    tones = wave(cw, ch, first=48, step=34, amplitude=36, time=3.0)
    body.append(f'<g transform="translate({cx} {cy})">\n')
    for tone in (1, 2, 3):
        body.append(f'<path d="{tones[tone]}" fill="{WAVE[tone]}"/>\n')
    body.append('</g>\n</g>\n')
    body.append(f'<rect x="{cx + .5}" y="{cy + .5}" width="{cw - 1}" height="{ch - 1}" rx="11.5" fill="none" stroke="rgb({PAPER_RGB})" stroke-opacity="{".06" if light else ".12"}"/>\n')
    size = 72
    body.append(mark(cx + (cw - size) / 2, cy + 40, size, BRIGHT))

    return svg(W, H, ''.join(body), 'Brewric: Observability for Physical AI', ''.join(defs))


# ---------- Buttons ----------

def button(t, label, icon, kind, theme):
    """brewric.com's small button (.btn-sm): 38 px tall, 14 px 500 text, a 16 px icon 10 px after it, radius 6."""
    pad, gap, h = 14, 10, 38
    tw = t.button.width(label, 14)
    w = pad + tw + gap + 16 + pad
    top, W, H = 1, w + 2, h + 4  # room for the shadow
    x0 = 1
    defs = ''
    caster = f'<rect x="{x0}" y="{top}" width="{num(w)}" height="{h}" rx="6" filter="url(#s)"/>\n'
    parts = []
    if kind == 'primary':
        defs = shadow('s', near=(1, 2, '.24'))
        parts.append(caster)
        parts.append(f'<rect x="{x0}" y="{top}" width="{num(w)}" height="{h}" rx="6" fill="{ACCENT}"/>\n')
        # The inset highlight along the top edge.
        parts.append(f'<path d="M{x0 + 6} {top + .5}h{num(w - 12)}" stroke="#fff" stroke-opacity=".18"/>\n')
        color = WHITE
    elif theme == 'light':
        defs = shadow('s', near=(1, 2, '.06'))
        parts.append(caster)
        parts.append(f'<rect x="{x0 + .5}" y="{top + .5}" width="{num(w - 1)}" height="{h - 1}" rx="5.5" fill="{WHITE}" stroke="{LINE_2}"/>\n')
        color = INK
    else:
        parts.append(f'<rect x="{x0 + .5}" y="{top + .5}" width="{num(w - 1)}" height="{h - 1}" rx="5.5" fill="none" stroke="rgb({PAPER_RGB})" stroke-opacity=".28"/>\n')
        color = ON_DARK
    # A 14/1.25 line box centred in the button; DM Sans' baseline sits 13.15 px down it.
    baseline = top + (h - 17.5) / 2 + 13.15
    parts.append(f'<path d="{t.button.path(label, x0 + pad, baseline, 14)}" fill="{color}"/>\n')
    ix, iy = x0 + pad + tw + gap, top + (h - 16) / 2
    parts.append(f'<path transform="translate({num(ix)} {num(iy)})" d="{icon}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>\n')
    return svg(W, H, ''.join(parts), label, defs)


# ---------- Icons ----------

GLYPHS = {
    # Braces round a dot: a schema, which is what OPAL is.
    'opal': ('M6 2.5C4.6 2.5 4.25 3.2 4.25 4.6V6.3C4.25 7.4 3.7 8 2.6 8C3.7 8 4.25 8.6 4.25 9.7V11.4C4.25 12.8 4.6 13.5 6 13.5'
             'M10 2.5C11.4 2.5 11.75 3.2 11.75 4.6V6.3C11.75 7.4 12.3 8 13.4 8C12.3 8 11.75 8.6 11.75 9.7V11.4C11.75 12.8 11.4 13.5 10 13.5'
             'M8 8h.01'),
    # Three bars, the last the tallest.
    'benchmarks': 'M3.5 13.5v-4M8 13.5v-7M12.5 13.5v-11',
}


def icon(name, theme):
    """A 40 px icon: the glyph in the accent on the accent's wash, radius 6, as brewric.com draws icon grounds."""
    color = ACCENT_INK if theme == 'light' else BRIGHT
    wash = '.12' if theme == 'light' else '.16'
    body = (f'<rect width="40" height="40" rx="6" fill="rgb({ACCENT_RGB})" fill-opacity="{wash}"/>\n'
            f'<path transform="translate(8 8) scale(1.5)" d="{GLYPHS[name]}" fill="none" stroke="{color}" '
            f'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>\n')
    return svg(40, 40, body, '')


# ---------- The mark on its own, and the avatar ----------

def mark_file(theme):
    return svg(48, 48, mark(0, 0, 48, MARK if theme == 'light' else BRIGHT), 'Brewric')


def avatar():
    """The organization's picture: the bright mark on espresso, as on brewric.com's home-screen icon."""
    size = 512
    m = size * 0.72
    return svg(size, size, f'<rect width="{size}" height="{size}" fill="{DARK}"/>\n' + mark((size - m) / 2, (size - m) / 2, m, BRIGHT), 'Brewric')


BUTTONS = {
    'talk': ('Talk to an engineer', ARROW, 'primary'),
    'website': ('brewric.com', OUT_ARROW, 'ghost'),
    'benchmarks': ('Benchmarks', OUT_ARROW, 'ghost'),
    'opal': ('Open standard', OUT_ARROW, 'ghost'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--fonts', required=True, help='folder with DM Sans (DMSans[opsz,wght].ttf)')
    parser.add_argument('--avatar', help='also write the organization picture (SVG) here')
    args = parser.parse_args()
    t = Type(args.fonts)
    os.makedirs(OUT, exist_ok=True)
    files = {}
    for theme in ('light', 'dark'):
        files[f'hero-{theme}.svg'] = hero(t, theme)
        files[f'mark-{theme}.svg'] = mark_file(theme)
        for key, (label, glyph, kind) in BUTTONS.items():
            # The orange button is the same on both grounds, so it is one file.
            name = f'button-{key}.svg' if kind == 'primary' else f'button-{key}-{theme}.svg'
            files[name] = button(t, label, glyph, kind, theme)
        for name in GLYPHS:
            files[f'icon-{name}-{theme}.svg'] = icon(name, theme)
    for name, text in files.items():
        with open(os.path.join(OUT, name), 'w') as f:
            f.write(text)
        print(f'{len(text) / 1024:7.1f} KB  profile/assets/{name}')
    if args.avatar:
        with open(args.avatar, 'w') as f:
            f.write(avatar())
        print(f'avatar: {args.avatar}')


if __name__ == '__main__':
    main()
