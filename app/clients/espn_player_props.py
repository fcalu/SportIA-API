import httpx
from app.clients.espn_athletes import get_athlete_info


def extract_athlete_id(ref: str) -> str:
    """
    Convierte:
    .../athletes/12483?lang=en&region=us
    en:
    12483
    """
    if not ref:
        return ""
    return ref.split("/athletes/")[-1].split("?")[0]


async def get_player_props(sport: str, league: str, event_id: str):
    """
    Obtiene player props reales desde ESPN
    (NFL / NBA)
    """

    url = (
        f"https://sports.core.api.espn.com/v2/"
        f"sports/{sport}/leagues/{league}/"
        f"events/{event_id}/competitions/{event_id}/odds/100/propBets"
    )

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)

        if resp.status_code != 200:
            return []

        data = resp.json()

    items = data.get("items", [])
    props = []
    seen = set()

    for item in items:
        athlete_ref = item.get("athlete", {}).get("$ref", "")
        athlete_id = extract_athlete_id(athlete_ref)

        if not athlete_id:
            continue

        prop_type = item.get("type", {}).get("name")
        line = item.get("current", {}).get("target", {}).get("value")

        if not prop_type or line is None:
            continue

        # DEDUPLICACIÓN
        key = f"{athlete_id}-{prop_type}"
        if key in seen:
            continue
        seen.add(key)

        athlete = await get_athlete_info(
            sport=sport,
            league=league,
            athlete_id=athlete_id
        )

        if not athlete:
            continue

        props.append({
            "name": athlete["name"],
            "team": athlete["team"],
            "role": athlete["position"],
            "type": prop_type,
            "line": float(line)
        })

    return props
