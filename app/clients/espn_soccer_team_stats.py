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
        value = s.get("value")

        if name and value is not None:
            stat_map[name] = value

    goals_for = float(pick_first(stat_map, [
        "goalsFor",
        "goals",
        "pointsFor",
        "scored"
    ], 0))

    goals_against = float(pick_first(stat_map, [
        "goalsAgainst",
        "pointsAgainst",
        "conceded"
    ], 0))

    games_played = float(pick_first(stat_map, [
        "gamesPlayed",
        "games",
        "matches",
        "played"
    ], 1))

    if games_played <= 0:
        games_played = 1

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
