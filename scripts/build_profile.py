#!/usr/bin/env python3
"""Regenerate README.md and every profile SVG from live GitHub data.

    GITHUB_TOKEN=... python scripts/build_profile.py            # fetch + build
    python scripts/build_profile.py --cache .profile-cache.json # reuse a local API snapshot
"""

from __future__ import annotations

import argparse
import urllib.parse
from datetime import date
from pathlib import Path

import glitch_titles
import svg_art
from profile_data import Profile, load_profile

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
RAW = "https://raw.githubusercontent.com/T3lluz/T3lluz/main/assets"
DEVICON = "https://cdn.jsdelivr.net/npm/devicon@2.17.0/icons"
ICONIFY = "https://api.iconify.design/simple-icons"

# Language name (as GitHub reports it) -> icon. Languages without an icon are skipped in the row.
LANGUAGE_ICONS = {
    "Kotlin": f"{DEVICON}/kotlin/kotlin-original.svg",
    "JavaScript": f"{DEVICON}/javascript/javascript-original.svg",
    "TypeScript": f"{DEVICON}/typescript/typescript-original.svg",
    "Python": f"{DEVICON}/python/python-original.svg",
    "QML": f"{DEVICON}/qt/qt-original.svg",
    "C++": f"{DEVICON}/cplusplus/cplusplus-original.svg",
    "HTML": f"{DEVICON}/html5/html5-original.svg",
    "CSS": f"{DEVICON}/css3/css3-original.svg",
    "Shell": f"{DEVICON}/bash/bash-original.svg",
    "PLpgSQL": f"{DEVICON}/postgresql/postgresql-original.svg",
}

FRAMEWORKS = [
    ("React", f"{DEVICON}/react/react-original.svg"),
    ("Vite", f"{DEVICON}/vitejs/vitejs-original.svg"),
    ("Tailwind CSS", f"{DEVICON}/tailwindcss/tailwindcss-original.svg"),
    ("Node.js", f"{DEVICON}/nodejs/nodejs-original.svg"),
    ("Supabase", f"{DEVICON}/supabase/supabase-original.svg"),
    ("PostgreSQL", f"{DEVICON}/postgresql/postgresql-original.svg"),
    ("Jetpack Compose", f"{DEVICON}/jetpackcompose/jetpackcompose-original.svg"),
    ("Android", f"{DEVICON}/android/android-original.svg"),
    ("Qt / QML", f"{DEVICON}/qt/qt-original.svg"),
    ("Playwright", f"{DEVICON}/playwright/playwright-original.svg"),
]

TOOLS = [
    ("Linux", f"{DEVICON}/linux/linux-original.svg"),
    ("Arch Linux", f"{DEVICON}/archlinux/archlinux-original.svg"),
    ("KDE Plasma", f"{ICONIFY}:kde.svg?color=%231D99F3"),
    ("Git", f"{DEVICON}/git/git-original.svg"),
    ("GitHub Actions", f"{ICONIFY}:githubactions.svg?color=%232088FF"),
    ("VS Code", f"{DEVICON}/vscode/vscode-original.svg"),
    ("Cursor", f"{ICONIFY}:cursor.svg?color=%2393C5FD"),
    ("Android Studio", f"{DEVICON}/androidstudio/androidstudio-original.svg"),
    ("Stream Deck", f"{ICONIFY}:elgato.svg?color=%2358A6FF"),
    ("Chrome extensions", f"{DEVICON}/chrome/chrome-original.svg"),
]


def icon_row(items: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'  <img src="{src}" alt="{name}" title="{name}" width="40" height="40" />' for name, src in items
    )


def themed(name: str, alt: str, width: int, height: int) -> str:
    """<picture> that follows GitHub's light/dark theme."""
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg" />\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="{RAW}/{name}-light.svg" />\n'
        f'  <img src="{RAW}/{name}-dark.svg" alt="{alt}" width="{width}" height="{height}" />\n'
        "</picture>"
    )


def typing_url(p: Profile) -> str:
    now = p.recent[0] if p.recent else None
    lines = [
        f"{p.contributions:,} contributions in the last year and counting",
        f"Currently building: {now.name} ({now.language})" if now else "Currently building something new",
        f"{p.public_repos} public repos · mostly {', '.join(p.top_languages(3))}",
        f"On a {p.current_streak}-day commit streak" if p.current_streak > 1
        else f"Longest streak this year: {p.longest_streak} days",
        "I build the tools I want to use every day",
    ]
    query = urllib.parse.urlencode({
        "font": "Fira Code", "weight": "500", "size": "20", "duration": "2800", "pause": "1200",
        "color": "58A6FF", "center": "true", "vCenter": "true", "width": "760", "height": "40",
        "lines": ";".join(lines),
    }, quote_via=urllib.parse.quote)
    return f"https://readme-typing-svg.demolab.com?{query}"


def month_label(iso: str) -> str:
    return f"{date.fromisoformat(iso[:10]):%b %Y}"


