import math
from itertools import product


# ==========================================================
# 🎯 POISSON PMF
# ==========================================================
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)

# ==========================================================
# ⚽ DIXON-COLES ADJUSTMENT
# ==========================================================
def dixon_coles_adjustment(h, a, rho=-0.05):

    if h == 0 and a == 0:
        return 1 - rho
    elif h == 0 and a == 1:
        return 1 + rho
    elif h == 1 and a == 0:
        return 1 + rho
    elif h == 1 and a == 1:
        return 1 - rho
    else:
        return 1
# ==========================================================
# ⚽ BUILD SCORE MATRIX
# ==========================================================
def build_score_matrix(home_xg, away_xg, max_goals=8):
    matrix = {}

    for h, a in product(range(max_goals + 1), repeat=2):

        prob = poisson_pmf(home_xg, h) * poisson_pmf(away_xg, a)

        # Dixon-Coles correction
        prob *= dixon_coles_adjustment(h, a)

        matrix[(h, a)] = prob

    # 🔹 Normalización para evitar truncamiento
    total_prob = sum(matrix.values())
    if total_prob > 0:
        for key in matrix:
            matrix[key] /= total_prob

    return matrix


# ==========================================================
# 📊 DERIVE MARKETS FROM MATRIX
# ==========================================================
def derive_markets(matrix, goal_line=2.5):

    over = 0
    under = 0
    home_win = 0
    draw = 0
    away_win = 0
    btts_yes = 0

    for (h, a), p in matrix.items():

        # Over / Under
        if h + a > goal_line:
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
# 💰 EXPECTED VALUE (DECIMAL ODDS)
# ==========================================================
def expected_value(prob, decimal_odds):
    if decimal_odds <= 1:
        return 0
    return round((prob * (decimal_odds - 1)) - (1 - prob), 4)


# ==========================================================
# 📈 IMPLIED PROBABILITY (DECIMAL)
# ==========================================================
def implied_probability_decimal(decimal_odds):
    if decimal_odds <= 1:
        return None
    return 1 / decimal_odds


# ==========================================================
# ⚽ MAIN SOCCER PROJECTION ENGINE
# ==========================================================
def soccer_projection_engine(home_xg, away_xg, goal_line=2.5):

    # 1️⃣ Construir matriz
    matrix = build_score_matrix(home_xg, away_xg)

    # 2️⃣ Derivar mercados
    markets = derive_markets(matrix, goal_line)

    return markets


# ==========================================================
# 🧪 EJEMPLO DE USO
# ==========================================================
if __name__ == "__main__":
    
    # Ejemplo realista
    home_xg = 2.13
    away_xg = 0.97

    markets = soccer_projection_engine(home_xg, away_xg, goal_line=2.5)

    print("📊 PROBABILIDADES DERIVADAS\n")

    for k, v in markets.items():
        print(f"{k}: {v}")

    # ======================================================
    # 🔥 BTTS DEBUG + ODDS DERIVADAS
    # ======================================================

    btts_yes_prob = markets["btts_yes"]
    btts_no_prob = markets["btts_no"]

    print("\n⚽ BTTS PROBABILITIES")
    print(f"BTTS YES: {btts_yes_prob}")
    print(f"BTTS NO:  {btts_no_prob}")

    # ======================================================
    # 💰 CONVERTIR A ODDS (DECIMAL + AMERICAN)
    # ======================================================

    def prob_to_decimal(prob):
        if prob <= 0:
            return None
        return round(1 / prob, 2)

    def decimal_to_american(decimal_odds):
        if decimal_odds is None:
            return None
        if decimal_odds >= 2:
            return round((decimal_odds - 1) * 100)
        else:
            return round(-100 / (decimal_odds - 1))

    # Decimal odds
    btts_yes_decimal = prob_to_decimal(btts_yes_prob)
    btts_no_decimal = prob_to_decimal(btts_no_prob)

    # American odds
    btts_yes_american = decimal_to_american(btts_yes_decimal)
    btts_no_american = decimal_to_american(btts_no_decimal)

    print("\n💰 BTTS ODDS DERIVADAS")
    print(f"YES → Decimal: {btts_yes_decimal} | American: {btts_yes_american}")
    print(f"NO  → Decimal: {btts_no_decimal}  | American: {btts_no_american}")

    # ======================================================
    # 💡 COMPARACIÓN CON MERCADO (SIMULADO)
    # ======================================================

    market_yes_odds = 105  # ejemplo DraftKings
    market_no_odds = -165

    from app.services.wspm_engine import implied_probability

    market_yes_prob = implied_probability(market_yes_odds)
    market_no_prob = implied_probability(market_no_odds)

    print("\n📊 MERCADO (IMPLIED)")
    print(f"YES → {round(market_yes_prob, 4)}")
    print(f"NO  → {round(market_no_prob, 4)}")

    # ======================================================
    # 🚀 EDGE
    # ======================================================

    edge_yes = btts_yes_prob - market_yes_prob
    edge_no = btts_no_prob - market_no_prob

    print("\n🔥 EDGE CALCULADO")
    print(f"YES EDGE: {round(edge_yes, 4)}")
    print(f"NO EDGE:  {round(edge_no, 4)}")
