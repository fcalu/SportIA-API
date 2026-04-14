import traceback
import json

from app.clients.espn_odds import get_event_odds
from app.clients.espn_sportsbook_props import get_sportsbook_player_props
from app.clients.espn_event import get_event_teams, get_event_player_status
from app.clients.espn_soccer_team_stats import get_team_stats
from app.clients.espn_nba_roster import get_team_roster
from app.clients.espn_player_gamelog import get_player_game_log
from app.services.player_form_engine import analyze_player_form
from app.services.wspm_engine import implied_probability
from app.services.soccer_market_enhancer import enhance_soccer_markets
from datetime import datetime, timezone
from app.services.model_tracking import (
    save_prediction,
    calculate_performance_metrics
)

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
        home_id = None
        away_id = None

        # ======================================================
        # 🏈 NFL
        # ======================================================
        if sport == "football":

            home_id, away_id = await get_event_teams(
                sport, league, event_id
            )

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

                if prop.get("player_id"):
                    prop["player_image"] = (
                        f"https://a.espncdn.com/i/headshots/nfl/players/full/{prop['player_id']}.png"
                    )

                name_lower = prop["name"].lower()

                for book in sportsbook_props:
                    # Limpiamos nombres (quitamos puntos y espacios extra)
                    book_clean = book.get("name", "").lower().replace(".", "").strip()
                    model_clean = name_lower.replace(".", "").strip()

                    # 🛡️ VALIDACIÓN DOBLE: Nombre Y Tipo de Mercado
                    name_match = (model_clean in book_clean or book_clean in model_clean)
                    market_match = (prop["type"] == book.get("type"))

                    if name_match and market_match:
                        prop["line"] = safe_float(book.get("line"))
                        prop["over_odds"] = book.get("over_odds", -110)
                        prop["under_odds"] = book.get("under_odds", -110)
                        # Log para que veas en consola que está funcionando
                        print(f"🎯 MATCH: {prop['name']} | {prop['type']} | Line: {prop['line']}")
                        break

                # Esto sigue igual para NFL
                prop["projection_model"] = wspm_nfl_projection(prop, odds, script)

       # ======================================================
        # 🏀 NBA (CONECTADO AL NUEVO BUILDER Y CUOTAS REALES)
        # ======================================================
        elif sport == "basketball":

            home_id, away_id = await get_event_teams(sport, league, event_id)

            players = (
                await get_team_roster(home_id)
                + await get_team_roster(away_id)
            )

            statuses = await get_event_player_status(sport, league, event_id)

            # --- NUEVO: TRAEMOS LAS CUOTAS REALES DE DRAFTKINGS ---
            sportsbook_props = await get_sportsbook_player_props(
                sport=sport,
                league=league,
                event_id=event_id
            )

            # El builder genera la base: Points, Rebounds, Assists y 3PT
            raw_props = build_nba_props_from_roster(players, statuses, odds)
            filtered_props = []

            for prop in raw_props:
                normalize_prop(prop)

                if prop.get("player_id"):
                    prop["player_image"] = f"https://a.espncdn.com/i/headshots/nba/players/full/{prop['player_id']}.png"

                status = statuses.get(prop.get("player_id"), {}).get("status", "active")
                prop["injury_status"] = status

                if status in ["out", "doubtful"]:
                    continue

                prop["reliability_factor"] = 0.4 if status == "questionable" else 0.7

                projection = wspm_nba_projection(prop, odds, script)
                minutes_proj = projection.get("projected_minutes", 0)

                if minutes_proj < 12:
                    continue

                prop["projection_model"] = projection
                prop["projected_minutes"] = minutes_proj

                mean = projection.get("mean", 0)
                if mean <= 0:
                    continue

                # 1. VALORES POR DEFECTO (Si no hay match con la casa)
                prop["line"] = round(mean, 1)
                prop["over_odds"] = -110
                prop["under_odds"] = -110

                # 2. --- LOGICA DE MATCH CON DRAFTKINGS ---
                # Esto es lo que activa el "Edge" real
                name_model = prop["name"].lower().replace(".", "").strip()
                
                for book in sportsbook_props:
                    name_book = book.get("name", "").lower().replace(".", "").strip()
                    
                    # Comparamos nombre (difuso) Y tipo de mercado
                    if (name_model in name_book or name_book in name_model) and prop["type"] == book["type"]:
                        prop["line"] = book["line"]
                        prop["over_odds"] = book["over_odds"]
                        prop["under_odds"] = book["under_odds"]
                        # Debug opcional para ver matches en consola
                        print(f"🎯 NBA MATCH: {prop['name']} | {prop['type']} | Line: {prop['line']}")
                        break

                filtered_props.append(prop)

            player_props = filtered_props

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
            # 🔥 ENHANCE MARKETS (NUEVA CAPA)
            markets = enhance_soccer_markets(
                markets=markets,
                odds=odds,
                home_stats=home_stats,
                away_stats=away_stats
            )
            player_props = []

            # ======================================================
            # 🎯 TOTAL GOALS
            # ======================================================

            player_props.append({
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
            })

          # ======================================================
            # 🎯 BOTH TEAMS TO SCORE
            # ======================================================

            # 🔧 proxy BTTS usando OU (temporal)
            over_odds = odds.get("over_odds")
            under_odds = odds.get("under_odds")

            btts_yes_odds = over_odds if over_odds else -110
            btts_no_odds = under_odds if under_odds else -110

            player_props.append({
                "name": "Both Teams To Score",
                "role": "team",
                "type": "btts",
                "line": 0.5,  # dummy para engine
                "model_prob_over": markets["btts_yes"],
                "model_prob_under": markets["btts_no"],
                "over_odds": btts_yes_odds,
                "under_odds": btts_no_odds,
                "is_active": True
            })
            # ======================================================
            # 🎯 1X2 CON HOLD NORMALIZADO
            # ======================================================

            home_ml = odds.get("home_moneyline")
            away_ml = odds.get("away_moneyline")
            draw_ml = odds.get("draw_moneyline")  # si no existe será None

            home_raw = implied_probability(home_ml)
            away_raw = implied_probability(away_ml)
            draw_raw = implied_probability(draw_ml) if draw_ml else None

            home_fair = None
            away_fair = None
            draw_fair = None

            if home_raw and away_raw and draw_raw:
                hold = home_raw + away_raw + draw_raw - 1
                if hold > -1:
                    home_fair = home_raw / (1 + hold)
                    away_fair = away_raw / (1 + hold)
                    draw_fair = draw_raw / (1 + hold)

            player_props.append({
                "name": "Full Time Result - Home",
                "role": "team",
                "type": "moneyline_home",
                "model_prob": markets["home_win"],
                "market_implied_prob": home_fair,
                "is_active": True
            })

            player_props.append({
                "name": "Full Time Result - Draw",
                "role": "team",
                "type": "moneyline_draw",
                "model_prob": markets["draw"],
                "market_implied_prob": draw_fair,
                "is_active": True
            })

            player_props.append({
                "name": "Full Time Result - Away",
                "role": "team",
                "type": "moneyline_away",
                "model_prob": markets["away_win"],
                "market_implied_prob": away_fair,
                "is_active": True
            })

            # ======================================================
            # 🎯 DOUBLE CHANCE DERIVADO CORRECTAMENTE
            # ======================================================

            if home_fair and draw_fair and away_fair:

                dc_home_market = home_fair + draw_fair
                dc_away_market = away_fair + draw_fair

                player_props.append({
                    "name": "Double Chance - Home or Draw",
                    "role": "team",
                    "type": "double_chance_home",
                    "model_prob": markets["home_win"] + markets["draw"],
                    "market_implied_prob": dc_home_market,
                    "is_active": True
                })

                player_props.append({
                    "name": "Double Chance - Away or Draw",
                    "role": "team",
                    "type": "double_chance_away",
                    "model_prob": markets["away_win"] + markets["draw"],
                    "market_implied_prob": dc_away_market,
                    "is_active": True
                })

        else:
            return {"ERROR": "Unsupported sport"}

        if not player_props:
            print("⚠️ NO PLAYER PROPS GENERATED")

        # ======================================================
        # 💰 TRADING ENGINE
        # ======================================================
        enriched_props = []

        for prop in player_props:

            normalize_prop(prop)

            prop.update(player_prop_confidence(prop, script, sport))

            prop = validate_model_projection(prop)
            prop = calculate_betting_edge(prop)
            prop = apply_validated_edge(prop)
            prop = classify_bet(prop)

            # 🔥 SAVE VALUE BETS
            if prop.get("bet_tier") in [
                "VALUE_BET",
                "STRONG_VALUE",
                "ELITE_VALUE"
            ]:
                save_prediction(
                    event_id=event_id,
                    market_type=prop.get("type"),
                    bet_tier=prop.get("bet_tier"),
                    odds=prop.get("over_odds") or -110
                )

            enriched_props.append(prop)

        # ======================================================
        # 🎯 DECISION POLICY
        # ======================================================
        tipster_decisions = tipster_decision_policy(
            enriched_props, odds
        )

        top_decisions_for_ai = tipster_decisions[:3]
        # ======================================================
        # 🧠 LLM
        # ======================================================
        try:
            if sport == "football":
                final_prompt = nfl_prompt(match, odds, top_decisions_for_ai)
            elif sport == "basketball":
                final_prompt = nba_prompt(match, odds, top_decisions_for_ai)
            else:
                final_prompt = soccer_prompt(
                    match, 
                    odds, 
                    top_decisions_for_ai, 
                    {"xg": xg, "markets": enriched_props}
                )

            analysis = run_llm(final_prompt)
        except Exception as e:
            print(f"⚠️ Error OpenAI (Saldo/Cuota): {e}")
            # Esto evita que el bot se detenga si falla el saldo
            analysis = "Análisis no disponible por límite de cuota. Revisa los datos de ventaja arriba."

        # ======================================================
        # 📊 PERFORMANCE REAL
        # ======================================================
        performance_metrics = calculate_performance_metrics()

        # ======================================================
        # 🏟 TEAM LOGOS
        # ======================================================
        home_logo = None
        away_logo = None

        if sport == "basketball":
            home_logo = f"https://a.espncdn.com/i/teamlogos/nba/500/{home_id}.png"
            away_logo = f"https://a.espncdn.com/i/teamlogos/nba/500/{away_id}.png"

        elif sport == "football":
            home_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{home_id}.png"
            away_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{away_id}.png"

        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "match": match,
            "league": raw_league,
            "odds": odds,
            "game_script": script,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "player_props": enriched_props,
            "tipster_decisions": tipster_decisions,
            "analysis": analysis,
            "meta": {
                "schema_version": "2.0",
                "model_engine": "WSPM",
                "generated_from_event_id": event_id,
            },
            "event": {
                "event_id": event_id,
                "sport": sport,
                "league_code": league,
                "raw_league": raw_league
            },
            "teams": {
                "home": {
                    "id": home_id,
                    "name": req.home_team,
                    "logo": home_logo
                },
                "away": {
                    "id": away_id,
                    "name": req.away_team,
                    "logo": away_logo
                }
            },
            "performance_metrics": performance_metrics,
            "timestamp": timestamp
        }

    except Exception as e:
        print("\n💥 FULL TRACEBACK 💥")
        traceback.print_exc()
        return {"ERROR": str(e)}

