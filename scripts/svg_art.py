"""Data-driven SVGs for the profile: sliding ASCII banner, about carousel and the pulse card."""

from __future__ import annotations

import re
from datetime import date, datetime

import icons
from profile_data import Profile
from svg_common import BLUE_RAMP, MONO, SANS, THEMES, discrete, discrete_translate, esc, num

try:
    import pyfiglet
except ImportError:  # pragma: no cover
    pyfiglet = None

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


def age(stamp: str, now: str) -> str:
    """Human 'x ago' between an ISO timestamp and the build time."""
    then = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    minutes = int((datetime.fromisoformat(now) - then).total_seconds() // 60)
    if minutes < 60:
        return "just now" if minutes < 5 else f"{minutes} min ago"
    if minutes < 48 * 60:
        return f"{minutes // 60}h ago"
    days = minutes // 1440
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{days // 7} weeks ago"
    return f"{days // 30} months ago"


def latest_commit(p: Profile, repo: str | None = None) -> dict | None:
    return next((c for c in p.latest_commits if repo is None or c["repo"] == repo), None)


def tech_labels(p: Profile, keys: tuple[str, ...]) -> list[str]:
    return [icons.TECH[k][0] for k in p.tech if k in keys]


WEB_TECH = ("react", "vite", "tailwind", "supabase", "reactrouter", "nextjs", "electron", "chrome", "playwright", "node")
APP_TECH = ("compose", "android", "sqlite", "ktor", "qt", "kde", "streamdeck", "docker")


def activity(p: Profile, idx: int) -> str:
    """'Kotlin, 46 commits this month' for the idx-th project I'm working on."""
    repo, commits = p.focus[idx]
    lang = f"{repo.language}, " if repo.language else ""
    if commits:
        return f"{lang}{commits} commit{'s' * (commits != 1)} this month"
    return f"{lang}pushed {age(repo.pushed_at, p.generated_at)}"


# --------------------------------------------------------------------------- banner

def banner_items(p: Profile) -> list[tuple[str, object, str]]:
    """(kind, payload, caption): 'word' -> figlet rows, 'icon' -> Simple Icons slug."""
    role = p.bio.replace("Bachelor - ", "").lower() if p.bio else "software engineering"
    items: list[tuple[str, object, str]] = [
        ("word", figlet(p.login), f"{role}, {(p.location or 'norway').lower()}"),
        ("icon", "github", f"{_fmt(p.contributions)} contributions in the last year"),
    ]
    labels = ["working on", "also working on"]
    for i, (repo, _) in enumerate(p.focus[:2]):
        if re.fullmatch(r"[A-Za-z0-9-]{1,13}", repo.name):
            items.append(("word", figlet(repo.name), f"{labels[i]}: {activity(p, i)}"))
        else:
            items.append(("icon", "git", f"{labels[i]} {repo.name}: {activity(p, i)}"))
        commit = latest_commit(p, repo.name)
        caption = (f'last commit: "{_clip(commit["message"], 44)}", {age(commit["date"], p.generated_at)}' if commit
                   else f"{repo.language}: {_clip(repo.description, 40)}")
        items.append(("icon", icons.language_slug(repo.language) or "git", caption))
    if "kde" in p.tech:
        widgets = sum(1 for r in p.recent if r.language == "QML")
        items.append(("icon", "kdeplasma", f"{widgets} kde plasma widgets"))
    langs = p.top_languages(3)
    if langs:
        items.append(("icon", "git", f"mostly writing {', '.join(langs)}"))
    items.append(("icon", "githubactions",
                  f"{_fmt(p.commits)} commits, {p.pull_requests} pull requests this year"))
    return [(k, v, c) for k, v, c in items if k == "word" or icons.simple_icon_path(v)]


def banner(p: Profile) -> str:
    W, H = 1200, 260
    t = THEMES["dark"]
    bg = "#0a0d12"
    cw, ch = 10.0, 19.0  # ANSI Shadow cell
    icon_size = 100
    art_top, art_h = 36, 6 * ch
    cap_y, cap_fs = 190, 14
    gap = 90

    x = 0.0
    blocks, shadows, logos, captions = [], [], [], []
    for kind, payload, caption in banner_items(p):
        art_w = max(len(r) for r in payload) * cw if kind == "word" else icon_size
        slot = max(art_w, len(caption) * cap_fs * 0.6 + 10)
        ax = x + (slot - art_w) / 2
        if kind == "word":
            blk, shd = art_paths(payload, ax, art_top, cw, ch)
            blocks.append(blk)
            shadows.append(shd)
        else:
            # Logo drawn like the letters: solid face plus an offset outline as its shadow.
            scale = icon_size / 24
            top = art_top + (art_h - icon_size) / 2 - 4
            d = icons.simple_icon_path(payload)
            logos.append(f'<path transform="translate({num(ax + 5)} {num(top + 5)}) scale({num(scale)})" d="{d}" '
                         f'fill="none" stroke="#fff" stroke-opacity=".4" stroke-width="{num(1.5 / scale)}"/>'
                         f'<path transform="translate({num(ax)} {num(top)}) scale({num(scale)})" d="{d}" fill="#fff"/>')
        captions.append(f'<text x="{num(x + slot / 2)}" y="{cap_y}" text-anchor="middle">{esc(caption)}</text>')
        x += slot + gap
    loop_w = x
    dur = loop_w / 62

    strip = (f'<path d="{"".join(blocks)}" fill="#fff"/>'
             f'<path d="{"".join(shadows)}" fill="none" stroke="#fff" stroke-opacity=".4" stroke-width="1.5" stroke-linejoin="round"/>'
             f'{"".join(logos)}')
    slide = (f'<animateTransform attributeName="transform" type="translate" from="24 0" to="{num(24 - loop_w)} 0" '
             f'dur="{num(dur)}s" repeatCount="indefinite"/>')

    # Now and then two thin bands of the strip jump sideways.
    glitch = []
    loop = 8.0
    bands = [(art_top + 20, 14, "#cae8ff", -14, (5.2, 5.5)), (art_top + 70, 10, "#1f6feb", 10, (5.3, 7.1))]
    for n, (by, bh, color, dx, starts) in enumerate(bands):
        op = [(0.0, 0)]
        tr = [(0.0, (0, 0))]
        for st in starts:
            op += [(st, 1), (st + 0.16, 0)]
            tr += [(st, (dx, 0)), (st + 0.06, (-dx / 2, 0)), (st + 0.11, (dx / 3, 0)), (st + 0.16, (0, 0))]
        glitch.append(
            f'<clipPath id="band{n}"><rect x="0" y="{by}" width="{W}" height="{bh}"/></clipPath>'
            f'<g clip-path="url(#band{n})" opacity="0">{discrete("opacity", loop, op)}'
            f'<g>{discrete_translate(loop, tr)}<rect width="{W}" height="{H}" fill="{color}" mask="url(#stripMask)"/></g></g>'
        )

    focus = p.focus[0][0].name if p.focus else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="T3lluz: sliding ASCII banner with GitHub activity">
  <title>T3lluz, working on {esc(focus)}, {_fmt(p.contributions)} contributions in the last year</title>
  <defs>
    <linearGradient id="ink" x1="0" y1="{art_top}" x2="0" y2="{art_top + art_h}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#a5d6ff"/><stop offset="1" stop-color="#388bfd"/>
    </linearGradient>
    <linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>
    <linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="{bg}" stop-opacity="0"/><stop offset="1" stop-color="{bg}"/></linearGradient>
    <g id="strip">{strip}</g>
    <mask id="stripMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <g>{slide}<use href="#strip"/><use href="#strip" x="{num(loop_w)}"/></g>
    </mask>
    <clipPath id="stripClip"><rect x="0" y="0" width="{W}" height="{cap_y + 16}"/></clipPath>
  </defs>

  <rect width="{W}" height="{H}" rx="6" fill="{bg}"/>

  <g clip-path="url(#stripClip)">
    <rect width="{W}" height="{H}" fill="url(#ink)" mask="url(#stripMask)"/>
    {''.join(glitch)}
    <g font-family="{MONO}" font-size="{cap_fs}" fill="{t['muted']}">
      <g>{slide}{''.join(captions)}<g transform="translate({num(loop_w)} 0)">{''.join(captions)}</g></g>
    </g>
    <rect x="0" y="0" width="60" height="{cap_y + 16}" fill="url(#fadeL)"/>
    <rect x="{W - 60}" y="0" width="60" height="{cap_y + 16}" fill="url(#fadeR)"/>
  </g>

  <g font-family="{MONO}" font-size="13" fill="{t['muted']}">
    <text x="24" y="{H - 22}"><tspan fill="{t['accent']}">t3lluz@github</tspan>:~$ updated {p.generated_at[:10]} {p.generated_at[11:16]} UTC<tspan fill="{t['text']}"> _<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></tspan></text>
    <text x="{W - 24}" y="{H - 22}" text-anchor="end">{esc(f"working on {focus}" if focus else "")}</text>
  </g>
</svg>
"""


# --------------------------------------------------------------------------- about carousel

def about_slides(p: Profile) -> list[tuple[str, list[str]]]:
    recent = [(n, pct) for n, pct, _ in (p.recent_languages or p.languages) if n != "Other"]
    langs = ", ".join(f"{n} {pct:.0f}%" for n, pct in recent[:4])
    working = [f"› {r.name}: {activity(p, i).split(', ')[-1]}" + (f", {_clip(r.description, 44)}" if r.description else "")
               for i, (r, _) in enumerate(p.focus[:3])]
    log = [f"› {c['repo']}: {_clip(c['message'], 58)} ({age(c['date'], p.generated_at)})"
           for c in p.latest_commits[:3]]
    streak = (f"› current streak: {p.current_streak} days (best {p.longest_streak})"
              if p.current_streak > 1 else f"› longest streak: {p.longest_streak} days")
    stack = [f"› last 90 days: {langs}"]
    for label, keys in (("web", WEB_TECH), ("apps", APP_TECH)):
        found = tech_labels(p, keys)
        if found:
            stack.append(f"› {label}: {', '.join(found[:5])}")
    slides = [
        ("whoami", [
            f"› {p.bio.replace('Bachelor - ', 'bachelor in ').lower() or 'software engineer'}, {p.location or 'Norway'}",
            f"› on GitHub for {p.years_on_github}",
            f"› {_fmt(p.contributions)} contributions in the last year",
        ]),
        ("git log --oneline -3", log),
        ("ls ~/projects --active", working),
        ("cat stack.txt", stack),
        ("gh stats", [
            f"› {_fmt(p.commits)} commits, {_fmt(p.pull_requests)} pull requests, {p.issues} issues",
            streak,
            f"› {p.active_days} active days, most of them on {p.busiest_weekday}s",
        ]),
        ("cat interests.txt", [
            "› android apps",
            "› kde plasma widgets and stream deck plugins",
            "› browser extensions and small web apps",
        ]),
    ]
    return [(cmd, lines) for cmd, lines in slides if lines]


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
        (f"{p.current_streak}d" if p.current_streak else p.focus[0][0].name if p.focus else "–",
         "current streak" if p.current_streak else "top repo this month"),
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
    out.append(f'<text x="{cx1}" y="40" font-size="12" text-anchor="end" fill="{t["muted"]}">last 12 months, updated {p.generated_on}</text>')
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
    out.append(f'<text x="{lx0}" y="{ly - 10}" font-size="12" fill="{t["muted"]}">Languages in my repos, by code size</text>')
    out.append(f'<clipPath id="langclip-{theme}"><rect x="{lx0}" y="{ly}" width="{lw}" height="10" rx="5"/></clipPath>')
    segs, legend = [], []
    x = lx0
    lgx = lx0
    ramp = BLUE_RAMP[theme]
    for rank, (name, pct, _) in enumerate(p.languages):
        color = ramp[-1] if name == "Other" else ramp[min(rank, len(ramp) - 2)]
        w = lw * pct / 100
        segs.append(f'<rect x="{num(x)}" y="{ly}" width="{num(max(w - 2, 1))}" height="10" fill="{color}"/>')
        x += w
        label = f"{name} {pct:.1f}%"
        slug = icons.language_slug(name)
        path = icons.simple_icon_path(slug) if slug else None
        mark = (f'<path transform="translate({num(lgx - 1)} {ly + 25}) scale(.5)" d="{path}" fill="{color}"/>' if path
                else f'<circle cx="{num(lgx + 5)}" cy="{ly + 31}" r="5" fill="{color}"/>')
        legend.append(mark +
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
