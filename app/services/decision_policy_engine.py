def tipster_decision_policy(props, odds):
    
    # Filtrar solo apuestas válidas
    valid_props = [
        p for p in props
        if p.get("bet_decision") != "PASS"
    ]

    if not valid_props:
        return []

    # Calcular edge máximo por prop
    for p in valid_props:
        p["max_edge"] = max(
            p.get("edge_over", 0),
            p.get("edge_under", 0)
        )

    # Ordenar por edge descendente
    valid_props.sort(key=lambda x: x["max_edge"], reverse=True)

    # Obtener máximo edge del evento
    max_event_edge = valid_props[0]["max_edge"]

    strategies = []

    for idx, prop in enumerate(valid_props):

        label = prop.get("name")
        decision = prop.get("bet_decision")
        line = prop.get("line")
        edge = prop["max_edge"]

        # Percentil relativo
        relative_strength = edge / max_event_edge if max_event_edge > 0 else 0

        # 🔥 Top 20% del evento
        if relative_strength >= 0.8:
            profile = "AGRESIVA"

        # 🟢 50%–80%
        elif 0.5 <= relative_strength < 0.8:
            profile = "BALANCEADA"

        # 🟡 Resto positivo
        else:
            profile = "CONSERVADORA"

        strategies.append({
            "profile": profile,
            "play": f"{label} → {decision} {line}",
            "logic": f"Edge relativo {round(relative_strength,2)} vs mejor pick del evento"
        })

    return strategies
