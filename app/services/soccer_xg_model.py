# =========================================
# ⚽ SOCCER EXPECTED GOALS MODEL (IMPROVED)
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
    "default": 2.5
}

HOME_ADVANTAGE = 1.08
REGRESSION_WEIGHT = 0.30   # antes era 0.50 implícito


# =========================================
# 📊 TEAM STRENGTH
# =========================================
def calculate_team_strength(team_stats, league_avg):

    goals_for = safe_float(team_stats.get("goals_for"), league_avg / 2)
    goals_against = safe_float(team_stats.get("goals_against"), league_avg / 2)
    games = max(safe_float(team_stats.get("games_played"), 10), 1)

    gf_per_game = goals_for / games
    ga_per_game = goals_against / games

    league_half = league_avg / 2

    # 🔥 Regresión ponderada realista
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

    # --- Datos crudos ---
    home_gf = safe_float(home_stats.get("goals_for"), league_half)
    home_ga = safe_float(home_stats.get("goals_against"), league_half)
    home_games = max(safe_float(home_stats.get("games_played"), 10), 1)

    away_gf = safe_float(away_stats.get("goals_for"), league_half)
    away_ga = safe_float(away_stats.get("goals_against"), league_half)
    away_games = max(safe_float(away_stats.get("games_played"), 10), 1)

    # --- Promedios reales ---
    home_gf_pg = home_gf / home_games
    home_ga_pg = home_ga / home_games
    away_gf_pg = away_gf / away_games
    away_ga_pg = away_ga / away_games

    # --- Fuerza relativa contra promedio liga ---
    home_attack = home_gf_pg / league_half
    home_defense = home_ga_pg / league_half

    away_attack = away_gf_pg / league_half
    away_defense = away_ga_pg / league_half

    # --- Modelo multiplicativo clásico ---
    home_xg = league_half * home_attack * away_defense * HOME_ADVANTAGE
    away_xg = league_half * away_attack * home_defense

    total_xg = home_xg + away_xg

    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2)
    }
