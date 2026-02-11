import httpx
from app.clients.espn_player_stats import get_player_stats

BASE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2026/teams"


# ==========================================================
# TEAM ROSTER LOADER
# ==========================================================
async def get_team_roster(team_id: str):

    url = f"{BASE}/{team_id}/athletes?lang=en&region=us"

    print(f"\n📡 FETCH ROSTER → TEAM {team_id}")
    print(f"🌐 URL → {url}")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

        players = []

        items = data.get("items", [])
        print(f"👥 PLAYERS FOUND → {len(items)}")

        for item in items:
            ref = item["$ref"]

            pr = await client.get(ref)
            pr.raise_for_status()
            p = pr.json()

            raw_player = {
                "id": p.get("id"),
                "fullName": p.get("displayName"),
                "position": {
                    "abbreviation": p.get("position", {}).get("abbreviation", "SF")
                },
                "teamId": team_id
            }

            norm = await normalize_player(raw_player)
            players.append(norm)

    print(f"✅ NORMALIZED PLAYERS → {len(players)}")
    return players


# ==========================================================
# PLAYER NORMALIZER — PRODUCTION SAFE + DEBUG
# ==========================================================
async def normalize_player(raw):

    player_id = raw["id"]
    pos = raw.get("position", {}).get("abbreviation", "SF")

    stats = await get_player_stats(player_id)

    if not stats:
        minutes, pts, reb, ast = 18, 6, 3, 2
        std_pts = 3
        std_reb = 2
        std_ast = 2
        form = 1
    else:
        minutes = stats.get("minutes", 18)
        pts = stats.get("points", 6)
        reb = stats.get("rebounds", 3)
        ast = stats.get("assists", 2)
        std_pts = stats.get("points_std_dev", pts * 0.22)
        std_reb = stats.get("reb_std_dev", reb * 0.25)
        std_ast = stats.get("ast_std_dev", ast * 0.30)
        form = stats.get("form_factor", 1)

    if not minutes or minutes == 0:
        minutes = 18

    ppm = pts / minutes if minutes else 0
    rpm = reb / minutes if minutes else 0
    apm = ast / minutes if minutes else 0

    usage = max(0.12, min(0.36, ppm * 1.25))

    return {
        "id": player_id,
        "name": raw["fullName"],
        "position": pos,
        "role": "Primary" if usage > 0.24 else "Secondary",
        "base_minutes": round(minutes, 2),
        "usage_rate": round(usage, 3),
        "points_per_min": round(ppm, 3),
        "reb_per_min": round(rpm, 3),
        "ast_per_min": round(apm, 3),
        "points_std_dev": round(std_pts, 2),
        "reb_std_dev": round(std_reb, 2),
        "ast_std_dev": round(std_ast, 2),
        "form_factor": form
    }
