#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path


README_PATH = Path("README.md")
START_MARKER = "<!-- TYPING_SVG_START -->"
END_MARKER = "<!-- TYPING_SVG_END -->"


def api_get(url: str, token: str | None) -> dict | list:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def build_typing_url(lines: list[str]) -> str:
    params = {
        "font": "Fira Code",
        "size": "22",
        "duration": "2600",
        "pause": "900",
        "color": "58A6FF",
        "center": "true",
        "vCenter": "true",
        "width": "900",
        "lines": ";".join(lines),
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote_plus)
    return f"https://readme-typing-svg.demolab.com?{query}"


def main() -> int:
    username = os.getenv("README_USERNAME", "T3lluz")
    token = os.getenv("GITHUB_TOKEN")

    user = api_get(f"https://api.github.com/users/{username}", token)
    repos = api_get(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
        token,
    )

    non_fork_repos = [repo for repo in repos if not repo.get("fork", False)]
    total_stars = sum(int(repo.get("stargazers_count", 0)) for repo in non_fork_repos)
    recent_names = [repo.get("name", "") for repo in non_fork_repos[:3] if repo.get("name")]

    recent_display = ", ".join(recent_names) if recent_names else "no public repos yet"

    lines = [
        f"Public repos: {user.get('public_repos', 0)} | Followers: {user.get('followers', 0)}",
        f"Total stars across repos: {total_stars}",
        f"Recently updated: {recent_display}",
        "Full-stack student | MERN + PERN | Linux + Windows tweaks",
    ]

    svg_url = build_typing_url(lines)
    replacement = (
        f'{START_MARKER}\n'
        f'<img src="{svg_url}" alt="Typing intro" />\n'
        f"{END_MARKER}"
    )

    readme = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )

    if not pattern.search(readme):
        raise RuntimeError("Typing markers were not found in README.md")

    updated = pattern.sub(replacement, readme)
    if updated == readme:
        print("No README changes needed.")
        return 0

    README_PATH.write_text(updated, encoding="utf-8")
    print("README typing section updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
