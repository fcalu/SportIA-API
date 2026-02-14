def build_prompt(match, odds, decisions, quant_summary):
    
    if not decisions:
        return f"""
Eres un analista cuantitativo profesional.

PARTIDO: {match}

El modelo probabilístico no detecta ventaja estadística.
Recomendación: NO APOSTAR.

Explica brevemente por qué no existe edge relevante.
"""

    decision_text = "\n".join([
        f"- {d.get('profile')}: {d.get('play')} ({d.get('logic')})"
        for d in decisions
    ])

    totals = quant_summary.get("totals", {})
    moneyline = quant_summary.get("moneyline", {})
    btts = quant_summary.get("btts", {})
    double_chance = quant_summary.get("double_chance", {})

    return f"""
Eres un ANALISTA CUANTITATIVO.

PROHIBIDO:
- Inventar estadísticas
- Inventar probabilidades
- Inventar cuotas
- Usar números distintos a los proporcionados
- Usar estructura fija repetitiva

PARTIDO: {match}

DATOS DEL MODELO:

TOTAL GOALS:
Línea: {totals.get("line")}
Prob OVER: {totals.get("model_over")}
Prob UNDER: {totals.get("model_under")}
Prob Mercado UNDER: {totals.get("market_under")}
Edge UNDER: {totals.get("edge_under")}

MONEYLINE:
Local: {moneyline.get("model_home")}
Empate: {moneyline.get("model_draw")}
Visitante: {moneyline.get("model_away")}

DOUBLE CHANCE:
Local o Empate: {double_chance.get("home_or_draw")}
Visitante o Empate: {double_chance.get("away_or_draw")}

BTTS:
Sí: {btts.get("model_yes")}
No: {btts.get("model_no")}

DECISIONES DEL MODELO:
{decision_text}

TAREA:
1. Analiza el panorama completo del partido.
2. Explica dónde existe la mayor discrepancia modelo vs mercado.
3. Menciona totales, 1X2, empate y BTTS aunque no haya valor.
4. Usa únicamente los números proporcionados.
5. No repitas estructuras estándar como "Control de varianza" o "Gestión de riesgo".
6. Redacta como informe cuantitativo, no como tipster narrativo.
"""
