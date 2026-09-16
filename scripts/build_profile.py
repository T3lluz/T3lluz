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
import icons
import svg_art
from profile_data import Profile, load_profile

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
RAW = "https://raw.githubusercontent.com/T3lluz/T3lluz/main/assets"

# Stack rows. Detected keys appear only when a recently active repo actually uses them.
BUILD_KEYS = svg_art.WEB_TECH + svg_art.APP_TECH + ("postgres",)
ENV_DETECTED = ("githubactions", "cursor", "androidstudio", "intellij", "streamdeck")
AI_DETECTED = ("cursor", "claude")


def themed(name: str, alt: str, width: int, height: int) -> str:
    """<picture> that follows GitHub's light/dark theme."""
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg" />\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="{RAW}/{name}-light.svg" />\n'
        f'  <img src="{RAW}/{name}-dark.svg" alt="{alt}" width="{width}" height="{height}" />\n'
        "</picture>"
    )


def indent(text: str, spaces: int) -> str:
    return text.replace("\n", "\n" + " " * spaces)


def _cap(text: str, limit: int = 78) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def typing_url(p: Profile) -> str:
    focus = p.focus
    lines = []
    if focus:
        repo = focus[0][0]
        lines.append(_cap(f"Now building: {repo.name}" + (f" — {repo.description}" if repo.description else "")))
    commit = svg_art.latest_commit(p)
    if commit:
        lines.append(_cap(f"Latest commit ({commit['repo']}): {commit['message']}"))
    if len(focus) > 2:
        lines.append(_cap(f"Also shipping: {focus[1][0].name} ({focus[1][0].language}) + "
                          f"{focus[2][0].name} ({focus[2][0].language})"))
    if p.top_languages():
        lines.append(f"Recently writing: {', '.join(p.top_languages(3))}")
    lines.append(f"Last 12 months: {p.contributions:,} contributions · {p.commits:,} commits · {p.pull_requests} PRs")
    lines.append(f"Currently on a {p.current_streak}-day streak" if p.current_streak > 1
                 else "I build the tools I want to use every day.")
    query = urllib.parse.urlencode({
        "font": "Fira Code", "size": "22", "duration": "2600", "pause": "1100", "color": "58A6FF",
        "center": "true", "vCenter": "true", "width": "1100", "lines": ";".join(lines),
    }, quote_via=urllib.parse.quote_plus)
    return f"https://readme-typing-svg.demolab.com?{query}"


def badge(label: str, message: str, color: str, logo: str | None = None, href: str | None = None) -> str:
    def part(v: str) -> str:
        return urllib.parse.quote(v.replace("-", "--").replace("_", "__"))
    extra = f"&logo={logo}&logoColor=white" if logo else ""
    img = (f'<img src="https://img.shields.io/badge/{part(label)}-{part(message)}-{color}?style=flat-square{extra}" '
           f'alt="{label}: {message}" />')
    return f'<a href="{href}">{img}</a>' if href else img


def icon_row(keys: list[str], size: int = 40) -> str:
    """Linked icons with hover titles, plus a caption naming them in the same order."""
    seen = list(dict.fromkeys(keys))
    imgs = "\n".join(
        f'<a href="{icons.TECH[k][2]}"><img src="{icons.TECH[k][1]}" alt="{icons.TECH[k][0]}" '
        f'title="{icons.TECH[k][0]}" width="{size}" height="{size}" /></a>'
        for k in seen
    )
    return f"{imgs}\n<br /><sub>{' · '.join(icons.TECH[k][0] for k in seen)}</sub>"


def language_row(p: Profile) -> str:
    rows = [(n, pct) for n, pct, _ in (p.recent_languages or p.languages) if n in icons.LANGUAGES][:7]
    imgs = "\n".join(
        f'<img src="{icons.LANGUAGES[n][1]}" alt="{n}" title="{n}: {pct:.0f}% of my recent commits" '
        f'width="40" height="40" />' for n, pct in rows
    )
    return f"{imgs}\n<br /><sub>{' · '.join(f'{n} {pct:.0f}%' for n, pct in rows)}</sub>"


def inline_icon(language: str) -> str:
    entry = icons.LANGUAGES.get(language)
    return f'<img src="{entry[1]}" alt="" width="16" height="16" /> ' if entry else ""


