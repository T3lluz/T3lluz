#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
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


def graphql_get(query: str, variables: dict, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload


def fetch_contributed_repo_names_graphql(username: str, token: str | None) -> set[str]:
    if not token:
        return set()

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          commitContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner owner { login } }
          }
          pullRequestContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner owner { login } }
          }
        }
      }
    }
    """
    now = datetime.now(timezone.utc)
    variables = {
        "login": username,
        "from": (now - timedelta(days=365 * 5)).isoformat(),
        "to": now.isoformat(),
    }
    payload = graphql_get(query, variables, token)
    user_data = payload.get("data", {}).get("user", {})
    collection = user_data.get("contributionsCollection", {})

    names: set[str] = set()
    own_login = username.lower()
    for key in ("commitContributionsByRepository", "pullRequestContributionsByRepository"):
        for item in collection.get(key, []):
            repo = item.get("repository", {})
            owner = str(repo.get("owner", {}).get("login", "")).lower()
            name_with_owner = str(repo.get("nameWithOwner", "")).strip()
            if name_with_owner and owner and owner != own_login:
                names.add(name_with_owner)
    return names


def fetch_contributed_repo_names(username: str, token: str | None) -> set[str]:
    # Prefer GraphQL contribution data for accuracy, then fall back to public events.
    try:
        graphql_names = fetch_contributed_repo_names_graphql(username, token)
        if graphql_names:
            return graphql_names
    except Exception:
        pass

    contributed: set[str] = set()
    own_prefix = f"{username.lower()}/"

    # Public events give us a good approximation of repositories the user has
    # contributed to outside their own profile repos.
    for page in range(1, 6):
        events = api_get(
            f"https://api.github.com/users/{username}/events/public?per_page=100&page={page}",
            token,
        )
        if not isinstance(events, list) or not events:
            break

        for event in events:
            event_type = str(event.get("type", ""))
            if event_type not in {
                "PushEvent",
                "PullRequestEvent",
                "PullRequestReviewEvent",
                "IssueCommentEvent",
                "IssuesEvent",
            }:
                continue

            repo_name = str(event.get("repo", {}).get("name", "")).strip()
            if not repo_name:
                continue
            if repo_name.lower().startswith(own_prefix):
                continue
            contributed.add(repo_name)

    return contributed


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
    own_stars = sum(int(repo.get("stargazers_count", 0)) for repo in non_fork_repos)
    contributed_repo_names = fetch_contributed_repo_names(username, token)
    contributed_stars = 0
    for full_name in sorted(contributed_repo_names):
        try:
            repo_data = api_get(f"https://api.github.com/repos/{full_name}", token)
            if isinstance(repo_data, dict):
                contributed_stars += int(repo_data.get("stargazers_count", 0))
        except Exception:
            # Keep the updater resilient if one repo cannot be fetched.
            continue

    total_stars = own_stars + contributed_stars
    recent_names = [repo.get("name", "") for repo in non_fork_repos[:3] if repo.get("name")]
    primary_langs = Counter(
        repo.get("language")
        for repo in non_fork_repos
        if isinstance(repo.get("language"), str) and repo.get("language")
    )
    top_langs = ", ".join(lang for lang, _ in primary_langs.most_common(3))

    theme_keywords = {
        "streamdeck": "Stream Deck plugins",
        "stream deck": "Stream Deck plugins",
        "hid": "HID tooling",
        "battery": "Battery integrations",
        "animation": "UI animations",
        "theme": "Theme customization",
        "portfolio": "Portfolio/web projects",
    }
    theme_counts: Counter[str] = Counter()
    for repo in non_fork_repos:
        haystack = " ".join(
            [
                str(repo.get("name", "")).lower(),
                str(repo.get("description", "")).lower(),
            ]
        )
        for keyword, label in theme_keywords.items():
            if keyword in haystack:
                theme_counts[label] += 1
    top_themes = ", ".join(label for label, _ in theme_counts.most_common(2))

    recent_display = ", ".join(recent_names) if recent_names else "no public repos yet"
    lang_display = top_langs if top_langs else "JavaScript, HTML, CSS"
    theme_display = top_themes if top_themes else "Web apps, customization"

    lines = [
        f"Public repos: {user.get('public_repos', 0)} | Followers: {user.get('followers', 0)}",
        f"Contributed repos tracked: {len(contributed_repo_names)}",
        f"Recently updated: {recent_display}",
        f"Top langs: {lang_display} | Focus: {theme_display}",
        "Fun fact: I tweak configs until the config tweaks me back.",
        "Status: shipping small commits and pretending tabs are temporary.",
        "Debug mode: print(), pray(), and one more coffee.",
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
