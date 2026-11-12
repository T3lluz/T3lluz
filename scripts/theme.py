"""The look of t3lluz.com as SVG building blocks: tokens, embedded font, icons, window frame, glitch text.

GitHub serves README SVGs as images, so nothing here may depend on scripts, external files or CSS
on child elements. Animation is SMIL, and every element's base attributes describe the finished
state, so a renderer that skips animation still shows the real content.
"""

from __future__ import annotations

import base64
import json
import random
from functools import cache
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent / "assets"

# Same values as :root on t3lluz.com.
DESK, BG, RAISE, LINE, LINE2 = "#111111", "#181818", "#222222", "#262626", "#333333"
FG, SOFT, DIM, FAINT = "#e4e4e4", "#cccccc", "#9d9d9d", "#6e6e6e"
BLUE, TEAL, GREEN, YELLOW, ORANGE, RED, MAGENTA = "#4daafc", "#4ec9b0", "#3fb96b", "#d7ba7d", "#ce9178", "#f14c4c", "#c586c0"
SERIES = [TEAL, BLUE, YELLOW, MAGENTA, ORANGE, GREEN]

FONT = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
FS, SMALL = 13, 12
ADVANCE = 0.6  # JetBrains Mono: every glyph is 0.6em wide

# Every image is a piece of the site's desk, 828 wide, shown at the full width of the page.
# Windows are inset by M sideways and V up and down. Images touch, so windows end up the
# site's 14px apart both ways (2M sideways, 2V + TOP down).
HALF, FULL = 414, 828
M, V, TOP, PAD = 7, 3, 8, 16
X0 = M + PAD
Y0 = V + TOP + 18
BOTTOM = V + 14  # space under a window's content


def x1(width: int) -> int:
    return width - M - PAD


def esc(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})


def num(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".") or "0"


def tw(value: str, size: float = FS) -> float:
    return len(value) * size * ADVANCE


def fit(value: str, width: float, size: float = FS, words: bool = False) -> str:
    """Cut text with an ellipsis so it fits in `width` pixels. `words` cuts at a nearby space."""
    limit = int(width / (size * ADVANCE))
    if len(value) <= limit:
        return value
    cut = value[: max(limit - 1, 0)]
    if words and " " in cut[-9:]:
        cut = cut[: cut.rindex(" ")]
    return cut.rstrip(" ,.:;") + "…"


def _pinned(value: str, size: float) -> str:
    """Fix the rendered width, so a fallback font with other letter widths cannot break the layout."""
    return f' textLength="{num(tw(value, size))}"' if len(value) > 1 else ""


def text(x: float, y: float, value: str, fill: str = FG, size: float = FS, weight: int = 400, anchor: str = "start") -> str:
    attrs = f'x="{num(x)}" y="{num(y)}" fill="{fill}"{_pinned(value, size)}'
    if size != FS:
        attrs += f' font-size="{num(size)}"'
    if weight != 400:
        attrs += f' font-weight="{weight}"'
    if anchor != "start":
        attrs += f' text-anchor="{anchor}"'
    return f"<text {attrs}>{esc(value)}</text>"


# --------------------------------------------------------------------------- icons

@cache
def _icons() -> dict:
    return json.loads((ASSETS / "icons.json").read_text(encoding="utf-8"))


def lucide(name: str, x: float, y: float, size: float = 14, color: str = DIM) -> str:
    return (f'<g transform="translate({num(x)} {num(y)}) scale({num(size / 24)})" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_icons()["lucide"][name]}</g>')


def has_brand(slug: str | None) -> bool:
    return bool(slug) and slug in _icons()["brand"]


def brand(slug: str, x: float, y: float, size: float = 14, color: str = SOFT) -> str:
    """One-colour brand mark (Simple Icons path, 24x24 box)."""
    return (f'<path transform="translate({num(x)} {num(y)}) scale({num(size / 24)})" fill="{color}" '
            f'd="{_icons()["brand"][slug]}"/>')


