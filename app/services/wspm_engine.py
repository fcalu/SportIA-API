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
# 🏀 NBA PROJECTION ENGINE
# ==========================================================
def wspm_nba_projection(prop, odds, script):
    # Extraemos valores base
    mean = prop["projection_model"]["mean"]
    std_dev = prop["projection_model"]["std_dev"]
    minutes = prop.get("projected_minutes", 30)
    prop_type = prop.get("type", "").lower() # Importante: detectar el mercado

    spread = abs(float(odds.get("spread", 0))) if odds else 0

    # ==========================================================
    # 🏀 AJUSTE POR BLOWOUT (Saturación de minutos)
    # ==========================================================
    if spread >= 15:
        if 15 <= spread < 20:
            primary_cut, bench_boost, variance_boost = 0.15, 0.08, 0.15
        else:
            primary_cut, bench_boost, variance_boost = 0.22, 0.12, 0.22

        if prop.get("role") == "Primary":
            mean *= (1 - primary_cut)
            minutes *= (1 - primary_cut)
        else:
            # Los suplentes suben mucho en Puntos/3PT en minutos basura
            mean *= (1 + bench_boost)
            minutes *= (1 + bench_boost)
        
        std_dev *= (1 + variance_boost)

    # ==========================================================
    # 🎯 AJUSTE ESPECÍFICO POR MERCADO (Edge Fino)
    # ==========================================================
    # High Scoring beneficia más a Puntos/Asistencias que a Rebotes
    if script == "high_scoring":
        if "points" in prop_type: mean *= 1.05
        elif "assists" in prop_type: mean *= 1.04
        elif "rebounds" in prop_type: mean *= 1.02
        else: mean *= 1.03
    elif script == "defensive":
        if "points" in prop_type: mean *= 0.94
        elif "three" in prop_type: mean *= 0.92 # Los triples sufren más en defensas cerradas
        else: mean *= 0.97

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
# ⚽ POISSON SOCCER CORE
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def build_score_matrix(home_xg, away_xg, max_goals=6):
    matrix = {}
    for h, a in product(range(max_goals + 1), repeat=2):
        matrix[(h, a)] = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)
    return matrix


def derive_soccer_markets(matrix, market_line):

    over = under = 0
    home_win = draw = away_win = 0
    btts_yes = 0

    for (h, a), p in matrix.items():

        if h + a > market_line:
            over += p
        else:
            under += p

        if h > a:
            home_win += p
        elif h == a:
            draw += p
        else:
            away_win += p

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
# ⚽ SOCCER PROJECTION ENGINE
# ==========================================================
def wspm_soccer_projection(home_xg, away_xg, market_line, odds=None):
    
    # Optional calibration with moneyline
    if odds:
        home_ml = odds.get("home_moneyline")
        away_ml = odds.get("away_moneyline")

        if home_ml and away_ml:

            home_prob = implied_probability(home_ml)
            away_prob = implied_probability(away_ml)

            total = home_prob + away_prob

            if total > 0:
                home_prob /= total
                away_prob /= total

                diff = home_prob - away_prob
                adjustment = max(min(diff * 0.55, 0.25), -0.25)

                home_xg *= (1 + adjustment)
                away_xg *= (1 - adjustment)

    # ==========================================================
    # 📊 MARKET CALIBRATION
    # ==========================================================

    market_total = market_line + 0.05
    model_total = home_xg + away_xg

    if model_total > 0:

        scale = market_total / model_total

        home_xg *= scale
        away_xg *= scale

    matrix = build_score_matrix(home_xg, away_xg)

    return derive_soccer_markets(matrix, market_line)
