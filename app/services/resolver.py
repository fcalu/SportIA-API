from app.clients.espn import get_scoreboard

async def resolve_event(sport, home, away):
    data = await get_scoreboard(sport)
    for e in data["events"]:
        c = e["competitions"][0]["competitors"]
        h = next(x for x in c if x["homeAway"]=="home")
        a = next(x for x in c if x["homeAway"]=="away")
        if home.lower() in h["team"]["displayName"].lower() and away.lower() in a["team"]["displayName"].lower():
            return e
    raise ValueError("Event not found")
