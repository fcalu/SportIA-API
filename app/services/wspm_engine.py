import math
from itertools import product


# ==========================================================
# 🛡️ SAFE FLOAT
# ==========================================================
def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ==========================================================
# 📊 IMPLIED PROBABILITY (AMERICAN ODDS)
# ==========================================================
def implied_probability(odds):

    if odds is None:
        return None

    odds = float(odds)

    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


# ==========================================================
# ⚽ POISSON SOCCER CORE
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def build_score_matrix(home_xg, away_xg, max_goals=6):
    matrix = {}

    for h, a in product(range(max_goals + 1), repeat=2):
        matrix[(h, a)] = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)

    return matrix


# ==========================================================
# ⚽ DERIVE ALL MARKETS FROM SCORE MATRIX
# ==========================================================
def derive_soccer_markets(matrix, market_line):

    over = under = 0
    home_win = draw = away_win = 0
    btts_yes = 0

    for (h, a), p in matrix.items():

        # Totals
        if h + a > market_line:
            over += p
        else:
            under += p

        # 1X2
        if h > a:
            home_win += p
        elif h == a:
            draw += p
        else:
            away_win += p

        # BTTS
        if h > 0 and a > 0:
            btts_yes += p

    return {
        "over": round(over, 4),
        "under": round(under, 4),
        "home_win": round(home_win, 4),
        "draw": round(draw, 4),
        "away_win": round(away_win, 4),
        "btts_yes": round(btts_yes, 4),
        "btts_no": round(1 - btts_yes, 4),
        "double_chance_home": round(home_win + draw, 4),
        "double_chance_away": round(away_win + draw, 4)
    }


# ==========================================================
# ⚖️ MARKET CALIBRATION ENGINE (PRO VERSION)
# ==========================================================
def calibrate_xg_with_market(home_xg, away_xg, odds):

    if not odds:
        return home_xg, away_xg

    home_ml = odds.get("home_moneyline")
    away_ml = odds.get("away_moneyline")
    draw_ml = odds.get("draw_odds")

    if home_ml is None or away_ml is None:
        return home_xg, away_xg

    # Convert to implied probabilities
    home_prob = implied_probability(home_ml)
    away_prob = implied_probability(away_ml)
    draw_prob = implied_probability(draw_ml) if draw_ml else 0

    # Remove overround
    total = home_prob + away_prob + draw_prob

    if total <= 0:
        return home_xg, away_xg

    home_prob /= total
    away_prob /= total
    draw_prob /= total

    # Market strength difference
    strength_diff = home_prob - away_prob

    # Controlled adjustment (anti-overfit)
    adjustment_factor = 0.55  # 0.45–0.65 ideal range

    adjustment = strength_diff * adjustment_factor

    # Clamp adjustment to avoid crazy distortions
    adjustment = max(min(adjustment, 0.25), -0.25)

    home_xg *= (1 + adjustment)
    away_xg *= (1 - adjustment)

    return home_xg, away_xg


# ==========================================================
# ⚽ FINAL SOCCER PROJECTION ENGINE
# ==========================================================
def wspm_soccer_projection(home_xg, away_xg, market_line, odds=None):

    # Step 1️⃣ Market calibration
    home_xg, away_xg = calibrate_xg_with_market(home_xg, away_xg, odds)

    # Step 2️⃣ Build score matrix
    matrix = build_score_matrix(home_xg, away_xg)

    # Step 3️⃣ Derive markets
    markets = derive_soccer_markets(matrix, market_line)

    return markets
