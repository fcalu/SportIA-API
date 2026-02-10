def tipster_decision_policy(prop, odds):
    
    # 🔒 Compatibilidad con distintos formatos de props
    label = prop.get("name") or prop.get("title") or prop.get("player") or "Market"

    model_data = prop.get("projection_model", {})
    mean = model_data.get("mean", 0)
    std = model_data.get("std_dev", 1)

    edge = max(prop.get("edge_over", 0), prop.get("edge_under", 0))
    model_prob = max(prop.get("model_prob_over", 0), prop.get("model_prob_under", 0))
    decision = prop.get("bet_decision", "PASS")
    line = prop.get("line", "")

    strategies = []

    # 🔥 Alta convicción
    if edge > 0.12 and model_prob > 0.64:
        strategies.append({
            "profile": "AGRESIVA",
            "play": f"{label} → {decision} {line}",
            "logic": "Ventaja estadística clara"
        })

    # 🟢 Balance riesgo/retorno
    if 0.06 < edge <= 0.12:
        safer_line = line + 1 if decision == "UNDER" else line - 1
        strategies.append({
            "profile": "BALANCEADA",
            "play": f"{label} → {decision} {safer_line}",
            "logic": "Reducimos varianza manteniendo EV positivo"
        })

    # 🟡 Conservadora contextual
    if model_prob > 0.65 and odds.get("home_moneyline", 0) < -250:
        strategies.append({
            "profile": "CONSERVADORA",
            "play": "Doble oportunidad favorito + Under 3.5",
            "logic": "Dominio esperado + baja producción de goles"
        })

    return strategies
