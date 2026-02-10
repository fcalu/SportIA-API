from app.services.llm import run_llm
import json

def normalize_ai_prop(p):
    if not isinstance(p, dict):
        return None
    return {
        "name": (p.get("name") or p.get("player") or "Unknown"),
        "role": p.get("role", "Secondary"),
        "type": p.get("type", "Passing Yards"),
        "line": p.get("line"),
        "season_avg": p.get("season_avg", 0),
        "is_active": True
    }

def generate_ai_props(match, sport, league, odds, script):
    # Inyectamos contexto real del Super Bowl LX para que la IA no invente
    context_players = ""
    if "Patriots" in match or "Seahawks" in match:
        context_players = """
        Jugadores Clave hoy: 
        Patriots: Drake Maye (QB), Rhamondre Stevenson (RB), Hunter Henry (TE), Kayshon Boutte (WR).
        Seahawks: Sam Darnold (QB), Kenneth Walker III (RB), Jaxon Smith-Njigba (WR), Cooper Kupp (WR).
        """

    prompt = f"""
    Eres un experto en apuestas de la NFL. Genera props realistas para el Super Bowl LX.
    {context_players}
    
    Deporte: {sport}
    Partido: {match}
    Total O/U: {odds.get("over_under")}
    Spread: {odds.get("spread")}
    Script: {script}

    Genera al menos 6 props (3 por equipo) combinando Passing Yards, Rushing Yards y Receptions.
    Usa los nombres EXACTOS de los jugadores.

    Devuelve SOLAMENTE un JSON válido:
    [
      {{
        "name": "Drake Maye",
        "role": "Star",
        "type": "Passing Yards",
        "line": 245.5,
        "season_avg": 258.5
      }},
      {{
        "name": "Jaxon Smith-Njigba",
        "role": "Star",
        "type": "Receiving Yards",
        "line": 82.5,
        "season_avg": 95.0
      }}
    ]
    """

    try:
        raw = run_llm(prompt)
        # Limpiar posibles marcas de markdown del LLM
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        if not isinstance(data, list):
            return []

        clean = []
        for p in data:
            norm = normalize_ai_prop(p)
            if norm:
                clean.append(norm)
        return clean

    except Exception as e:
        print("LLM PROP ERROR:", e)
        return []