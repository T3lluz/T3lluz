"""Data-driven SVGs for the profile: terminal banner, about carousel and the pulse card."""

from __future__ import annotations

import random
from datetime import date

from profile_data import Profile
from svg_common import MONO, SANS, THEMES, discrete, discrete_translate, esc, num, reveal_steps

# figlet -f "ANSI Shadow" T3LLUZ — drawn as vectors so it renders identically in every browser/font.
LOGO = [
    "████████╗██████╗ ██╗     ██╗     ██╗   ██╗███████╗",
    "╚══██╔══╝╚════██╗██║     ██║     ██║   ██║╚══███╔╝",
    "   ██║    █████╔╝██║     ██║     ██║   ██║  ███╔╝ ",
    "   ██║    ╚═══██╗██║     ██║     ██║   ██║ ███╔╝  ",
    "   ██║   ██████╔╝███████╗███████╗╚██████╔╝███████╗",
    "   ╚═╝   ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚══════╝",
]


def _box_segments(ch: str, x: float, y: float, w: float, h: float) -> str:
    cx, cy, d, e = x + w / 2, y + h / 2, w * 0.2, h * 0.14
    left, right, top, bottom = x, x + w, y, y + h
    shapes = {
        "═": [(left, cy - e, right, cy - e), (left, cy + e, right, cy + e)],
        "║": [(cx - d, top, cx - d, bottom), (cx + d, top, cx + d, bottom)],
        "╗": [(left, cy - e, cx + d, cy - e, cx + d, bottom), (left, cy + e, cx - d, cy + e, cx - d, bottom)],
        "╔": [(right, cy - e, cx - d, cy - e, cx - d, bottom), (right, cy + e, cx + d, cy + e, cx + d, bottom)],
        "╝": [(left, cy + e, cx + d, cy + e, cx + d, top), (left, cy - e, cx - d, cy - e, cx - d, top)],
        "╚": [(right, cy + e, cx - d, cy + e, cx - d, top), (right, cy - e, cx + d, cy - e, cx + d, top)],
    }
    out = []
    for pts in shapes.get(ch, []):
        coords = [num(v) for v in pts]
        pairs = [f"{coords[i]} {coords[i + 1]}" for i in range(0, len(coords), 2)]
        out.append("M" + "L".join(pairs))
    return "".join(out)


def logo_paths(x0: float, y0: float, cw: float, ch: float) -> tuple[str, str]:
    blocks, lines = [], []
    for r, row in enumerate(LOGO):
        c = 0
        while c < len(row):
            if row[c] == "█":
                s = c
                while c < len(row) and row[c] == "█":
                    c += 1
                blocks.append(f"M{num(x0 + s * cw)} {num(y0 + r * ch)}h{num((c - s) * cw)}v{num(ch + 0.5)}"
                              f"h{num(-(c - s) * cw)}z")
                continue
            lines.append(_box_segments(row[c], x0 + c * cw, y0 + r * ch, cw, ch))
            c += 1
    return "".join(blocks), "".join(lines)


