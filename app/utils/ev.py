def expected_value(prob, odds):
    if not odds:
        return None
    return round((prob * (odds - 1)) - (1 - prob), 3)