@cache
def logo_def() -> str:
    """The cube from the site's top bar, defined once per image."""
    inner = (ASSETS / "logo.svg").read_text(encoding="utf-8")
    inner = inner[inner.index(">") + 1: inner.rindex("</svg>")]
    return f'<defs><g id="cube">{inner}</g></defs>'


def logo(x: float, y: float, size: float) -> str:
    return f'<use href="#cube" transform="translate({num(x)} {num(y)}) scale({num(size / 64)})"/>'


# --------------------------------------------------------------------------- animation

def _timeline(dur: float, points: list[tuple[float, str]]) -> tuple[str, str]:
    """(seconds, value) points as SMIL values/keyTimes. Later points win on ties."""
    by_t: dict[str, str] = {}
    for t, v in sorted(points, key=lambda p: p[0]):
        by_t[f"{min(max(t / dur, 0.0), 1.0):.4f}".rstrip("0").rstrip(".") or "0"] = v
    keys = sorted(by_t, key=float)
    return ";".join(by_t[k] for k in keys), ";".join(keys)


def discrete(attr: str, dur: float, points: list[tuple[float, object]]) -> str:
    values, key_times = _timeline(dur, [(t, str(v)) for t, v in points])
    return (f'<animate attributeName="{attr}" dur="{num(dur)}s" repeatCount="indefinite" calcMode="discrete" '
            f'values="{values}" keyTimes="{key_times}"/>')


def discrete_shift(dur: float, points: list[tuple[float, float]]) -> str:
    values, key_times = _timeline(dur, [(t, f"{num(dx)} 0") for t, dx in points])
    return (f'<animateTransform attributeName="transform" type="translate" dur="{num(dur)}s" repeatCount="indefinite" '
            f'calcMode="discrete" values="{values}" keyTimes="{key_times}"/>')


def grow(attr: str, to: float, delay: float, dur: float = 0.6) -> str:
    """Ease an attribute from 0 to its real value once, after `delay` seconds."""
    return (f'<animate attributeName="{attr}" values="0;0;{num(to)}" keyTimes="0;{num(delay / (delay + dur))};1" '
            f'dur="{num(delay + dur)}s" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1"/>')


NOISE = "#%&@$*+=?/<>[]{}01"
FRAME = 0.06  # a multiple of 0.01, so rounded begin times never make two frames overlap


