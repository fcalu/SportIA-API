import httpx

ESPN_BASE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2026"

async def get_team_roster(team_id: str):

    url = f"{ESPN_BASE}/teams/{team_id}/athletes?lang=en&region=us"

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        data = r.json()

    players = []

    for item in data.get("items", []):
        athlete_ref = item.get("$ref")
        if not athlete_ref:
            continue

        async with httpx.AsyncClient(timeout=20) as client:
            athlete_data = (await client.get(athlete_ref)).json()

        player = {
            "id": athlete_data.get("id"),
            "name": athlete_data.get("displayName"),
            "position": normalize_position(
                athlete_data.get("position", {}).get("abbreviation")
            ),
            "team_id": team_id
        }

        players.append(player)

    return players


def normalize_position(pos):

    if pos in ["PG", "SG"]:
        return pos

    if pos in ["SF", "PF"]:
        return "PF"

    if pos in ["C"]:
        return "C"

    return "SG"
