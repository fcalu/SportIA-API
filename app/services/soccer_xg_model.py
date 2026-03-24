# =========================================
# ⚽ SOCCER EXPECTED GOALS MODEL (STABLE)
# =========================================

def safe_float(v, default=0):
    try:
        return float(v)
    except:
        return default


# =========================================
# 🎯 CONFIGURACIÓN BASE LIGA
# =========================================

LEAGUE_BASELINES = {
    "mex.1": 2.6,
    "fra.1": 2.5,
    "eng.1": 2.8,
    "esp.1": 2.6,
    "ned.1": 3.0,   # Eredivisie más goleadora
    "usa.1": 2.8,   # MLS
    "fifa.friendly": 2.7,      # Amistosos: Suelen ser abiertos, más goles (Promedio ~2.65 - 2.8)
    "fifa.worldq.uefa": 2.4,   # Repechaje: Mucha tensión, suelen ser de pocos goles (Under 2.5)
    "fifa.wcq.ply": 2.3,       # Play-offs Intercontinentales: Máxima tensión, promedio muy bajo
    "default": 2.5
}

HOME_ADVANTAGE = 1.09
REGRESSION_WEIGHT = 0.30
MARKET_BLEND = 0.40


# =========================================
# 📊 TEAM STRENGTH
# =========================================

def calculate_team_strength(team_stats, league_avg):

    goals_for = safe_float(team_stats.get("goals_for"), league_avg / 2)
    goals_against = safe_float(team_stats.get("goals_against"), league_avg / 2)
    games = max(safe_float(team_stats.get("games_played"), 10), 1)

    gf_per_game = goals_for / games
    ga_per_game = goals_against / games

    # limitar extremos
    gf_per_game = max(min(gf_per_game, 3.2), 0.6)
    ga_per_game = max(min(ga_per_game, 3.2), 0.6)

    league_half = league_avg / 2

    # regresión a la media
    attack_strength = (
        (1 - REGRESSION_WEIGHT) * gf_per_game
        + REGRESSION_WEIGHT * league_half
    )

    defense_strength = (
        (1 - REGRESSION_WEIGHT) * ga_per_game
        + REGRESSION_WEIGHT * league_half
    )

    return attack_strength, defense_strength


# =========================================
# ⚽ MATCH EXPECTED GOALS
# =========================================

def expected_goals_match(home_stats, away_stats, league="default"):
    
    league_avg = LEAGUE_BASELINES.get(league, LEAGUE_BASELINES["default"])
    league_half = league_avg / 2

    # =========================================
    # TEAM STRENGTH
    # =========================================

    home_attack, home_defense = calculate_team_strength(home_stats, league_avg)
    away_attack, away_defense = calculate_team_strength(away_stats, league_avg)

    # fuerza relativa
    home_attack_rel = home_attack / league_half
    home_def_rel = home_defense / league_half

    away_attack_rel = away_attack / league_half
    away_def_rel = away_defense / league_half

    # =========================================
    # MODELO MULTIPLICATIVO
    # =========================================

    home_xg = league_half * home_attack_rel * away_def_rel * HOME_ADVANTAGE
    away_xg = league_half * away_attack_rel * home_def_rel

    model_total = home_xg + away_xg


    # =========================================
    # 📊 MARKET TOTAL CALIBRATION
    # =========================================

    market_total = league_avg

    adjusted_total = (
        (1 - MARKET_BLEND) * model_total
        + MARKET_BLEND * market_total
    )

    if model_total > 0:

        scale = adjusted_total / model_total

        home_xg *= scale
        away_xg *= scale


    # =========================================
    # 🚨 XG STABILITY LIMITS
    # evita probabilidades irreales
    # =========================================

    home_xg = max(min(home_xg, 2.6), 0.35)
    away_xg = max(min(away_xg, 2.3), 0.35)


    # =========================================
    # TOTAL FINAL
    # =========================================

    total_xg = home_xg + away_xg


    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2)
    }