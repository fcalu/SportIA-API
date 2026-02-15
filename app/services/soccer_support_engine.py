def calculate_over_support(model_prob, home_history, away_history):
    
    # Histórico basado en la línea real
    historical = (
        home_history["over_rate_line"] +
        away_history["over_rate_line"]
    ) / 2

    # Peso 70% modelo, 30% historia
    hybrid = (model_prob * 0.7) + (historical * 0.3)

    return round(hybrid, 4)
