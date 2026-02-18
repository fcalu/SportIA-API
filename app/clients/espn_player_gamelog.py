import httpx


BASE_URL = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


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

    games = []

    season_types = data.get("seasonTypes", [])

    if not season_types:
        return []

    categories = season_types[0].get("categories", [])

    for category in categories:
        events = category.get("events", [])

        for event in events:
            stats = event.get("stats", [])

            if len(stats) < 14:
                continue

            try:
                games.append({
                    "minutes": float(stats[0]),
                    "rebounds": float(stats[7]),
                    "assists": float(stats[8]),
                    "points": float(stats[13])
                })
            except:
                continue

            if len(games) >= last_n:
                return games

    return games
