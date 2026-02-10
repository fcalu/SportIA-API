# app/services/tipster_ai.py

from app.services.llm import run_llm


# ==========================================================
# 🛡️ BLOQUEO DURO DEL MODELO (NO IA LIBRE)
# ==========================================================
def filter_official_props(props):
    """
    Solo permite props aprobadas por el modelo.
    """
    return [
        p for p in props
        if p.get("bet_tier") in ["VALUE_BET", "STRONG_VALUE", "ELITE_VALUE"]
    ]


# ==========================================================
# 🎯 PROMPT CONTROLADO
# ==========================================================
def build_tipster_prompt(game, odds, props):

    top_props = sorted(
        props,
        key=lambda x: x.get("validated_edge", 0),
        reverse=True
    )[:6]

    return f"""
Actúa como un TIPSTER profesional.

REGLAS OBLIGATORIAS:
- SOLO puedes usar los mercados listados abajo.
- NO inventes picks.
- NO cambies líneas.
- Si no hay picks claros, di que no hay valor.

PARTIDO: {game}
SPREAD: {odds.get("spread")}
TOTAL: {odds.get("over_under")}

MERCADOS CON EDGE REAL:
{top_props}

Formato EXACTO:

🔒 PICK PRINCIPAL:
...

⭐ MEJOR PROP:
...

💰 VALUE PLAY:
...

⚠️ PICK ARRIESGADO:
...

🚫 EVITAR:
...
"""


# ==========================================================
# 🧠 TIPSTER AI CONTROLADO
# ==========================================================
async def run_tipster_ai(game, odds, props):

    official_props = filter_official_props(props)

    # 🔒 BLOQUEO TOTAL SI NO HAY EDGE
    if not official_props:
        return (
            "🚫 NO HAY APUESTAS OFICIALES\n\n"
            "El modelo no detecta ventaja estadística suficiente.\n"
            "Evento clasificado como de baja oportunidad de valor.\n"
            "Recomendación profesional: NO APOSTAR."
        )

    prompt = build_tipster_prompt(game, odds, official_props)

    return run_llm(prompt)
