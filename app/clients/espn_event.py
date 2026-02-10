import httpx

BASE = "https://sports.core.api.espn.com/v2"


async def get_event_teams(sport: str, league: str, event_id: str):
    url = f"{BASE}/sports/{sport}/leagues/{league}/events/{event_id}/competitions/{event_id}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    competitors = data["competitors"]

    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")

    home_team_id = home["team"]["$ref"].split("/")[-1].split("?")[0]
    away_team_id = away["team"]["$ref"].split("/")[-1].split("?")[0]

    return home_team_id, away_team_id

async def get_event_player_status(sport: str, league: str, event_id: str):

    summary_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={event_id}"

    async with httpx.AsyncClient() as client:
        r = await client.get(summary_url)
        r.raise_for_status()
        data = r.json()

    status_map = {}

    boxscore = data.get("boxscore", {})

    # 🔥 CASO 1 — GAME LIVE / POSTGAME (tiene jugadores)
    players_section = boxscore.get("players")
    if players_section:
        for team in players_section:
            for group in team.get("statistics", []):
                for athlete in group.get("athletes", []):
                    athlete_data = athlete.get("athlete")
                    if not athlete_data:
                        continue

                    pid = athlete_data.get("id")
                    active = athlete.get("active", True)

                    status_map[pid] = "ACTIVE" if active else "INACTIVE"

    # 🔥 CASO 2 — PREGAME (NO HAY BOX SCORE)
    # Solo usamos lesiones
    injuries = data.get("injuries", [])
    for injury in injuries:
        athlete_data = injury.get("athlete")
        if not athlete_data:
            continue

        pid = athlete_data.get("id")
        status_map[pid] = injury.get("status", "OUT").upper()

    return status_map
