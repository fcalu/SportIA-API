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

    team = data.get("team", {})
    stats = team.get("statistics", [])

    goals_for = 0
    goals_against = 0
    games_played = 0

    for stat in stats:
        name = stat.get("name")
        value = safe_float(stat.get("value"))

        if name == "goalsFor":
            goals_for = value
        elif name == "goalsAgainst":
            goals_against = value
        elif name == "gamesPlayed":
            games_played = value

    # 🔒 Fallback realista si ESPN no devuelve nada
    if games_played == 0:
        games_played = 10

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
