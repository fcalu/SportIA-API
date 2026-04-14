from app.services.wspm_engine import implied_probability


def enhance_soccer_markets(markets, odds, home_stats, away_stats):

    try:
        # =========================
        # 1. AJUSTE POR TOTAL LINE
        # =========================
        total_line = odds.get("over_under", 2.5)

        if total_line >= 3:
            markets["btts_yes"] *= 1.08
        elif total_line <= 2:
            markets["btts_yes"] *= 0.92

        # =========================
        # 2. AJUSTE POR DEFENSA
        # =========================
        home_conceded = _get_stat(home_stats, "goalsConceded")
        away_conceded = _get_stat(away_stats, "goalsConceded")

        if home_conceded and away_conceded:
            gap = abs(home_conceded - away_conceded)

            if gap > 10:
                markets["btts_yes"] *= 1.05

        # =========================
        # 3. AJUSTE POR MERCADO (OU)
        # =========================
        over_odds = odds.get("over_odds")
        under_odds = odds.get("under_odds")

        if over_odds and under_odds:
            market_over = implied_probability(over_odds)

            model_over = markets.get("over")

            if model_over and market_over:
                delta = model_over - market_over

                # si modelo ve más goles que mercado → sube BTTS
                if delta > 0.05:
                    markets["btts_yes"] *= 1.05

        # =========================
        # 4. NORMALIZAR
        # =========================
        markets["btts_yes"] = min(max(markets["btts_yes"], 0.05), 0.95)
        markets["btts_no"] = 1 - markets["btts_yes"]

    except Exception as e:
        print(f"⚠️ enhance_soccer_markets error: {e}")

    return markets


def _get_stat(stats, key):
    try:
        for s in stats.get("statistics", []):
            if s.get("name") == key:
                return float(s.get("displayValue"))
    except:
        return None