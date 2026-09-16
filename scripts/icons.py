"""Icon catalog: image URLs for the README and raw Simple Icons paths for embedding in SVGs."""

from __future__ import annotations

import re
import urllib.request
from functools import lru_cache

SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.31.0/icons"
DEVICON = "https://cdn.jsdelivr.net/npm/devicon@2.17.0/icons"
ICONIFY = "https://api.iconify.design/simple-icons"
LOBE = "https://unpkg.com/@lobehub/icons-static-svg@1.95.0/icons"


def devicon(name: str, variant: str = "original") -> str:
    return f"{DEVICON}/{name}/{name}-{variant}.svg"


def iconify(slug: str, color: str) -> str:
    return f"{ICONIFY}:{slug}.svg?color=%23{color.lstrip('#')}"


# GitHub language name -> (Simple Icons slug, README icon URL).
LANGUAGES = {
    "Kotlin": ("kotlin", devicon("kotlin")),
    "JavaScript": ("javascript", devicon("javascript")),
    "TypeScript": ("typescript", devicon("typescript")),
    "Python": ("python", devicon("python")),
    "QML": ("qt", devicon("qt")),
    "C++": ("cplusplus", devicon("cplusplus")),
    "HTML": ("html5", devicon("html5")),
    "CSS": ("css", devicon("css3")),
    "Shell": ("gnubash", devicon("bash")),
    "PLpgSQL": ("postgresql", devicon("postgresql")),
    "Java": ("openjdk", devicon("java")),
    "CMake": ("cmake", devicon("cmake")),
    "Mermaid": ("mermaid", iconify("mermaid", "FF3670")),
    "Dockerfile": ("docker", devicon("docker")),
}

# Detected technology key -> (label, README icon URL, homepage).
TECH = {
    "react": ("React", devicon("react"), "https://react.dev"),
    "vite": ("Vite", devicon("vitejs"), "https://vite.dev"),
    "tailwind": ("Tailwind CSS", devicon("tailwindcss"), "https://tailwindcss.com"),
    "supabase": ("Supabase", devicon("supabase"), "https://supabase.com"),
    "postgres": ("PostgreSQL", devicon("postgresql"), "https://www.postgresql.org"),
    "node": ("Node.js", devicon("nodejs"), "https://nodejs.org"),
    "playwright": ("Playwright", devicon("playwright"), "https://playwright.dev"),
    "nextjs": ("Next.js", devicon("nextjs"), "https://nextjs.org"),
    "electron": ("Electron", devicon("electron"), "https://www.electronjs.org"),
    "reactrouter": ("React Router", devicon("reactrouter"), "https://reactrouter.com"),
    "eslint": ("ESLint", devicon("eslint"), "https://eslint.org"),
    "chrome": ("Chrome extensions", devicon("chrome"), "https://developer.chrome.com/docs/extensions"),
    "android": ("Android", devicon("android"), "https://developer.android.com"),
    "compose": ("Jetpack Compose", devicon("jetpackcompose"), "https://developer.android.com/compose"),
    "sqlite": ("Room / SQLite", devicon("sqlite"), "https://developer.android.com/training/data-storage/room"),
    "ktor": ("Ktor", devicon("ktor"), "https://ktor.io"),
    "gradle": ("Gradle", devicon("gradle"), "https://gradle.org"),
    "kde": ("KDE Plasma", iconify("kdeplasma", "1D99F3"), "https://kde.org/plasma-desktop"),
    "qt": ("Qt / QML", devicon("qt"), "https://www.qt.io"),
    "docker": ("Docker", devicon("docker"), "https://www.docker.com"),
    "githubactions": ("GitHub Actions", devicon("githubactions"), "https://github.com/features/actions"),
    "streamdeck": ("Stream Deck", iconify("elgato", "58A6FF"), "https://www.elgato.com/stream-deck"),
    # Editors and AI tools (detected from .idea / .cursor / .claude / .vscode folders).
    "androidstudio": ("Android Studio", devicon("androidstudio"), "https://developer.android.com/studio"),
    "intellij": ("IntelliJ IDEA", devicon("intellij"), "https://www.jetbrains.com/idea"),
    "vscode": ("VS Code", devicon("vscode"), "https://code.visualstudio.com"),
    "cursor": ("Cursor", iconify("cursor", "E6EDF3"), "https://cursor.com"),
    "claude": ("Claude Code", f"{LOBE}/claude-color.svg", "https://claude.com/claude-code"),
    "lmstudio": ("LM Studio", iconify("lmstudio", "58A6FF"), "https://lmstudio.ai"),
    "hermes": ("Hermes Agent", "https://raw.githubusercontent.com/T3lluz/T3lluz/main/assets/icons/hermes.svg",
               "https://hermes-agent.nousresearch.com"),
    # Always-on environment (self-reported).
    "linux": ("Linux", devicon("linux"), "https://kernel.org"),
    "arch": ("Arch Linux", devicon("archlinux"), "https://archlinux.org"),
    "git": ("Git", devicon("git"), "https://git-scm.com"),
    "virtualbox": ("VirtualBox VMs", iconify("virtualbox", "60A5FA"), "https://www.virtualbox.org"),
}

# Tech key -> Simple Icons slug for the banner / cards.
TECH_SLUGS = {
    "kde": "kdeplasma", "react": "react", "android": "android", "compose": "jetpackcompose",
    "chrome": "googlechrome", "supabase": "supabase", "qt": "qt", "vite": "vite",
    "githubactions": "githubactions", "linux": "linux", "arch": "archlinux", "git": "git",
}


@lru_cache(maxsize=None)
def simple_icon_path(slug: str) -> str | None:
    """Path data (24x24 viewBox) for a Simple Icons slug, or None if unavailable."""
    try:
        with urllib.request.urlopen(f"{SIMPLE_ICONS}/{slug}.svg", timeout=15) as resp:
            svg = resp.read().decode()
    except OSError:
        return None
    match = re.search(r'<path d="([^"]+)"', svg)
    return match.group(1) if match else None


def language_slug(language: str) -> str | None:
    entry = LANGUAGES.get(language)
    return entry[0] if entry else None
