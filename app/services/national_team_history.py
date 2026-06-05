import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

NATIONAL_COMPETITIONS = [
    "fifa.friendly",
    "fifa.wcq.uefa",
    "fifa.wcq.conmebol",
    "fifa.wcq.concacaf",
    "uefa.nations",
    "uefa.euro"
]


async def get_national_team_events(team_id):

    all_events = []

    async with httpx.AsyncClient(timeout=10) as client:

        for league in NATIONAL_COMPETITIONS:

            try:

                url = (
                    f"{BASE}/{league}"
                    f"/teams/{team_id}"
                    f"/schedule?limit=50"
                )

                r = await client.get(url)

                data = r.json()

                events = data.get("events", [])

                print(
                    f"🌎 {league} -> {len(events)} events",
                    flush=True
                )

                if events:

                    try:

                        first = events[0]

                        print(
                            f"📋 {league}: "
                            f"{first.get('name','NO_NAME')}",
                            flush=True
                        )

                    except:
                        pass

                all_events.extend(events)

            except Exception as e:

                print(
                    f"❌ {league}: {e}",
                    flush=True
                )

    return all_events