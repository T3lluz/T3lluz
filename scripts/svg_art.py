"""Data-driven SVGs for the profile: sliding ASCII banner, about carousel and the pulse card."""

from __future__ import annotations

import re
from datetime import date

from profile_data import Profile
from svg_common import MONO, SANS, THEMES, discrete, discrete_translate, esc, num

try:
    import pyfiglet
except ImportError:  # pragma: no cover
    pyfiglet = None

# Hand-drawn ASCII icons (monospace, padded to a rectangle when rendered).
TUX = [
    "    .--.    ",
    "   |o_o |   ",
    "   |:_/ |   ",
    "  //   \\ \\  ",
    " (|     | ) ",
    "/'\\_   _/`\\ ",
    "\\___)=(___/ ",
]
ARCH = [
    "      /\\      ",
    "     /  \\     ",
    "    /\\   \\    ",
    "   /      \\   ",
    "  /   ,,   \\  ",
    " /   |  |  -\\ ",
    "/_-''    ''-_\\",
]
TERMINAL = [
    " ______________ ",
    "|.------------.|",
    "|| >_         ||",
    "||            ||",
    "||            ||",
    "|'------------'|",
    " '------------' ",
]
CHIP = [
    "   | | | | |   ",
    " .-'-'-'-'-'-. ",
    "-|  .-----.  |-",
    "-|  | </> |  |-",
    "-|  '-----'  |-",
    " '-.-.-.-.-.-' ",
    "   | | | | |   ",
]


def figlet(word: str) -> list[str]:
    """ANSI Shadow rows for a word (only █ and double box-drawing characters)."""
    if pyfiglet is None:
        raise SystemExit("pyfiglet is required: pip install -r scripts/requirements.txt")
    rows = [r.rstrip() for r in pyfiglet.figlet_format(word.upper(), font="ansi_shadow", width=1000).split("\n")]
    while rows and not rows[-1]:
        rows.pop()
    width = max(len(r) for r in rows)
    return [r.ljust(width) for r in rows]


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
        out.append("M" + "L".join(f"{coords[i]} {coords[i + 1]}" for i in range(0, len(coords), 2)))
    return "".join(out)


def art_paths(rows: list[str], x0: float, y0: float, cw: float, ch: float) -> tuple[str, str]:
    """Vector version of ANSI Shadow art: solid blocks + thin double-line shadows."""
    blocks, lines = [], []
    for r, row in enumerate(rows):
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


def activity(p: Profile, idx: int) -> str:
    """'Kotlin · 46 commits this month' for the idx-th project I'm focused on."""
    repo, commits = p.focus[idx]
    lang = f"{repo.language} · " if repo.language else ""
    if commits:
        return f"{lang}{commits} commit{'s' * (commits != 1)} this month"
    return f"{lang}pushed {_age(repo.pushed_at, date.fromisoformat(p.generated_on))}"


# --------------------------------------------------------------------------- banner

def banner_items(p: Profile) -> list[tuple[str, list[str], str]]:
    projects = [i for i, (r, _) in enumerate(p.focus) if re.fullmatch(r"[A-Za-z0-9-]{1,13}", r.name)]
    langs = [(n, pct) for n, pct, _ in (p.recent_languages or p.languages) if n != "Other"]
    role = p.bio.replace("Bachelor - ", "").lower() if p.bio else "software engineering"
    items = [("word", figlet(p.login), f"{role} · {(p.location or 'norway').lower()}"),
             ("icon", TUX, "linux desktop tinkerer · kde plasma")]
    if projects:
        items.append(("word", figlet(p.focus[projects[0]][0].name), f"now building · {activity(p, projects[0])}"))
    items.append(("icon", TERMINAL, f"{_fmt(p.contributions)} contributions in the last 12 months"))
    if len(projects) > 1:
        items.append(("word", figlet(p.focus[projects[1]][0].name), f"also shipping · {activity(p, projects[1])}"))
    items.append(("icon", CHIP, "recently writing " + " · ".join(n for n, _ in langs[:3])))
    if langs:
        items.append(("word", figlet(langs[0][0]), f"top language · last 90 days · {langs[0][1]:.0f}% of my commits"))
    items.append(("icon", ARCH, f"{p.active_days} active days · best streak {p.longest_streak} days"))
    return items


