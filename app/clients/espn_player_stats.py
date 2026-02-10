import httpx

BASE = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


async def get_player_stats(player_id: str):

    url = f"{BASE}/{player_id}/stats"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)

        if r.status_code != 200:
            print("❌ ESPN Stats HTTP:", r.status_code)
            return None

        data = r.json()

    try:
        categories = data.get("categories", [])

        averages = next(
            c for c in categories if c.get("name") == "averages"
        )

        stats_list = averages.get("statistics", [])

        if not stats_list:
            print("⚠️ ESPN sin statistics")
            return None

        # 👇 usa temporada más reciente automática
        latest = sorted(
            stats_list,
            key=lambda x: x["season"]["year"],
            reverse=True
        )[0]

        stats = latest["stats"]

        per_game = {
            "minutes": float(stats[2]),
            "points": float(stats[17]),
            "rebounds": float(stats[11]),
            "assists": float(stats[12])
        }

        print("✅ ESPN PER GAME:", per_game)

        return per_game

    except Exception as e:
        print("❌ ESPN Parse Error:", e)
        return None
