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
# 🏀 NBA PROJECTION ENGINE (UPGRADED)
# ==========================================================
# ==========================================
# 🏀 WSPM NBA PROJECTION ENGINE + BLOWOUT
# ==========================================

def wspm_nba_projection(prop, odds, script):

    mean = prop["projection_model"]["mean"]
    std_dev = prop["projection_model"]["std_dev"]
    minutes = prop.get("projected_minutes", 30)

    spread = abs(float(odds.get("spread", 0))) if odds else 0

    # ======================================
    # 🧨 BLOWOUT MODEL (APLICACIÓN REAL)
    # ======================================
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

    # ======================================
    # SCRIPT ADJUSTMENT
    # ======================================
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
# 🏈 NFL PROJECTION ENGINE (UPGRADED)
# ==========================================================
def wspm_nfl_projection(prop, odds, script):

    prop_type = prop.get("type", "").lower()
    role = prop.get("role", "").lower()

    total = safe_float(odds.get("over_under"), 44)
    spread = safe_float(odds.get("spread"), 0)

    plays = 68 if total > 50 else 58 if total < 40 else 63
    pass_boost, rush_boost = (1.12, 0.93) if script == "high_scoring" else (0.90, 1.10) if script == "low_scoring" else (1.0, 1.0)

    if "passing yards" in prop_type:
        attempts = 34 + (5 if spread > 6 else -4 if spread < -6 else 0)
        mean = attempts * 7.2 * pass_boost
    elif "rushing yards" in prop_type:
        share = 0.58 if "rb" in role else 0.18
        mean = plays * share * 4.3 * rush_boost
    else:
        mean = safe_float(prop.get("line"), 0)

    # 📊 Varianza histórica NFL props
    std_dev = mean * 0.22 if mean > 0 else 1

    return {
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2)
    }


# ==========================================================
# ⚽ POISSON SOCCER MODEL (NO CAMBIA)
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def build_score_matrix(home_xg, away_xg, max_goals=6):
    matrix = {}
    for h, a in product(range(max_goals + 1), repeat=2):
        matrix[(h, a)] = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)
    return matrix


def market_probs_from_matrix(matrix):

    over25 = btts = home_win = draw = away_win = 0

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
        "away_win": round(away_win, 3),
    }


# ==========================================================
# ⚽ SOCCER PROJECTION ENGINE (SIGUE IGUAL)
# ==========================================================
def wspm_soccer_projection(market, odds, script, league):

    total = safe_float(odds.get("over_under"), 2.5)
    spread = abs(safe_float(odds.get("spread"), 0))

    if spread >= 1:
        home_xg = total * 0.65
        away_xg = total * 0.35
    else:
        home_xg = total * 0.52
        away_xg = total * 0.48

    matrix = build_score_matrix(home_xg, away_xg)
    probs = market_probs_from_matrix(matrix)

    return probs.get(market)
