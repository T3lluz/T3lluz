"""Everything personal. The rest of scripts/ reads from here and from the GitHub API."""

USERNAME = "T3lluz"
INTRO = "Bachelor in computer engineering, from Norway."
TAGLINE = "bachelor in computer engineering"

# (label, icon, kind of icon, url). No url means the button is not a link.
LINKS = [
    ("github", "github", "brand", "https://github.com/T3lluz"),
    ("x", "x", "brand", "https://x.com/T3lluz_"),
    ("linkedin", "linkedin", "brand", "https://www.linkedin.com/in/fredrik-stalsberg-427821151/"),
    ("email", "mail", "lucide", "mailto:fstalsberg@gmail.com"),
    ("T3lluz1337", "discord", "brand", None),
]

# Repos that are not "my code" or "what I'm building".
EXCLUDED_REPOS = {USERNAME, "Gruppe-17"}
EXCLUDED_PREFIXES = ("FORK-",)

# Used when the GitHub description is empty or not in English.
DESCRIPTIONS = {
    "DailyDash": "Android dashboard: health, weather, F1, GitHub and servers on one screen",
    "Cinema-Info": "Live cinema schedule with seats, times and posters for Buen Kino",
    "PorcoRosso": "React 19 + Vite site published on GitHub Pages",
    "proslides-overview": "Project site for ProSlides, our bachelor project",
}

# Stack entries no repo can prove. Everything else in the stack window is detected (see detect.py).
ALWAYS = ["linux", "arch", "git"]
