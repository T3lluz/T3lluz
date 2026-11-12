"""Look inside the repos I've been committing to: the stack each one uses, its version, my latest commits."""

from __future__ import annotations

import json
import re

# key -> (label, group). Order inside a group comes from recent commits.
TECH = {
    "android": ("Android", "build"),
    "compose": ("Jetpack Compose", "build"),
    "ktor": ("Ktor", "build"),
    "room": ("Room", "build"),
    "qt": ("Qt Quick", "build"),
    "quickshell": ("Quickshell", "build"),
    "react": ("React", "build"),
    "nextjs": ("Next.js", "build"),
    "vite": ("Vite", "build"),
    "tailwind": ("Tailwind", "build"),
    "node": ("Node.js", "build"),
    "deno": ("Deno", "build"),
    "bun": ("Bun", "build"),
    "supabase": ("Supabase", "build"),
    "postgres": ("Postgres", "build"),
    "playwright": ("Playwright", "build"),
    "webext": ("WebExtensions", "build"),
    "electron": ("Electron", "build"),
    "dotnet": (".NET", "build"),
    "winui": ("WinUI 3", "build"),
    "linux": ("Linux", "system"),
    "arch": ("Arch", "system"),
    "omarchy": ("Omarchy", "system"),
    "hyprland": ("Hyprland", "system"),
    "pipewire": ("PipeWire", "system"),
    "docker": ("Docker", "system"),
    "tailscale": ("Tailscale", "system"),
    "git": ("Git", "tools"),
    "githubactions": ("GitHub Actions", "tools"),
    "gradle": ("Gradle", "tools"),
    "androidstudio": ("Android Studio", "tools"),
    "intellij": ("IntelliJ IDEA", "tools"),
    "claude": ("Claude Code", "tools"),
    "cursor": ("Cursor", "tools"),
    "opencode": ("OpenCode", "tools"),
    "t3code": ("T3 Code", "tools"),
    "hermes": ("Hermes Agent", "tools"),
}
GROUPS = ("build", "system", "tools")

# GitHub language name -> Simple Icons slug.
LANGUAGE_ICONS = {
    "Kotlin": "kotlin", "JavaScript": "javascript", "TypeScript": "typescript", "Python": "python", "QML": "qt",
    "C++": "cplusplus", "HTML": "html5", "CSS": "css", "Shell": "gnubash", "PLpgSQL": "postgresql",
    "Java": "openjdk", "CMake": "cmake", "Dockerfile": "docker", "Go": "go", "Go Template": "go", "Zig": "zig",
    "C#": "dotnet", "Rust": "rust",
}

FILES = {
    "pkg": "package.json",
    "gradle": "app/build.gradle.kts",
    "req": "requirements.txt",
    "pyproject": "pyproject.toml",
    "manifest": "manifest.json",
    "extension": "extension/manifest.json",
}

NPM_DEPS = {
    "react": "react", "vite": "vite", "tailwindcss": "tailwind", "@tailwindcss/vite": "tailwind",
    "@supabase/supabase-js": "supabase", "@playwright/test": "playwright", "playwright": "playwright",
    "next": "nextjs", "electron": "electron",
}

TOPICS = {
    "omarchy": "omarchy", "omarchy-plugin": "omarchy", "hyprland": "hyprland", "quickshell": "quickshell",
    "pipewire": "pipewire", "docker": "docker", "tailscale": "tailscale", "t3code": "t3code",
    "hermes-agent": "hermes", "deno": "deno", "chrome-extension": "webext", "firefox-extension": "webext",
    "winui3": "winui",
}

ROOT_ENTRIES = {
    "supabase": ("supabase", "postgres"),
    "playwright.config.ts": ("playwright",), "playwright.config.js": ("playwright",),
    "deno.json": ("deno",), "deno.jsonc": ("deno",), "bun.lock": ("bun",), "bun.lockb": ("bun",),
    "build.gradle.kts": ("gradle",), "build.gradle": ("gradle",), "settings.gradle.kts": ("gradle",),
    "Dockerfile": ("docker",), "docker-compose.yml": ("docker",), "compose.yaml": ("docker",),
    "Directory.Build.props": ("dotnet",), "global.json": ("dotnet",),
    ".cursor": ("cursor",), ".claude": ("claude",), "CLAUDE.md": ("claude",),
    ".opencode": ("opencode",), "opencode.json": ("opencode",),
}


def details_query(owner: str, names: list[str]) -> str:
    """One GraphQL query with an alias per repo."""
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
      history(first: 8, author: {{id: $uid}}) {{ nodes {{ messageHeadline committedDate url }} }}
    }} }} }}
  }}""")
    return "query($uid: ID!) {" + "".join(parts) + "\n}"


def _text(repo: dict, key: str) -> str:
    return (repo.get(key) or {}).get("text") or ""


def _json(repo: dict, key: str) -> dict:
    try:
        data = json.loads(_text(repo, key) or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def stack(repo: dict, language: str, topics: list[str]) -> set[str]:
    entries = {e["name"] for e in ((repo.get("root") or {}).get("entries") or [])}
    tech = {key for topic, key in TOPICS.items() if topic in topics}
    for entry, keys in ROOT_ENTRIES.items():
        if entry in entries:
            tech.update(keys)

    pkg = _json(repo, "pkg")
    if pkg:
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        tech |= {key for dep, key in NPM_DEPS.items() if dep in deps}
        if "deno" not in tech and "bun" not in tech:
            tech.add("node")
    if "manifest_version" in _json(repo, "manifest") or "manifest_version" in _json(repo, "extension"):
        tech.add("webext")

    gradle = _text(repo, "gradle")
    if "android" in gradle:
        tech.add("android")
    if "compose" in gradle:
        tech.add("compose")
    if "room" in gradle:
        tech.add("room")
    if "ktor" in gradle:
        tech.add("ktor")

    python_deps = (_text(repo, "req") + _text(repo, "pyproject")).lower()
    if language == "QML" or "pyqt" in python_deps or "pyside" in python_deps:
        tech.add("qt")
    if language == "C#":
        tech.add("dotnet")
    if (repo.get("workflows") or {}).get("entries"):
        tech.add("githubactions")
    if ".idea" in entries:
        tech.add("androidstudio" if "android" in tech else "intellij")
    return tech


def version(repo: dict) -> str:
    """Version from the plugin or extension manifest, else package.json."""
    for key in ("manifest", "pkg"):
        value = _json(repo, key).get("version")
        if isinstance(value, str) and re.fullmatch(r"\d+(\.\d+){1,3}([-+.\w]*)", value) and value != "0.0.0":
            return value
    return ""


NOISE = re.compile(r"^(Update|Create|Delete|Add files via upload|Initial commit)\b( [\w./-]+)?$")


def _clean(message: str) -> str:
    return re.sub(r"\s*\[(skip ci|ci skip|skip actions)\]", "", message).strip()


def commits(repo: dict) -> list[dict]:
    target = (repo.get("defaultBranchRef") or {}).get("target") or {}
    nodes = (target.get("history") or {}).get("nodes") or []
    return [
        {"repo": repo["name"], "message": _clean(n["messageHeadline"]), "date": n["committedDate"], "url": n["url"]}
        for n in nodes
        if not n["messageHeadline"].startswith("Merge ") and not NOISE.match(_clean(n["messageHeadline"]))
    ]
