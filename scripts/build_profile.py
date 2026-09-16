#!/usr/bin/env python3
"""Regenerate README.md and every profile SVG from live GitHub data.

    GITHUB_TOKEN=... python scripts/build_profile.py            # fetch + build
    python scripts/build_profile.py --cache .profile-cache.json # reuse a local API snapshot
"""

from __future__ import annotations

import argparse
import urllib.parse
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


def themed(name: str, alt: str, width: int, height: int) -> str:
    """<picture> that follows GitHub's light/dark theme."""
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg" />\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="{RAW}/{name}-light.svg" />\n'
        f'  <img src="{RAW}/{name}-dark.svg" alt="{alt}" width="{width}" height="{height}" />\n'
        "</picture>"
    )


def _cap(text: str, limit: int = 78) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def typing_url(p: Profile) -> str:
    focus = p.focus
    langs = p.top_languages(3)
    lines = []
    if focus:
        repo = focus[0][0]
        lines.append(_cap(f"Now building: {repo.name}" + (f" — {repo.description}" if repo.description else "")))
    if len(focus) > 2:
        lines.append(_cap(f"Also shipping: {focus[1][0].name} ({focus[1][0].language}) + "
                          f"{focus[2][0].name} ({focus[2][0].language})"))
    if langs:
        lines.append(f"Recently writing: {', '.join(langs)}")
    lines.append(f"Last 12 months: {p.contributions:,} contributions · {p.commits:,} commits · {p.pull_requests} PRs")
    lines.append(f"Currently on a {p.current_streak}-day streak" if p.current_streak > 1
                 else "I build the tools I want to use every day.")
    query = urllib.parse.urlencode({
        "font": "Fira Code", "size": "22", "duration": "2600", "pause": "1100", "color": "58A6FF",
        "center": "true", "vCenter": "true", "width": "1100", "lines": ";".join(lines),
    }, quote_via=urllib.parse.quote_plus)
    return f"https://readme-typing-svg.demolab.com?{query}"


def badge(label: str, message: str, color: str) -> str:
    def part(v: str) -> str:
        return urllib.parse.quote(v.replace("-", "--").replace("_", "__"))
    return (f'<img src="https://img.shields.io/badge/{part(label)}-{part(message)}-{color}?style=flat-square" '
            f'alt="{label}: {message}" />')


def stack_cell(title: str, items: list[tuple[str, str]], attrs: str = "") -> str:
    icons = "\n".join(f'          <img src="{src}" alt="{name}" title="{name}" width="40" height="40" />'
                      for name, src in items)
    return f"""        <td align="center"{attrs}>
          <b>{title}</b><br /><br />
{icons}
        </td>"""


