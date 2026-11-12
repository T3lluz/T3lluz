"""Fetch live GitHub data and turn it into the numbers and lists the README shows.

Nothing here depends on the clock beyond "which day is it", and nothing is phrased as "x minutes
ago". The output only changes when the data does, so a scheduled run with no news writes nothing.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import detect
from config import ALWAYS, DESCRIPTIONS, EXCLUDED_PREFIXES, EXCLUDED_REPOS, USERNAME

QUERY = """
query($login: String!, $from90: DateTime!, $from30: DateTime!) {
  user(login: $login) {
    id
    location
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes { ...RepoFields }
    }
    pullRequests(first: 60, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        title state createdAt mergedAt url
        repository { nameWithOwner isPrivate stargazerCount owner { login } }
      }
    }
    last90: contributionsCollection(from: $from90) {
      commitContributionsByRepository(maxRepositories: 50) {
        contributions { totalCount }
        repository { ...RepoFields }
      }
    }
    last30: contributionsCollection(from: $from30) {
      commitContributionsByRepository(maxRepositories: 50) {
        contributions { totalCount }
        repository { nameWithOwner }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
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
  isFork
  isArchived
  description
  url
  pushedAt
  primaryLanguage { name }
  languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
  repositoryTopics(first: 12) { nodes { topic { name } } }
  releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) { nodes { tagName } }
}
"""


@dataclass
class Repo:
    name: str
    description: str
    url: str
    pushed_at: str
    language: str
    version: str = ""


@dataclass
class Profile:
    login: str
    location: str
    public_repos: int
    contributions: int
    commits: int
    pull_requests: int
    active_days: int
    longest_streak: int
    weekly: list[tuple[str, int]]
    # Share of my commits per language over the last 90 days (all-time code size if I've been idle).
    languages: list[tuple[str, float]]
    # My own repos ranked by commits in the last 30 days, and how many of them there are.
    active: list[tuple[Repo, int]]
    active_count: int
    latest_commits: list[dict]
    # Open and merged pull requests to repos I don't own, newest first.
    upstream: list[dict]
    # Detected tech keys per group (see detect.TECH), most used first.
    stack: dict[str, list[str]] = field(default_factory=dict)
    today: str = ""


def day(stamp: str, today: str) -> str:
    """'nov 12', or 'nov 2025' once it is far enough back to be ambiguous."""
    then = datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
    if (date.fromisoformat(today) - then).days > 300:
        return f"{then:%b %Y}".lower()
    return f"{then:%b} {then.day}".lower()


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


def _include(name: str) -> bool:
    return name not in EXCLUDED_REPOS and not name.startswith(EXCLUDED_PREFIXES)


def _public_commits(window: dict) -> list[tuple[dict, int]]:
    return [
        (item["repository"], item["contributions"]["totalCount"])
        for item in window["commitContributionsByRepository"]
        if not item["repository"].get("isPrivate") and _include(item["repository"]["nameWithOwner"].split("/")[-1])
    ]


def _mine(repo: dict) -> bool:
    return repo["owner"]["login"] == USERNAME and not repo["isFork"]


def _fetch(token: str) -> dict:
    now = datetime.now(timezone.utc)
    user = _post(token, QUERY, {
        "login": USERNAME,
        "from90": (now - timedelta(days=90)).isoformat(),
        "from30": (now - timedelta(days=30)).isoformat(),
    })["user"]
    # Second round: look inside the repos I've been committing to.
    names = [repo["name"] for repo, _ in _public_commits(user["last90"]) if _mine(repo)][:16]
    if not names:
        names = [r["name"] for r in user["repositories"]["nodes"] if _include(r["name"])][:6]
    details = _post(token, detect.details_query(USERNAME, names), {"uid": user["id"]})
    return {"user": user, "details": details}


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def _repo(r: dict, manifest_version: str = "") -> Repo:
    # A release tag can lag behind the version in the manifest, so take whichever is newer.
    release = (r["releases"]["nodes"] or [{}])[0].get("tagName", "")
    version = max(release, manifest_version, key=_version_key)
    if version and version[0].isdigit():
        version = "v" + version
    return Repo(
        name=r["name"],
        description=(DESCRIPTIONS.get(r["name"]) or r["description"] or "").strip(),
        url=r["url"],
        pushed_at=r["pushedAt"],
        language=(r["primaryLanguage"] or {}).get("name", ""),
        version=version,
    )


def _shares(weights: Counter[str], top: int = 6) -> list[tuple[str, float]]:
    total = sum(weights.values()) or 1
    return [(name, weight / total * 100) for name, weight in weights.most_common(top)]


def _longest_streak(days: list[int]) -> int:
    longest = run = 0
    for count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    return longest


def _upstream(nodes: list[dict], limit: int = 5) -> list[dict]:
    out, per_repo = [], Counter()
    for pr in nodes:
        repo = pr["repository"]
        name = repo["nameWithOwner"]
        if repo["owner"]["login"] == USERNAME or repo["isPrivate"] or pr["state"] not in ("OPEN", "MERGED"):
            continue
        if per_repo[name] >= 2:
            continue
        per_repo[name] += 1
        out.append({
            "repo": name, "title": pr["title"].strip(), "state": pr["state"].lower(), "url": pr["url"],
            "date": pr["mergedAt"] or pr["createdAt"], "stars": repo["stargazerCount"],
        })
    return out[:limit]


def build_profile(raw: dict, now: datetime) -> Profile:
    user, details = raw["user"], raw["details"]
    today = now.date().isoformat()
    repos = [r for r in user["repositories"]["nodes"] if not r["isArchived"] and _include(r["name"])]
    cc = user["contributionsCollection"]
    weeks = cc["contributionCalendar"]["weeks"]
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]

    last90 = _public_commits(user["last90"])
    by_name = {repo["nameWithOwner"]: repo for repo, _ in last90}
    commits90 = {repo["name"]: n for repo, n in last90 if _mine(repo)}
    detail = {d["name"]: d for d in details.values() if d}

    # Languages: each repo's language mix, weighted by how many commits I made there.
    weights: Counter[str] = Counter()
    for repo, commits in last90:
        edges = repo["languages"]["edges"]
        total = sum(e["size"] for e in edges) or 1
        for e in edges:
            weights[e["node"]["name"]] += commits * e["size"] / total
    if not weights:
        for r in repos:
            for e in r["languages"]["edges"]:
                weights[e["node"]["name"]] += e["size"]

    def repo_of(r: dict) -> Repo:
        return _repo(r, detect.version(detail.get(r["name"], {})))

    active = sorted(
        ((repo_of(by_name[repo["nameWithOwner"]]), commits)
         for repo, commits in _public_commits(user["last30"])
         if repo["nameWithOwner"] in by_name and _mine(by_name[repo["nameWithOwner"]])),
        key=lambda rc: rc[0].pushed_at, reverse=True,
    )
    # Most commits first. On a tie the repo I pushed to last wins (the sort above is stable).
    active.sort(key=lambda rc: -rc[1])
    shown = active[:4] or [(repo_of(r), 0) for r in repos[:4]]

    tech: Counter[str] = Counter()
    latest: list[dict] = []
    topics = {r["name"]: [t["topic"]["name"] for t in r["repositoryTopics"]["nodes"]] for r in repos}
    language = {r["name"]: (r["primaryLanguage"] or {}).get("name", "") for r in repos}
    for name, repo in detail.items():
        for key in detect.stack(repo, language.get(name, ""), topics.get(name, [])):
            tech[key] += commits90.get(name, 0) + 1
        latest += detect.commits(repo)
    latest.sort(key=lambda c: c["date"], reverse=True)
    for key in ALWAYS:
        tech[key] += 10 ** 6
    # Rank by use. Ties keep the order of detect.TECH, so the result is the same on every run.
    order = list(detect.TECH)
    ranked = sorted(tech, key=lambda k: (-tech[k], order.index(k)))
    stack = {group: [k for k in ranked if detect.TECH[k][1] == group] for group in detect.GROUPS}

    # At most three commits per repo, so one busy project does not fill the whole log.
    log, per_repo = [], Counter()
    for commit in latest:
        if per_repo[commit["repo"]] < 3:
            per_repo[commit["repo"]] += 1
            log.append(commit)

    return Profile(
        login=USERNAME,
        location=(user.get("location") or "").strip(),
        public_repos=user["repositories"]["totalCount"],
        contributions=cc["contributionCalendar"]["totalContributions"],
        commits=cc["totalCommitContributions"],
        pull_requests=cc["totalPullRequestContributions"],
        active_days=sum(1 for c in counts if c),
        longest_streak=_longest_streak(counts),
        weekly=[(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
                for w in weeks],
        languages=_shares(weights),
        active=shown,
        active_count=len(active),
        latest_commits=log[:6],
        upstream=_upstream(user["pullRequests"]["nodes"]),
        stack=stack,
        today=today,
    )


def load_profile(cache: Path | None = None) -> Profile:
    """Fetch from GitHub. With a cache path, reuse the raw responses between local runs."""
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
    from dataclasses import asdict
    profile = asdict(load_profile())
    profile.pop("weekly")
    print(json.dumps(profile, indent=2, default=str))
