from app.services.probability_engine import prob_over, prob_under
from app.services.market_engine import no_vig_prob


# ==========================================================
# 🛡️ MODEL SANITY CHECK
# ==========================================================
def validate_model_projection(prop):

    position_limits = {
        "QB": {"Carries": 15, "Rushing Yards": 80, "Pass Completions": 45},
        "RB": {"Carries": 35, "Rushing Yards": 220},
        "WR": {"Rushing Yards": 40},
    }

    role = prop.get("role", "")
    market = prop.get("type", "")

    model_data = prop.get("projection_model", {})

    # 🛡️ COMPATIBILIDAD FLOAT → DISTRIBUCIÓN
    if isinstance(model_data, dict):
        projection = float(model_data.get("mean", 0))
    else:
        projection = float(model_data)
        prop["projection_model"] = {
            "mean": projection,
            "std_dev": max(projection * 0.2, 1)
        }

    season_avg = float(prop.get("season_avg", projection))
    confidence = prop.get("confidence", 50)

    exceeds_limits = False
    is_outlier = False

    if role in position_limits and market in position_limits[role]:
        if projection > position_limits[role][market]:
            exceeds_limits = True

    if season_avg > 0 and projection > season_avg * 2.2:
        is_outlier = True

    if exceeds_limits:
        reliability = 0
    elif is_outlier:
        reliability = 0.2
    elif confidence >= 70:
        reliability = 1.0
    elif confidence >= 50:
        reliability = 0.6
    else:
        reliability = 0.4

    prop["model_validation"] = {
        "is_outlier": is_outlier,
        "exceeds_physical_limits": exceeds_limits,
        "edge_validated": reliability > 0,
    }

    prop["reliability_factor"] = reliability
    return prop


# ==========================================================
# 📊 EDGE MATEMÁTICO REAL
# ==========================================================
def calculate_betting_edge(prop):
    
    market_type = prop.get("type")

    # ======================================================
    # ⚽ MONEYLINE 1X2
    # ======================================================
    if market_type in [
        "moneyline_home",
        "moneyline_draw",
        "moneyline_away",
        "double_chance_home",
        "double_chance_away"
    ]:

        model_prob = prop.get("model_prob")
        market_prob = prop.get("market_implied_prob")

        if model_prob is None or market_prob is None:
            prop["edge"] = 0
            prop["market_prob"] = market_prob
            return prop

        edge = model_prob - market_prob

        prop["market_prob"] = market_prob
        prop["edge"] = round(edge, 4)

        # Compatibilidad con sistema existente
        prop["model_prob_over"] = model_prob
        prop["model_prob_under"] = 1 - model_prob
        prop["market_prob_over"] = market_prob
        prop["market_prob_under"] = 1 - market_prob
        prop["edge_over"] = round(edge, 4)
        prop["edge_under"] = round(-edge, 4)

        return prop

    # ======================================================
    # ⚽ TOTALS & BTTS
    # ======================================================
    if market_type in ["total_goals", "btts"]:

        if market_type == "btts":
            model_over = prop.get("model_prob_yes")
            model_under = prop.get("model_prob_no")
        else:
            model_over = prop.get("model_prob_over")
            model_under = prop.get("model_prob_under")

    # ======================================================
    # 🏀🏈 NORMAL DISTRIBUTION (NBA / NFL)
    # ======================================================
    else:

        model_data = prop.get("projection_model", {})

        if isinstance(model_data, dict):
            mean = float(model_data.get("mean", 0))
            std = float(model_data.get("std_dev", 1))
        else:
            mean = float(model_data)
            std = max(mean * 0.2, 1)
            prop["projection_model"] = {
                "mean": mean,
                "std_dev": std
            }

        line = float(prop.get("line", 0))

        model_over = prob_over(line, mean, std)
        model_under = prob_under(line, mean, std)

    # ======================================================
    # 💰 MARKET PROBABILITIES (OVER/UNDER TYPE)
    # ======================================================

    over_odds = prop.get("over_odds")
    under_odds = prop.get("under_odds")

    if over_odds is None or under_odds is None:
        prop["model_prob_over"] = model_over
        prop["model_prob_under"] = model_under
        prop["market_prob_over"] = None
        prop["market_prob_under"] = None
        prop["edge_over"] = 0
        prop["edge_under"] = 0
        return prop

    market_over, market_under = no_vig_prob(over_odds, under_odds)

    prop["model_prob_over"] = model_over
    prop["model_prob_under"] = model_under
    prop["market_prob_over"] = market_over
    prop["market_prob_under"] = market_under

    prop["edge_over"] = round((model_over or 0) - market_over, 4)
    prop["edge_under"] = round((model_under or 0) - market_under, 4)

    return prop
# ==========================================================
# 🧠 EDGE AJUSTADO POR FIABILIDAD
# ==========================================================
def apply_validated_edge(prop):

    reliability = prop.get("reliability_factor", 1)

    prop["edge_over"] = round(prop.get("edge_over", 0) * reliability, 4)
    prop["edge_under"] = round(prop.get("edge_under", 0) * reliability, 4)

    return prop


# ==========================================================
# 🎯 DECISION LAYER
# ==========================================================
def classify_bet(prop):

    validation = prop.get("model_validation", {})
    confidence = prop.get("confidence", 50)

    if validation.get("is_outlier") or validation.get("exceeds_physical_limits"):
        prop["bet_tier"] = "NO BET"
        prop["bet_decision"] = "PASS"
        return prop

    edge_over = prop.get("edge_over", 0)
    edge_under = prop.get("edge_under", 0)

    if edge_over > 0.08 and confidence >= 70:
        tier = "VALUE BET - STRONG"
        decision = "OVER"
    elif edge_under > 0.08 and confidence >= 70:
        tier = "VALUE BET - STRONG"
        decision = "UNDER"
    elif edge_over > 0.05:
        tier = "VALUE BET"
        decision = "OVER"
    elif edge_under > 0.05:
        tier = "VALUE BET"
        decision = "UNDER"
    else:
        tier = "NO BET"
        decision = "PASS"

    prop["bet_tier"] = tier
    prop["bet_decision"] = decision

    return prop
