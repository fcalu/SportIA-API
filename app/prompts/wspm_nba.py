def build_prompt(match, odds, players):
    return f"""
Actúa como analista cuantitativo WSPM NBA.
Tu función es PRIORIZAR eficiencia, no opinión.

PARTIDO:
{match}

ODDS REALES:
- Spread visitante: {odds.get("away_spread")}
- Spread local: {odds.get("home_spread")}
- Total puntos: {odds.get("over_under")}
- Moneyline local: {odds.get("home_moneyline")}
- Moneyline visitante: {odds.get("away_moneyline")}

PLAYER PROPS REALES (top confianza):
{players[:6]}

REGLAS:
- NO inventes estadísticas
- NO contradigas total con picks de puntos
- SI total > 230 → prioriza scorers
- SI spread corto → prioriza estrellas
- SOLO usa props con confidence ≥ 70

PROCESO:
1) Identifica favorito por mercado
2) Evalúa ritmo implícito (total)
3) Alinea props al ritmo y spread

FORMATO DE SALIDA OBLIGATORIO:

### PICK GANADOR
Equipo y justificación mercado

### PICK SPREAD O TOTAL
Selección y motivo

### PLAYER PROPS RECOMENDADOS
- Jugador | Mercado | Línea | Confianza
(1–3 máximo)

### RIESGOS
Solo riesgos reales

### CONCLUSIÓN
1 frase ejecutiva
"""
