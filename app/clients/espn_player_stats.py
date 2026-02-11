import httpx
import statistics

BASE_STATS = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"
BASE_GAMELOG = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


def blend_stats(current, previous, current_games=50):

    if not previous:
        return current

    if current_games < 20:
        w_current = 0.5
        w_prev = 0.5
    else:
        w_current = 0.7
        w_prev = 0.3

    return {
        "games": current["games"],
        "minutes": current["minutes"] * w_current + previous["minutes"] * w_prev,
        "points": current["points"] * w_current + previous["points"] * w_prev,
        "rebounds": current["rebounds"] * w_current + previous["rebounds"] * w_prev,
        "assists": current["assists"] * w_current + previous["assists"] * w_prev
    }


async def get_player_stats(player_id: str):

    async with httpx.AsyncClient(timeout=15) as client:

        stats_url = f"{BASE_STATS}/{player_id}/stats"
        stats_res = await client.get(stats_url)

        if stats_res.status_code != 200:
            return None

        stats_data = stats_res.json()

        categories = stats_data.get("categories", [])
        averages = next(
            (c for c in categories if c.get("name") == "averages"),
            None
        )

        if not averages:
            return None

        stats_list = averages.get("statistics", [])
        if not stats_list:
            return None

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

        # ===============================
        # GAME LOG (para varianza real)
        # ===============================
        gamelog_url = f"{BASE_GAMELOG}/{player_id}/gamelog"
        gl_res = await client.get(gamelog_url)

        recent_points = []

        if gl_res.status_code == 200:
            gl_data = gl_res.json()
            events = gl_data.get("events")

            games = []

            if isinstance(events, list):
                games = events[:10]
            elif isinstance(events, dict) and "$ref" in events:
                ref_res = await client.get(events["$ref"])
                if ref_res.status_code == 200:
                    ref_data = ref_res.json()
                    games = ref_data.get("items", [])[:10]

            for game in games:
                stats = game.get("statistics", {})
                pts = float(stats.get("points", 0))
                mins = float(stats.get("minutes", 0))
                if mins > 0:
                    recent_points.append(pts)

        # ===============================
        # VARIANZA MULTI-STAT
        # ===============================
        if len(recent_points) >= 5:
            try:
                std_points = statistics.stdev(recent_points)
                if std_points < 1:
                    std_points = blended["points"] * 0.22
            except:
                std_points = blended["points"] * 0.22

            avg_last5 = sum(recent_points[:5]) / min(5, len(recent_points))
        else:
            std_points = blended["points"] * 0.22
            avg_last5 = blended["points"]

        std_reb = max(0.8, blended["rebounds"] * 0.25)
        std_ast = max(0.8, blended["assists"] * 0.30)

        season_avg = blended["points"]
        form_factor = (avg_last5 / season_avg) if season_avg > 0 else 1

        return {
            "minutes": blended["minutes"],
            "points": blended["points"],
            "rebounds": blended["rebounds"],
            "assists": blended["assists"],
            "points_std_dev": round(std_points, 2),
            "reb_std_dev": round(std_reb, 2),
            "ast_std_dev": round(std_ast, 2),
            "form_factor": round(form_factor, 3)
        }
