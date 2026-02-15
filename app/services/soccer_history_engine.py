import httpx

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


async def calculate_team_history(league, team_id, line=2.5, last_n=20):

    url = f"{BASE}/{league}/teams/{team_id}/schedule?limit=50"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    events = data.get("events", [])

    games = 0
    over_line = 0
    btts = 0
    wins = 0
    draws = 0
    losses = 0

    last5 = []
    last10 = []

    for event in events:

        competitions = event.get("competitions", [])
        if not competitions:
            continue

        comp = competitions[0]
        status = comp.get("status", {}).get("type", {}).get("completed", False)

        if not status:
            continue

        competitors = comp.get("competitors", [])
        if len(competitors) != 2:
            continue

        home = competitors[0]
        away = competitors[1]

        # 🔥 FIX SCORE STRUCTURE
        def extract_score(team):
            score_obj = team.get("score")
            if isinstance(score_obj, dict):
                return int(score_obj.get("value", 0))
            try:
                return int(score_obj)
            except:
                return 0

        home_score = extract_score(home)
        away_score = extract_score(away)

        total_goals = home_score + away_score

        # 🧮 OVER LINE DINÁMICO
        if total_goals > line:
            over_line += 1

        # 🧮 BTTS
        if home_score > 0 and away_score > 0:
            btts += 1

        # 🧮 RESULTADOS
        if str(home["team"]["id"]) == str(team_id):

            if home_score > away_score:
                wins += 1
                result_letter = "W"
            elif home_score == away_score:
                draws += 1
                result_letter = "D"
            else:
                losses += 1
                result_letter = "L"

        else:

            if away_score > home_score:
                wins += 1
                result_letter = "W"
            elif away_score == home_score:
                draws += 1
                result_letter = "D"
            else:
                losses += 1
                result_letter = "L"

        last10.append(result_letter)
        last5 = last10[-5:]

        games += 1

        if games >= last_n:
            break

    if games == 0:
        return {
            "sample_size": 0,
            "over_rate_line": 0.5,
            "btts_rate": 0.5,
            "win_rate": 0.33,
            "draw_rate": 0.33,
            "loss_rate": 0.33,
            "last5": [],
            "last10": []
        }

    return {
        "sample_size": games,
        "line_used": line,
        "over_rate_line": round(over_line / games, 4),
        "btts_rate": round(btts / games, 4),
        "win_rate": round(wins / games, 4),
        "draw_rate": round(draws / games, 4),
        "loss_rate": round(losses / games, 4),
        "last5": last5,
        "last10": last10
    }
