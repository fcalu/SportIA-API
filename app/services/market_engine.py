def american_to_prob(odds):
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)

def no_vig_prob(over_odds, under_odds):
    
    if over_odds is None or under_odds is None:
        return None, None

    p_over = american_to_prob(over_odds)
    p_under = american_to_prob(under_odds)

    total = p_over + p_under

    if total == 0:
        return None, None

    return p_over / total, p_under / total
