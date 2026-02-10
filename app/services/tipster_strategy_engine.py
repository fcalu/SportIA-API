def build_tipster_strategy(prop, odds):
    
    label = prop.get("name") or prop.get("title") or prop.get("player_name") or "Market"

    model_data = prop.get("projection_model", {})
    mean = model_data.get("mean", 0)

    model_under = prop.get("model_prob_under", 0)
    edge = max(prop.get("edge_over", 0), prop.get("edge_under", 0))
    decision = prop.get("bet_decision", "PASS")
    line = prop.get("line", "")

    strategies = []

    # 🔥 Caso 1: Edge fuerte
    if edge >= 0.12:
        strategies.append({
            "type": "PRIMARY",
            "market": f"{label} {decision} {line}",
            "reason": "Ventaja estadística clara detectada por modelo"
        })

    # 🔥 Caso 2: Edge medio
    elif 0.06 <= edge < 0.12:
        safer_line = line + 1 if decision == "UNDER" else line - 1
        strategies.append({
            "type": "SAFER_LINE",
            "market": f"{decision} {safer_line}",
            "reason": "Reducimos varianza manteniendo expectativa favorable"
        })

    # 🔥 Caso 3: Combinación
    if model_under > 0.60 and odds.get("home_moneyline", 0) < -250:
        strategies.append({
            "type": "COMBO",
            "market": "Doble oportunidad local + Under 3.5",
            "reason": "Modelo indica partido controlado con dominio local"
        })

    return strategies
