import traceback
import json

from app.clients.espn_odds import get_event_odds
from app.clients.espn_sportsbook_props import get_sportsbook_player_props
from app.clients.espn_event import get_event_teams, get_event_player_status

from app.services.llm import run_llm
from app.services.bet_governor import get_official_picks
from app.services.nba_prop_builder import build_nba_props_from_roster
from app.services.ai_prop_generator import generate_ai_props

from app.services.wspm_engine import wspm_nba_projection, wspm_nfl_projection
from app.services.trading_engine import (
    validate_model_projection,
    calculate_betting_edge,
    apply_validated_edge,
    classify_bet
)

from app.services.confidence_engine import (
    infer_game_script,
    team_pick_confidence,
    player_prop_confidence
)

from app.services.recommendation_engine import generate_ai_recommendations
from app.services.decision_policy_engine import tipster_decision_policy

from app.prompts.wspm_nfl import build_prompt as nfl_prompt
from app.prompts.wspm_nba import build_prompt as nba_prompt
from app.prompts.wspm_soccer import build_prompt as soccer_prompt

from app.services.soccer_xg_model import expected_goals_match
from app.clients.espn_soccer_team_stats import get_team_stats


# ==========================================================
# DEBUG LOGGER
# ==========================================================
def debug(label, data):
    print(f"\n🧪 DEBUG → {label}")
    print(json.dumps(data, indent=2, default=str))


def safe_float(v, default=None):
    try:
        return float(v)
    except:
        return default


def normalize_prop(prop):
    prop["name"] = (
        prop.get("name")
        or prop.get("title")
        or prop.get("player_name")
        or prop.get("player")
        or prop.get("description")
        or "Market"
    )
    return prop


# ==========================================================
# MAIN
# ==========================================================
async def ai_predict(req):
    try:
        sport = req.sport
        league = req.league.split("/")[-1]
        event_id = req.event_id
        match = f"{req.home_team} vs {req.away_team}"

        odds = await get_event_odds(sport=sport, league=league, event_id=event_id)
        script = infer_game_script(sport, odds)

        debug("ODDS", odds)

        player_props = []

        # 🏈 NFL
        if sport == "football":
            player_props = generate_ai_props(match, sport, league, odds, script)
            debug("RAW AI PROPS NFL", player_props)

            sportsbook_props = await get_sportsbook_player_props(sport=sport, league=league, event_id=event_id)

            for p in player_props:
                p = normalize_prop(p)
                p_name_lower = p["name"].lower()

                # Búsqueda flexible para NFL (evita el error de las 6.5 yardas)
                for book in sportsbook_props:
                    book_name_lower = book.get("name","").lower()
                    if p_name_lower in book_name_lower:
                        p["line"] = safe_float(book.get("line"))
                        p["over_odds"] = book.get("over_odds", -110)
                        p["under_odds"] = book.get("under_odds", -110)
                        break

                p["projection_model"] = wspm_nfl_projection(p, odds, script)

        # 🏀 NBA
        # 🏀 NBA
        elif sport == "basketball":

            home_id, away_id = await get_event_teams(sport, league, event_id)

            from app.clients.espn_nba_roster import get_team_roster

            # 🔹 1. Traemos roster completo por equipo (temporada)
            roster_home = await get_team_roster(home_id)
            roster_away = await get_team_roster(away_id)

            players = roster_home + roster_away

            # 🔹 2. Traemos status REAL del evento
            statuses = await get_event_player_status(sport, league, event_id)

            # 🔒 3. FILTRO DEFINITIVO → SOLO JUGADORES QUE REALMENTE ESTÁN EN EL PARTIDO
            filtered_players = []

            for p in players:
                pid = str(p.get("id"))

                # Si el jugador no aparece en el evento → NO juega
                if pid not in statuses:
                    continue

                status = statuses.get(pid)

                # Solo jugadores activos / disponibles
                if status not in ["ACTIVE", "PROBABLE", "STARTER"]:
                    continue

                filtered_players.append(p)

            debug("FILTERED NBA PLAYERS", [p["name"] for p in filtered_players])

            # 🔹 4. Construimos props SOLO con jugadores válidos
            player_props = build_nba_props_from_roster(
                filtered_players,
                statuses,
                odds
            )

            debug("RAW NBA PROPS", player_props)

            # 🔹 5. Proyección WSPM + línea artificial (como ya lo tienes)
            for prop in player_props:
                prop = normalize_prop(prop)

                projection = wspm_nba_projection(prop, odds, script)

                if isinstance(projection, dict):
                    prop["projection_model"] = projection
                    prop["line"] = round(projection.get("mean", 0) * 0.97, 1)
                else:
                    prop["projection_model"] = {
                        "mean": projection,
                        "std_dev": max(projection * 0.2, 1)
                    }
                    prop["line"] = round(projection * 0.97, 1)

                prop["over_odds"] = -110
                prop["under_odds"] = -110


        # ⚽ Soccer
        elif sport == "soccer":
            home_id, away_id = await get_event_teams(sport, league, event_id)
            home_stats = await get_team_stats(league, home_id)
            away_stats = await get_team_stats(league, away_id)

            xg = expected_goals_match(home_stats, away_stats)
            total_line = safe_float(odds.get("over_under"), 2.5)

            player_props = [{
                "name": "Match Total Goals",
                "role": "team",
                "type": "total_goals",
                "line": total_line,
                "projection_model": {
                    "mean": xg["total_xg"],
                    "std_dev": xg["total_xg"] ** 0.5
                },
                "over_odds": odds.get("over_odds", -110),
                "under_odds": odds.get("under_odds", -110),
                "confidence": 60,
                "is_active": True
            }]

        debug("PROPS BEFORE TRADING ENGINE", player_props)

        # 💰 TRADING ENGINE
        enriched_props = []
        for prop in player_props:
            prop = normalize_prop(prop)
            prop.update(player_prop_confidence(prop, script, sport))
            prop = validate_model_projection(prop)
            prop = calculate_betting_edge(prop)
            prop = apply_validated_edge(prop)
            prop = classify_bet(prop)
            enriched_props.append(prop)

        # DECISION POLICY
        tipster_decisions = []
        for p in enriched_props:
            decisions = tipster_decision_policy(p, odds)
            tipster_decisions.extend(decisions)

        # LLM - Selección dinámica de Prompt por deporte
        if sport == "football":
            final_prompt = nfl_prompt(match, odds, tipster_decisions)
        elif sport == "basketball":
            final_prompt = nba_prompt(match, odds, tipster_decisions)
        else:
            final_prompt = soccer_prompt(match, odds, tipster_decisions)

        analysis = run_llm(final_prompt)

        return {
            "match": match,
            "league": f"{sport}/{league}",
            "odds": odds,
            "game_script": script,
            "player_props": enriched_props,
            "tipster_decisions": tipster_decisions,
            "analysis": analysis
        }

    except Exception as e:
        print("\n💥 FULL TRACEBACK 💥")
        traceback.print_exc()
        return {"ERROR": str(e)}