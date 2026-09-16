"""Collect live GitHub data for the profile README and derive the numbers shown on it."""

from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import repo_insights

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
query($login: String!, $from90: DateTime!, $from30: DateTime!) {
  user(login: $login) {
    id
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
      nodes { ...RepoFields }
    }
    last90: contributionsCollection(from: $from90) {
      commitContributionsByRepository(maxRepositories: 25) {
        contributions { totalCount }
        repository { ...RepoFields }
      }
    }
    last30: contributionsCollection(from: $from30) {
      commitContributionsByRepository(maxRepositories: 25) {
        contributions { totalCount }
        repository { nameWithOwner }
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

fragment RepoFields on Repository {
  name
  nameWithOwner
  owner { login }
  isPrivate
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
    # Languages weighted by my commits in the last 90 days, and repos ranked by commits in the last 30.
    recent_languages: list[tuple[str, float, str]] = field(default_factory=list)
    active: list[tuple[Repo, int]] = field(default_factory=list)
    generated_on: str = ""
    generated_at: str = ""
    # Latest commits of mine across active public repos, newest first.
    latest_commits: list[dict] = field(default_factory=list)
    # Detected tech (keys from icons.TECH), ranked by my recent commits in repos using it.
    tech: list[str] = field(default_factory=list)

    @property
    def years_on_github(self) -> str:
        start = datetime.fromisoformat(self.created_at.replace("Z", "+00:00")).date()
        today = date.fromisoformat(self.generated_on)
        months = (today.year - start.year) * 12 + today.month - start.month
        return f"{months // 12}y {months % 12}m"

    def top_languages(self, n: int = 3) -> list[str]:
        """Most-used languages lately (falls back to all-time code size)."""
        source = self.recent_languages or self.languages
        return [name for name, _, _ in source[:n] if name != "Other"]

    @property
    def focus(self) -> list[tuple[Repo, int]]:
        """What I'm working on: most commits this month, else most recently pushed."""
        return self.active or [(r, 0) for r in self.recent[:3]]


def _post(token: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def _fetch(token: str) -> dict:
    now = datetime.now(timezone.utc)
    user = _post(token, QUERY, {
        "login": USERNAME,
        "from90": (now - timedelta(days=90)).isoformat(),
        "from30": (now - timedelta(days=30)).isoformat(),
    })["user"]
    # Second round: peek inside the repos I've actually been committing to.
    names = [repo["name"] for repo, _ in _public_commits(user["last90"]) if repo["owner"]["login"] == USERNAME][:12]
    if not names:
        names = [r["name"] for r in user["repositories"]["nodes"] if _include(r["name"])][:6]
    details = _post(token, repo_insights.details_query(USERNAME, names), {"uid": user["id"]})
    return {"user": user, "details": details}


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


def _repo(r: dict) -> Repo:
    return Repo(
        name=r["name"],
        description=(DESCRIPTION_OVERRIDES.get(r["name"]) or r["description"] or "").strip(),
        url=r["url"],
        pushed_at=r["pushedAt"],
        stars=r["stargazerCount"],
        language=(r["primaryLanguage"] or {}).get("name", ""),
        language_color=(r["primaryLanguage"] or {}).get("color") or "#8b949e",
    )


def _shares(weights: Counter[str], colors: dict[str, str], top: int = 6) -> list[tuple[str, float, str]]:
    total = sum(weights.values()) or 1
    out = [(n, w / total * 100, colors[n]) for n, w in weights.most_common(top)]
    other = 100 - sum(pct for _, pct, _ in out)
    if other >= 0.5:
        out.append(("Other", other, "#6e7681"))
    return out


def _public_commits(window: dict) -> list[tuple[dict, int]]:
    return [
        (item["repository"], item["contributions"]["totalCount"])
        for item in window["commitContributionsByRepository"]
        if not item["repository"].get("isPrivate") and _include(item["repository"]["nameWithOwner"].split("/")[-1])
    ]


def build_profile(raw: dict, now: datetime) -> Profile:
    user, details = raw["user"], raw["details"]
    today = now.date()
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
    langs = _shares(sizes, colors)

    # Recent languages: each repo's language mix, weighted by how many commits I made there.
    recent_weights: Counter[str] = Counter()
    last90 = _public_commits(user["last90"])
    for repo, commits in last90:
        edges = repo["languages"]["edges"]
        repo_total = sum(e["size"] for e in edges) or 1
        for e in edges:
            recent_weights[e["node"]["name"]] += commits * e["size"] / repo_total
            colors[e["node"]["name"]] = e["node"]["color"] or "#8b949e"
    by_name = {repo["nameWithOwner"]: repo for repo, _ in last90}
    active = [
        (_repo(by_name[repo["nameWithOwner"]]), commits)
        for repo, commits in _public_commits(user["last30"])
        if repo["nameWithOwner"] in by_name
    ]
    active.sort(key=lambda rc: -rc[1])

    recent = [_repo(r) for r in repos if _include(r["name"])]

    commit_weight = {repo["name"]: n for repo, n in last90}
    language_of = {r["name"]: (r["primaryLanguage"] or {}).get("name", "") for r in repos}
    tech_weight: Counter[str] = Counter()
    latest: list[dict] = []
    for repo in details.values():
        if not repo:
            continue
        for key in repo_insights.detect(repo, language_of.get(repo["name"], "")):
            tech_weight[key] += commit_weight.get(repo["name"], 0) + 1
        latest += repo_insights.commits(repo)
    latest.sort(key=lambda c: c["date"], reverse=True)

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
        recent_languages=_shares(recent_weights, colors),
        active=active,
        generated_on=today.isoformat(),
        generated_at=now.isoformat(timespec="minutes"),
        latest_commits=latest[:8],
        tech=[k for k, _ in tech_weight.most_common()],
    )


def load_profile(cache: Path | None = None) -> Profile:
    """Fetch from GitHub; with a cache path, reuse the raw responses between local runs."""
    if cache and cache.exists():
        raw = json.loads(cache.read_text(encoding="utf-8"))
    else:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            raise SystemExit("Set GITHUB_TOKEN (or GH_TOKEN) to query the GitHub GraphQL API.")
        raw = _fetch(token)
        if cache:
            cache.write_text(json.dumps(raw), encoding="utf-8")
    return build_profile(raw, datetime.now(timezone.utc))


if __name__ == "__main__":
    p = load_profile()
    print(json.dumps({k: v for k, v in asdict(p).items() if k not in {"weekly"}}, indent=2, default=str))
