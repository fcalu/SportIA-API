def evaluate_prediction(prediction, home_score, away_score):
    
    decision = prediction.decision
    market = prediction.market_type

    # =========================
    # TOTAL GOALS
    # =========================
    if market == "total_goals":

        total = home_score + away_score

        if decision == "OVER":
            return "WIN" if total > 2.5 else "LOSS"

        if decision == "UNDER":
            return "WIN" if total < 2.5 else "LOSS"

    # =========================
    # MONEYLINE
    # =========================
    if market == "moneyline":

        if decision == "HOME":
            return "WIN" if home_score > away_score else "LOSS"

        if decision == "AWAY":
            return "WIN" if away_score > home_score else "LOSS"

    return "PUSH"
