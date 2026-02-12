# =========================================
# ⚽ SOCCER EXPECTED GOALS MODEL (CALIBRATED)
# =========================================

def safe_float(v, default=0):
    try:
        return float(v)
    except:
        return default


# =========================================
# 🎯 CONFIGURACIÓN BASE LIGA
# =========================================
# Puedes personalizar por liga
LEAGUE_BASELINES = {
    "mex.1": 2.6,
    "fra.1": 2.5,
    "eng.1": 2.8,
    "esp.1": 2.6,
    "default": 2.5
}

HOME_ADVANTAGE = 1.08  # ~8% boost local


# =========================================
# 📊 TEAM STRENGTH (REGRESIÓN A LA MEDIA)
# =========================================
def calculate_team_strength(team_stats, league_avg):

    goals_for = safe_float(team_stats.get("goals_for"), league_avg / 2)
    goals_against = safe_float(team_stats.get("goals_against"), league_avg / 2)
    games = max(safe_float(team_stats.get("games_played"), 10), 1)

    gf_per_game = goals_for / games
    ga_per_game = goals_against / games

    # Regresión hacia promedio liga (evita extremos)
    attack_strength = (gf_per_game + league_avg / 2) / 2
    defense_strength = (ga_per_game + league_avg / 2) / 2

    return attack_strength, defense_strength


# =========================================
# ⚽ MATCH EXPECTED GOALS
# =========================================
def expected_goals_match(home_stats, away_stats, league="default"):

    league_avg = LEAGUE_BASELINES.get(league, LEAGUE_BASELINES["default"])

    home_attack, home_def = calculate_team_strength(home_stats, league_avg)
    away_attack, away_def = calculate_team_strength(away_stats, league_avg)

    # Modelo multiplicativo ajustado
    home_xg = home_attack * away_def / (league_avg / 2)
    away_xg = away_attack * home_def / (league_avg / 2)

    # Aplicar ventaja local
    home_xg *= HOME_ADVANTAGE

    total_xg = home_xg + away_xg

    # 🔒 Calibración final hacia promedio liga
    calibration_factor = league_avg / max(total_xg, 0.01)
    total_xg *= calibration_factor
    home_xg *= calibration_factor
    away_xg *= calibration_factor

    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2)
    }
