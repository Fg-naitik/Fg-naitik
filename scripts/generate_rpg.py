#!/usr/bin/env python3
import base64, json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "rpg-config.json").read_text())
THEME, PROG = CFG["theme"], CFG["progression"]

def fetch_stats():
    token = os.environ["GITHUB_TOKEN"]
    query = '''
    query($login: String!) {
      user(login: $login) {
        name
        followers { totalCount }
        repositories(privacy: PUBLIC, first: 1) { totalCount }
        contributionsCollection {
          totalPullRequestContributions
          totalIssueContributions
          contributionCalendar { totalContributions }
        }
      }
    }'''
    body = json.dumps({"query":query,"variables":{"login":CFG["username"]}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization":"Bearer "+token, "Content-Type":"application/json",
        "User-Agent":"naitik-exe-rpg-generator"
    })
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read())
    if data.get("errors"): raise RuntimeError(json.dumps(data["errors"]))
    u = data["data"]["user"]
    if not u: raise RuntimeError("GitHub user not found")
    c = u["contributionsCollection"]
    return {
        "contributions":c["contributionCalendar"]["totalContributions"],
        "repos":u["repositories"]["totalCount"],
        "followers":u["followers"]["totalCount"],
        "prs":c["totalPullRequestContributions"],
        "issues":c["totalIssueContributions"]
    }

def build_svg(s):
    xp = s["contributions"]*PROG["contribution_xp"] + s["repos"]*PROG["public_repo_xp"]
    level = 1 + xp//PROG["level_xp_step"]
    progress = xp % PROG["level_xp_step"]
    pct = round(progress/PROG["level_xp_step"]*100)
    avatar = base64.b64encode((ROOT/"assets/rpg-avatar.jpg").read_bytes()).decode()
    skill_svg, y = [], 548
    for name, val in list(PROG["manual_skill_points"].items())[:6]:
        val = max(0,min(100,int(val)))
        skill_svg.append(f'<text x="690" y="{y}" class="skill">{escape(name.upper())}</text><rect x="900" y="{y-12}" width="300" height="10" rx="5" fill="#1D2B40"/><rect x="900" y="{y-12}" width="{3*val}" height="10" rx="5" fill="url(#skill)"><animate attributeName="width" from="0" to="{3*val}" dur="1.3s" fill="freeze"/></rect><text x="1220" y="{y}" class="value">{val}%</text>')
        y += 37
    achievements = []
    tests = [
      (s["contributions"] >= 1, "FIRST SIGNAL", "First contribution recorded"),
      (s["repos"] >= 1, "PROJECT FOUNDER", "Public repository detected"),
      (s["prs"] >= 1, "COLLABORATOR", "Pull request contribution"),
      (s["issues"] >= 1, "BUG HUNTER", "Issue contribution"),
      (s["contributions"] >= 100, "CONSISTENCY", "100+ contributions"),
      (s["repos"] >= 5, "PORTFOLIO BUILDER", "5+ public repositories")
    ]
    for ok, title, detail in tests:
        if ok and len(achievements)<4: achievements.append((title,detail,True))
    while len(achievements)<4: achievements.append(("LOCKED","Keep building to unlock",False))
    ach_svg=[]
    for (title, detail, ok),(x,yy) in zip(achievements,[(690,790),(960,790),(690,855),(960,855)]):
        col = THEME["cyan"] if ok else "#526176"
        ach_svg.append(f'<rect x="{x}" y="{yy}" width="245" height="52" rx="9" fill="#0A1423" stroke="{col}" stroke-opacity=".7"/><circle cx="{x+19}" cy="{yy+26}" r="6" fill="{col}"/><text x="{x+34}" y="{yy+23}" class="ach" fill="{col}">{escape(title)}</text><text x="{x+34}" y="{yy+40}" class="tiny">{escape(detail)}</text>')
    t=THEME
    updated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1500" height="940" viewBox="0 0 1500 940" role="img" aria-labelledby="title desc">
<title id="title">NAITIK.EXE dynamic RPG player card</title>
<desc id="desc">GitHub contribution and repository metrics power XP and achievements. Skill levels are manually configured.</desc>
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{t['background']}"/><stop offset=".65" stop-color="#111A2B"/><stop offset="1" stop-color="#1B102C"/></linearGradient>
 <linearGradient id="edge"><stop stop-color="{t['red']}"/><stop offset=".5" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['purple']}"/></linearGradient>
 <linearGradient id="skill"><stop stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['purple']}"/></linearGradient>
 <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#28405B" stroke-opacity=".25"/></pattern>
 <clipPath id="portrait"><rect x="38" y="130" width="590" height="700" rx="18"/></clipPath>
