def tipster_decision_policy(props, odds):
    
    # 🔒 Validación defensiva
    if not isinstance(props, list):
        return []

    # Filtrar solo apuestas válidas
    valid_props = [
        p for p in props
        if isinstance(p, dict) and p.get("bet_decision") != "PASS"
    ]

    if not valid_props:
        return []

    # Calcular edge máximo por prop
    for p in valid_props:
        p["max_edge"] = max(
            p.get("edge_over", 0) or 0,
            p.get("edge_under", 0) or 0
        )

    # Ordenar por edge descendente
    valid_props.sort(key=lambda x: x["max_edge"], reverse=True)

    max_event_edge = valid_props[0]["max_edge"] or 0

    strategies = []

    for prop in valid_props:

        label = prop.get("name", "Market")
        decision = prop.get("bet_decision", "")
        line = prop.get("line", "")
        edge = prop.get("max_edge", 0)

        if max_event_edge > 0:
            relative_strength = edge / max_event_edge
        else:
            relative_strength = 0

        if relative_strength >= 0.8:
            profile = "AGRESIVA"
        elif 0.5 <= relative_strength < 0.8:
            profile = "BALANCEADA"
        else:
            profile = "CONSERVADORA"

        strategies.append({
            "profile": profile,
            "play": f"{label} → {decision} {line}",
            "logic": f"Edge relativo {round(relative_strength,2)} vs mejor pick del evento"
        })

    return strategies
