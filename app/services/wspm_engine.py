import math
from itertools import product

# ==========================================================
# 🛡️ SAFE FLOAT
# ==========================================================
def safe_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ==========================================================
# 🏀 NBA PROJECTION ENGINE
# ==========================================================
def wspm_nba_projection(prop, odds, script):

    mean = prop["projection_model"]["mean"]
    std_dev = prop["projection_model"]["std_dev"]
    minutes = prop.get("projected_minutes", 30)

    spread = abs(float(odds.get("spread", 0))) if odds else 0

    # Blowout logic
    if spread >= 15:
        if 15 <= spread < 20:
            primary_cut = 0.15
            bench_boost = 0.08
            variance_boost = 0.15
        else:
            primary_cut = 0.22
            bench_boost = 0.12
            variance_boost = 0.22

        if prop["role"] == "Primary":
            mean *= (1 - primary_cut)
            minutes *= (1 - primary_cut)
        else:
            mean *= (1 + bench_boost)
            minutes *= (1 + bench_boost)

        std_dev *= (1 + variance_boost)

    if script == "high_scoring":
        mean *= 1.03
    elif script == "defensive":
        mean *= 0.97

    return {
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "projected_minutes": round(minutes, 2)
    }


# ==========================================================
# 🏈 NFL PROJECTION ENGINE
# ==========================================================
def wspm_nfl_projection(prop, odds, script):

    prop_type = prop.get("type", "").lower()
    role = prop.get("role", "").lower()

    total = safe_float(odds.get("over_under"), 44)
    spread = safe_float(odds.get("spread"), 0)

    plays = 68 if total > 50 else 58 if total < 40 else 63

    if script == "high_scoring":
        pass_boost, rush_boost = 1.12, 0.93
    elif script == "low_scoring":
        pass_boost, rush_boost = 0.90, 1.10
    else:
        pass_boost, rush_boost = 1.0, 1.0

    if "passing yards" in prop_type:
        attempts = 34 + (5 if spread > 6 else -4 if spread < -6 else 0)
        mean = attempts * 7.2 * pass_boost
    elif "rushing yards" in prop_type:
        share = 0.58 if "rb" in role else 0.18
        mean = plays * share * 4.3 * rush_boost
    else:
        mean = safe_float(prop.get("line"), 0)

    std_dev = mean * 0.22 if mean > 0 else 1

    return {
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2)
    }


# ==========================================================
# ⚽ POISSON SOCCER MODEL
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def build_score_matrix(home_xg, away_xg, max_goals=6):
    matrix = {}
    for h, a in product(range(max_goals + 1), repeat=2):
        matrix[(h, a)] = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)
    return matrix


# ==========================================================
# ⚽ DERIVE ALL MARKETS FROM MATRIX
# ==========================================================
def derive_soccer_markets(matrix, market_line):

    over = 0
    under = 0
    home_win = 0
    draw = 0
    away_win = 0
    btts_yes = 0

    for (h, a), p in matrix.items():

        # Totales dinámicos
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
# ⚽ SOCCER PROJECTION ENGINE (FINAL VERSION)
# ==========================================================
def wspm_soccer_projection(home_xg, away_xg, market_line):

    matrix = build_score_matrix(home_xg, away_xg)
    markets = derive_soccer_markets(matrix, market_line)

    return markets
