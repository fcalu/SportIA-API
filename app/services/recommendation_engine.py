# ==========================================================
# 🧠 AI RECOMMENDATION ENGINE (MODEL-GOVERNED Y COMPATIBLE)
# ==========================================================

def safe_float(v):
    try:
        return float(v)
    except:
        return None


# 🔒 Normalizador universal de nombre
def get_label(prop):
    return (
        prop.get("name")
        or prop.get("title")
        or prop.get("player_name")
        or prop.get("player")
        or "Market"
    )


def generate_ai_recommendations(sport, odds, player_props, script):
    """
    Genera recomendaciones SOLO si el modelo autorizó la apuesta.
    Compatible con sistema viejo y nuevo.
    """

    recommendations = []

    # ======================================================
    # 🎯 TEAM CONTEXT MARKETS (NO SON PICKS, SON LECTURA)
    # ======================================================
    total = safe_float(odds.get("total") or odds.get("over_under"))
    spread = safe_float(odds.get("spread"))

    if sport in ["basketball", "football"]:
        if total and total > 0:
            if script == "high_scoring":
                recommendations.append(
                    f"Tendencia ofensiva: partido proyectado alto en puntos ({total})."
                )
            elif script == "low_scoring":
                recommendations.append(
                    f"Tendencia defensiva: partido proyectado bajo en puntos ({total})."
                )

        if spread and abs(spread) <= 3.5:
            recommendations.append("Spread corto sugiere juego competitivo.")

    # ======================================================
    # 🏀🏈 PLAYER PROPS (MODELO MANDA)
    # ======================================================
    for prop in player_props:

        # 🔥 Compatibilidad con tiers viejos y nuevos
        tier = prop.get("bet_tier", "")
        if tier not in [
            "VALUE BET",
            "VALUE BET - STRONG",
            "VALUE_BET",
            "STRONG_VALUE",
            "ELITE_VALUE",
        ]:
            continue

        # Compatibilidad edge viejo/nuevo
        edge = max(
            prop.get("edge", 0),
            prop.get("edge_over", 0),
            prop.get("edge_under", 0),
        )
        if edge <= 0:
            continue

        line = prop.get("line")
        if line is None:
            continue

        name = get_label(prop)
        prop_type = prop.get("type", "")
        decision = prop.get("bet_decision", "OVER")

        # 🧠 NFL MARKETS
        if sport == "football":

            if "Passing" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} yardas por pase.")

            elif "Rushing" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} yardas por tierra.")

            elif "Receiving" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} yardas por recepción.")

            elif "Carries" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} acarreos.")

        # 🏀 NBA MARKETS
        elif sport == "basketball":

            if "Points" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} puntos.")

            elif "Rebounds" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} rebotes.")

            elif "Assists" in prop_type:
                recommendations.append(f"{name} {decision.lower()} {line} asistencias.")

    # ======================================================
    # ⚽ SOCCER TEAM MARKETS
    # ======================================================
    if sport == "soccer":

        for prop in player_props:

            if prop.get("role") != "team":
                continue

            tier = prop.get("bet_tier", "")
            if tier not in [
                "VALUE BET",
                "VALUE BET - STRONG",
                "VALUE_BET",
                "STRONG_VALUE",
                "ELITE_VALUE",
            ]:
                continue

            decision = prop.get("bet_decision", "OVER")
            line = prop.get("line")
            name = get_label(prop)

            recommendations.append(f"{name}: {decision} {line} goles totales.")

    # ======================================================
    # 🚫 SI NO HAY EDGE REAL
    # ======================================================
    if not recommendations:
        recommendations.append(
            "La IA no detecta apuestas con ventaja estadística real en este evento."
        )

    return recommendations
