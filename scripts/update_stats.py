"""Generate profile SVGs using GitHub data and the preinstalled gh CLI.

Run with GH_TOKEN in CI, or an authenticated gh session locally.
Only public, non-fork repositories owned by PROFILE_USER enter repository metrics.
"""

from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get("PROFILE_USER", "astrorehan")
if not re.fullmatch(r"[A-Za-z0-9-]+", USER):
    raise ValueError("Invalid GitHub username")


def api(endpoint, *args):
    result = subprocess.run(
        ["gh", "api", endpoint, *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return json.loads(result.stdout)


def collect():
    repos = []
    page = 1
    while True:
        batch = api(f"users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos.extend(r for r in batch if not r["private"] and not r["fork"])
        if len(batch) < 100:
            break
        page += 1

    languages = Counter()
    for repo in repos:
        # The profile repository contains generated SVGs rather than project code.
        if repo["name"].lower() != USER.lower():
            languages.update(api(f"repos/{USER}/{repo['name']}/languages"))

    query = """query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar { totalContributions }
        }
      }
    }"""
    response = api("graphql", "-f", f"query={query}", "-f", f"login={USER}")
    contributions = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    return {
        "repositories": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "contributions": contributions,
        "languages": languages,
    }


COLORS = {
    "TypeScript": "#60a5fa", "JavaScript": "#facc15", "Python": "#34d399",
    "C++": "#a78bfa", "Luau": "#22d3ee", "HTML": "#fb923c", "CSS": "#f472b6",
}


def render(data, dark, updated):
    bg, panel, ink, muted, line, accent = (
        ("#0b1324", "#111e33", "#edf5ff", "#9aadc7", "#24354e", "#67e8f9") if dark
        else ("#f5f9ff", "#e8f0fb", "#11213a", "#526782", "#c8d8ea", "#087f9a")
    )
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="330" viewBox="0 0 960 330" role="img" aria-labelledby="title desc">
<title id="title">{escape(USER)} — GitHub at a glance</title>
<desc id="desc">{data['contributions']} contributions in the past year, {data['repositories']} public original repositories, {data['stars']} stars. Language share is based on public original repository code bytes.</desc>
<rect x="1" y="1" width="958" height="328" rx="22" fill="{bg}" stroke="{line}"/>
<g font-family="Segoe UI, Arial, sans-serif">
<text x="32" y="39" fill="{accent}" font-size="13" font-weight="700" letter-spacing="2">BUILDING IN PUBLIC</text>
<text x="928" y="39" text-anchor="end" fill="{muted}" font-size="12">UPDATED {updated} UTC</text>''']
    metrics = [
        ("Contributions / past year", data["contributions"]),
        ("Public original repos", data["repositories"]),
        ("Stars on original repos", data["stars"]),
        ("Languages across projects", len(data["languages"])),
    ]
    for i, (label, value) in enumerate(metrics):
        x = 32 + i * 226
        parts.append(f'''<rect x="{x}" y="59" width="216" height="98" rx="12" fill="{panel}"/>
<text x="{x+18}" y="105" fill="{ink}" font-size="34" font-weight="700">{value:,}</text>
<text x="{x+18}" y="135" fill="{muted}" font-size="12">{label}</text>''')
    parts.append(f'<text x="32" y="193" fill="{ink}" font-size="15" font-weight="600">Languages in my public projects</text>')
    languages = data["languages"].most_common(5)
    rest = sum(data["languages"].values()) - sum(value for _, value in languages)
    if rest:
        languages.append(("Other", rest))
    total = sum(value for _, value in languages)
    x = 32.0
    parts.append('<defs><clipPath id="bar"><rect x="32" y="210" width="896" height="14" rx="7"/></clipPath></defs><g clip-path="url(#bar)">')
    for name, value in languages:
        width = 896 * value / total
        color = COLORS.get(name, "#94a3b8")
        parts.append(f'<rect x="{x:.2f}" y="210" width="{width:.2f}" height="14" fill="{color}"/>')
        x += width
    parts.append('</g>')
    if not total:
        parts.append(f'<text x="32" y="254" fill="{muted}" font-size="13">No public language data yet.</text>')
    for i, (name, value) in enumerate(languages):
        x = 32 + (i % 3) * 300
        y = 250 + (i // 3) * 25
        color = COLORS.get(name, "#94a3b8")
        parts.append(f'''<circle cx="{x+5}" cy="{y-4}" r="4" fill="{color}"/>
<text x="{x+18}" y="{y}" fill="{muted}" font-size="13">{escape(name)} <tspan fill="{ink}">{100*value/total:.1f}%</tspan></text>''')
    parts.append(f'<text x="32" y="307" fill="{muted}" font-size="11">Code bytes · public original repositories · excludes this profile repository</text></g></svg>')
    return "\n".join(parts) + "\n"


def main():
    data = collect()
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        (assets / f"stats-{theme}.svg").write_text(render(data, theme == "dark", updated), encoding="utf-8")
    print(f"Updated stats: {data['repositories']} repos, {data['contributions']} contributions, {len(data['languages'])} languages")


if __name__ == "__main__":
    main()
