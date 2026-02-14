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

        if not status:
            continue

        competitors = comp.get("competitors", [])
        if len(competitors) != 2:
            continue

        for team in competitors:
            score_data = team.get("score") or {}
            team_score = int(score_data.get("value", 0))

            if str(team["team"]["id"]) == str(team_id):
                goals_for += team_score
            else:
                goals_against += team_score

        games_played += 1

        if games_played >= last_n:
            break

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
