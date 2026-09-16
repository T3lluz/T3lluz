"""Collect live GitHub data for the profile README and derive the numbers shown on it."""

from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

USERNAME = os.getenv("PROFILE_USERNAME", "T3lluz")

# Repos that should not count as "my code" or "what I'm building".
EXCLUDED_REPOS = {USERNAME, "Gruppe-17"}
EXCLUDED_PREFIXES = ("FORK-",)

# Short English descriptions; these win over the GitHub description (many are empty or Norwegian).
DESCRIPTION_OVERRIDES = {
    "DailyDash": "Android dashboard: health, weather, F1, GitHub and servers on one screen",
    "PorcoRosso": "React 19 + Vite site published on GitHub Pages",
    "Sonus": "Sonar-style PipeWire volume mixer with per-channel EQ",
    "streamdeck-hyperx-caw-battery-Linux": "Linux Stream Deck battery tile for HyperX Cloud Alpha Wireless",
    "Cinema-Info": "Live cinema schedule with seats, times and posters for Buen Kino",
    "proslides-overview": "Project site for ProSlides, our bachelor project",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    bio
    location
    createdAt
    followers { totalCount }
    pullRequests(states: MERGED) { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST], includeUserRepositories: false) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        url
        pushedAt
        stargazerCount
        isArchived
        primaryLanguage { name color }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


@dataclass
class Repo:
    name: str
    description: str
    url: str
    pushed_at: str
    stars: int
    language: str
    language_color: str


@dataclass
class Profile:
    login: str
    bio: str
    location: str
    created_at: str
    followers: int
    public_repos: int
    merged_prs: int
    contributed_to: int
    stars: int
    contributions: int
    commits: int
    pull_requests: int
    reviews: int
    issues: int
    current_streak: int
    longest_streak: int
    active_days: int
    busiest_weekday: str
    best_day: tuple[str, int]
    weekly: list[tuple[str, int]]
    languages: list[tuple[str, float, str]]
    recent: list[Repo] = field(default_factory=list)
    generated_on: str = ""

    @property
    def years_on_github(self) -> str:
        start = datetime.fromisoformat(self.created_at.replace("Z", "+00:00")).date()
        today = date.fromisoformat(self.generated_on)
        months = (today.year - start.year) * 12 + today.month - start.month
        return f"{months // 12}y {months % 12}m"

    def top_languages(self, n: int = 3) -> list[str]:
        return [name for name, _, _ in self.languages[:n] if name != "Other"]


def _graphql(token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def _streaks(days: list[tuple[str, int]]) -> tuple[int, int]:
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # Today may not have a contribution yet; the streak is still alive if yesterday did.
    tail = days[:-1] if days and days[-1][1] == 0 else days
    current = 0
    for _, count in reversed(tail):
        if not count:
            break
        current += 1
    return current, longest


def _include(name: str) -> bool:
    return name not in EXCLUDED_REPOS and not name.startswith(EXCLUDED_PREFIXES)


def build_profile(user: dict, today: date) -> Profile:
    repos = [r for r in user["repositories"]["nodes"] if not r["isArchived"]]
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    current, longest = _streaks(days)

    weekday_totals: Counter[str] = Counter()
    for day, count in days:
        weekday_totals[date.fromisoformat(day).strftime("%A")] += count
    best = max(days, key=lambda d: d[1]) if days else ("", 0)
    weekly = [(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
              for w in cal["weeks"]]

    sizes: Counter[str] = Counter()
    colors: dict[str, str] = {}
    for r in repos:
        if not _include(r["name"]):
            continue
        for edge in r["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8b949e"
    total = sum(sizes.values()) or 1
    langs = [(n, s / total * 100, colors[n]) for n, s in sizes.most_common(6)]
    other = 100 - sum(p for _, p, _ in langs)
    if other >= 0.5:
        langs.append(("Other", other, "#6e7681"))

    recent = [
        Repo(
            name=r["name"],
            description=(DESCRIPTION_OVERRIDES.get(r["name"]) or r["description"] or "").strip(),
            url=r["url"],
            pushed_at=r["pushedAt"],
            stars=r["stargazerCount"],
            language=(r["primaryLanguage"] or {}).get("name", ""),
            language_color=(r["primaryLanguage"] or {}).get("color") or "#8b949e",
        )
        for r in repos
        if _include(r["name"])
    ]

    return Profile(
        login=USERNAME,
        bio=(user.get("bio") or "").strip(),
        location=(user.get("location") or "").strip(),
        created_at=user["createdAt"],
        followers=user["followers"]["totalCount"],
        public_repos=user["repositories"]["totalCount"],
        merged_prs=user["pullRequests"]["totalCount"],
        contributed_to=user["repositoriesContributedTo"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        contributions=cal["totalContributions"],
        commits=cc["totalCommitContributions"],
        pull_requests=cc["totalPullRequestContributions"],
        reviews=cc["totalPullRequestReviewContributions"],
        issues=cc["totalIssueContributions"],
        current_streak=current,
        longest_streak=longest,
        active_days=sum(1 for _, c in days if c),
        busiest_weekday=weekday_totals.most_common(1)[0][0] if weekday_totals else "",
        best_day=best,
        weekly=weekly,
        languages=langs,
        recent=recent,
        generated_on=today.isoformat(),
    )


def load_profile(cache: Path | None = None) -> Profile:
    """Fetch from GitHub; with a cache path, reuse the raw response between local runs."""
    if cache and cache.exists():
        user = json.loads(cache.read_text(encoding="utf-8"))
    else:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            raise SystemExit("Set GITHUB_TOKEN (or GH_TOKEN) to query the GitHub GraphQL API.")
        user = _graphql(token)
        if cache:
            cache.write_text(json.dumps(user), encoding="utf-8")
    return build_profile(user, datetime.now(timezone.utc).date())


if __name__ == "__main__":
    p = load_profile()
    print(json.dumps({k: v for k, v in asdict(p).items() if k not in {"weekly"}}, indent=2, default=str))