def readme(p: Profile, title_widths: dict[str, int]) -> str:
    def title(key: str, alt: str) -> str:
        return themed(f"titles/glitch-{key}", alt, title_widths[key], glitch_titles.HEIGHT)

    recent_langs = p.recent_languages or p.languages
    lang_icons = [(n, LANGUAGE_ICONS[n]) for n, _, _ in recent_langs if n in LANGUAGE_ICONS][:7]
    lang_summary = ", ".join(f"{n} ({pct:.0f}%)" for n, pct, _ in recent_langs if n != "Other")
    slides = svg_art.about_slides(p)
    focus = [r for r, _ in p.focus]
    projects = ", ".join(f"[{r.name}]({r.url})" for r in focus[:3])
    active_count = len(p.active)
    checklist = "\n".join(
        f"**{cmd}**\n\n" + "\n".join(f"- {ln.lstrip('› ')}" for ln in lines) + "\n" for cmd, lines in slides
    )

    return f"""<!--
  Generated by scripts/build_profile.py — edit the script, not this file.
  Refreshed daily by .github/workflows/profile.yml (last run: {p.generated_on}).
-->

<div align="center">

<img src="./assets/banner/ascii-banner.svg" width="100%" alt="Sliding ASCII banner: now building {focus[0].name if focus else ''}" />

{title("hey", "Hey, I'm T3lluz")}

<p>
  Computer engineering (bachelor) from {p.location or "Norway"} who builds the tools I want to use every day.<br />
  Right now that's {projects}, mostly in {", ".join(p.top_languages(3))}.
</p>

<img width="910" src="{typing_url(p)}" alt="Typing intro: what I'm working on right now" />

<br />

<a href="https://x.com/T3lluz_"><img src="https://img.shields.io/badge/X-111111?style=flat-square&logo=x&logoColor=white" alt="X" /></a>
<a href="https://www.linkedin.com/in/fredrik-stalsberg-427821151/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="https://github.com/T3lluz"><img src="https://img.shields.io/badge/GitHub-T3lluz-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" /></a>

</div>

---

<div align="center">
  {title("about", "About").replace(chr(10), chr(10) + "  ")}<br /><br />
  {badge("Now building", focus[0].name if focus else "—", "58A6FF")}
  {badge("Recently writing", " | ".join(p.top_languages(3)), "1F6FEB")}
  {badge("Active repos this month", str(active_count), "58A6FF")}<br /><br />
  <table align="center" width="100%">
    <tbody>
      <tr>
        <td align="center">
          {themed("about/about-carousel", "About T3lluz", 1000, 150).replace(chr(10), chr(10) + "          ")}
        </td>
      </tr>
    </tbody>
  </table>
</div>

<details>
<summary><strong>Plain checklist</strong></summary>

{checklist}
</details>

---

<div align="center">
  {title("pulse", "GitHub Pulse").replace(chr(10), chr(10) + "  ")}<br /><br />
  {themed("stats/pulse", f"{p.contributions} contributions, {p.commits} commits and {p.pull_requests} pull requests in the last year. Languages: {lang_summary}", 1000, 390).replace(chr(10), chr(10) + "  ")}
</div>

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="{RAW}/snake/github-contribution-grid-snake-neon.svg" />
    <source media="(prefers-color-scheme: light)" srcset="{RAW}/snake/github-contribution-grid-snake.svg" />
    <img alt="Snake eating my contribution graph" src="{RAW}/snake/github-contribution-grid-snake.svg" />
  </picture>
</div>

---

<div align="center">
  {title("stack", "Stack and tools").replace(chr(10), chr(10) + "  ")}<br /><br />
  <table align="center" width="100%">
    <tbody>
      <tr valign="top">
{stack_cell("Recently writing", lang_icons, ' width="50%"')}
{stack_cell("Building with", FRAMEWORKS, ' width="50%"')}
      </tr>
      <tr>
{stack_cell("Environment and tooling", TOOLS, ' colspan="2"')}
      </tr>
    </tbody>
  </table>

  <p><b>Local AI workflow</b></p>
  <p><code>LM Studio</code> · <code>OpenCLAW</code> · <code>Cursor IDE</code> · <code>VM-based test setups</code></p>
</div>

---

<div align="center">
  {title("contact", "Contact").replace(chr(10), chr(10) + "  ")}<br /><br />
  <a href="https://github.com/T3lluz"><img src="https://img.shields.io/badge/GitHub-T3lluz-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub profile" /></a>
  <a href="mailto:fstalsberg@gmail.com"><img src="https://img.shields.io/badge/Email-fstalsberg%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email Fredrik" /></a>
  <img src="https://img.shields.io/badge/Discord-T3lluz1337-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord T3lluz1337" />
</div>

<div align="center">
  <sub>Open to collaboration, side projects, and cool build ideas.</sub>
</div>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, help="read/write the raw API response here")
    args = parser.parse_args()

    p = load_profile(args.cache)
    widths = glitch_titles.write_all(ASSETS / "titles")

    outputs = {ASSETS / "banner" / "ascii-banner.svg": svg_art.banner(p)}
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
