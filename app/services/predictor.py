import traceback
import json

from app.clients.espn_odds import get_event_odds
from app.clients.espn_sportsbook_props import get_sportsbook_player_props
from app.clients.espn_event import get_event_teams, get_event_player_status
from app.clients.espn_soccer_team_stats import get_team_stats
from app.clients.espn_nba_roster import get_team_roster
from app.clients.espn_player_gamelog import get_player_game_log
from app.services.player_form_engine import analyze_player_form

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
# MAIN ENGINE
# ==========================================================

async def ai_predict(req):

    try:

        sport = req.sport
        raw_league = req.league
        league = raw_league.split("/")[-1]

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
        # 🏈 NFL
        # ======================================================
        if sport == "football":

            player_props = generate_ai_props(
                match, sport, league, odds, script
            )

            sportsbook_props = await get_sportsbook_player_props(
                sport=sport,
                league=league,
                event_id=event_id
            )

            for prop in player_props:

                normalize_prop(prop)

                name_lower = prop["name"].lower()

                for book in sportsbook_props:
                    book_name = book.get("name", "").lower()

                    if (
                        name_lower in book_name
                        or book_name in name_lower
                    ):
                        prop["line"] = safe_float(book.get("line"))
                        prop["over_odds"] = book.get("over_odds", -110)
                        prop["under_odds"] = book.get("under_odds", -110)
                        break

                prop["projection_model"] = wspm_nfl_projection(
                    prop, odds, script
                )

        # ======================================================
        # 🏀 NBA
        # ======================================================
        elif sport == "basketball":

            home_id, away_id = await get_event_teams(
                sport, league, event_id
            )

            players = (
                await get_team_roster(home_id)
                + await get_team_roster(away_id)
            )

            statuses = await get_event_player_status(
                sport, league, event_id
            )

            debug("NBA_STATUSES", statuses)

            player_props = build_nba_props_from_roster(
                players, statuses, odds
            )

            for prop in player_props:

                normalize_prop(prop)

                projection = wspm_nba_projection(
                    prop, odds, script
                )

                prop["projection_model"] = projection

                mean = projection.get("mean", 0)
                minutes_proj = projection.get("projected_minutes", 0)

                # 🎯 shading + stat key mapping
                if prop["type"] == "Points":
                    prop["line"] = round(mean * 0.98)
                    stat_key = "points"
                elif prop["type"] == "Rebounds":
                    prop["line"] = round(mean * 0.95)
                    stat_key = "rebounds"
                elif prop["type"] == "Assists":
                    prop["line"] = round(mean * 0.93)
                    stat_key = "assists"
                else:
                    prop["line"] = round(mean * 0.97)
                    stat_key = None

                prop["over_odds"] = -110
                prop["under_odds"] = -110

                # ==================================================
                # 🔥 HISTORICAL ANALYSIS (NO ROMPE NADA)
                # ==================================================
                if stat_key:

                    try:

                        game_log = await get_player_game_log(
                            prop["player_id"],
                            last_n=10
                        )

                        form_analysis = analyze_player_form(
                            game_log,
                            stat_key,
                            prop["line"],
                            minutes_proj
                        )

                        prop["recent_form"] = form_analysis

                        # 📊 Modelo vs reciente
                        if form_analysis.get("avg_last_n"):

                            delta = round(
                                form_analysis["avg_last_n"] - mean,
                                2
                            )

                            prop["model_vs_recent_delta"] = delta

                    except Exception as e:
                        print("⚠️ L10 fetch error:", e)

        # ======================================================
        # ⚽ SOCCER
        # ======================================================
        elif sport == "soccer":

            home_id, away_id = await get_event_teams(
                sport, league, event_id
            )

            home_stats = await get_team_stats(league, home_id)
            away_stats = await get_team_stats(league, away_id)

            xg = expected_goals_match(
                home_stats, away_stats, league
            )

            total_line = safe_float(
                odds.get("over_under"), 2.5
            )

            matrix = build_score_matrix(
                xg["home_xg"],
                xg["away_xg"]
            )

            markets = derive_markets(
                matrix, total_line
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
                }
            ]

        else:
            return {"ERROR": "Unsupported sport"}

        # ======================================================
        # 🛡 PROTECTION
        # ======================================================
        if not player_props:
            print("⚠️ NO PLAYER PROPS GENERATED")

        # ======================================================
        # 💰 TRADING ENGINE
        # ======================================================
        enriched_props = []

        for prop in player_props:

            normalize_prop(prop)

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
        tipster_decisions = tipster_decision_policy(
            enriched_props, odds
        )

        # ======================================================
        # 🧠 LLM
        # ======================================================
        if sport == "football":
            final_prompt = nfl_prompt(match, odds, tipster_decisions)
        elif sport == "basketball":
            final_prompt = nba_prompt(match, odds, tipster_decisions)
        else:
            final_prompt = soccer_prompt(
                match, odds, tipster_decisions, {}
            )

        analysis = run_llm(final_prompt)

        return {
            "match": match,
            "league": raw_league,
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
