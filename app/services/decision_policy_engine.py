def tipster_decision_policy(prop, odds):
    
    label = prop.get("name") or prop.get("title") or prop.get("player") or "Market"

    decision = prop.get("bet_decision", "PASS")
    edge = max(prop.get("edge_over", 0), prop.get("edge_under", 0))
    model_prob = max(prop.get("model_prob_over", 0), prop.get("model_prob_under", 0))
    line = prop.get("line")

    # 🔒 No sugerimos nada si no hay apuesta válida
    if decision == "PASS":
        return []

    strategies = []

    # 🔥 Alta convicción
    if edge > 0.12 and model_prob > 0.64:
        strategies.append({
            "profile": "AGRESIVA",
            "play": f"{label} → {decision} {line}",
            "logic": "Ventaja estadística clara"
        })

    # 🟢 Balanceado (sin inventar línea)
    elif 0.06 < edge <= 0.12:
        strategies.append({
            "profile": "BALANCEADA",
            "play": f"{label} → {decision} {line}",
            "logic": "Reducimos varianza manteniendo EV positivo"
        })

    # 🟡 Conservador contextual (alineado al edge real)
    if (
        prop.get("type") == "total_goals" and
        decision == "UNDER" and
        edge > 0.05 and
        odds.get("home_moneyline", 0) < -250
    ):
        strategies.append({
            "profile": "CONSERVADORA",
            "play": f"Doble oportunidad favorito + Under {line}",
            "logic": "Dominio esperado + baja producción de goles"
        })

    return strategies
