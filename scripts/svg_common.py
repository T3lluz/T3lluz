"""Small helpers shared by the SVG generators (escaping, themes, discrete SMIL timelines)."""

from __future__ import annotations

from xml.sax.saxutils import escape

MONO = "ui-monospace, 'Cascadia Code', 'JetBrains Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, 'Segoe UI', 'Noto Sans', Helvetica, Arial, system-ui, sans-serif"

# Light/dark tokens follow GitHub's own Primer surfaces so the art sits naturally on the page.
THEMES = {
    "dark": dict(
        surface="#0d1117", panel="#0b1118", border="#21262d", grid="#21262d",
        text="#e6edf3", muted="#8b949e", accent="#58a6ff", accent2="#a371f7", accent3="#39d0d8",
        title_a="#e6f3ff", title_b="#79c0ff", red="#ff2e88", cyan="#00e5ff", blend="screen",
    ),
    "light": dict(
        surface="#ffffff", panel="#f6f8fa", border="#d0d7de", grid="#eaeef2",
        text="#1f2328", muted="#59636e", accent="#0969da", accent2="#8250df", accent3="#1b7c83",
        title_a="#0a3069", title_b="#0969da", red="#e5007a", cyan="#0098b3", blend="multiply",
    ),
}


def esc(text: str) -> str:
    return escape(str(text), {'"': "&quot;"})


def num(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


def _timeline(dur: float, points: list[tuple[float, str]]) -> tuple[str, str]:
    """Turn (seconds, value) points into SMIL values/keyTimes; later points win on ties."""
    by_t: dict[str, str] = {}
    for t, v in sorted(points, key=lambda p: p[0]):
        by_t[num(min(max(t / dur, 0.0), 1.0))] = v
    if "0" not in by_t:
        raise ValueError("timeline needs a value at t=0")
    keys = sorted(by_t, key=float)
    return ";".join(by_t[k] for k in keys), ";".join(keys)


def discrete(attr: str, dur: float, points: list[tuple[float, object]], begin: str = "0s") -> str:
    values, key_times = _timeline(dur, [(t, str(v)) for t, v in points])
    return (f'<animate attributeName="{attr}" dur="{num(dur)}s" begin="{begin}" repeatCount="indefinite" '
            f'calcMode="discrete" values="{values}" keyTimes="{key_times}"/>')


def discrete_translate(dur: float, points: list[tuple[float, tuple[float, float]]], begin: str = "0s") -> str:
    values, key_times = _timeline(dur, [(t, f"{num(x)} {num(y)}") for t, (x, y) in points])
    return (f'<animateTransform attributeName="transform" type="translate" dur="{num(dur)}s" begin="{begin}" '
            f'repeatCount="indefinite" calcMode="discrete" values="{values}" keyTimes="{key_times}"/>')


def reveal_steps(width: float, chars: int, begin: float, per_char: float = 0.028) -> str:
    """Clip-rect width animation that uncovers monospace text one character at a time, once."""
    chars = max(chars, 1)
    step = width / chars
    values = ";".join(num(step * i) for i in range(chars + 1))
    return (f'<animate attributeName="width" begin="{num(begin)}s" dur="{num(chars * per_char)}s" '
            f'calcMode="discrete" values="{values}" fill="freeze"/>')