</defs>
<rect x="5" y="5" width="1490" height="930" rx="24" fill="url(#bg)" stroke="url(#edge)" stroke-width="3"/>
<rect x="7" y="7" width="1486" height="926" rx="22" fill="url(#grid)"/>
<g font-family="monospace">
 <text x="42" y="61" fill="{t['text']}" font-size="27" font-weight="bold" letter-spacing="3">NAITIK.EXE</text>
 <text x="1455" y="59" fill="{t['cyan']}" font-size="14" text-anchor="end" letter-spacing="2">PLAYER PROFILE // LIVE DATA</text>
 <circle cx="43" cy="84" r="5" fill="#00FF9D" filter="url(#glow)"><animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle>
 <text x="58" y="89" fill="#91A4BA" font-size="13">SYSTEM ONLINE • UPDATED {updated}</text>
</g>
<rect x="28" y="125" width="610" height="720" rx="20" fill="#0A1220" stroke="#29415B"/>
<g clip-path="url(#portrait)">
 <image x="38" y="130" width="590" height="700" xlink:href="data:image/jpeg;base64,{avatar}" preserveAspectRatio="xMidYMid slice"/>
 <rect x="38" y="130" width="590" height="700" fill="#07111F" opacity=".07"/>
</g>
<rect x="48" y="755" width="570" height="66" rx="12" fill="#07101E" fill-opacity=".92" stroke="{t['red']}" stroke-opacity=".8"/>
<g font-family="monospace"><text x="70" y="783" fill="{t['text']}" font-size="20" font-weight="bold">NAITIK // THE BUILDER</text><text x="70" y="806" fill="{t['cyan']}" font-size="13">{escape(CFG['class_name'])}</text></g>
<g font-family="monospace">
 <text x="690" y="153" fill="{t['muted']}" font-size="15" letter-spacing="3">CURRENT CLASS</text>
 <text x="690" y="190" fill="{t['text']}" font-size="27" font-weight="bold">{escape(CFG['class_name'])}</text>
 <text x="690" y="220" fill="{t['muted']}" font-size="15">{escape(CFG['tagline'])}</text>
 <rect x="690" y="250" width="760" height="150" rx="16" fill="#0A1423" stroke="#29415B"/>
 <text x="720" y="287" fill="{t['cyan']}" font-size="14" letter-spacing="2">PLAYER LEVEL</text>
 <text x="720" y="360" fill="{t['text']}" font-size="68" font-weight="bold">{level:02d}</text>
 <text x="850" y="337" fill="{t['text']}" font-size="19">LEVEL {level}</text>
 <text x="850" y="365" fill="{t['muted']}" font-size="14">{xp:,} TOTAL XP • {PROG['level_xp_step']-progress:,} XP TO NEXT LEVEL</text>
 <rect x="850" y="375" width="520" height="10" rx="5" fill="#1D2B40"/>
 <rect x="850" y="375" width="{5.2*pct}" height="10" rx="5" fill="url(#edge)"><animate attributeName="width" from="0" to="{5.2*pct}" dur="1.5s" fill="freeze"/></rect>
 <text x="690" y="450" fill="{t['cyan']}" font-size="15" letter-spacing="2">LIVE GITHUB ATTRIBUTES</text>
 {''.join(f'<rect x="{x}" y="470" width="{w}" height="65" rx="10" fill="#0A1423" stroke="#263D57"/><text x="{x+18}" y="495" fill="{t["muted"]}" font-size="12">{label}</text><text x="{x+18}" y="520" fill="{t["text"]}" font-size="24" font-weight="bold">{value:,}</text>' for x,w,label,value in [(690,175,"CONTRIBUTIONS",s["contributions"]),(880,175,"PUBLIC REPOS",s["repos"]),(1070,175,"FOLLOWERS",s["followers"]),(1260,190,"PULL REQUESTS",s["prs"])])}
 <text x="690" y="578" fill="{t['cyan']}" font-size="15" letter-spacing="2">MANUAL SKILL TREE // EDIT rpg-config.json</text>
 {''.join(skill_svg)}
 <text x="690" y="765" fill="{t['cyan']}" font-size="15" letter-spacing="2">ACHIEVEMENTS</text>
 {''.join(ach_svg)}
</g>
<rect x="8" y="8" width="1484" height="4" fill="{t['cyan']}" opacity=".45" filter="url(#glow)"><animate attributeName="y" values="8;928;8" dur="10s" repeatCount="indefinite"/></rect>
</svg>'''

def main():
    stats=fetch_stats()
    out=ROOT/"assets/naitik-exe-rpg.svg"
    out.write_text(build_svg(stats),encoding="utf-8")
    print(f"Generated {out}; contributions={stats['contributions']}, repos={stats['repos']}")

if __name__=="__main__": main()
