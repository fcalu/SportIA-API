import httpx

BASE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes"

async def get_player_stats(player_id: str):
    """
    Obtiene promedios por juego del jugador desde ESPN Core API
    """

    url = f"{BASE}/{player_id}/statistics"
    params = {
        "season": 2025,      # ✅ temporada válida actual
        "seasontype": 2      # ✅ regular season
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)

        # ESPN usa 404 cuando no hay stats
        if r.status_code == 404:
            return None

        r.raise_for_status()
        data = r.json()

    per_game = {
        "minutes": 0.0,
        "points": 0.0,
        "rebounds": 0.0,
        "assists": 0.0
    }

    splits = data.get("splits") or {}
    categories = splits.get("categories") or []

    for cat in categories:
        for stat in cat.get("stats", []):
            name = stat.get("name")
            value = float(stat.get("value", 0))

            if name == "avgMinutes":
                per_game["minutes"] = value
            elif name == "avgPoints":
                per_game["points"] = value
            elif name == "avgRebounds":
                per_game["rebounds"] = value
            elif name == "avgAssists":
                per_game["assists"] = value

    return per_game
