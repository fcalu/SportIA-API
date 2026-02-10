import math
from itertools import product


# ==========================================================
# 🎯 POISSON FUNCTION
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


# ==========================================================
# ⚽ SCORE MATRIX
# ==========================================================
def build_score_matrix(home_xg, away_xg, max_goals=6):
    matrix = {}

    for h, a in product(range(max_goals + 1), repeat=2):
        prob = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)
        matrix[(h, a)] = prob

    return matrix


# ==========================================================
# 🧮 MARKET PROBABILITIES
# ==========================================================
def market_probs_from_matrix(matrix):

    over25 = 0
    btts = 0
    home_win = 0
    draw = 0
    away_win = 0

    for (h, a), p in matrix.items():

        if h + a >= 3:
            over25 += p

        if h > 0 and a > 0:
            btts += p

        if h > a:
            home_win += p
        elif h == a:
            draw += p
        else:
            away_win += p

    return {
        "over_2_5": round(over25, 3),
        "btts": round(btts, 3),
        "home_win": round(home_win, 3),
        "draw": round(draw, 3),
        "away_win": round(away_win, 3)
    }


# ==========================================================
# 💰 EXPECTED VALUE
# ==========================================================
def expected_value(prob, odds):
    """
    odds = decimal odds
    """
    return round((prob * (odds - 1)) - (1 - prob), 3)
