import httpx


BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes"


async def get_player_game_log(player_id, last_n=10):

    url = f"{BASE_URL}/{player_id}/gamelog"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return []

        data = response.json()

    except Exception:
        return []

    events = data.get("events", [])

    games = []

    for event in events[:last_n]:

        try:
            stats = event.get("statistics", [])

            stat_map = {}

            for s in stats:
                name = s.get("name")
                value = s.get("displayValue")

                if name and value:
                    stat_map[name] = value

            games.append({
                "points": float(stat_map.get("points", 0)),
                "rebounds": float(stat_map.get("rebounds", 0)),
                "assists": float(stat_map.get("assists", 0)),
                "minutes": float(stat_map.get("minutes", 0))
            })

        except:
            continue

    return games
