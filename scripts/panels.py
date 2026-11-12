"""Every image in the README: the header strip, the windows, the snake frame and the link buttons."""

from __future__ import annotations

import re
from datetime import date

import detect
from config import LINKS, TAGLINE
from data import Profile, day
from theme import (BG, BLUE, BOTTOM, DESK, DIM, FAINT, FG, FULL, GREEN, HALF, LINE, LINE2, M, MAGENTA, ORANGE, PAD,
                   RAISE, SMALL, SOFT, TEAL, TOP, V, X0, Y0, YELLOW, bar_line, brand, chip, desk, discrete, esc, fit,
                   glitch, has_brand, logo, logo_def, lucide, num, svg, text, tile, tw, window, x1, NARROW_CSS)

TABS = [("home", "house"), ("projects", "folder-git-2"), ("log", "git-commit-horizontal"), ("activity", "activity"),
        ("stack", "package"), ("upstream", "git-pull-request")]


def _stars(count: int) -> str:
    return f"{count / 1000:.1f}k" if count >= 1000 else str(count)


# --------------------------------------------------------------------------- header

def _typed(lines: list[str], x: float, y: float, slot: float = 6.0) -> str:
    """One prompt line that types each entry in turn. Line 0 is the resting state."""
    dur = slot * len(lines)
    cw = tw("x")
    out = []
    for i, line in enumerate(lines):
        start = i * slot
        chars = len(line) + 2
        widths = [(0.0, 0.0)] + [(start + 0.35 + k * 0.02, k * cw) for k in range(chars + 1)]
        shown = [(0.0, 1 if i == 0 else 0), (start, 1), (start + slot, 0)]
        out.append(
            f'<clipPath id="typed-{i}"><rect x="{num(x)}" y="{num(y - 14)}" width="{num(chars * cw)}" height="20">'
            f'{discrete("width", dur, [(t, num(w)) for t, w in widths])}</rect></clipPath>'
            f'<g opacity="{1 if i == 0 else 0}">{discrete("opacity", dur, shown)}'
            f'<text x="{num(x)}" y="{num(y)}" fill="{SOFT}" textLength="{num(chars * cw)}" clip-path="url(#typed-{i})">'
            f'<tspan fill="{TEAL}">›</tspan> {esc(line)}</text>'
            f'<rect x="{num(x + chars * cw + 3)}" y="{num(y - 11)}" width="7" height="14" fill="{TEAL}">'
            f'{discrete("x", dur, [(t, num(x + w + 3)) for t, w in widths])}'
            f'<animate attributeName="opacity" values="1;0" dur="1.6s" calcMode="discrete" repeatCount="indefinite"/>'
            f'</rect></g>'
        )
    return "".join(out)


