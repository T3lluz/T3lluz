"""Glitch section titles: scramble-decode intro, RGB-split + slice-shift bursts, scanline sweep.

Everything animates whole <text>/<use>/<g> elements with SMIL, because GitHub serves README
SVGs as images and browsers ignore CSS transforms/filters on individual <tspan>s.
"""

from __future__ import annotations

import random
from pathlib import Path

from svg_common import SANS, THEMES, discrete, discrete_translate, esc, num

SIZE = 30
HEIGHT = 56
BASELINE = 40
GLYPHS = "#%&@$*+=?/\\<>[]{}01Ø§¥¤"
FRAME = 0.06

# name, text, loop duration (s) — different loops keep the titles from glitching in sync.
TITLES = [
    ("hey", "Hey, I'm T3lluz", 11.0),
    ("about", "About", 12.4),
    ("pulse", "GitHub Pulse", 12.7),
    ("stack", "Stack and tools", 13.9),
    ("contact", "Contact", 11.7),
]


def char_width(ch: str) -> float:
    if ch == " ":
        return 0.3
    if ch in ",.'!|":
        return 0.3
    if ch in "&":
        return 0.72
    if ch.isupper() or ch in "MW@%":
        return 0.7
    if ch in "ilj":
        return 0.3
    if ch in "mw":
        return 0.86
    return 0.6


def scrambles(text: str, rng: random.Random, frames: int) -> list[str]:
    n = len(text)
    reveal = [min(frames, int(i / max(n, 1) * frames * 0.6) + rng.randint(2, 5)) for i in range(n)]
    out = []
    for k in range(frames):
        out.append("".join(
            c if c == " " or k >= reveal[i] else rng.choice(GLYPHS) for i, c in enumerate(text)
        ))
    return out


def bursts(dur: float, rng: random.Random) -> list[float]:
    """Start times of glitch bursts, spread over the part of the loop after the decode."""
    return sorted({round(dur * f + rng.uniform(-0.3, 0.3), 2) for f in (0.33, 0.61, 0.64, 0.86)})


