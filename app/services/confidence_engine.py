# ==========================================================
# 🎯 GAME SCRIPT (SE CONSERVA)
# ==========================================================
def infer_game_script(sport: str, odds: dict) -> str:

    total = odds.get("over_under")
    if not total:
        return "neutral"

    total = float(total)

    if sport == "basketball":
        if total >= 230:
            return "high_scoring"
        elif total <= 215:
            return "low_scoring"
        return "neutral"

    if sport == "football":
        if total >= 48:
            return "high_scoring"
        elif total <= 46:
            return "low_scoring"
        return "neutral"

    return "neutral"


# ==========================================================
# 🏆 TEAM CONFIDENCE (AHORA LIGADA A MERCADO)
# ==========================================================
def team_pick_confidence(game_script: str) -> dict:

    if game_script == "high_scoring":
        return {"moneyline": 62, "spread": 55, "total": 68}
    if game_script == "low_scoring":
        return {"moneyline": 66, "spread": 62, "total": 60}

    return {"moneyline": 58, "spread": 58, "total": 58}


# ==========================================================
# 📊 EDGE → CONFIDENCE CONVERSIÓN
# ==========================================================
def edge_to_confidence(edge: float, reliability: float) -> int:
    """
    Convierte edge matemático en confianza real.
    """
    base = 50
    edge_component = abs(edge) * 350   # sensibilidad cuant
    reliability_component = reliability * 20

    confidence = base + edge_component + reliability_component
    return max(45, min(int(confidence), 90))


# ==========================================================
# 🧠 PLAYER PROP CONFIDENCE (MODELO HÍBRIDO)
# ==========================================================
def player_prop_confidence(prop: dict, game_script: str, sport: str) -> dict:

    reasons = []

    # 🔹 CONTEXTO DEPORTIVO (tu lógica original)
    context_bonus = 0
    role = prop.get("role")
    prop_type = prop.get("type", "")

    if role in ("QB", "G", "RB"):
        context_bonus += 8
        reasons.append("Jugador con rol principal")

    if game_script == "high_scoring" and ("Points" in prop_type or "Passing" in prop_type):
        context_bonus += 10
        reasons.append("Entorno de alto ritmo")

    if game_script == "low_scoring" and ("Carries" in prop_type or "Completions" in prop_type):
        context_bonus += 10
        reasons.append("Volumen estable esperado")

    # 🔹 EDGE REAL DEL MODELO
    edge = max(abs(prop.get("edge_over", 0)), abs(prop.get("edge_under", 0)))
    reliability = prop.get("reliability_factor", 0.6)

    quantitative_conf = edge_to_confidence(edge, reliability)

    # 🔹 COMBINACIÓN FINAL
    confidence = min(90, quantitative_conf + context_bonus)

    # 🔹 TIER AUTOMÁTICO
    if confidence >= 80:
        tier = "MUY RECOMENDADO"
    elif confidence >= 65:
        tier = "BUENA OPCIÓN"
    else:
        tier = "SOLO INFORMATIVO"

    return {
        "confidence": confidence,
        "tier": tier,
        "confidence_reason": " + ".join(reasons) if reasons else "Modelo estadístico"
    }