def glitch(value: str, x: float, y: float, *, size: float = FS, weight: int = 600, fill: str = FG, seed: str = "",
           loop: float = 11.0, slices: int = 0, backdrop: str = BG, bursts: bool = True) -> str:
    """Text that decodes out of noise once on load. With `bursts` it also splits sideways now and then.

    One teal ghost and one grey ghost slide out from under the text. `slices` adds horizontal bands
    that jump sideways, which only reads at headline sizes. Window titles decode and then stay
    still, so the name in the header is the only thing on the page that keeps glitching.
    """
    rng = random.Random(f"glitch:{seed or value}")
    attrs = f'x="{num(x)}" y="{num(y)}" font-size="{num(size)}" font-weight="{weight}"{_pinned(value, size)}'
    frames = 9
    settle = [min(frames, int(i / max(len(value), 1) * frames * 0.6) + rng.randint(2, 4)) for i in range(len(value))]
    starts = sorted(loop * f + rng.uniform(-0.3, 0.3) for f in (0.34, 0.66, 0.9)) if bursts else []
    reach = max(1.0, size * 0.09)
    out = []

    for color, sign, opacity in ((TEAL, -1, 0.9), (FAINT, 1, 0.7)) if bursts else ():
        show, move = [(0.0, 0)], [(0.0, 0.0)]
        for s in starts:
            a, b = rng.uniform(1.2, 2.2) * reach, rng.uniform(0.5, 1.2) * reach
            show += [(s, opacity), (s + 0.16, 0)]
            move += [(s, sign * a), (s + 0.06, -sign * b), (s + 0.11, sign * b), (s + 0.16, 0.0)]
        out.append(f'<g opacity="0">{discrete("opacity", loop, show)}<text {attrs} fill="{color}">{esc(value)}'
                   f'{discrete_shift(loop, move)}</text></g>')

    # The real text hides only while the noise frames play.
    out.append(f'<text {attrs} fill="{fill}">{esc(value)}'
               f'<set attributeName="opacity" to="0" begin="0s" dur="{num(frames * FRAME)}s"/></text>')
    for k in range(frames):
        noise = "".join(c if c == " " or k >= settle[i] else rng.choice(NOISE) for i, c in enumerate(value))
        out.append(f'<text {attrs} fill="{TEAL if k < 3 else fill}" opacity="0">{esc(noise)}'
                   f'<set attributeName="opacity" to="1" begin="{num(k * FRAME)}s" dur="{num(FRAME)}s"/></text>')

    width = tw(value, size) + 4 * reach
    for i in range(slices if bursts else 0):
        band_y, band_h, show, move = [(0.0, 0)], [(0.0, 0)], [(0.0, 0)], [(0.0, 0.0)]
        for s in starts:
            top = y - size * rng.uniform(0.15, 0.7)
            dx = rng.choice([-1, 1]) * rng.uniform(1.5, 3.5) * reach
            band_y += [(s, num(top))]
            band_h += [(s, num(size * rng.uniform(0.08, 0.2)))]
            show += [(s, 1), (s + 0.16, 0)]
            move += [(s, dx), (s + 0.06, -dx * 0.5), (s + 0.11, dx * 0.3), (s + 0.16, 0.0)]
        clip_id = f"slice-{rng.randrange(10 ** 8)}"
        out.append(
            f'<clipPath id="{clip_id}"><rect x="{num(x - 2 * reach)}" y="0" width="{num(width)}" height="0">'
            f'{discrete("y", loop, band_y)}{discrete("height", loop, band_h)}</rect></clipPath>'
            f'<g clip-path="url(#{clip_id})" opacity="0">{discrete("opacity", loop, show)}'
            f'<rect x="{num(x - 2 * reach)}" y="{num(y - size)}" width="{num(width)}" height="{num(size * 1.3)}" fill="{backdrop}"/>'
            f'<text {attrs} fill="{fill}">{esc(value)}{discrete_shift(loop, move)}</text></g>'
        )
    return "".join(out)


# --------------------------------------------------------------------------- frames

@cache
def _font_face() -> str:
    data = base64.b64encode((ASSETS / "jetbrains-mono.woff2").read_bytes()).decode()
    return ("@font-face{font-family:'JetBrains Mono';font-weight:100 800;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def svg(width: int, height: int, label: str, body: str, css: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{esc(label)}"><title>{esc(label)}</title><style>{_font_face()}{css}</style>'
            f'<g font-family="{FONT}" font-size="{FS}" style="font-variant-ligatures:none">{body}</g></svg>\n')


def desk(width: int, height: int) -> str:
    """The site's page colour behind an image. A title on a window border needs it under its top half."""
    return f'<rect width="{width}" height="{height}" fill="{DESK}"/>'


# An SVG loaded through <img> evaluates media queries against its own rendered size. A full-width
# image scaled down to a phone has 5px text, so below 520px it shows a larger `narrow` variant.
NARROW_CSS = ".narrow{display:none}@media (max-width:520px){.wide{display:none}.narrow{display:inline}}"


