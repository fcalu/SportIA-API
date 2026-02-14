import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

def safe_float(v, default=0):
    try:
        return float(v)
    except:
        return default


async def get_team_stats(league, team_id):
    url = f"{BASE}/{league}/teams/{team_id}"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    team = data.get("team", {})

    goals_for = 0
    goals_against = 0
    games_played = 1

    # ✅ Primero intenta statistics
    statistics = team.get("statistics")

    if statistics:
        stat_map = {s.get("name"): s.get("value") for s in statistics}

        goals_for = safe_float(stat_map.get("goalsFor") or stat_map.get("goals"))
        goals_against = safe_float(stat_map.get("goalsAgainst"))
        games_played = safe_float(stat_map.get("gamesPlayed") or stat_map.get("games"))

    # ✅ Si no existe statistics, usa record
    if not goals_for:
        record = team.get("record", {}).get("items", [])

        for item in record:
            if item.get("description") == "Overall":
                stats = item.get("stats", [])
                stat_map = {s.get("name"): s.get("value") for s in stats}

                goals_for = safe_float(stat_map.get("pointsFor"))
                goals_against = safe_float(stat_map.get("pointsAgainst"))
                games_played = safe_float(stat_map.get("gamesPlayed"))
                break

    if games_played <= 0:
        games_played = 1

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
