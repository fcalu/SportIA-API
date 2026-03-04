from app.services.wspm_engine import implied_probability

def calculate_edge(prop=None, odds=None, script=None, sport=None, league=None):

    if not prop:
        return prop

    # ======================================================
    # ⚽ SOCCER — EDGE BASADO EN PROBABILIDADES
    # ======================================================
    if sport == "soccer":

        model_over = prop.get("model_prob_over")
        model_under = prop.get("model_prob_under")

        over_odds = prop.get("over_odds")
        under_odds = prop.get("under_odds")

        edge_over = 0
        edge_under = 0
        implied_over = None
        implied_under = None

        # ---------- OVER ----------
        if over_odds and model_over:
            implied_over = implied_probability(over_odds)
            edge_over = model_over - implied_over

        # ---------- UNDER ----------
        if under_odds and model_under:
            implied_under = implied_probability(under_odds)
            edge_under = model_under - implied_under

        # Determinar mejor lado
        if edge_over >= edge_under:
            edge = edge_over
            decision = "OVER"
        else:
            edge = edge_under
            decision = "UNDER"

        # Guardar métricas
        prop["edge"] = round(edge, 4)
        prop["edge_over"] = round(edge_over, 4)
        prop["edge_under"] = round(edge_under, 4)

        prop["implied_prob_over"] = implied_over
        prop["implied_prob_under"] = implied_under

        prop["bet_decision"] = decision

        # ---------- Expected Value ----------
        if decision == "OVER" and over_odds:
            decimal = 1 + (over_odds / 100) if over_odds > 0 else 1 + (100 / abs(over_odds))
            ev = model_over * decimal - 1
        elif decision == "UNDER" and under_odds:
            decimal = 1 + (under_odds / 100) if under_odds > 0 else 1 + (100 / abs(under_odds))
            ev = model_under * decimal - 1
        else:
            ev = 0

        prop["expected_value"] = round(ev, 4)

        # ======================================================
        # TIERS DE APUESTA (MEJORADOS)
        # ======================================================

        if edge <= 0:
            tier = "NO_BET"
        elif edge < 0.02:
            tier = "LEAN"
        elif edge < 0.05:
            tier = "VALUE_BET"
        elif edge < 0.08:
            tier = "STRONG_VALUE"
        else:
            tier = "ELITE_VALUE"

        prop["bet_tier"] = tier

        return prop

    # ======================================================
    # 🏀🏈 NBA / NFL — EDGE POR PROYECCIÓN
    # ======================================================

    projection = prop.get("projection_model")
    line = prop.get("line")

    if projection is None or line is None:
        prop["bet_tier"] = "NO_BET"
        prop["edge"] = 0
        return prop

    try:
        edge = float(projection) - float(line)
    except:
        prop["bet_tier"] = "NO_BET"
        prop["edge"] = 0
        return prop

    prop["edge"] = round(edge, 2)

    if edge <= 0:
        tier = "NO_BET"
    elif edge < 1:
        tier = "LEAN"
    elif edge < 2.5:
        tier = "VALUE_BET"
    elif edge < 4:
        tier = "STRONG_VALUE"
    else:
        tier = "ELITE_VALUE"

    prop["bet_tier"] = tier

    return prop