def _prompt_lines(p: Profile, width: float) -> list[str]:
    lines = []
    if p.active:
        names = [repo.name for repo, _ in p.active[:3]]
        lines.append("working on " + (names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"))
    if p.latest_commits:
        commit = p.latest_commits[0]
        lines.append(f"last commit: {commit['repo']} · {commit['message']}")
    released = next((r for r, _ in p.active if r.version), None)
    if released:
        lines.append(f"latest version: {released.name} {released.version}")
    if p.upstream:
        pr = p.upstream[0]
        lines.append(f"upstream: {pr['repo']} · {pr['title']}")
    names = [name for name, _ in p.languages[:3]]
    if len(names) > 1:
        lines.append(f"mostly writing {', '.join(names[:-1])} and {names[-1]} lately")
    return [fit(line, width - tw("› ") - 14, words=True) for line in lines] or ["hello"]




def hero(p: Profile) -> str:
    """The site's top bar and the big clock row, with my name where the clock is."""
    width, bar, body = FULL, 42, 132
    height = bar + body
    left, right = X0, width - X0
    place = p.location or "Norway"

    wide = [f'<line x1="0" x2="{width}" y1="{bar + 0.5}" y2="{bar + 0.5}" stroke="{LINE}"/>', logo(left, 11, 20)]
    x = left + 28
    name = p.login.lower()
    wide.append(text(x, 25.5, name, FG, 13.5, 700))
    x += tw(name, 13.5) + 16
    for i, (label, icon) in enumerate(TABS):
        w = 31 + tw(label) + 10
        if i == 0:
            wide.append(f'<rect x="{num(x + 0.5)}" y="7.5" width="{num(w - 1)}" height="27" rx="4" fill="{BG}" stroke="{LINE2}"/>')
        wide.append(lucide(icon, x + 10, 14, 14, FG if i == 0 else DIM))
        wide.append(text(x + 31, 25.5, label, FG if i == 0 else DIM))
        x += w + 2
    wide.append(text(right, 25.5, place, SOFT, anchor="end"))
    wide.append(lucide("map-pin", right - tw(place) - 21, 14, 14, DIM))

    wide.append(glitch(p.login, left, bar + 60, size=46, weight=300, fill=SOFT, seed="hero", loop=9.5, slices=2, backdrop=DESK))
    wide.append(text(left, bar + 86, f"{TAGLINE} · on github since {p.since}", DIM))
    wide.append(_typed(_prompt_lines(p, right - left), left, bar + 114))

    # Three numbers on the right, on the same two baselines as the name and the line under it.
    stats = [
        (str(p.active_count), "active repos", 29),
        (f"{p.contributions:,}", "contributions", 0),
        (str(p.public_repos), "public repos", 0),
    ]
    widths = [max(tw(label, 12.5), inset + tw(value, 26)) for value, label, inset in stats]
    x = right - sum(widths) - 28 * (len(stats) - 1)
    for (value, label, inset), w in zip(stats, widths):
        if inset:
            wide.append(lucide("circle-check", x, bar + 41, 21, GREEN))
        wide.append(text(x + inset, bar + 60, value, SOFT, 26, 300))
        wide.append(text(x, bar + 86, label, DIM, 12.5))
        x += w + 28

    # Twice the window inset, because on a phone this image is drawn at half the scale of the windows.
    nleft = 2 * X0
    narrow = [
        logo(nleft - 9, 26, 64),
        glitch(p.login, nleft + 72, 82, size=64, weight=300, fill=SOFT, seed="hero-narrow", loop=9.5, slices=2, backdrop=DESK),
        text(nleft, 140, f"{TAGLINE} · {place.lower()}", DIM, 28),
    ]
    body = (f'{logo_def()}{desk(width, height)}<g class="wide">{"".join(wide)}</g>'
            f'<g class="narrow">{"".join(narrow)}</g>')
    return svg(width, height, f"{p.login}: {TAGLINE}, {place}", body, NARROW_CSS)


# --------------------------------------------------------------------------- windows

def projects(p: Profile, height: int) -> str:
    """What I'm working on: my repos with the most commits in the last 30 days."""
    rows = p.active[:4]
    right = x1(HALF)
    gap = 6
    th = (height - Y0 - BOTTOM - gap * (len(rows) - 1)) / max(len(rows), 1)
    most = max((c for _, c in rows), default=0) or 1
    out = []
    for i, (repo, commits) in enumerate(rows):
        y = Y0 + i * (th + gap)
        out.append(tile(X0, y, right - X0, th))
        slug = detect.LANGUAGE_ICONS.get(repo.language)
        out.append(brand(slug, X0 + 11, y + 13, 20, SOFT) if has_brand(slug)
                   else lucide("folder-git-2", X0 + 11, y + 13, 20, DIM))
        tx = X0 + 42
        room = right - 10 - tx
        note = f"{commits} commit{'s' * (commits != 1)}" if commits else f"pushed {day(repo.pushed_at, p.today)}"
        name = fit(repo.name, room - tw(note, SMALL) - 10)
        out.append(text(tx, y + 21, name, FG, weight=600))
        if repo.version and tw(name) + 8 + tw(repo.version, SMALL) <= room - tw(note, SMALL) - 10:
            out.append(text(tx + tw(name) + 8, y + 21, repo.version, FAINT, SMALL))
        out.append(text(right - 10, y + 21, note, DIM, SMALL, anchor="end"))
        out.append(text(tx, y + 38, fit(repo.description or repo.language or "no description yet", room, SMALL, words=True), DIM, SMALL))
        out.append(bar_line(tx, y + th - 11, room, commits / most, TEAL, 0.2 + i * 0.12, h=3))
    tag = "most commits, 30 days" if p.active_count else "recently pushed"
    return window(HALF, height, "projects", "folder-git-2", TEAL, "".join(out), tag)


def log(p: Profile, height: int) -> str:
    """My latest commits across public repos, drawn like a one-branch git graph."""
    rows = 6
    right = x1(HALF)
    row_h = (height - Y0 - BOTTOM - 37) / (rows - 1)  # a row's own content is 37px tall
    commits = p.latest_commits[:rows]
    gx, tx = X0 + 5, X0 + 22
    out = []
    if len(commits) > 1:
        out.append(f'<line x1="{gx}" x2="{gx}" y1="{num(Y0 + 11.5)}" y2="{num(Y0 + (len(commits) - 1) * row_h + 11.5)}" stroke="{LINE2}"/>')
    for i, commit in enumerate(commits):
        y = Y0 + i * row_h
        stamp = day(commit["date"], p.today)
        if i == 0:
            out.append(f'<circle cx="{gx}" cy="{num(y + 11.5)}" r="4" fill="{YELLOW}"/>')
        else:
            out.append(f'<circle cx="{gx}" cy="{num(y + 11.5)}" r="3.5" fill="{BG}" stroke="{FAINT}" stroke-width="1.5"/>')
        out.append(text(tx, y + 16, fit(commit["repo"], right - tx - tw(stamp, SMALL) - 10), FG, weight=600))
        out.append(text(right, y + 16, stamp, FAINT, SMALL, anchor="end"))
        out.append(text(tx, y + 33, fit(commit["message"], right - tx, SMALL, words=True), DIM, SMALL))
    if not commits:
        out.append(text(X0, Y0 + 14, "No public commits lately.", DIM))
    return window(HALF, height, "log", "git-commit-horizontal", YELLOW, "".join(out), "latest commits")


def activity(p: Profile, height: int) -> str:
    """Last twelve months: four totals and one bar per week. The grand total is in the header."""
    right = x1(HALF)
    gap, th = 8, 54
    tile_w = (right - X0 - gap) / 2
    stats = [
        ("git-commit-horizontal", "commits", f"{p.commits:,}"),
        ("git-pull-request", "pull requests", f"{p.pull_requests:,}"),
        ("calendar-days", "active days", str(p.active_days)),
        ("flame", "longest streak", f"{p.longest_streak} days"),
    ]  # a value may carry a unit after a space; the unit is set small
    out = []
    for i, (icon, label, value) in enumerate(stats):
        x = X0 + (i % 2) * (tile_w + gap)
        y = Y0 + (i // 2) * (th + gap)
        out.append(tile(x, y, tile_w, th))
        out.append(lucide(icon, x + 12, y + 10, 13, DIM))
        out.append(text(x + 31, y + 20.5, label, DIM, SMALL))
        number, _, unit = value.partition(" ")
        out.append(text(x + 12, y + 44, number, FG, 21, 500))
        if unit:
            out.append(text(x + 12 + tw(number, 21) + 7, y + 44, unit, DIM, SMALL))

    weeks = p.weekly[-53:]
    peak = max((c for _, c in weeks), default=0) or 1
    head = Y0 + 2 * th + gap + 24
    base = height - BOTTOM - 13
    area = base - head - 12
    slot = (right - X0) / max(len(weeks), 1)
    bw = max(slot - 2, 2)
    out.append(text(X0, head, "contributions per week", DIM, SMALL))
    out.append(text(right, head, f"peak {peak}", FAINT, SMALL, anchor="end"))
    out.append(f'<line x1="{X0}" x2="{right}" y1="{num(base + 0.5)}" y2="{num(base + 0.5)}" stroke="{LINE}"/>')
    month = None
    for i, (start, count) in enumerate(weeks):
        x = X0 + i * slot + (slot - bw) / 2
        d = date.fromisoformat(start)
        if d.month != month and d.day <= 7:
            month = d.month
            if x + tw("jan", 11) <= right:
                out.append(text(x, base + 14, f"{d:%b}".lower(), FAINT, 11))
        if not count:
            continue
        h = max(area * count / peak, 1.5)
        delay = 0.25 + i * 0.012
        out.append(
            f'<g transform="translate(0 {num(base)})"><rect x="{num(x)}" y="{num(-h)}" width="{num(bw)}" height="{num(h)}" '
            f'rx="1" fill="{TEAL}"><animateTransform attributeName="transform" type="scale" values="1 0;1 0;1 1" '
            f'keyTimes="0;{num(delay / (delay + 0.5))};1" dur="{num(delay + 0.5)}s" calcMode="spline" '
            f'keySplines="0 0 1 1;.2 .8 .2 1"/></rect></g>'
        )
    return window(HALF, height, "activity", "activity", GREEN, "".join(out), "last 12 months")


def languages(p: Profile, height: int) -> str:
    """Language share of my commits. The bar is the share of all of them, not of the top entry."""
    rows = p.languages[:6]
    right = x1(HALF)
    row_h = (height - Y0 - BOTTOM - 27) / 5  # a row's own content is 27px tall
    out = []
    for i, (name, pct) in enumerate(rows):
        y = Y0 + i * row_h
        slug = detect.LANGUAGE_ICONS.get(name)
        if has_brand(slug):
            out.append(brand(slug, X0, y + 3, 14, SOFT))
        else:
            out.append(f'<circle cx="{X0 + 7}" cy="{num(y + 10)}" r="3.5" fill="{DIM}"/>')
        out.append(text(X0 + 23, y + 14.5, name, FG))
        out.append(text(right, y + 14.5, f"{pct:.0f}%" if pct >= 1 else "<1%", DIM, anchor="end"))
        out.append(bar_line(X0, y + 23, right - X0, pct / 100, TEAL, 0.2 + i * 0.1))
    return window(HALF, height, "languages", "code-xml", BLUE, "".join(out), "last 90 days")


def _stack_body(p: Profile, build: int, spread: float = 0.0) -> tuple[str, float]:
    """Chip groups. `spread` is extra space between groups. Returns the markup and where it ends."""
    limits = {"build": build, "system": 7, "tools": 8}
    right = x1(HALF)
    y = Y0 + 4
    out = []
    for group in detect.GROUPS:
        keys = p.stack.get(group, [])[: limits[group]]
        if not keys:
            continue
        out.append(text(X0, y + 10, group, DIM, SMALL))
        y += 18
        x = X0
        for key in keys:
            label = detect.TECH[key][0]
            markup, w = chip(x, y, label)
            if x + w > right:
                x, y = X0, y + 26
                markup, w = chip(x, y, label)
            out.append(markup)
            x += w + 6
        y += 20 + 14 + spread
    return "".join(out), y - 14 - spread


def _stack_height(p: Profile, build: int) -> int:
    return round(_stack_body(p, build)[1] + BOTTOM)


def bottom_row(p: Profile) -> tuple[int, int]:
    """Height shared by stack and upstream, and how many build chips fit in it.

    Upstream sets the height. The build group, the longest one, drops its least used entries
    until the two are as close as they get, so neither window ends in empty space.
    """
    height = upstream_height(p)
    build = max(range(6, 13), key=lambda n: (-max(_stack_height(p, n), height), n))
    return max(height, _stack_height(p, build)), build


def stack(p: Profile, height: int, build: int) -> str:
    """Frameworks and tools found in the repos I've committed to in the last 90 days."""
    groups = sum(1 for g in detect.GROUPS if p.stack.get(g))
    spare = height - _stack_height(p, build)
    body, _ = _stack_body(p, build, min(spare / max(groups - 1, 1), 16))
    return window(HALF, height, "stack", "package", MAGENTA, body, "from my repos", foot=M - V)


UPSTREAM_ROW = 44


def upstream_height(p: Profile) -> int:
    return round(Y0 + (max(len(p.upstream), 1) - 1) * UPSTREAM_ROW + 37 + BOTTOM)


def upstream(p: Profile, height: int) -> str:
    """Pull requests to other people's repos."""
    right = x1(HALF)
    tx = X0 + 22
    looks = {"merged": (MAGENTA, "git-merge"), "open": (GREEN, "git-pull-request")}
    out = []
    pitch = UPSTREAM_ROW + (height - upstream_height(p)) / max(len(p.upstream) - 1, 1)
    for i, pr in enumerate(p.upstream):
        y = Y0 + i * pitch
        color, icon = looks[pr["state"]]
        stamp = f"· {day(pr['date'], p.today)}"
        state = f"{pr['state']} {stamp}"
        out.append(lucide(icon, X0, y + 4, 14, color))
        name = fit(pr["repo"], right - tx - tw(state, SMALL) - 10)
        out.append(text(tx, y + 16, name, FG, weight=600))
        stars = _stars(pr["stars"])
        sx = tx + tw(name) + 9
        if pr["stars"] >= 10 and sx + 15 + tw(stars, SMALL) <= right - tw(state, SMALL) - 10:
            out.append(lucide("star", sx, y + 6, 11, FAINT))
            out.append(text(sx + 15, y + 16, stars, FAINT, SMALL))
        out.append(text(right, y + 16, stamp, FAINT, SMALL, anchor="end"))
        out.append(text(right - tw(stamp + " ", SMALL), y + 16, pr["state"], color, SMALL, anchor="end"))
        out.append(text(tx, y + 33, fit(pr["title"], right - tx, SMALL, words=True), DIM, SMALL))
    if not p.upstream:
        out.append(text(X0, Y0 + 14, "No pull requests elsewhere lately.", DIM))
    return window(HALF, height, "upstream", "git-pull-request", ORANGE, "".join(out), "pull requests elsewhere",
                  foot=M - V)


def snake(p: Profile, raw: str) -> str:
    """Put the generated contribution snake inside a window, cropped to where the snake actually goes."""
    vx, _, vw, _ = (float(v) for v in re.search(r'viewBox="([-\d. ]+)"', raw).group(1).split())
    inner = raw[raw.index(">") + 1: raw.rindex("</svg>")]
    inner = re.sub(r"<desc>.*?</desc>", "", inner, flags=re.S)
    # The progress bar under the grid has no track or label and reads as a stray block.
    inner = re.sub(r'<rect class="u [^>]*/>', "", inner)
    # Crop to the grid of 12px cells plus the snake's overhang, so the grid lines up with the
    # content edge of the other windows. The snake's first hop in from above the grid is cut off.
    cells = re.findall(r'<rect class="c[^"]*" x="(-?[\d.]+)" y="(-?[\d.]+)"', raw) or [("2", "2"), ("834", "98")]
    xs, ys = [float(x) for x, _ in cells], [float(y) for _, y in cells]
    vx, vy = min(xs) - 3, min(ys) - 3
    vw, vh = max(xs) + 12 + 3 - vx, max(ys) + 12 + 3 - vy
    width = FULL - 2 * (M + PAD)
    h = vh * width / vw
    top = V + TOP + 18
    height = round(top + h + BOTTOM + 2)
    body = (f'<g class="grid"><svg x="{M + PAD}" y="{top}" width="{width}" height="{num(h)}" '
            f'viewBox="{num(vx)} {num(vy)} {num(vw)} {num(vh)}">{inner}</svg></g>')
    # Phone variant: the grid moves down and shrinks to sit between the doubled title and the border.
    under_title = 2 * (V + TOP) + 22
    k = min((height - under_title - 2 * V - 14) / h, (FULL - 4 * (M + PAD)) / width)
    shift = f"translate({num((FULL - width * k) / 2 - (M + PAD) * k)}px,{num(under_title - top * k)}px) scale({num(k)})"
    return window(FULL, height, "contributions", "calendar-days", GREEN, body,
                  f"{p.contributions:,} in the last year", "Snake eating my contribution graph",
                  f"@media (max-width:520px){{.grid{{transform:{shift}}}}}")


# Colours for generate-snake-animation: empty cell, then four levels of the teal from the logo.
SNAKE_OPTIONS = f"color_snake={SOFT}&color_dots={RAISE},#17403b,#1f6b61,#2f9c8a,{TEAL}&color_dot_border={LINE}"


def button(label: str, icon: str, kind: str, linked: bool) -> tuple[str, int, int]:
    """The site's .btn. A handle that leads nowhere gets no box, so it does not look clickable.

    It sits straight on GitHub's page, so its grey is GitHub's muted text colour, which reads on
    both the light and the dark theme.
    """
    pad = 3
    width = round(2 * pad + 10 + 14 + 7 + tw(label) + 11)
    height = 28 + 2 * pad
    ink = SOFT if linked else "#8b949e"
    mark = brand(icon, pad + 10, pad + 7, 14, ink) if kind == "brand" else lucide(icon, pad + 10, pad + 7, 14, ink)
    frame = (f'<rect x="{pad + 0.5}" y="{pad + 0.5}" width="{width - 2 * pad - 1}" height="27" rx="4" fill="{RAISE}" '
             f'stroke="{LINE2}"/>') if linked else ""
    return svg(width, height, label, f"{frame}{mark}{text(pad + 31, pad + 18.5, label, FG if linked else ink)}"), width, height


def buttons() -> dict[str, tuple[str, int, int]]:
    return {label: button(label, icon, kind, bool(url)) for label, icon, kind, url in LINKS}
