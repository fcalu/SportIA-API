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
    stats_section = team.get("statistics")

    goals_for = 0
    goals_against = 0
    games_played = 0

    if isinstance(stats_section, list):
        # Caso plano
        for stat in stats_section:
            name = stat.get("name")
            value = safe_float(stat.get("value"))

            if name == "goalsFor":
                goals_for = value
            elif name == "goalsAgainst":
                goals_against = value
            elif name == "gamesPlayed":
                games_played = value

    elif isinstance(stats_section, dict):
        # Caso anidado (más común en soccer)
        for split in stats_section.get("splits", []):
            for stat in split.get("stats", []):
                name = stat.get("name")
                value = safe_float(stat.get("value"))

                if name == "goalsFor":
                    goals_for = value
                elif name == "goalsAgainst":
                    goals_against = value
                elif name == "gamesPlayed":
                    games_played = value

    # 🔒 Fallback inteligente
    if games_played == 0:
        games_played = 10

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
