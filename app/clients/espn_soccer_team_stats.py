import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

async def get_team_stats(league, team_id):
    url = f"{BASE}/{league}/teams/{team_id}?enable=stats"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    stats = data.get("team", {}).get("statistics", [])

    stat_map = {}

    for s in stats:
        name = s.get("name")
        value = s.get("value")  # 🔥 usar value, no displayValue

        if name and value is not None:
            stat_map[name] = value

    goals_for = float(stat_map.get("goalsFor", 0))
    goals_against = float(stat_map.get("goalsAgainst", 0))
    games_played = float(stat_map.get("gamesPlayed", 1))

    # 🔥 Protección contra división absurda
    if games_played <= 0:
        games_played = 1

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
