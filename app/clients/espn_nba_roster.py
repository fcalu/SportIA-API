import httpx
from app.clients.espn_player_stats import get_player_stats

BASE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2026/teams"


async def get_team_roster(team_id: str):

    url = f"{BASE}/{team_id}/athletes?lang=en&region=us"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

        players = []

        for item in data.get("items", []):
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

    return players


# ================= NORMALIZADOR =================

async def normalize_player(raw):

    player_id = raw["id"]
    pos = raw.get("position", {}).get("abbreviation", "SF")

    stats = await get_player_stats(player_id)

    # ESPN puede devolver None si no hay stats
    if not stats:
        minutes, pts, reb, ast = 18, 6, 3, 2
    else:
        minutes = stats.get("minutes", 18)
        pts = stats.get("points", 6)
        reb = stats.get("rebounds", 3)
        ast = stats.get("assists", 2)

    ppm = pts / minutes if minutes else 0
    rpm = reb / minutes if minutes else 0
    apm = ast / minutes if minutes else 0

    usage = min(0.32, max(0.14, ppm * 1.45))

    return {
        "id": player_id,
        "name": raw["fullName"],
        "position": pos,
        "role": "Primary" if usage > 0.25 else "Secondary",
        "base_minutes": minutes,
        "usage_rate": round(usage, 3),
        "points_per_min": round(ppm, 3),
        "reb_per_min": round(rpm, 3),
        "ast_per_min": round(apm, 3)
    }
