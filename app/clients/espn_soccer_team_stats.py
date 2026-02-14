import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


async def get_team_stats(league, team_id):
    url = f"{BASE}/{league}/teams/{team_id}?enable=stats"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    stats = (
        data.get("team", {})
            .get("record", {})
            .get("items", [{}])[0]
            .get("stats", [])
    )

    stat_map = {}

    for s in stats:
        name = s.get("name")

        value = (
            s.get("value")
            or s.get("displayValue")
            or s.get("stat")
        )

        if name and value not in [None, ""]:
            try:
                stat_map[name] = float(value)
            except:
                continue

    # 🔥 FIX REAL AQUÍ
    goals_for = (
        stat_map.get("goalsFor")
        or stat_map.get("pointsFor")
        or stat_map.get("goals")
        or 0
    )

    goals_against = (
        stat_map.get("goalsAgainst")
        or stat_map.get("pointsAgainst")
        or 0
    )

    games_played = stat_map.get("gamesPlayed") or 0

    if games_played <= 0:
        games_played = 1  # evitar división por cero

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
