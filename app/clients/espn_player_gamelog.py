import aiohttp


BASE_URL = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


async def get_player_game_log(player_id, last_n=10):

    url = f"{BASE_URL}/{player_id}/gamelog"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()

    events = data.get("events", [])

    games = []

    for event in events[:last_n]:

        stats = event.get("statistics", {})

        games.append({
            "points": stats.get("points"),
            "rebounds": stats.get("rebounds"),
            "assists": stats.get("assists"),
            "minutes": stats.get("minutes")
        })

    return games
