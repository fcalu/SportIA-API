# =========================================
# ⚽ SOCCER EXPECTED GOALS MODEL (REAL)
# =========================================

def safe_float(v, default=0):
    try:
        return float(v)
    except:
        return default


# -----------------------------------------
# TEAM STRENGTH
# -----------------------------------------
def calculate_team_strength(team_stats):
    goals_for = safe_float(team_stats.get("goals_for"), 1.2)
    goals_against = safe_float(team_stats.get("goals_against"), 1.2)
    shots = safe_float(team_stats.get("shots"), 10)
    shots_on_target = safe_float(team_stats.get("shots_on_target"), 3.5)

    shot_quality = shots_on_target / shots if shots > 0 else 0.32

    attack_strength = goals_for * shot_quality
    defense_weakness = goals_against

    return attack_strength, defense_weakness


# -----------------------------------------
# MATCH EXPECTED GOALS
# -----------------------------------------
def expected_goals_match(home_stats, away_stats):
    home_attack, home_def_weak = calculate_team_strength(home_stats)
    away_attack, away_def_weak = calculate_team_strength(away_stats)

    home_xg = (home_attack + away_def_weak) / 2
    away_xg = (away_attack + home_def_weak) / 2

    total_xg = home_xg + away_xg

    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2)
    }


# -----------------------------------------
# TOTAL GOALS EDGE
# -----------------------------------------
def soccer_total_edge(total_xg, market_line):
    edge = total_xg - market_line

    if edge > 0.35:
        decision = "OVER"
        tier = "VALUE_BET"
    elif edge < -0.35:
        decision = "UNDER"
        tier = "VALUE_BET"
    else:
        decision = "NO BET"
        tier = "NO BET"

    return {
        "model_total": round(total_xg, 2),
        "market_line": market_line,
        "edge": round(edge, 2),
        "decision": decision,
        "bet_tier": tier
    }
