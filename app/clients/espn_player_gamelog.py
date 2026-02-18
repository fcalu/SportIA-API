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

    names = data.get("names", [])
    events = data.get("events", {})

    games = []

    # los events vienen como dict, no lista
    for event_id, event_data in list(events.items())[:last_n]:

        try:
            stats_values = event_data.get("stats", [])

            if not stats_values or len(stats_values) != len(names):
                continue

            stats_dict = dict(zip(names, stats_values))

            games.append({
                "points": float(stats_dict.get("points", 0)),
                "rebounds": float(stats_dict.get("totalRebounds", 0)),
                "assists": float(stats_dict.get("assists", 0)),
                "minutes": float(stats_dict.get("minutes", 0))
            })

        except Exception:
            continue

    return games
