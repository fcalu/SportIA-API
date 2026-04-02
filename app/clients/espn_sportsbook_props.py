import httpx
import asyncio

BASE_CORE = "https://sports.core.api.espn.com/v2/sports"

NFL_MARKETS = ["Passing Yards", "Passing Touchdowns", "Rushing Yards", "Receiving Yards", "Receptions"]
# He ajustado estos para que hagan match exacto con el JSON de ESPN
NBA_MARKETS = ["Points", "Rebounds", "Assists", "Three Point Field Goals Made", "Total Points", "Total Rebounds", "Total Assists"]

async def fetch_json(url):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
        except:
            return {}

async def get_sportsbook_player_props(sport, league, event_id):
    """
    Trae los props de DraftKings (Provider 100) y los formatea para el Predictor
    """
    # URL que descubrimos en el JSON anterior
    props_url = (
        f"{BASE_CORE}/{sport}/leagues/{league}/events/{event_id}"
        f"/competitions/{event_id}/odds/100/propBets?limit=100"
    )

    data = await fetch_json(props_url)
    results = []
    
    # Extraemos los items de la respuesta
    items = data.get("items", [])
    
    # Para no saturar con peticiones a la API de atletas, intentaremos extraer 
    # la info básica y solo pediremos el nombre si es estrictamente necesario.
    for item in items:
        # 1. Identificar el tipo de apuesta
        # ESPN a veces lo manda en item['type']['name'] o item['displayValue']
        raw_prop_type = item.get("displayValue") or item.get("type", {}).get("name", "")
        
        # Normalización rápida para el Predictor
        prop_type = "Points" if "Points" in raw_prop_type else \
                    "Rebounds" if "Rebounds" in raw_prop_type else \
                    "Assists" if "Assists" in raw_prop_type else \
                    "Three_Pointers_Made" if "Three Point" in raw_prop_type or "3-Pointers" in raw_prop_type else \
                    raw_prop_type

        # 2. Filtrar por deporte
        if sport == "basketball" and not any(m in raw_prop_type for m in ["Points", "Rebounds", "Assists", "Three Point"]):
            continue

        # 3. Obtener el Atleta (Usamos una técnica rápida para el nombre)
        athlete_ref = item.get("athlete", {}).get("$ref", "")
        if not athlete_ref:
            continue
        
        # Obtenemos info del atleta
        athlete_data = await fetch_json(athlete_ref)
        name = athlete_data.get("displayName", "Unknown Player")

        # 4. Obtener la Línea (Target Value)
        # En el JSON de la v2 suele estar en item['value']
        line = item.get("value")
        
        # 5. Obtener Momios (Odds)
        # Buscamos en las elecciones (choices) del Over/Under
        over_odds = -110
        under_odds = -110
        
        choices = item.get("choices", [])
        for choice in choices:
            if choice.get("shortDisplayValue") == "O":
                over_odds = choice.get("odds", {}).get("american", -110)
            elif choice.get("shortDisplayValue") == "U":
                under_odds = choice.get("odds", {}).get("american", -110)

        if line is not None:
            results.append({
                "name": name,
                "type": prop_type,
                "line": float(line),
                "over_odds": int(over_odds),
                "under_odds": int(under_odds),
                "source": "DraftKings"
            })

    return results