def readme(p: Profile, title_widths: dict[str, int]) -> str:
    def title(key: str, alt: str) -> str:
        return themed(f"titles/glitch-{key}", alt, title_widths[key], glitch_titles.HEIGHT)

    recent_langs = p.recent_languages or p.languages
    lang_summary = ", ".join(f"{n} ({pct:.0f}%)" for n, pct, _ in recent_langs if n != "Other")
    slides = svg_art.about_slides(p)
    focus = [r for r, _ in p.focus]
    projects = ", ".join(f'{inline_icon(r.language)}<a href="{r.url}"><b>{r.name}</b></a>' for r in focus[:3])
    checklist = "\n".join(
        f"**`{cmd}`**\n\n" + "\n".join(f"- {ln.lstrip('› ')}" for ln in lines) + "\n" for cmd, lines in slides
    )

    about_badges = []
    if focus:
        about_badges.append(badge("Now building", focus[0].name, "58A6FF",
                                  icons.language_slug(focus[0].language), focus[0].url))
    for name, pct, _ in recent_langs[:3]:
        if name != "Other":
            about_badges.append(badge(name, f"{pct:.0f}% lately", "1F6FEB", icons.language_slug(name)))
    commit = svg_art.latest_commit(p)
    if commit:
        about_badges.append(badge("Last commit", f"{commit['repo']} · {svg_art.age(commit['date'], p.generated_at)}",
                                  "A371F7", "git", commit["url"]))
    about_badges.append(badge("Active repos this month", str(len(p.active)), "58A6FF", "github",
                              "https://github.com/T3lluz?tab=repositories"))

    build = [k for k in p.tech if k in BUILD_KEYS][:12]
    env = ["linux", "arch"] + [k for k in p.tech if k in ENV_DETECTED] + ["git", "vscode", "virtualbox"]
    ai = ["lmstudio", "openclaw"] + [k for k in p.tech if k in AI_DETECTED]

    return f"""<!--
  Generated by scripts/build_profile.py — edit the script, not this file.
  Refreshed automatically by .github/workflows/profile.yml (last run: {p.generated_at[:16].replace("T", " ")} UTC).
-->

<div align="center">

<img src="./assets/banner/ascii-banner.svg" width="100%" alt="Sliding ASCII banner: now building {focus[0].name if focus else ''}" />

{title("hey", "Hey, I'm T3lluz")}

<p>
  Computer engineering (bachelor) from {p.location or "Norway"} who builds the tools I want to use every day.<br />
  Right now: {projects}.
</p>

<img width="910" src="{typing_url(p)}" alt="Typing intro: what I'm working on right now" />

<br />

<a href="https://x.com/T3lluz_"><img src="https://img.shields.io/badge/X-111111?style=flat-square&logo=x&logoColor=white" alt="X" /></a>
<a href="https://www.linkedin.com/in/fredrik-stalsberg-427821151/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="https://github.com/T3lluz"><img src="https://img.shields.io/badge/GitHub-T3lluz-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" /></a>

</div>

---

<div align="center">
  {indent(title("about", "About"), 2)}<br /><br />
  {indent(chr(10).join(about_badges), 2)}<br /><br />
  <table align="center" width="100%">
    <tbody>
      <tr>
        <td align="center">
          {indent(themed("about/about-carousel", "About T3lluz", 1000, 150), 10)}
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
  {indent(title("pulse", "GitHub Pulse"), 2)}<br /><br />
  <a href="https://github.com/T3lluz?tab=overview">
  {indent(themed("stats/pulse", f"{p.contributions} contributions, {p.commits} commits and {p.pull_requests} pull requests in the last year. Languages: {lang_summary}", 1000, 390), 2)}
  </a>
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
  {indent(title("stack", "Stack and tools"), 2)}<br /><br />
  <table align="center" width="100%">
    <tbody>
      <tr valign="top">
        <td align="center" width="50%">
          <b>Recently writing</b><br /><sub>share of my commits, last 90 days</sub><br /><br />
          {indent(language_row(p), 10)}
        </td>
        <td align="center" width="50%">
          <b>Building with</b><br /><sub>detected in my active repos</sub><br /><br />
          {indent(icon_row(build), 10)}
        </td>
      </tr>
      <tr>
        <td align="center" colspan="2">
          <b>Environment and tooling</b><br /><br />
          {indent(icon_row(env), 10)}
        </td>
      </tr>
      <tr>
        <td align="center" colspan="2">
          <b>Local AI workflow</b><br /><br />
          {indent(icon_row(ai), 10)}
        </td>
      </tr>
    </tbody>
  </table>
</div>

---

<div align="center">
  {indent(title("contact", "Contact"), 2)}<br /><br />
  <a href="https://github.com/T3lluz"><img src="https://img.shields.io/badge/GitHub-T3lluz-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub profile" /></a>
  <a href="mailto:fstalsberg@gmail.com"><img src="https://img.shields.io/badge/Email-fstalsberg%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email Fredrik" /></a>
  <a href="https://www.linkedin.com/in/fredrik-stalsberg-427821151/"><img src="https://img.shields.io/badge/LinkedIn-Fredrik_Stalsberg-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <img src="https://img.shields.io/badge/Discord-T3lluz1337-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord T3lluz1337" />
</div>

<div align="center">
  <sub>Open to collaboration, side projects, and cool build ideas · this page rebuilds itself from my GitHub activity every few hours.</sub>
</div>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, help="read/write the raw API responses here")
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