def window(width: int, height: int, title: str, icon: str, accent: str, body: str, tag: str = "", label: str = "",
           narrow_css: str = "") -> str:
    """A window from the site: 1px border, and the title sitting on the top edge.

    A half-width window comes back as bare markup for `row()` to place. A full-width one is a
    finished image.
    """
    top = V + TOP + 0.5
    right = width - M - 0.5
    title_x = M + 9
    frame = (f'<rect x="{M + 0.5}" y="{top}" width="{width - 2 * M - 1}" '
             f'height="{height - 2 * V - TOP - 1}" rx="6" fill="{BG}" stroke="{LINE2}"/>')
    head = (f'<rect x="{title_x}" y="{top - 8}" width="{num(33 + tw(title))}" height="16" fill="{BG}"/>'
            f'{lucide(icon, title_x + 6, top - 7, 14, accent)}'
            f'{glitch(title, title_x + 27, top + 4.5, seed=f"{title}-title", bursts=False)}')
    side = ""
    if tag:
        tag_w = tw(tag) + 12
        side = (f'<rect x="{num(right - 9 - tag_w)}" y="{top - 8}" width="{num(tag_w)}" height="16" fill="{BG}"/>'
                f'{text(right - 15, top + 4.5, tag, DIM, anchor="end")}')
    if width <= HALF:
        return frame + head + side + body

    # On a phone a full-width image is drawn at half the scale of a half-width one. Its narrow
    # variant doubles the frame's insets, corners, title and tag, so it matches the windows around it.
    wide_frame = (f'<rect x="{2 * M + 1}" y="{2 * (V + TOP) + 1}" width="{width - 4 * M - 2}" '
                  f'height="{height - 2 * (2 * V + TOP) - 2}" rx="12" fill="{BG}" stroke="{LINE2}" stroke-width="2"/>')
    doubled = f'<g transform="scale(2)">{head}</g><g transform="translate({-width} 0) scale(2)">{side}</g>'
    return svg(width, height, label or title,
               f'{desk(width, height)}<g class="wide">{frame}</g><g class="narrow">{wide_frame}</g>{body}'
               f'<g class="wide">{head}{side}</g><g class="narrow">{doubled}</g>', NARROW_CSS + narrow_css)


def row(left: str, right: str, height: int, label: str, foot: int = 0) -> tuple[str, str]:
    """Two half windows as one image, in two shapes: side by side for desktop, stacked for phones.

    GitHub's README column is anywhere from 575 to 846px wide on desktop. One image per row at
    width 100% always fills it, where two fixed-width images wrap into a single column as soon
    as it gets narrower than both. `foot` adds desk under the last row.
    """
    wide = svg(FULL, height + foot, label,
               f'{desk(FULL, height + foot)}{left}<g transform="translate({HALF} 0)">{right}</g>')
    tall = svg(HALF, 2 * height + foot, label,
               f'{desk(HALF, 2 * height + foot)}{left}<g transform="translate(0 {height})">{right}</g>')
    return wide, tall


def tile(x: float, y: float, w: float, h: float) -> str:
    return f'<rect x="{num(x + 0.5)}" y="{num(y + 0.5)}" width="{num(w - 1)}" height="{num(h - 1)}" rx="4" fill="{DESK}" stroke="{LINE}"/>'


def bar_line(x: float, y: float, w: float, share: float, color: str = TEAL, delay: float = 0.0, h: float = 4) -> str:
    """The site's .bar-line: a thin track with a filled part that grows in."""
    filled = max(w * min(max(share, 0.0), 1.0), h)
    return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{num(h / 2)}" fill="{LINE}"/>'
            f'<rect x="{num(x)}" y="{num(y)}" width="{num(filled)}" height="{num(h)}" rx="{num(h / 2)}" fill="{color}">'
            f'{grow("width", filled, delay)}</rect>')


def chip(x: float, y: float, label: str) -> tuple[str, float]:
    """The site's .chip: text on a raised pill, no icon. Returns the markup and its width."""
    width = tw(label, SMALL) + 14
    return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(width)}" height="20" rx="3" fill="{RAISE}"/>'
            + text(x + 7, y + 14.2, label, SOFT, SMALL)), width
