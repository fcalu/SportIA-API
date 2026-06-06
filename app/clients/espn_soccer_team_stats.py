import httpx
from app.services.national_team_history import (
    get_national_team_events
)
BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


async def get_team_stats(league, team_id, last_n=25):

    url = f"{BASE}/{league}/teams/{team_id}/schedule?limit=50"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        data = r.json()

    events = data.get("events", [])

    print(
        f"🏆 LEAGUE RECEIVED: {league}",
        flush=True
    )

    NATIONAL_LEAGUES = {
        "FIFA.FRIENDLY",
        "FIFA.WORLD"
    }

    if league.upper() in NATIONAL_LEAGUES:

        national_events = await get_national_team_events(
            team_id
        )

        print(
            f"🌎 TOTAL NATIONAL EVENTS: {len(national_events)}",
            flush=True
        )

        if len(national_events) > len(events):

            print(
                f"✅ USING NATIONAL EVENTS: {len(national_events)}",
                flush=True
            )

            events = national_events

    print(
        f"⚽ TEAM {team_id} | LEAGUE {league} | EVENTS FOUND: {len(events)}",
        flush=True
    )

    print(
    f"⚽ TEAM {team_id} | LEAGUE {league} | EVENTS FOUND: {len(events)}",
    flush=True
)
    goals_for = 0
    goals_against = 0
    games_played = 0

    wins = 0
    draws = 0
    losses = 0

    last10 = []

    home_games = 0
    home_goals_for = 0
    home_goals_against = 0

    away_games = 0
    away_goals_for = 0
    away_goals_against = 0

    btts_count = 0
    over25_count = 0

    weighted_gf = 0
    weighted_ga = 0
    weight_sum = 0

    print(
    f"📊 PROCESSING EVENTS: {len(events)}",
    flush=True
)

    for event in events:

        competitions = event.get("competitions", [])

        if not competitions:
            continue

        comp = competitions[0]

        status = (
            comp.get("status", {})
            .get("type", {})
            .get("completed", False)
        )

        if not status:
            continue

        competitors = comp.get("competitors", [])

        if len(competitors) != 2:
            continue

        home = competitors[0]
        away = competitors[1]

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

        weight = max(
            1,
            last_n - games_played
        )

        total_goals = home_score + away_score

        if total_goals > 2.5:
            over25_count += 1

        if home_score > 0 and away_score > 0:
            btts_count += 1

        # =========================================
        # TEAM IS HOME
        # =========================================

        if str(home["team"]["id"]) == str(team_id):

            goals_for += home_score
            goals_against += away_score
            weighted_gf += home_score * weight
            weighted_ga += away_score * weight
            weight_sum += weight
            home_games += 1
            home_goals_for += home_score
            home_goals_against += away_score

            if home_score > away_score:
                wins += 1
                last10.append("W")

            elif home_score == away_score:
                draws += 1
                last10.append("D")

            else:
                losses += 1
                last10.append("L")

        # =========================================
        # TEAM IS AWAY
        # =========================================

        else:

            goals_for += away_score
            goals_against += home_score
            weighted_gf += away_score * weight
            weighted_ga += home_score * weight
            weight_sum += weight
            away_games += 1
            away_goals_for += away_score
            away_goals_against += home_score

            if away_score > home_score:
                wins += 1
                last10.append("W")

            elif away_score == home_score:
                draws += 1
                last10.append("D")

            else:
                losses += 1
                last10.append("L")

        games_played += 1

        if games_played >= last_n:
            break

    if games_played == 0:

        return {
            "goals_for": 13,
            "goals_against": 13,
            "games_played": 10,

            "wins": 3,
            "draws": 3,
            "losses": 4,

            "last5": [],
            "last10": [],

            "win_rate": 0.33,
            "draw_rate": 0.33,
            "loss_rate": 0.34,

            "over25_rate": 0.50,
            "btts_rate": 0.50,

            "home_games": 0,
            "home_goals_for": 0,
            "home_goals_against": 0,

            "away_games": 0,
            "away_goals_for": 0,
            "away_goals_against": 0
        }
    if games_played < 5:

        print(
            f"⚠️ LOW SAMPLE SIZE TEAM {team_id}: {games_played}",
            flush=True
        )
    return {

        "goals_for": goals_for,
        "goals_against": goals_against,
        "games_played": games_played,

        "wins": wins,
        "draws": draws,
        "losses": losses,

        "last5": last10[-5:],
        "last10": last10,

        "win_rate": round(wins / games_played, 4),
        "draw_rate": round(draws / games_played, 4),
        "loss_rate": round(losses / games_played, 4),

        "over25_rate": round(over25_count / games_played, 4),
        "btts_rate": round(btts_count / games_played, 4),
        "weighted_goals_for":
    round(
        weighted_gf / max(weight_sum, 1),
        3
    ),

"weighted_goals_against":
    round(
        weighted_ga / max(weight_sum, 1),
        3
    ),

"sample_warning":
    games_played < 5,
        "home_games": home_games,
        "home_goals_for": home_goals_for,
        "home_goals_against": home_goals_against,

        "away_games": away_games,
        "away_goals_for": away_goals_for,
        "away_goals_against": away_goals_against
    }