def wspm_soccer_projection(market, odds, script):
    
    total = float(odds.get("over_under", 2.5))
    spread = abs(float(odds.get("spread", 0)))

    # Base goals expectation
    base_goals = total

    if script == "high_scoring":
        script_factor = 1.15
    elif script == "low_scoring":
        script_factor = 0.85
    else:
        script_factor = 1.0

    if market == "both_teams_score":
        projection = 0.62 * script_factor

    elif market == "total_goals":
        projection = base_goals * script_factor

    elif market == "corners":
        projection = 9.5 * script_factor

    else:
        projection = base_goals

    return round(projection, 2)
def build_prompt(match, odds, decisions):
    
    if not decisions:
        return "El modelo no encuentra ventaja estadística suficiente."

    decision_text = "\n".join([
        f"{d['profile']} → {d['play']} ({d['logic']})"
        for d in decisions
    ])

    return f"""
Eres un analista profesional de mercados deportivos.

PARTIDO: {match}

DECISIONES ESTRATÉGICAS DEL MODELO:
{decision_text}

Explica estas decisiones como lo haría un tipster profesional, hablando de probabilidad, riesgo y expectativa matemática.
"""
