import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

def safe_float(v, default=0):
    try:
        return float(v)
    except:
        return default


async def get_team_stats(league, team_id):
    url = f"{BASE}/{league}/teams/{team_id}?enable=stats"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    stats = data.get("team", {}).get("statistics", [])

    stat_map = {s["name"]: s["displayValue"] for s in stats}

    return {
        "goals_for": stat_map.get("goalsFor", 1.4),
        "goals_against": stat_map.get("goalsAgainst", 1.4),
        "games_played": stat_map.get("gamesPlayed", 10),  # 🔥 ESTA LÍNEA FALTABA
        "shots": stat_map.get("shots", 12),
        "shots_on_target": stat_map.get("shotsOnTarget", 4)
    }
