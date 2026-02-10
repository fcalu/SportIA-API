import httpx

BASE_CORE = "https://sports.core.api.espn.com/v2/sports"


NFL_MARKETS = [
    "Passing Yards",
    "Pass Completions",
    "Passing Touchdowns",
    "Carries",
    "Rushing Yards",
    "Receiving Yards",
    "Receptions",
    "Longest Reception",
    "Longest Rush",
    "Anytime Touchdown",
    "Rush + Receiving Yards"
]

NBA_MARKETS = [
    "Points",
    "Rebounds",
    "Assists",
    "3 Pointers Made",
    "Pts + Reb + Ast",
    "Points + Rebounds",
    "Points + Assists",
    "Rebounds + Assists",
    "Double Double",
    "Triple Double",
    "Steals",
    "Blocks"
]



async def fetch_json(url):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()


async def get_athlete_name(athlete_ref):
    data = await fetch_json(athlete_ref)
    return data.get("displayName"), data.get("position", {}).get("abbreviation"), data.get("team", {}).get("$ref")


async def get_team_name(team_ref):
    data = await fetch_json(team_ref)
    return data.get("displayName")


async def get_sportsbook_player_props(sport, league, event_id):
    """
    Trae TODOS los props de DraftKings desde ESPN Core API
    """

    props_url = (
        f"{BASE_CORE}/{sport}/leagues/{league}/events/{event_id}"
        f"/competitions/{event_id}/odds/100/propBets"
    )

    data = await fetch_json(props_url)

    results = []
    seen = set()

    for item in data.get("items", []):

        prop_type = item.get("type", {}).get("name")
        if not prop_type:
            continue

        # 🔥 FILTRO PROFESIONAL DE MERCADOS
        if sport == "football":
            if not any(m in prop_type for m in NFL_MARKETS):
                continue

        elif sport == "basketball":
            if not any(m in prop_type for m in NBA_MARKETS):
                continue


        athlete_ref = item.get("athlete", {}).get("$ref")
        if not athlete_ref:
            continue

        name, role, team_ref = await get_athlete_name(athlete_ref)

        team = None
        if team_ref:
            team = await get_team_name(team_ref)

        line = item.get("current", {}).get("target", {}).get("value")
        if line is None:
            continue

        key = (name, prop_type, line)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "name": name,
            "team": team,
            "role": role,
            "type": prop_type,
            "line": line,
            "source": "DraftKings",
            "status": "Active"
        })

    return results