def _fmt(n: int) -> str:
    return f"{n:,}"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _age(pushed_at: str, today: date) -> str:
    days = (today - date.fromisoformat(pushed_at[:10])).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{days // 7} weeks ago"
    return f"{days // 30} months ago"


# --------------------------------------------------------------------------- banner

def banner(p: Profile) -> str:
    W, H = 1200, 420
    t = THEMES["dark"]
    today = date.fromisoformat(p.generated_on)
    cw, chh = 12.0, 22.0
    lx, ly = 48, 118
    blocks, shadow = logo_paths(lx, ly, cw, chh)
    logo_w = len(LOGO[0]) * cw
    logo_h = len(LOGO) * chh
    rng = random.Random(p.generated_on)

    now = p.recent[0] if p.recent else None
    info = [
        ("OS", "Linux · KDE Plasma"),
        ("Host", f"GitHub · {p.location}" if p.location else "GitHub"),
        ("Uptime", f"{p.years_on_github} of pushing code"),
        ("Focus", p.bio.replace("Bachelor - ", "BSc ") if p.bio else "Software engineering"),
        ("Langs", " · ".join(p.top_languages(4))),
        ("Repos", f"{p.public_repos} public · {p.stars} stars · {p.merged_prs} merged PRs"),
        ("Year", f"{_fmt(p.contributions)} contributions · {_fmt(p.commits)} commits"),
        ("Streak", f"{p.current_streak} day{'s' * (p.current_streak != 1)} now · best {p.longest_streak}"
         if p.current_streak > 1 else f"best {p.longest_streak} days · {p.active_days} active days"),
        ("Now", f"{now.name} ({now.language})" if now else "something new"),
    ]
    ix, iy, row_h, fs = 700, 112, 23, 15
    char_w = fs * 0.6
    info_svg = [
        f'<text x="{ix}" y="{iy}" font-size="{fs}" fill="{t["accent"]}" font-weight="700">t3lluz<tspan fill="{t["muted"]}">@</tspan>github</text>',
        f'<text x="{ix}" y="{iy + 12}" font-size="{fs}" fill="{t["border"]}">{"─" * 20}</text>',
    ]
    clips = []
    for i, (label, value) in enumerate(info):
        y = iy + 34 + i * row_h
        line = f"{label}: {value}"
        line = _clip(line, 52)
        value = line[len(label) + 2:]
        clips.append(f'<clipPath id="info{i}"><rect x="{ix}" y="{y - 16}" height="22" width="0">'
                     f'{reveal_steps(len(line) * char_w + 4, len(line), 1.3 + i * 0.16, 0.012)}</rect></clipPath>')
        info_svg.append(
            f'<text x="{ix}" y="{y}" font-size="{fs}" clip-path="url(#info{i})">'
            f'<tspan fill="{t["accent3"]}" font-weight="700">{esc(label)}</tspan>'
            f'<tspan fill="{t["muted"]}">: </tspan><tspan fill="{t["text"]}">{esc(value)}</tspan></text>'
        )
    palette = ["#0d1117", "#ff7b72", "#7ee787", "#d29922", "#58a6ff", "#bc8cff", "#39d0d8", "#e6edf3"]
    py = iy + 34 + len(info) * row_h - 6
    for i, color in enumerate(palette):
        info_svg.append(
            f'<rect x="{ix + i * 30}" y="{py}" width="26" height="14" rx="2" fill="{color}" stroke="{t["border"]}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{num(3.0 + i * 0.05)}s" fill="freeze"/></rect>'
        )

    # Ticker: live facts, scrolled seamlessly (two copies, exact width via textLength).
    items = [f"{_fmt(p.contributions)} contributions in the last year",
             f"{_fmt(p.commits)} commits · {_fmt(p.pull_requests)} pull requests",
             f"longest streak: {p.longest_streak} days"]
    if p.best_day[1]:
        items.append(f"best day: {p.best_day[1]} contributions on {date.fromisoformat(p.best_day[0]):%d %b %Y}")
    if p.busiest_weekday:
        items.append(f"most productive on {p.busiest_weekday}s")
    items += [f"{r.name} updated {_age(r.pushed_at, today)}" for r in p.recent[:4]]
    items.append(f"refreshed {p.generated_on}")
    tick_fs = 14
    tick_cw = tick_fs * 0.6
    sep = "   ◆   "
    tick = sep.join(items) + sep
    while len(tick) * tick_cw < W:
        tick += tick
    tick_w = len(tick) * tick_cw
    tick_y = H - 34

    glitch_starts = [4.2, 4.5, 7.6]
    loop = 9.0
    def slice_layer(i: int) -> str:
        band_y = ly + rng.uniform(0, logo_h - 20)
        band_h = rng.uniform(8, 22)
        op = [(0.0, 0)]
        tr = [(0.0, (0, 0))]
        for s in glitch_starts:
            dx = rng.choice([-1, 1]) * rng.uniform(8, 26)
            op += [(s, 1), (s + 0.18, 0)]
            tr += [(s, (dx, 0)), (s + 0.06, (-dx / 2, 0)), (s + 0.12, (dx / 3, 0)), (s + 0.18, (0, 0))]
        return (f'<clipPath id="lslice{i}"><rect x="0" y="{num(band_y)}" width="{W}" height="{num(band_h)}"/></clipPath>'
                f'<g clip-path="url(#lslice{i})" opacity="0">{discrete("opacity", loop, op, "3s")}'
                f'<g>{discrete_translate(loop, tr, "3s")}<use href="#logoShadow"/><use href="#logoBlocks" fill="url(#logoFill)"/></g></g>')

    def split(color: str, sign: int) -> str:
        op = [(0.0, 0)]
        tr = [(0.0, (0, 0))]
        for s in glitch_starts:
            op += [(s, 0.9), (s + 0.2, 0)]
            tr += [(s, (sign * 5, 0)), (s + 0.08, (-sign * 3, 1)), (s + 0.14, (sign * 2, 0)), (s + 0.2, (0, 0))]
        return (f'<g opacity="0" style="mix-blend-mode:screen">{discrete("opacity", loop, op, "3s")}'
                f'<use href="#logoBlocks" fill="{color}">{discrete_translate(loop, tr, "3s")}</use></g>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="T3lluz terminal banner with live GitHub stats">
  <title>T3lluz · {_fmt(p.contributions)} contributions in the last year</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#111827"/></linearGradient>
    <linearGradient id="logoFill" x1="{lx}" y1="0" x2="{lx + logo_w}" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#00e5ff"/><stop offset=".5" stop-color="#58a6ff"/><stop offset="1" stop-color="#a371f7"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="#0a0f16"/><stop offset="1" stop-color="#0a0f16" stop-opacity="0"/></linearGradient>
    <linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="#0a0f16" stop-opacity="0"/><stop offset="1" stop-color="#0a0f16"/></linearGradient>
    <filter id="neon" x="-5%" y="-20%" width="110%" height="140%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".035"/></pattern>
    <path id="logoBlocks" d="{blocks}"/>
    <path id="logoShadow" d="{shadow}" fill="none" stroke="#1f6feb" stroke-width="1.6" stroke-linejoin="round"/>
    <clipPath id="logoClip"><use href="#logoBlocks"/></clipPath>
    <clipPath id="logoReveal"><rect x="{lx - 4}" y="{ly - 4}" height="{logo_h + 8}" width="0">{reveal_steps(logo_w + 8, len(LOGO[0]), 0.9, 0.018)}</rect></clipPath>
    <clipPath id="cmd"><rect x="48" y="62" height="24" width="0">{reveal_steps(9 * 17 + 2, 17, 0.2, 0.035)}</rect></clipPath>
    <clipPath id="tagline"><rect x="{lx}" y="{ly + logo_h + 14}" height="26" width="0">{reveal_steps(600, 60, 2.2, 0.014)}</rect></clipPath>
    <clipPath id="tickerClip"><rect x="30" y="{tick_y - 22}" width="{W - 60}" height="32"/></clipPath>
    {''.join(clips)}
  </defs>
  <rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="#30363d"/>
  <rect x="16" y="16" width="{W - 32}" height="{H - 32}" rx="11" fill="#0a0f16" stroke="#1f2a38"/>
  <rect x="16" y="16" width="{W - 32}" height="30" rx="11" fill="#111822"/>
  <rect x="16" y="36" width="{W - 32}" height="10" fill="#111822"/>
  <circle cx="36" cy="31" r="5.5" fill="#ff5f57"/><circle cx="54" cy="31" r="5.5" fill="#febc2e"/><circle cx="72" cy="31" r="5.5" fill="#28c840"/>
  <text x="{W / 2}" y="36" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{t['muted']}">t3lluz@github: ~</text>

  <g font-family="{MONO}">
    <text x="48" y="80" font-size="15" clip-path="url(#cmd)"><tspan fill="#7ee787">❯</tspan><tspan fill="{t['text']}"> fastfetch</tspan><tspan fill="{t['muted']}"> --live</tspan></text>

    <g clip-path="url(#logoReveal)">
      <g filter="url(#neon)"><use href="#logoShadow"/><use href="#logoBlocks" fill="url(#logoFill)"/></g>
      <g clip-path="url(#logoClip)">
        <rect x="-300" y="{ly}" width="220" height="{logo_h + 2}" fill="url(#shine)" transform="skewX(-20)">
          <animate attributeName="x" begin="2.4s" dur="7s" repeatCount="indefinite" values="{lx - 300};{lx + logo_w + 220};{lx + logo_w + 220}" keyTimes="0;.22;1"/>
        </rect>
      </g>
      {split('#ff2e88', -1)}{split('#00e5ff', 1)}
      {slice_layer(0)}{slice_layer(1)}{slice_layer(2)}
    </g>
    <text x="{lx}" y="{ly + logo_h + 32}" font-size="15" fill="{t['muted']}" clip-path="url(#tagline)"><tspan fill="{t['accent']}">//</tspan> building the tools I want to use every day</text>
    <text x="{lx}" y="{ly + logo_h + 74}" font-size="15"><tspan fill="#7ee787">❯</tspan><tspan fill="{t['text']}"> git push</tspan><tspan fill="{t['muted']}"> --daily</tspan>
      <tspan fill="{t['accent']}">▋<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></tspan></text>

    {''.join(info_svg)}

    <rect x="16" y="{tick_y - 26}" width="{W - 32}" height="1" fill="#1f2a38"/>
    <g clip-path="url(#tickerClip)">
      <g>
        <animateTransform attributeName="transform" type="translate" from="0 0" to="{num(-tick_w)} 0" dur="{num(tick_w / 55)}s" repeatCount="indefinite"/>
        <text x="40" y="{tick_y}" font-size="{tick_fs}" fill="{t['muted']}" textLength="{num(tick_w)}" lengthAdjust="spacing" xml:space="preserve">{esc(tick)}</text>
        <text x="{num(40 + tick_w)}" y="{tick_y}" font-size="{tick_fs}" fill="{t['muted']}" textLength="{num(tick_w)}" lengthAdjust="spacing" xml:space="preserve">{esc(tick)}</text>
      </g>
      <rect x="30" y="{tick_y - 22}" width="60" height="32" fill="url(#fadeL)"/>
      <rect x="{W - 90}" y="{tick_y - 22}" width="60" height="32" fill="url(#fadeR)"/>
    </g>
  </g>
  <rect x="16" y="46" width="{W - 32}" height="{H - 62}" fill="url(#scan)" pointer-events="none"/>
</svg>
"""


# --------------------------------------------------------------------------- about carousel

def about_slides(p: Profile) -> list[tuple[str, list[str]]]:
    langs = " · ".join(f"{n} {pct:.0f}%" for n, pct, _ in p.languages[:4] if n != "Other")
    building = [f"› {r.name} — {_clip(r.description, 62) or r.language}" for r in p.recent[:3]]
    streak = (f"› on a {p.current_streak}-day streak right now (best: {p.longest_streak})"
              if p.current_streak > 1 else f"› longest streak this year: {p.longest_streak} days in a row")
    return [
        ("cat whoami.txt", [
            f"› {p.bio.replace('Bachelor - ', 'bachelor in ').lower() or 'software engineer'} · based in {p.location or 'Norway'}",
            f"› {p.years_on_github} on GitHub · {_fmt(p.contributions)} contributions in the last year",
            "› I build the tools I actually want to use, then keep polishing them",
        ]),
        ("ls ~/projects --sort=recent", building),
        ("tokei ~/code --sort code", [
            f"› languages: {langs}",
            "› web: React 19 · Vite · TypeScript · Tailwind · Supabase",
            "› apps: Kotlin + Jetpack Compose · Qt/QML Plasma widgets · Python",
        ]),
        ("gh stats --year", [
            f"› {_fmt(p.commits)} commits · {_fmt(p.pull_requests)} pull requests · {p.issues} issues",
            streak,
            f"› {p.active_days} active days · most productive on {p.busiest_weekday}s",
        ]),
        ("cat ~/.enjoy", [
            "› turning small daily annoyances into polished little tools",
            "› Linux desktop hacking: Plasma widgets, Stream Deck plugins, HID",
            "› sweating the details: motion, theming and how an app feels",
        ]),
    ]


def about(p: Profile, theme: str) -> str:
    t = THEMES[theme]
    W, H = 1000, 150
    slides = about_slides(p)
    slot = 7.5
    dur = slot * len(slides)
    fs, cw = 17, 17 * 0.6
    ys = [66, 96, 126]
    parts, clips = [], []
    for si, (cmd, lines) in enumerate(slides):
        start = si * slot
        vis = [(0.0, 1 if si == 0 else 0), (start, 1), (start + slot, 0)]
        rows = [(f"❯ {cmd}", 30, t["muted"], 0.1)] + [(ln, y, t["text"], 0.55 + li * 0.45) for li, (ln, y) in enumerate(zip(lines, ys))]
        body = []
        for ri, (txt, y, color, delay) in enumerate(rows):
            n = len(txt)
            per = 0.03 if ri == 0 else 0.012
            values = ";".join(num(min(k, n) * cw + (4 if k >= n else 0)) for k in range(n + 1))
            times = ";".join(num((start + delay + k * per) / dur) for k in range(n + 1))
            cid = f"a{si}_{ri}"
            clips.append(
                f'<clipPath id="{cid}"><rect x="14" y="{y - 20}" height="28" width="0">'
                f'<animate attributeName="width" dur="{num(dur)}s" repeatCount="indefinite" calcMode="discrete" '
                f'values="0;{values}" keyTimes="0;{times}"/></rect></clipPath>'
            )
            fill = f'<tspan fill="{t["accent"]}">❯</tspan>{esc(txt[1:])}' if ri == 0 else \
                f'<tspan fill="{t["accent"]}">›</tspan>{esc(txt[1:])}'
            body.append(f'<text x="16" y="{y}" fill="{color}" clip-path="url(#{cid})" xml:space="preserve">{fill}</text>')
        parts.append(f'<g opacity="{1 if si == 0 else 0}">{discrete("opacity", dur, vis)}{"".join(body)}</g>')

    dots = []
    for si in range(len(slides)):
        x = W - 20 - (len(slides) - 1 - si) * 16
        pts = [(0.0, 1 if si == 0 else 0.25), (si * slot, 1), ((si + 1) * slot, 0.25)]
        dots.append(f'<circle cx="{x}" cy="24" r="4" fill="{t["accent"]}" opacity="{1 if si == 0 else 0.25}">'
                    f'{discrete("opacity", dur, pts)}</circle>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="About T3lluz">
  <title>About T3lluz</title>
  <desc>{esc(' / '.join(' '.join(lines) for _, lines in slides))}</desc>
  <defs>{''.join(clips)}</defs>
  <g font-family="{MONO}" font-size="{fs}">{''.join(parts)}</g>
  {''.join(dots)}
</svg>
"""


# --------------------------------------------------------------------------- pulse card

def _bar(x: float, base: float, w: float, h: float) -> str:
    r = min(3.0, w / 2, h)
    top = base - h
    return (f"M{num(x)} {num(base)}V{num(top + r)}Q{num(x)} {num(top)} {num(x + r)} {num(top)}"
            f"H{num(x + w - r)}Q{num(x + w)} {num(top)} {num(x + w)} {num(top + r)}V{num(base)}Z")


def pulse(p: Profile, theme: str) -> str:
    t = THEMES[theme]
    W, H = 1000, 390
    tiles = [
        (_fmt(p.contributions), "contributions"),
        (_fmt(p.commits), "commits"),
        (_fmt(p.pull_requests), "pull requests"),
        (f"{p.longest_streak}d", "longest streak"),
        (str(p.active_days), "active days"),
        (f"{p.current_streak}d" if p.current_streak else p.recent[0].name if p.recent else "–",
         "current streak" if p.current_streak else "latest push"),
    ]
    out = []
    for i, (value, label) in enumerate(tiles):
        col, row = i % 2, i // 2
        x, y = 24 + col * 172, 64 + row * 78
        size = 26 if len(value) <= 8 else 16
        out.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{num(0.1 + i * 0.08)}s" dur=".4s" fill="freeze"/>'
            f'<rect x="{x}" y="{y}" width="160" height="68" rx="8" fill="{t["panel"]}" stroke="{t["border"]}"/>'
            f'<text x="{x + 14}" y="{y + 34}" font-size="{size}" font-weight="700" fill="{t["text"]}">{esc(value)}</text>'
            f'<text x="{x + 14}" y="{y + 54}" font-size="12" fill="{t["muted"]}">{esc(label)}</text></g>'
        )

    # Weekly contributions, one hue; label only the peak.
    cx0, cx1, top, base = 400, 976, 70, 262
    weeks = p.weekly[-53:]
    peak = max((c for _, c in weeks), default=0) or 1
    ceiling = max(10, -(-peak // 10) * 10)
    slot = (cx1 - cx0) / max(len(weeks), 1)
    bw = max(slot - 2, 2)
    out.append(f'<text x="{cx0}" y="40" font-size="14" font-weight="600" fill="{t["text"]}">Weekly contributions</text>')
    out.append(f'<text x="{cx1}" y="40" font-size="12" text-anchor="end" fill="{t["muted"]}">last 12 months · updated {p.generated_on}</text>')
    for frac in (0.5, 1.0):
        gy = base - (base - top) * frac
        out.append(f'<line x1="{cx0}" x2="{cx1}" y1="{num(gy)}" y2="{num(gy)}" stroke="{t["grid"]}" stroke-dasharray="2 4"/>')
        out.append(f'<text x="{cx0 - 6}" y="{num(gy + 4)}" font-size="11" text-anchor="end" fill="{t["muted"]}">{int(ceiling * frac)}</text>')
    out.append(f'<line x1="{cx0}" x2="{cx1}" y1="{base}" y2="{base}" stroke="{t["border"]}"/>')
    last_month = None
    peak_i = max(range(len(weeks)), key=lambda i: weeks[i][1]) if weeks else -1
    for i, (start, count) in enumerate(weeks):
        x = cx0 + i * slot + (slot - bw) / 2
        h = (base - top) * count / ceiling
        d = date.fromisoformat(start)
        if d.month != last_month and d.day <= 7:
            out.append(f'<text x="{num(x)}" y="{base + 18}" font-size="11" fill="{t["muted"]}">{d:%b}</text>')
            last_month = d.month
        if count == 0:
            continue
        color = t["accent"] if i != len(weeks) - 1 else t["accent2"]
        # Grow from the baseline: scale an inner group whose origin sits on the axis.
        out.append(
            f'<g transform="translate(0 {base})"><g transform="scale(1 0)">'
            f'<animateTransform attributeName="transform" type="scale" values="1 0;1 1" '
            f'begin="{num(0.3 + i * 0.012)}s" dur=".5s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/>'
            f'<path d="{_bar(x, 0, bw, h)}" fill="{color}"/></g></g>'
        )
        if i == peak_i:
            out.append(f'<text x="{num(x + bw / 2)}" y="{num(base - h - 8)}" font-size="11" font-weight="600" '
                       f'text-anchor="middle" fill="{t["text"]}">{count}</text>')

    # Language split across my own repos.
    ly, lx0, lw = 330, 24, W - 48
    out.append(f'<text x="{lx0}" y="{ly - 10}" font-size="12" fill="{t["muted"]}">Languages across my repos (by code size)</text>')
    out.append(f'<clipPath id="langclip-{theme}"><rect x="{lx0}" y="{ly}" width="{lw}" height="10" rx="5"/></clipPath>')
    segs, legend = [], []
    x = lx0
    lgx = lx0
    for name, pct, color in p.languages:
        w = lw * pct / 100
        segs.append(f'<rect x="{num(x)}" y="{ly}" width="{num(max(w - 2, 1))}" height="10" fill="{color}"/>')
        x += w
        label = f"{name} {pct:.1f}%"
        legend.append(f'<circle cx="{num(lgx + 5)}" cy="{ly + 31}" r="5" fill="{color}"/>'
                      f'<text x="{num(lgx + 15)}" y="{ly + 35}" font-size="12" fill="{t["text"]}">{esc(name)} '
                      f'<tspan fill="{t["muted"]}">{pct:.1f}%</tspan></text>')
        lgx += 15 + len(label) * 7 + 22
    out.append(f'<g clip-path="url(#langclip-{theme})"><rect x="{lx0}" y="{ly}" width="{lw}" height="10" fill="{t["grid"]}"/>{"".join(segs)}</g>')
    out += legend

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub activity for {esc(p.login)}">
  <title>{_fmt(p.contributions)} contributions, {_fmt(p.commits)} commits and {_fmt(p.pull_requests)} pull requests in the last year</title>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t['surface']}" stroke="{t['border']}"/>
  <text x="24" y="40" font-family="{SANS}" font-size="14" font-weight="600" fill="{t['text']}">Last 12 months</text>
  <g font-family="{SANS}">{''.join(out)}</g>
</svg>
"""
