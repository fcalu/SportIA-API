import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

def pick_first(stat_map, keys, default=0):
    for k in keys:
        if k in stat_map and stat_map[k] not in [None, ""]:
            return stat_map[k]
    return default


async def get_team_stats(league, team_id):
    url = f"{BASE}/{league}/teams/{team_id}?enable=stats"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    stats = data.get("team", {}).get("statistics", [])

    stat_map = {}

    for s in stats:
        name = s.get("name")

        # 🔥 ESPN soccer normalmente usa displayValue
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

    goals_for = stat_map.get("goalsFor", stat_map.get("goals", 1.3))
    goals_against = stat_map.get("goalsAgainst", 1.3)
    games_played = stat_map.get("gamesPlayed", 10)

    if games_played <= 0:
        games_played = 10

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
