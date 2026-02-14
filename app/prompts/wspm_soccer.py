def build_prompt(match, odds, decisions, quant_summary):
    
    if not decisions:
        return f"""
Eres un analista cuantitativo profesional.

PARTIDO: {match}

El modelo no detecta discrepancias relevantes entre probabilidades modelo y mercado.
Conclusión: No existe edge estadísticamente significativo.
Explica brevemente por qué el evento se considera eficiente.
"""

    decision_text = "\n".join([
        f"- {d.get('profile')}: {d.get('play')} ({d.get('logic')})"
        for d in decisions
    ])

    totals = quant_summary.get("totals", {})
    moneyline = quant_summary.get("moneyline", {})
    btts = quant_summary.get("btts", {})
    xg = quant_summary.get("xg", {})

    return f"""
Eres un ANALISTA CUANTITATIVO PROFESIONAL.

PROHIBIDO:
- Inventar estadísticas
- Inventar probabilidades
- Inventar cuotas
- Usar números distintos a los proporcionados
- Usar narrativa subjetiva futbolística
- Repetir estructuras estándar como "control de varianza"

PARTIDO: {match}

DATOS DEL MODELO:

XG:
Home xG: {xg.get("home_xg")}
Away xG: {xg.get("away_xg")}
Total xG: {xg.get("total_xg")}

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

BTTS:
Sí: {btts.get("model_yes")}
No: {btts.get("model_no")}

DECISIONES DEL MODELO:
{decision_text}

TAREA:

1. Analiza el panorama completo del partido utilizando los datos anteriores.
2. Identifica explícitamente cuál es el mercado con mayor discrepancia modelo vs mercado.
3. Explica la coherencia entre xG proyectado y probabilidades derivadas.
4. Menciona totales, 1X2, empate y BTTS aunque no haya valor.
5. Usa únicamente los números proporcionados.
6. Redacta como informe cuantitativo institucional.
"""
