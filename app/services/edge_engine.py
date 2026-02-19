from app.services.wspm_engine import implied_probability

def calculate_edge(prop=None, odds=None, script=None, sport=None, league=None):
    
    # ======================================================
    # ⚽ SOCCER — PROBABILITY EDGE (NO GOALS DIFF)
    # ======================================================
    if sport == "soccer" and prop:

        prob = prop.get("projection_model")
        line = prop.get("line")

        if prob is None or line is None:
            prop.update({
                "edge": 0,
                "edge_type": "NO_DATA",
                "bet_tier": "NO BET"
            })
            return prop

        # Convert American odds to decimal (simplified)
        over_odds = prop.get("over_odds")
        if over_odds:
            implied = implied_probability(over_odds)
            edge = prop["model_prob_over"] - implied


        prop["edge"] = round(edge, 3)

        if edge <= 0:
            prop["bet_tier"] = "NO BET"
        elif edge < 0.04:
            prop["bet_tier"] = "LEAN"
        elif edge < 0.08:
            prop["bet_tier"] = "VALUE_BET"
        else:
            prop["bet_tier"] = "ELITE_VALUE"

        return prop

    # ======================================================
    # 🏀🏈 NBA & NFL (TU LÓGICA ACTUAL)
    # ======================================================
    if not prop:
        return prop

    projection = prop.get("projection_model")
    line = prop.get("line")

    if projection is None or line is None:
        prop["bet_tier"] = "NO BET"
        return prop

    try:
        edge = float(projection) - float(line)
    except:
        prop["bet_tier"] = "NO BET"
        return prop

    prop["edge"] = round(edge, 2)

    if edge <= 0:
        prop["bet_tier"] = "NO BET"
    elif edge < 1:
        prop["bet_tier"] = "LEAN"
    elif edge < 2.5:
        prop["bet_tier"] = "VALUE_BET"
    elif edge < 4:
        prop["bet_tier"] = "STRONG_VALUE"
    else:
        prop["bet_tier"] = "ELITE_VALUE"

    return prop
