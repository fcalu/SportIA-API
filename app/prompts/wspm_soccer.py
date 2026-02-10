def build_prompt(match, odds, decisions):
    
    if not decisions:
        return f"""
Eres un analista cuantitativo.

PARTIDO: {match}

El modelo probabilístico no detecta ventaja estadística.
La recomendación profesional es NO APOSTAR.
"""

    decision_text = "\n".join([
        f"""
PERFIL: {d.get("profile")}
JUGADA: {d.get("play")}
RAZÓN DEL MODELO: {d.get("logic")}
"""
        for d in decisions
    ])

    return f"""
Eres un ANALISTA CUANTITATIVO.

PROHIBIDO:
- Inventar estadísticas
- Inventar cuotas
- Inventar historiales
- Usar narrativa subjetiva

PARTIDO: {match}

MERCADO REAL:
Spread: {odds.get("spread")}
Total: {odds.get("over_under")}
ML Local: {odds.get("home_moneyline")}
ML Visitante: {odds.get("away_moneyline")}

DECISIONES DEL MODELO:
{decision_text}

TAREA:
Explica estas jugadas únicamente desde:
- Diferencia entre probabilidad modelo vs mercado
- Control de varianza
- Expectativa matemática
- Gestión de riesgo

No agregues contexto histórico ni análisis futbolístico.
"""
