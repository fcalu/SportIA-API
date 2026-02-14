import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

async def get_team_stats(league, team_id, last_n=25):
    url = f"{BASE}/{league}/teams/{team_id}/schedule?limit=50"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    events = data.get("events", [])

    goals_for = 0
    goals_against = 0
    games_played = 0

    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue

        comp = competitions[0]
        status = comp.get("status", {}).get("type", {}).get("completed", False)

        # Solo partidos ya jugados
        if not status:
            continue

        competitors = comp.get("competitors", [])

        if len(competitors) != 2:
            continue

        for team in competitors:
            if team["team"]["id"] == str(team_id):
                team_score = int(team.get("score", 0))
                goals_for += team_score
            else:
                opp_score = int(team.get("score", 0))
                goals_against += opp_score

        games_played += 1

        if games_played >= last_n:
            break

    # Protección mínima
    if games_played == 0:
        return {
            "goals_for": 1.3,
            "goals_against": 1.3,
            "games_played": 10
        }

    return {
        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played
    }
