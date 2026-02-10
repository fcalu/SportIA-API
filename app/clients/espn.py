import httpx
from datetime import datetime, timedelta

BASE = "https://site.api.espn.com/apis/site/v2/sports"

SPORT_PATHS = {
   "soccer": [
    "soccer/eng.1",
    "soccer/eng.2",
    "soccer/esp.1",
    "soccer/ger.1",
    "soccer/ita.1",
    "soccer/fra.1",
    "soccer/usa.1",
    "soccer/usa.nwsl",
    "soccer/uefa.champions",
    "soccer/uefa.europa",
    "soccer/fifa.world",
    "soccer/mex.1",
    "soccer/ned.1",
    "soccer/por.1",
    "soccer/sco.1",
    "soccer/bra.1",
    "soccer/conmebol.libertadores"
],

    "nba": ["basketball/nba"],
    "nfl": ["football/nfl"],
}

def _nba_date_range():
    today = datetime.utcnow().date()
    end = today + timedelta(days=7)
    return f"{today.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

async def get_scoreboard(path: str, sport: str):
    url = f"{BASE}/{path}/scoreboard"
    if sport == "nba":
        url += f"?dates={_nba_date_range()}"
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()

async def upcoming_matches(sport: str):
    events = []
    for path in SPORT_PATHS.get(sport, []):
        data = await get_scoreboard(path, sport)
        for e in data.get("events", []):
            if e.get("status", {}).get("type", {}).get("state") == "pre":
                comp = e["competitions"][0]["competitors"]
                h = next(x for x in comp if x["homeAway"]=="home")
                a = next(x for x in comp if x["homeAway"]=="away")
                events.append({
                    "sport": sport,
                    "league": path,
                    "event_id": e["id"],
                    "home": h["team"]["displayName"],
                    "away": a["team"]["displayName"],
                    "start_time": e["date"]
                })
    if not events and sport == "soccer":
        return [{
            "sport": "soccer",
            "league": "demo",
            "event_id": "demo-001",
            "home": "Internazionale",
            "away": "Pisa",
            "start_time": "2026-01-23T19:45Z"
        }]
    return events
