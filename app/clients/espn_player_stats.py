import httpx

BASE = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


def blend_stats(current, previous, current_games=50):

    if not previous:
        return current

    # ajuste early season
    if current_games < 20:
        w_current = 0.5
        w_prev = 0.5
    else:
        w_current = 0.7
        w_prev = 0.3

    return {
        "minutes": current["minutes"] * w_current + previous["minutes"] * w_prev,
        "points": current["points"] * w_current + previous["points"] * w_prev,
        "rebounds": current["rebounds"] * w_current + previous["rebounds"] * w_prev,
        "assists": current["assists"] * w_current + previous["assists"] * w_prev
    }


async def get_player_stats(player_id: str):

    url = f"{BASE}/{player_id}/stats"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)

        if r.status_code != 200:
            return None

        data = r.json()

    try:
        categories = data.get("categories", [])

        averages = next(
            c for c in categories if c.get("name") == "averages"
        )

        stats_list = averages.get("statistics", [])

        if not stats_list:
            return None

        # ordenar temporadas
        seasons_sorted = sorted(
            stats_list,
            key=lambda x: x["season"]["year"],
            reverse=True
        )

        def extract(stat_row):
            s = stat_row["stats"]
            return {
                "games": float(s[0]),
                "minutes": float(s[2]),
                "points": float(s[17]),
                "rebounds": float(s[11]),
                "assists": float(s[12])
            }

        current = extract(seasons_sorted[0])
        previous = extract(seasons_sorted[1]) if len(seasons_sorted) > 1 else None

        blended = blend_stats(
            current,
            previous,
            current_games=current["games"]
        )

        print("🧪 BLENDED STATS:", blended)

        return blended

    except Exception as e:
        print("❌ BLEND PARSE ERROR:", e)
        return None
