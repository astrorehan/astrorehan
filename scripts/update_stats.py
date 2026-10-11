"""Generate profile SVGs using GitHub data and the preinstalled gh CLI.

Run with GH_TOKEN in CI, or an authenticated gh session locally.
Only public, non-fork repositories owned by PROFILE_USER enter repository metrics.
"""

from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

from profile_svg import Svg, palette, shell, symbol


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
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    response = api("graphql", "-f", f"query={query}", "-f", f"login={USER}")
    calendar = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return {
        "repositories": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "contributions": calendar["totalContributions"],
        "weeks": [sum(day["contributionCount"] for day in week["contributionDays"]) for week in calendar["weeks"]],
        "languages": languages,
    }


def activity_bars(svg, weeks, x, baseline, width, height, colors):
    peak = max(weeks, default=0) or 1
    slot = width / max(len(weeks), 1)
    for i, value in enumerate(weeks):
        h = max(3, height * value / peak)
        ink = colors["ink"] if i >= len(weeks)-5 else colors["secondary"]
        if not value:
            ink = colors["border"]
        svg.rect(round(x+i*slot,2), round(baseline-h,2), round(slot*.60,2), round(h,2), ink, 2)


def render(data, dark, updated, mobile=False):
    c = palette(dark)
    w, h = (640, 1138) if mobile else (1280, 776)
    description = f"{data['contributions']} contributions in the past year, {data['repositories']} public original repositories, {data['stars']} stars, {len(data['languages'])} project languages. Weekly activity and language share by code bytes. Updated {updated}."
    svg = Svg(w, h, f"{USER} — GitHub at a glance", description)
    shell(svg, c)
    pad = 32 if mobile else 40
    symbol(svg, pad, 31, 22, c["ink"])
    svg.text("GITHUB / ACTIVITY", pad+35, 47, 12, c["secondary"], "GeistMono", 400, .05)
    if mobile:
        svg.text("GitHub, at a glance.", pad, 103, 34, c["ink"], "Geist", 500, -.03)
        svg.text(f"UPDATED {updated}", pad, 134, 13, c["muted"], "GeistMono", 400, .03)
        panel = dict(x=24,y=161,w=592,h=280)
    else:
        svg.text("GitHub, at a glance.", pad, 101, 38, c["ink"], "Geist", 500, -.03)
        svg.rect(972, 66, 268, 38, c["surface"], 19, c["border"])
        svg.text(f"UPDATED {updated}", 1106, 90, 13, c["muted"], "GeistMono", 400, .03, "center")
        panel = dict(x=40,y=136,w=770,h=294)
    x,y,pw,ph = panel.values()
    svg.rect(x,y,pw,ph,c["surface"],26,c["border"])
    svg.text("Contributions",x+28,y+40,20,c["secondary"],weight=500)
    number_size = 88 if data["contributions"] < 100_000 else 70
    number_width = svg.text(f"{data['contributions']:,}",x+24,y+139,number_size,c["ink"],"Geist",500,-.04)
    svg.text("in the past year",x+24+number_width+18,y+134,17,c["muted"])
    activity_bars(svg,data["weeks"],x+28,y+ph-49,pw-56,70,c)
    svg.text("Weekly activity",x+28,y+ph-23,13,c["muted"])
    svg.text("12 months",x+pw-28,y+ph-23,13,c["muted"],align="right")

    metrics = [(data["repositories"],"Repositories","public / original"),
               (data["stars"],"Stars","on original repos"),
               (len(data["languages"]),"Languages","across projects")]
    if mobile:
        for i,(value,label,caption) in enumerate(metrics):
            mx = pad+i*196
            if i:
                svg.line(mx-17,472,mx-17,590,c["border"])
            svg.text(f"{value:,}",mx,524,54,c["ink"],"Geist",500,-.03)
            svg.text(label,mx,554,18,c["secondary"],weight=500)
            svg.text(caption,mx,581,13,c["muted"])
        svg.line(pad,612,w-pad,612,c["border"])
        svg.text("Language mix",pad,657,28,c["ink"],"Geist",500,-.03)
        svg.text("By code bytes / public projects",pad,684,15,c["muted"])
        row_start, row_step = 729,56
    else:
        for i,(value,label,caption) in enumerate(metrics):
            my = 136+i*102
            svg.rect(830,my,410,90,c["bg"],26,c["border"])
            svg.text(f"{value:,}",858,my+59,48,c["ink"],"Geist",500,-.03)
            svg.text(label,983,my+38,19,c["secondary"],weight=500)
            svg.text(caption,983,my+65,14,c["muted"])
        svg.text("Language mix",pad,487,28,c["ink"],"Geist",500,-.03)
        svg.text("By code bytes / public projects",w-pad,482,15,c["muted"],align="right")
        row_start, row_step = 538,66
    languages = data["languages"].most_common(5)
    rest = sum(data["languages"].values()) - sum(value for _,value in languages)
    if rest:
        languages.append(("Other",rest))
    total = sum(value for _,value in languages)
    if not total:
        svg.text("No public language data yet.",pad,row_start,20,c["muted"])
    for i,(name,value) in enumerate(languages):
        lx = pad if mobile else pad+(i%2)*628
        ly = row_start+(i if mobile else i//2)*row_step
        bar_width = w-2*pad if mobile else 572
        share = value/total
        svg.text(f"0{i+1}",lx,ly-1,12,c["muted"],"GeistMono")
        svg.text(name,lx+29,ly,19,c["secondary"],weight=500)
        svg.text(f"{share*100:.1f}%",lx+bar_width,ly,20,c["ink"],"Geist",500,align="right")
        svg.rect(lx,ly+13,bar_width,5,c["subtle"],2.5)
        svg.rect(lx,ly+13,round(bar_width*share,2),5,c["ink"],2.5)
    if mobile:
        svg.line(pad,1072,w-pad,1072,c["border"])
        svg.text("Public, original repos. Profile repo excluded from mix.",pad,1105,12,c["muted"])
    else:
        svg.line(pad,724,w-pad,724,c["border"])
        svg.text("Public, original repositories. Profile repository excluded from language mix.",pad,754,13,c["muted"])
        svg.text(f"@{USER}",w-pad,754,13,c["secondary"],"GeistMono",align="right")
    return svg.finish()


def main():
    data = collect()
    updated = datetime.now(timezone.utc).strftime("%d %b %Y")
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        for mobile in (False, True):
            suffix = "-mobile" if mobile else ""
            (assets / f"stats-{theme}{suffix}.svg").write_text(render(data, theme == "dark", updated, mobile), encoding="utf-8", newline="\n")
    print(f"Updated stats: {data['repositories']} repos, {data['contributions']} contributions, {len(data['languages'])} languages")


if __name__ == "__main__":
    main()