def banner(p: Profile) -> str:
    W, H = 1200, 320
    t = THEMES["dark"]
    cw, ch = 10.0, 19.0          # ANSI Shadow cell
    icon_fs, icon_lh = 16, 17.0  # ASCII icon text
    icon_cw = icon_fs * 0.6
    art_top, art_h = 94, 6 * ch
    cap_y, cap_fs = 246, 14
    gap = 90

    x = 0.0
    blocks, shadows, icons, captions = [], [], [], []
    for kind, rows, caption in banner_items(p):
        cols = max(len(r) for r in rows)
        art_w = cols * (cw if kind == "word" else icon_cw)
        cap_w = len(caption) * cap_fs * 0.6 + 26
        slot = max(art_w, cap_w)
        ax = x + (slot - art_w) / 2
        if kind == "word":
            b, s = art_paths(rows, ax, art_top, cw, ch)
            blocks.append(b)
            shadows.append(s)
        else:
            top = art_top + (art_h - len(rows) * icon_lh) / 2 + icon_fs * 0.8
            for li, row in enumerate(rows):
                if row.strip():
                    icons.append(f'<text x="{num(ax)}" y="{num(top + li * icon_lh)}" textLength="{num(cols * icon_cw)}" '
                                 f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc(row.ljust(cols))}</text>')
        captions.append(f'<text x="{num(x + slot / 2)}" y="{cap_y}" text-anchor="middle">'
                        f'<tspan fill="{t["accent"]}">// </tspan>{esc(caption)}</text>')
        x += slot + gap
    loop_w = x
    dur = loop_w / 62

    strip = (f'<path d="{"".join(blocks)}" fill="#fff"/>'
             f'<path d="{"".join(shadows)}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.5" stroke-linejoin="round"/>'
             f'<g font-family="{MONO}" font-size="{icon_fs}" font-weight="700" fill="#fff">{"".join(icons)}</g>')
    slide = (f'<animateTransform attributeName="transform" type="translate" from="44 0" to="{num(44 - loop_w)} 0" '
             f'dur="{num(dur)}s" repeatCount="indefinite"/>')

    # Occasional glitch: two thin bands of the strip jump sideways with a colour tint.
    glitch = []
    loop = 8.0
    bands = [(art_top + 20, 14, "#ff2e88", -14, (5.2, 5.5)), (art_top + 70, 10, "#00e5ff", 10, (5.3, 7.1))]
    for i, (by, bh, color, dx, starts) in enumerate(bands):
        op = [(0.0, 0)]
        tr = [(0.0, (0, 0))]
        for s in starts:
            op += [(s, 1), (s + 0.16, 0)]
            tr += [(s, (dx, 0)), (s + 0.06, (-dx / 2, 0)), (s + 0.11, (dx / 3, 0)), (s + 0.16, (0, 0))]
        glitch.append(
            f'<clipPath id="band{i}"><rect x="0" y="{by}" width="{W}" height="{bh}"/></clipPath>'
            f'<g clip-path="url(#band{i})" opacity="0">{discrete("opacity", loop, op)}'
            f'<g>{discrete_translate(loop, tr)}<rect width="{W}" height="{H}" fill="{color}" mask="url(#stripMask)"/></g></g>'
        )

    focus = p.focus[0][0].name if p.focus else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Sliding ASCII banner for T3lluz with live GitHub activity">
  <title>T3lluz · now building {esc(focus)} · {_fmt(p.contributions)} contributions in the last year</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#161b22"/></linearGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#00e5ff"/><stop offset=".35" stop-color="#58a6ff"/>
      <stop offset=".65" stop-color="#a371f7"/><stop offset="1" stop-color="#00e5ff"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="#58a6ff" stop-opacity=".4"/><stop offset="1" stop-color="#58a6ff" stop-opacity=".04"/></linearGradient>
    <linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="#0a0f16"/><stop offset="1" stop-color="#0a0f16" stop-opacity="0"/></linearGradient>
    <linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="#0a0f16" stop-opacity="0"/><stop offset="1" stop-color="#0a0f16"/></linearGradient>
    <filter id="neon" x="-5%" y="-30%" width="110%" height="160%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".035"/></pattern>
    <g id="strip">{strip}</g>
    <mask id="stripMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <g>{slide}<use href="#strip"/><use href="#strip" x="{num(loop_w)}"/></g>
    </mask>
    <clipPath id="stripClip"><rect x="32" y="70" width="{W - 64}" height="196" rx="6"/></clipPath>
  </defs>

  <rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="13" fill="none" stroke="#30363d"/>
  <rect x="20" y="20" width="{W - 40}" height="{H - 40}" rx="10" fill="#0b1118" stroke="#1f2a38"/>
  <rect x="20" y="52" width="{W - 40}" height="1" fill="url(#rule)"/>
  <rect x="20" y="58" width="{W - 40}" height="1" fill="url(#rule)"/>
  <rect x="28" y="66" width="{W - 56}" height="204" rx="8" fill="#0a0f16" stroke="#172231"/>
  <circle cx="38" cy="36" r="5.2" fill="#ff6b6b"/><circle cx="56" cy="36" r="5.2" fill="#f7b955"/><circle cx="74" cy="36" r="5.2" fill="#7ee787"/>
  <text x="{W / 2}" y="41" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{t['muted']}">t3lluz@github: ~/projects</text>

  <g clip-path="url(#stripClip)">
    <g filter="url(#neon)"><rect width="{W}" height="{H}" fill="url(#ink)" mask="url(#stripMask)"/></g>
    {''.join(glitch)}
    <g font-family="{MONO}" font-size="{cap_fs}" fill="{t['muted']}">
      <g>{slide}{''.join(captions)}<g transform="translate({num(loop_w)} 0)">{''.join(captions)}</g></g>
    </g>
    <rect x="32" y="70" width="70" height="196" fill="url(#fadeL)"/>
    <rect x="{W - 102}" y="70" width="70" height="196" fill="url(#fadeR)"/>
  </g>
  <rect x="28" y="66" width="{W - 56}" height="204" fill="url(#scan)"/>

  <g font-family="{MONO}" font-size="13">
    <text x="36" y="292" fill="{t['muted']}"><tspan fill="#7ee787">❯</tspan> live · refreshed {p.generated_on}<tspan fill="{t['accent']}"> ▋<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></tspan></text>
    <text x="{W - 36}" y="292" text-anchor="end" fill="{t['muted']}">{esc(f"now building: {focus}" if focus else "")}</text>
  </g>
</svg>
"""


# --------------------------------------------------------------------------- about carousel

def about_slides(p: Profile) -> list[tuple[str, list[str]]]:
    recent = [(n, pct) for n, pct, _ in (p.recent_languages or p.languages) if n != "Other"]
    langs = " · ".join(f"{n} {pct:.0f}%" for n, pct in recent[:4])
    building = [f"› {r.name} ({activity(p, i).split(' · ')[-1]}) — {_clip(r.description, 44) or r.language}"
                for i, (r, _) in enumerate(p.focus[:3])]
    streak = (f"› on a {p.current_streak}-day streak right now (best: {p.longest_streak})"
              if p.current_streak > 1 else f"› longest streak this year: {p.longest_streak} days in a row")
    return [
        ("cat whoami.txt", [
            f"› {p.bio.replace('Bachelor - ', 'bachelor in ').lower() or 'software engineer'} · based in {p.location or 'Norway'}",
            f"› {p.years_on_github} on GitHub · {_fmt(p.contributions)} contributions in the last year",
            "› I build the tools I actually want to use, then keep polishing them",
        ]),
        ("git log --since=\"1 month\" --stat", building),
        ("tokei ~/code --recent", [
            f"› last 90 days: {langs}",
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
