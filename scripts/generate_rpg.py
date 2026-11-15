#!/usr/bin/env python3
import base64, json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "rpg-config.json").read_text(encoding="utf-8"))
THEME, PROG = CFG["theme"], CFG["progression"]

def fetch_stats():
    token = os.environ["GITHUB_TOKEN"]
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(privacy: PUBLIC, first: 1) { totalCount }
        contributionsCollection {
          totalPullRequestContributions
          totalIssueContributions
          contributionCalendar { totalContributions }
        }
      }
    }"""
    body = json.dumps({"query": query, "variables": {"login": CFG["username"]}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "naitik-exe-rpg-generator"})
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read())
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"]))
    user = data["data"]["user"]
    if not user:
        raise RuntimeError("GitHub user not found")
    c = user["contributionsCollection"]
    return {
        "contributions": c["contributionCalendar"]["totalContributions"],
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "prs": c["totalPullRequestContributions"],
        "issues": c["totalIssueContributions"]
    }

def build_svg(stats):
    xp = stats["contributions"] * PROG["contribution_xp"] + stats["repos"] * PROG["public_repo_xp"]
    level = 1 + xp // PROG["level_xp_step"]
    progress = xp % PROG["level_xp_step"]
    pct = round(progress / PROG["level_xp_step"] * 100)
    xp_to_next = PROG["level_xp_step"] - progress
    avatar = base64.b64encode((ROOT / "assets/rpg-avatar.jpg").read_bytes()).decode()
    t = THEME

    skills = []
    for i, (name, raw) in enumerate(list(PROG["manual_skill_points"].items())[:6]):
        value = max(0, min(100, int(raw)))
        y = 625 + i * 39
        skills.append(f"""
        <text x="700" y="{y}" class="skill-name">{escape(name.upper())}</text>
        <rect x="940" y="{y-13}" width="300" height="11" rx="5.5" fill="#202D42"/>
        <rect x="940" y="{y-13}" width="{3*value}" height="11" rx="5.5" fill="url(#skill)">
          <animate attributeName="width" from="0" to="{3*value}" dur="1.2s" begin="{i*0.12}s" fill="freeze"/>
        </rect>
        <text x="1260" y="{y}" class="skill-value">{value}%</text>""")

    tests = [
        (stats["contributions"] >= 1, "FIRST SIGNAL", "First contribution recorded"),
        (stats["repos"] >= 1, "PROJECT FOUNDER", "Public repository detected"),
        (stats["prs"] >= 1, "COLLABORATOR", "Pull request contribution"),
        (stats["issues"] >= 1, "BUG HUNTER", "Issue contribution"),
        (stats["contributions"] >= 100, "CONSISTENCY", "100+ contributions"),
        (stats["repos"] >= 5, "PORTFOLIO BUILDER", "5+ public repositories")
    ]
    achievements = [(title, detail, True) for ok, title, detail in tests if ok][:4]
    while len(achievements) < 4:
        achievements.append(("LOCKED", "Keep building to unlock", False))

    ach = []
    for (title, detail, unlocked), (x, y) in zip(
        achievements, [(700, 900), (1080, 900), (700, 965), (1080, 965)]
    ):
        color = t["cyan"] if unlocked else "#63748A"
        ach.append(f"""
        <rect x="{x}" y="{y}" width="340" height="52" rx="11" fill="#0B1626" stroke="{color}" stroke-opacity=".65"/>
        <circle cx="{x+22}" cy="{y+26}" r="5.5" fill="{color}"/>
        <text x="{x+40}" y="{y+23}" class="achievement-title" fill="{color}">{escape(title)}</text>
        <text x="{x+40}" y="{y+40}" class="achievement-detail">{escape(detail)}</text>""")

    stat_cards = []
    for x, width, label, value in [
        (700, 170, "CONTRIBUTIONS", stats["contributions"]),
        (885, 170, "PUBLIC REPOS", stats["repos"]),
        (1070, 170, "FOLLOWERS", stats["followers"]),
        (1255, 195, "PULL REQUESTS", stats["prs"])
    ]:
        stat_cards.append(f"""
        <rect x="{x}" y="465" width="{width}" height="78" rx="12" fill="#0B1626" stroke="#293D56"/>
        <text x="{x+17}" y="493" class="stat-label">{label}</text>
        <text x="{x+17}" y="525" class="stat-value">{value:,}</text>""")

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
      width="1500" height="1050" viewBox="0 0 1500 1050" role="img" aria-labelledby="title desc">
<title id="title">NAITIK.EXE dynamic RPG player card</title>
<desc id="desc">GitHub metrics power XP and achievements; skill levels are manually configured.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="{t['background']}"/><stop offset=".65" stop-color="#111A2B"/><stop offset="1" stop-color="#1B102C"/>
  </linearGradient>
  <linearGradient id="edge"><stop stop-color="{t['red']}"/><stop offset=".5" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['purple']}"/></linearGradient>
  <linearGradient id="skill"><stop stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['purple']}"/></linearGradient>
  <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="3.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse">
    <path d="M34 0H0V34" fill="none" stroke="#28405B" stroke-opacity=".22"/>
  </pattern>
  <clipPath id="portrait"><rect x="38" y="130" width="590" height="850" rx="18"/></clipPath>
  <style>
    .ui {{ font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; }}
    .mono {{ font-family: "SFMono-Regular", Consolas, monospace; }}
    .section {{ font-size:18px; font-weight:800; letter-spacing:1.2px; }}
    .stat-label {{ font-size:15px; font-weight:750; fill:#DCE7F4; letter-spacing:.25px; }}
    .stat-value {{ font-size:29px; font-weight:800; fill:#FFFFFF; }}
    .skill-name {{ font-size:17px; font-weight:750; fill:#F0F5FC; letter-spacing:.2px; }}
    .skill-value {{ font-size:17px; font-weight:800; fill:#FFFFFF; }}
    .achievement-title {{ font-size:15px; font-weight:800; letter-spacing:.2px; }}
    .achievement-detail {{ font-size:14px; font-weight:650; fill:#D0DBE8; }}
  </style>
</defs>

<rect x="5" y="5" width="1490" height="1040" rx="24" fill="url(#bg)" stroke="url(#edge)" stroke-width="3"/>
<rect x="7" y="7" width="1486" height="1036" rx="22" fill="url(#grid)"/>

<!-- Header -->
<g class="ui">
  <text x="42" y="61" fill="{t['text']}" font-size="29" font-weight="750" letter-spacing="2">NAITIK.EXE</text>
  <text x="1455" y="58" fill="{t['cyan']}" font-size="15" font-weight="650" text-anchor="end" letter-spacing="1.8">PLAYER PROFILE  /  LIVE DATA</text>
  <circle cx="44" cy="87" r="5" fill="#00FF9D" filter="url(#glow)">
    <animate attributeName="opacity" values="1;.35;1" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="59" y="92" fill="#91A4BA" font-size="15" font-weight="650">SYSTEM ONLINE  •  UPDATED {updated}</text>
</g>
<path d="M30 112H1470" stroke="{t['cyan']}" stroke-opacity=".22"/>

<!-- Character portrait -->
<rect x="28" y="130" width="610" height="850" rx="20" fill="#0A1220" stroke="#29415B"/>
<g clip-path="url(#portrait)">
  <image x="38" y="130" width="590" height="850" xlink:href="data:image/jpeg;base64,{avatar}" preserveAspectRatio="xMidYMid slice"/>
  <rect x="38" y="130" width="590" height="850" fill="#07111F" opacity=".055"/>
</g>
<rect x="48" y="890" width="570" height="70" rx="12" fill="#07101E" fill-opacity=".94" stroke="{t['red']}" stroke-opacity=".85"/>
<g class="ui">
  <text x="72" y="920" fill="{t['text']}" font-size="22" font-weight="750">NAITIK  /  THE BUILDER</text>
  <text x="72" y="944" fill="{t['cyan']}" font-size="14" font-weight="650" letter-spacing=".8">{escape(CFG['class_name'])}</text>
</g>

<!-- Dashboard -->
<g class="ui">
  <text x="700" y="157" fill="{t['muted']}" font-size="16" font-weight="750" letter-spacing="1.2">CURRENT CLASS</text>
  <text x="700" y="197" fill="{t['text']}" font-size="29" font-weight="750">{escape(CFG['class_name'])}</text>
  <text x="700" y="226" fill="{t['muted']}" font-size="17">{escape(CFG['tagline'])}</text>

  <rect x="690" y="252" width="760" height="176" rx="17" fill="#0A1423" stroke="#29415B"/>
  <text x="720" y="290" fill="{t['cyan']}" font-size="16" font-weight="800" letter-spacing="1.2">PLAYER LEVEL</text>
  <text x="720" y="375" fill="{t['text']}" font-size="76" font-weight="800">{level:02d}</text>
  <text x="860" y="343" fill="{t['text']}" font-size="22" font-weight="700">LEVEL {level}</text>
  <text x="860" y="372" fill="{t['muted']}" font-size="17" font-weight="650">{xp:,} TOTAL XP  ·  {xp_to_next:,} XP TO NEXT LEVEL</text>
  <rect x="860" y="390" width="520" height="12" rx="6" fill="#1D2B40"/>
  <rect x="860" y="390" width="{5.2*pct}" height="12" rx="6" fill="url(#edge)">
    <animate attributeName="width" from="0" to="{5.2*pct}" dur="1.4s" fill="freeze"/>
  </rect>

  <text x="700" y="458" class="section" fill="{t['cyan']}">LIVE GITHUB ATTRIBUTES</text>
  {''.join(stat_cards)}

  <text x="700" y="585" class="section" fill="{t['cyan']}">SKILL TREE</text>
  <text x="1450" y="585" fill="{t['muted']}" font-size="14" font-weight="650" text-anchor="end" letter-spacing=".3">MANUALLY CONFIGURED</text>
  {''.join(skills)}

  <text x="700" y="875" class="section" fill="{t['cyan']}">ACHIEVEMENTS</text>
  {''.join(ach)}
</g>

<!-- Subtle animated scan -->
<rect x="8" y="8" width="1484" height="3" fill="{t['cyan']}" opacity=".28" filter="url(#glow)">
  <animate attributeName="y" values="8;1038;8" dur="14s" repeatCount="indefinite"/>
</rect>
</svg>"""

def main():
    stats = fetch_stats()
    output = ROOT / "assets" / "naitik-exe-rpg.svg"
    output.write_text(build_svg(stats), encoding="utf-8")
    print(f"Generated {output}; contributions={stats['contributions']}, repos={stats['repos']}")

if __name__ == "__main__":
    main()
