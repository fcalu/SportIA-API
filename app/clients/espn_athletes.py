import httpx

_cache = {}

async def get_athlete_info(sport: str, league: str, athlete_id: str):
    cache_key = f"{sport}-{league}-{athlete_id}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = (
        f"https://sports.core.api.espn.com/v2/"
        f"sports/{sport}/leagues/{league}/athletes/{athlete_id}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return None

        data = r.json()

    info = {
        "name": data.get("displayName"),
        "position": data.get("position", {}).get("abbreviation"),
        "team": data.get("team", {}).get("displayName")
    }

    _cache[cache_key] = info
    return info
