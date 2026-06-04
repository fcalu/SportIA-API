# =========================================
# ⚽ SOCCER EXPECTED GOALS MODEL (ENHANCED)
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
    "eng.2": 2.6,
    "esp.1": 2.6,
    "ger.1": 3.1,
    "ita.1": 2.6,
    "usa.1": 2.7,
    "ned.1": 3.0,
    "por.1": 2.5,
    "ksa.1": 2.7,
    "swe.1": 2.9,
    "conmebol.sudamericana": 2.4,
    "bra.1": 2.5,
    "nor.1": 2.9,
    "uefa.champions": 2.9,
    "uefa.europa": 2.7,
    "uefa.europa.conf": 2.6,
    "conmebol.libertadores": 2.4,
    "fifa.friendly": 2.7,
    "fifa.wcq.ply": 2.2,
    "fifa.worldcup": 2.7,
    "aut.1": 3.0,
    "bel.1": 2.8,
    "sui.1": 2.9,
    "jpn.1": 2.5,
    "chn.1": 2.95,
    "default": 2.5
}

HOME_ADVANTAGE = 1.09
REGRESSION_WEIGHT = 0.30
MARKET_BLEND = 0.15


# =========================================
# 🔥 FORMA RECIENTE
# =========================================

def calculate_form_factor(last5):

    if not last5:
        return 1.0

    points = 0

    for result in last5:

        if result == "W":
            points += 3

        elif result == "D":
            points += 1

    max_points = 15
    pct = points / max_points

    # rango 0.92 - 1.08
    return 0.92 + (pct * 0.16)


# =========================================
# 📊 TEAM STRENGTH
# =========================================

def calculate_team_strength(team_stats, league_avg, is_home=True):

    goals_for = safe_float(
        team_stats.get("goals_for"),
        league_avg / 2
    )

    goals_against = safe_float(
        team_stats.get("goals_against"),
        league_avg / 2
    )

    games = max(
        safe_float(
            team_stats.get("games_played"),
            10
        ),
        1
    )

    gf_per_game = goals_for / games
    ga_per_game = goals_against / games

    # =====================================
    # LOCAL / VISITANTE
    # =====================================

    if is_home:

        hg = team_stats.get("home_games", 0)

        if hg >= 5:

            gf_per_game = (
                team_stats["home_goals_for"] / hg
            )

            ga_per_game = (
                team_stats["home_goals_against"] / hg
            )

    else:

        ag = team_stats.get("away_games", 0)

        if ag >= 5:

            gf_per_game = (
                team_stats["away_goals_for"] / ag
            )

            ga_per_game = (
                team_stats["away_goals_against"] / ag
            )

    gf_per_game = max(min(gf_per_game, 3.2), 0.6)
    ga_per_game = max(min(ga_per_game, 3.2), 0.6)

    league_half = league_avg / 2

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

def expected_goals_match(
    home_stats,
    away_stats,
    league="default"
):

    league_avg = LEAGUE_BASELINES.get(
        league,
        LEAGUE_BASELINES["default"]
    )

    league_half = league_avg / 2

    # =====================================
    # STRENGTH
    # =====================================

    home_attack, home_defense = calculate_team_strength(
        home_stats,
        league_avg,
        is_home=True
    )

    away_attack, away_defense = calculate_team_strength(
        away_stats,
        league_avg,
        is_home=False
    )

    home_attack_rel = home_attack / league_half
    home_def_rel = home_defense / league_half

    away_attack_rel = away_attack / league_half
    away_def_rel = away_defense / league_half

    # =====================================
    # XG BASE
    # =====================================

    home_xg = (
        league_half
        * home_attack_rel
        * away_def_rel
        * HOME_ADVANTAGE
    )

    away_xg = (
        league_half
        * away_attack_rel
        * home_def_rel
    )

    # =====================================
    # FORMA RECIENTE
    # =====================================

    home_form = calculate_form_factor(
        home_stats.get("last5", [])
    )

    away_form = calculate_form_factor(
        away_stats.get("last5", [])
    )

    home_xg *= home_form
    away_xg *= away_form

    # =====================================
    # WIN RATE BOOST
    # =====================================

    home_win_rate = safe_float(
        home_stats.get("win_rate"),
        0.33
    )

    away_win_rate = safe_float(
        away_stats.get("win_rate"),
        0.33
    )

    home_xg *= (0.95 + home_win_rate * 0.15)
    away_xg *= (0.95 + away_win_rate * 0.15)

    # =====================================
    # OVER / BTTS AJUSTE
    # =====================================

    home_over = safe_float(
        home_stats.get("over25_rate"),
        0.5
    )

    away_over = safe_float(
        away_stats.get("over25_rate"),
        0.5
    )

    avg_over = (home_over + away_over) / 2

    if avg_over > 0.60:
        home_xg *= 1.04
        away_xg *= 1.04

    elif avg_over < 0.40:
        home_xg *= 0.96
        away_xg *= 0.96

    model_total = home_xg + away_xg

    # =====================================
    # MARKET BLEND
    # =====================================

    adjusted_total = (
        (1 - MARKET_BLEND) * model_total
        + MARKET_BLEND * league_avg
    )

    if model_total > 0:

        scale = adjusted_total / model_total

        home_xg *= scale
        away_xg *= scale

    # =====================================
    # LIMITES
    # =====================================

    home_xg = max(min(home_xg, 3.4), 0.25)
    away_xg = max(min(away_xg, 3.0), 0.25)

    total_xg = home_xg + away_xg

    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2),

        "home_form": round(home_form, 3),
        "away_form": round(away_form, 3),

        "home_win_rate": home_win_rate,
        "away_win_rate": away_win_rate
    }