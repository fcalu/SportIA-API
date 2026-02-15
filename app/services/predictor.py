import traceback
import json

from app.clients.espn_odds import get_event_odds
from app.clients.espn_sportsbook_props import get_sportsbook_player_props
from app.clients.espn_event import get_event_teams, get_event_player_status
from app.clients.espn_soccer_team_stats import get_team_stats

from app.services.llm import run_llm
from app.services.nba_prop_builder import build_nba_props_from_roster
from app.services.ai_prop_generator import generate_ai_props
from app.services.wspm_engine import (
    wspm_nba_projection,
    wspm_nfl_projection
)

from app.services.poisson_soccer import (
    build_score_matrix,
    derive_markets
)

from app.services.soccer_xg_model import expected_goals_match

from app.services.trading_engine import (
    validate_model_projection,
    calculate_betting_edge,
    apply_validated_edge,
    classify_bet
)

from app.services.confidence_engine import (
    infer_game_script,
    player_prop_confidence
)

from app.services.decision_policy_engine import tipster_decision_policy

from app.prompts.wspm_nfl import build_prompt as nfl_prompt
from app.prompts.wspm_nba import build_prompt as nba_prompt
from app.prompts.wspm_soccer import build_prompt as soccer_prompt
from app.services.soccer_history_engine import calculate_team_history
from app.services.db_saver import save_prediction


# ==========================================================
# HELPERS
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
# 🧠 QUANT SUMMARY BUILDER (SOCCER)
# ==========================================================

def build_quant_summary(props):
    
    summary = {}

    for p in props:

        # =========================
        # TOTALS
        # =========================
        if p.get("type") == "total_goals":

            projection = p.get("projection_model", {})

            summary["totals"] = {
                "line": p.get("line"),
                "model_over": p.get("model_prob_over"),
                "model_under": p.get("model_prob_under"),
                "market_under": p.get("market_prob_under"),
                "edge_under": p.get("edge_under")
            }

            summary["xg"] = {
                "home_xg": projection.get("home_xg"),
                "away_xg": projection.get("away_xg"),
                "total_xg": projection.get("total_xg")
            }

        # =========================
        # MONEYLINE
        # =========================
        if p.get("type") == "moneyline":
            summary["moneyline"] = {
                "model_home": p.get("model_prob_home"),
                "model_draw": p.get("model_prob_draw"),
                "model_away": p.get("model_prob_away")
            }

        # =========================
        # BTTS
        # =========================
        if p.get("type") == "btts":
            summary["btts"] = {
                "model_yes": p.get("model_prob_yes"),
                "model_no": p.get("model_prob_no")
            }

    return summary

# ==========================================================
# MAIN ENGINE
# ==========================================================

async def ai_predict(req):

    try:

        sport = req.sport
        league = req.league.split("/")[-1]
        event_id = req.event_id
        match = f"{req.home_team} vs {req.away_team}"

        odds = await get_event_odds(
            sport=sport,
            league=league,
            event_id=event_id
        )

        script = infer_game_script(sport, odds)

        debug("ODDS", odds)

        player_props = []

        # ======================================================
        # ⚽ SOCCER
        # ======================================================
        # ======================================================
# ⚽ SOCCER
# ======================================================
        if sport == "soccer":

            from app.services.soccer_support_engine import calculate_over_support

            home_id, away_id = await get_event_teams(
                sport, league, event_id
            )

            home_stats = await get_team_stats(league, home_id)
            away_stats = await get_team_stats(league, away_id)

            debug("HOME_STATS", home_stats)
            debug("AWAY_STATS", away_stats)

            # 🔹 1️⃣ DEFINIR TOTAL LINE PRIMERO
            total_line = safe_float(
                odds.get("over_under"), 2.5
            )

            # 🔹 2️⃣ HISTORIAL (usa total_line)
            home_history = await calculate_team_history(
                league, home_id, total_line
            )

            away_history = await calculate_team_history(
                league, away_id, total_line
            )

            debug("HOME_HISTORY", home_history)
            debug("AWAY_HISTORY", away_history)

            historical_support = (
                home_history["over_rate_line"] +
                away_history["over_rate_line"]
            ) / 2

            # 🔹 3️⃣ MODELO xG
            xg = expected_goals_match(
                home_stats, away_stats, league
            )

            matrix = build_score_matrix(
                xg["home_xg"],
                xg["away_xg"]
            )

            markets = derive_markets(
                matrix, total_line
            )

            # 🔹 4️⃣ SOPORTE COMBINADO (modelo + historia)
            over_support = calculate_over_support(
                markets["over"],
                home_history,
                away_history
            )

            player_props = [

                {
                    "name": "Match Total Goals",
                    "role": "team",
                    "type": "total_goals",
                    "line": total_line,
                    "projection_model": xg,
                    "model_prob_over": markets["over"],
                    "model_prob_under": markets["under"],
                    "historical_support": round(historical_support, 4),
                    "hybrid_support": round(over_support, 4),
                    "home_history": home_history,
                    "away_history": away_history,
                    "over_odds": odds.get("over_odds"),
                    "under_odds": odds.get("under_odds"),
                    "is_active": True
                },

                {
                    "name": "Match Result",
                    "role": "team",
                    "type": "moneyline",
                    "projection_model": xg,
                    "model_prob_home": markets["home_win"],
                    "model_prob_draw": markets["draw"],
                    "model_prob_away": markets["away_win"],
                    "home_odds": odds.get("home_moneyline"),
                    "draw_odds": odds.get("draw_odds"),
                    "away_odds": odds.get("away_moneyline"),
                    "is_active": True
                },

                {
                    "name": "Both Teams To Score",
                    "role": "team",
                    "type": "btts",
                    "projection_model": xg,
                    "model_prob_yes": markets["btts_yes"],
                    "model_prob_no": markets["btts_no"],
                    "yes_odds": odds.get("btts_yes_odds"),
                    "no_odds": odds.get("btts_no_odds"),
                    "is_active": True
                }
            ]


        # ======================================================
        # 💰 TRADING ENGINE
        # ======================================================

        enriched_props = []

        for prop in player_props:

            prop = normalize_prop(prop)

            prop.update(
                player_prop_confidence(prop, script, sport)
            )

            prop = validate_model_projection(prop)
            prop = calculate_betting_edge(prop)
            prop = apply_validated_edge(prop)
            prop = classify_bet(prop)

            enriched_props.append(prop)

        # ======================================================
        # 🎯 DECISION POLICY
        # ======================================================

        tipster_decisions = tipster_decision_policy(enriched_props, odds)

        # ======================================================
        # 🧠 LLM
        # ======================================================

        quant_summary = build_quant_summary(enriched_props)

        final_prompt = soccer_prompt(
            match,
            odds,
            tipster_decisions,
            quant_summary
        )

        analysis = run_llm(final_prompt)

        response = {
            "match": match,
            "league": f"{sport}/{league}",
            "odds": odds,
            "game_script": script,
            "player_props": enriched_props,
            "tipster_decisions": tipster_decisions,
            "analysis": analysis
        }

        save_prediction(req.dict(), response)

        return response

    except Exception as e:
        print("\n💥 FULL TRACEBACK 💥")
        traceback.print_exc()
        return {"ERROR": str(e)}