def build(name: str, text: str, dur: float, theme: str) -> tuple[str, int]:
    t = THEMES[theme]
    rng = random.Random(f"{name}-glitch")
    length = sum(char_width(c) for c in text) * SIZE
    width = int(length + 48)
    cx = width / 2
    frames = scrambles(text, rng, 14)
    decode_end = len(frames) * FRAME
    starts = bursts(dur, rng)
    text_attrs = (f'x="{num(cx)}" y="{BASELINE}" text-anchor="middle" textLength="{num(length)}" '
                  f'lengthAdjust="spacingAndGlyphs" font-family="{SANS}" font-size="{SIZE}" font-weight="800"')

    # Main text: hidden while decoding, dimmed on burst frames so the displaced slices read clearly.
    main_pts = [(0.0, 0), (decode_end, 1)]
    for s in starts:
        main_pts += [(s, 0.45), (s + 0.05, 1), (s + 0.1, 0.35), (s + 0.16, 1)]

    decode = []
    for k, frame in enumerate(frames):
        pts = [(0.0, 1 if k == 0 else 0), (k * FRAME, 1), ((k + 1) * FRAME, 0)]
        decode.append(
            f'<text {text_attrs} fill="{t["accent"]}" opacity="0">{esc(frame)}'
            f'{discrete("opacity", dur, pts)}</text>'
        )

    # Chromatic aberration pair: offset in opposite directions during the decode and bursts.
    def split(color: str, sign: int) -> str:
        pts_o = [(0.0, 0.8), (decode_end, 0)]
        pts_t = [(0.0, (sign * 3, 0)), (decode_end * 0.5, (-sign * 2, 0)), (decode_end, (0, 0))]
        for s in starts:
            a, b = rng.uniform(3, 7), rng.uniform(1, 4)
            pts_o += [(s, 0.85), (s + 0.16, 0)]
            pts_t += [(s, (sign * a, 0)), (s + 0.06, (-sign * b, 1)), (s + 0.11, (sign * b, 0)), (s + 0.16, (0, 0))]
        return (f'<g opacity="0">{discrete("opacity", dur, pts_o)}'
                f'<use href="#txt-{name}" fill="{color}">{discrete_translate(dur, pts_t)}</use></g>')

    # Horizontal slices that jump sideways; each burst picks new bands.
    clips, slices = [], []
    for i in range(3):
        ys = [(0.0, 0)]
        hs = [(0.0, 0)]
        op = [(0.0, 0)]
        tr = [(0.0, (0, 0))]
        for s in starts:
            y = rng.uniform(10, BASELINE - 4)
            h = rng.uniform(3, 9)
            dx = rng.choice([-1, 1]) * rng.uniform(4, 14)
            ys += [(s, num(y)), (s + 0.08, num(y + rng.uniform(-6, 6)))]
            hs += [(s, num(h)), (s + 0.08, num(h * 0.6))]
            op += [(s, 1), (s + 0.16, 0)]
            tr += [(s, (dx, 0)), (s + 0.05, (-dx * 0.6, 0)), (s + 0.1, (dx * 0.3, 0)), (s + 0.16, (0, 0))]
        clips.append(
            f'<clipPath id="slice-{name}-{i}"><rect x="0" y="0" width="{width}" height="0">'
            f'{discrete("y", dur, ys)}{discrete("height", dur, hs)}</rect></clipPath>'
        )
        slices.append(
            f'<g clip-path="url(#slice-{name}-{i})" opacity="0">{discrete("opacity", dur, op)}'
            f'<use href="#txt-{name}" fill="url(#fill-{name})">{discrete_translate(dur, tr)}</use></g>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{HEIGHT}" viewBox="0 0 {width} {HEIGHT}" role="img" aria-label="{esc(text)}">
  <title>{esc(text)}</title>
  <defs>
    <linearGradient id="fill-{name}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['title_a']}"/>
      <stop offset="1" stop-color="{t['title_b']}"/>
    </linearGradient>
    <filter id="glow-{name}" x="-10%" y="-40%" width="120%" height="180%">
      <feGaussianBlur stdDeviation="{3.2 if theme == 'dark' else 1.4}" result="b"/>
      <feColorMatrix in="b" type="matrix" values="0 0 0 0 {0.35 if theme == 'dark' else 0.04} 0 0 0 0 {0.65 if theme == 'dark' else 0.41} 0 0 0 0 1 0 0 0 {0.55 if theme == 'dark' else 0.25} 0" result="c"/>
      <feMerge><feMergeNode in="c"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <text id="txt-{name}" {text_attrs}>{esc(text)}</text>
    <clipPath id="clip-{name}"><use href="#txt-{name}"/></clipPath>
    {''.join(clips)}
  </defs>
  <g filter="url(#glow-{name})">
    <g opacity="0">{discrete('opacity', dur, main_pts)}<use href="#txt-{name}" fill="url(#fill-{name})"/></g>
    {''.join(decode)}
  </g>
  <g style="mix-blend-mode:{t['blend']}">{split(t['red'], -1)}{split(t['cyan'], 1)}</g>
  {''.join(slices)}
  <g clip-path="url(#clip-{name})">
    <rect x="0" y="-4" width="{width}" height="3" fill="{t['title_a']}" opacity=".55">
      <animate attributeName="y" dur="{num(dur)}s" repeatCount="indefinite" values="-4;-4;{HEIGHT};{HEIGHT}" keyTimes="0;{num((decode_end + 0.2) / dur)};{num((decode_end + 1.1) / dur)};1"/>
    </rect>
  </g>
</svg>
"""
    return svg, width


def write_all(out_dir: Path) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    widths = {}
    for name, text, dur in TITLES:
        for theme in THEMES:
            svg, width = build(name, text, dur, theme)
            (out_dir / f"glitch-{name}-{theme}.svg").write_text(svg, encoding="utf-8")
        widths[name] = width
    return widths


if __name__ == "__main__":
    print(write_all(Path(__file__).resolve().parent.parent / "assets" / "titles"))