def projects_table(p: Profile, limit: int = 6) -> str:
    rows = ["| Project | What it is | Lang | Last push |", "| --- | --- | --- | --- |"]
    for r in p.recent[:limit]:
        desc = r.description.replace("|", "\\|") or "—"
        rows.append(f"| [**{r.name}**]({r.url}) | {desc} | {r.language or '—'} | {month_label(r.pushed_at)} |")
    return "\n".join(rows)


def readme(p: Profile, title_widths: dict[str, int]) -> str:
    def title(key: str, alt: str) -> str:
        return themed(f"titles/glitch-{key}", alt, title_widths[key], glitch_titles.HEIGHT)

    langs = [(n, LANGUAGE_ICONS[n]) for n, _, _ in p.languages if n in LANGUAGE_ICONS]
    lang_summary = ", ".join(f"{n} ({pct:.0f}%)" for n, pct, _ in p.languages if n != "Other")
    slides = svg_art.about_slides(p)

    return f"""<!--
  Generated by scripts/build_profile.py — edit the script, not this file.
  Refreshed daily by .github/workflows/profile.yml (last run: {p.generated_on}).
-->

<div align="center">

<img src="./assets/banner/terminal-banner.svg" width="100%" alt="T3lluz terminal banner: {p.contributions:,} contributions in the last year" />

{title("hey", "Hey, I'm T3lluz")}

<p>
  Computer engineering (bachelor) · based in {p.location or "Norway"}.<br />
  I build the tools I want to use every day:
  Android apps, React web apps, KDE Plasma widgets and Stream Deck plugins.
</p>

<img src="{typing_url(p)}" alt="Live GitHub facts" />

<p>
  <a href="https://github.com/T3lluz?tab=repositories"><img src="https://img.shields.io/badge/public_repos-{p.public_repos}-58A6FF?style=flat-square&logo=github&logoColor=white" alt="{p.public_repos} public repos" /></a>
  <img src="https://img.shields.io/badge/contributions_(12m)-{p.contributions}-1F6FEB?style=flat-square" alt="{p.contributions} contributions in the last 12 months" />
  <img src="https://img.shields.io/badge/pull_requests_(12m)-{p.pull_requests}-A371F7?style=flat-square" alt="{p.pull_requests} pull requests in the last 12 months" />
</p>

</div>

---

<div align="center">

{title("about", "About me")}

{themed("about/about-carousel", "About T3lluz", 1000, 150)}

</div>

<details>
<summary><strong>Plain-text version</strong></summary>

{chr(10).join(f"**{cmd}**{chr(10)}{chr(10)}" + chr(10).join(f"- {ln.lstrip('› ')}" for ln in lines) + chr(10) for cmd, lines in slides)}
</details>

---

<div align="center">

{title("building", "Now building")}

</div>

{projects_table(p)}

<sub>Sorted by most recent push · updated automatically every day.</sub>

---

<div align="center">

{title("pulse", "GitHub pulse")}

{themed("stats/pulse", f"{p.contributions} contributions, {p.commits} commits and {p.pull_requests} pull requests in the last year. Languages: {lang_summary}", 1000, 390)}

<br /><br />

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/snake/github-contribution-grid-snake-neon.svg" />
  <source media="(prefers-color-scheme: light)" srcset="{RAW}/snake/github-contribution-grid-snake.svg" />
  <img alt="Snake eating my contribution graph" src="{RAW}/snake/github-contribution-grid-snake.svg" />
</picture>

</div>

---

<div align="center">

{title("stack", "Stack & tools")}

**Languages I ship in** <sub>(ordered by how much code is in my repos)</sub>

<p>
{icon_row(langs)}
</p>

**Frameworks & platforms**

<p>
{icon_row(FRAMEWORKS)}
</p>

**Daily setup**

<p>
{icon_row(TOOLS)}
</p>

</div>

---

<div align="center">

{title("contact", "Get in touch")}

<a href="https://github.com/T3lluz"><img src="https://img.shields.io/badge/GitHub-T3lluz-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
<a href="https://www.linkedin.com/in/fredrik-stalsberg-427821151/"><img src="https://img.shields.io/badge/LinkedIn-Fredrik_Stalsberg-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="https://x.com/T3lluz_"><img src="https://img.shields.io/badge/X-@T3lluz__-111111?style=for-the-badge&logo=x&logoColor=white" alt="X" /></a>
<a href="mailto:fstalsberg@gmail.com"><img src="https://img.shields.io/badge/Email-fstalsberg%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email" /></a>
<img src="https://img.shields.io/badge/Discord-T3lluz1337-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord: T3lluz1337" />

<sub>Always up for talking about side projects, Linux desktops and good tooling.</sub>

</div>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, help="read/write the raw API response here")
    args = parser.parse_args()

    p = load_profile(args.cache)
    widths = glitch_titles.write_all(ASSETS / "titles")

    outputs = {ASSETS / "banner" / "terminal-banner.svg": svg_art.banner(p)}
    for theme in ("dark", "light"):
        outputs[ASSETS / "about" / f"about-carousel-{theme}.svg"] = svg_art.about(p, theme)
        outputs[ASSETS / "stats" / f"pulse-{theme}.svg"] = svg_art.pulse(p, theme)
    outputs[ROOT / "README.md"] = readme(p, widths)

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
