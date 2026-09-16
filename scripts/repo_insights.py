"""Look inside my recently active repos: latest commits and the stack each one actually uses."""

from __future__ import annotations

import json
import re

FILES = {
    "pkg": "package.json",
    "gradle": "app/build.gradle.kts",
    "req": "requirements.txt",
    "pyproject": "pyproject.toml",
    "manifest": "manifest.json",
}

NPM_DEPS = {
    "react": "react", "vite": "vite", "tailwindcss": "tailwind", "@tailwindcss/vite": "tailwind",
    "@supabase/supabase-js": "supabase", "@playwright/test": "playwright", "playwright": "playwright",
    "next": "nextjs", "electron": "electron", "react-router-dom": "reactrouter", "react-router": "reactrouter",
    "eslint": "eslint",
}


def details_query(owner: str, names: list[str]) -> str:
    """One GraphQL query with an alias per repo (names must be GitHub-safe, which repo names are)."""
    blobs = " ".join(f'{k}: object(expression: "HEAD:{path}") {{ ... on Blob {{ text }} }}' for k, path in FILES.items())
    parts = []
    for i, name in enumerate(names):
        parts.append(f"""
  r{i}: repository(owner: "{owner}", name: "{name}") {{
    name
    root: object(expression: "HEAD:") {{ ... on Tree {{ entries {{ name }} }} }}
    workflows: object(expression: "HEAD:.github/workflows") {{ ... on Tree {{ entries {{ name }} }} }}
    {blobs}
    defaultBranchRef {{ target {{ ... on Commit {{
      history(first: 6, author: {{id: $uid}}) {{ nodes {{ messageHeadline committedDate url }} }}
    }} }} }}
  }}""")
    return "query($uid: ID!) {" + "".join(parts) + "\n}"


def _text(repo: dict, key: str) -> str:
    return ((repo.get(key) or {}).get("text") or "")


def detect(repo: dict, language: str) -> set[str]:
    entries = {e["name"] for e in ((repo.get("root") or {}).get("entries") or [])}
    tech: set[str] = set()

    try:
        pkg = json.loads(_text(repo, "pkg") or "{}")
    except ValueError:
        pkg = {}
    if pkg:
        tech.add("node")
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        tech |= {key for dep, key in NPM_DEPS.items() if dep in deps}
    if '"manifest_version"' in _text(repo, "manifest"):
        tech.add("chrome")
    if "supabase" in entries:
        tech |= {"supabase", "postgres"}
    if "playwright.config.ts" in entries or "playwright.config.js" in entries:
        tech.add("playwright")

    gradle = _text(repo, "gradle")
    if entries & {"build.gradle.kts", "build.gradle", "settings.gradle.kts"}:
        tech.add("gradle")
    if "android" in gradle:
        tech.add("android")
    if re.search(r"compose", gradle):
        tech.add("compose")
    if "room" in gradle:
        tech.add("sqlite")
    if "ktor" in gradle:
        tech.add("ktor")

    python_deps = (_text(repo, "req") + _text(repo, "pyproject")).lower()
    if language == "QML" or "pyqt" in python_deps or "pyside" in python_deps:
        tech.add("qt")
    if entries & {"metadata.json", "plasmoid", "kwin"} or "plasma" in (repo.get("name") or "").lower():
        tech.add("kde")
    if entries & {"Dockerfile", "docker-compose.yml", "compose.yaml"}:
        tech.add("docker")
    if (repo.get("workflows") or {}).get("entries"):
        tech.add("githubactions")
    if "streamdeck" in (repo.get("name") or "").lower():
        tech.add("streamdeck")

    if ".idea" in entries:
        tech.add("androidstudio" if "android" in tech else "intellij")
    if ".cursor" in entries:
        tech.add("cursor")
    if entries & {".claude", "CLAUDE.md"}:
        tech.add("claude")
    if ".vscode" in entries:
        tech.add("vscode")
    return tech


NOISE = re.compile(r"^(Update|Create|Delete|Add files via upload)\b( [\w./-]+)?$")


def clean_message(message: str) -> str:
    return re.sub(r"\s*\[(skip ci|ci skip|skip actions)\]", "", message).strip()


def commits(repo: dict) -> list[dict]:
    target = ((repo.get("defaultBranchRef") or {}).get("target") or {})
    nodes = (target.get("history") or {}).get("nodes") or []
    return [
        {"repo": repo["name"], "message": clean_message(n["messageHeadline"]), "date": n["committedDate"], "url": n["url"]}
        for n in nodes
        if not n["messageHeadline"].startswith("Merge ") and not NOISE.match(clean_message(n["messageHeadline"]))
    ]
