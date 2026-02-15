import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


async def get_event_result(league: str, event_id: str):

    url = f"{BASE}/{league}/summary?event={event_id}"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)

    if r.status_code != 200:
        return None

    data = r.json()

    header = data.get("header", {})
    competitions = header.get("competitions", [])

    if not competitions:
        return None

    comp = competitions[0]

    status = comp.get("status", {}).get("type", {})
    completed = status.get("completed", False)

    competitors = comp.get("competitors", [])

    if len(competitors) != 2:
        return None

    home_score = 0
    away_score = 0

    for team in competitors:
        score = int(team.get("score", 0))
        if team.get("homeAway") == "home":
            home_score = score
        else:
            away_score = score

    return {
        "completed": completed,
        "home_score": home_score,
        "away_score": away_score
    }
