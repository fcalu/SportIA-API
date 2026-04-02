import httpx
import asyncio

BASE_CORE = "https://sports.core.api.espn.com/v2/sports"

async def fetch_json(url):
    async with httpx.AsyncClient(timeout=12) as client:
        try:
            r = await client.get(url)
            return r.json() if r.status_code == 200 else {}
        except:
            return {}

async def get_sportsbook_player_props(sport, league, event_id):
    """
    Versión Optimizada para la estructura real de ESPN Core v2
    """
    props_url = f"{BASE_CORE}/{sport}/leagues/{league}/events/{event_id}/competitions/{event_id}/odds/100/propBets?limit=200"
    
    data = await fetch_json(props_url)
    items = data.get("items", [])
    results = []

    for item in items:
        # 1. Mapeo de Mercados (Normalización)
        raw_name = item.get("type", {}).get("name", "")
        
        # Detectamos el mercado según el nombre de ESPN
        prop_type = None
        if "Points" in raw_name: prop_type = "Points"
        elif "Rebounds" in raw_name: prop_type = "Rebounds"
        elif "Assists" in raw_name: prop_type = "Assists"
        elif "Three Point" in raw_name: prop_type = "Three_Pointers_Made"
        
        if not prop_type: continue

        # 2. Extraer la LÍNEA (Target) - Según tu JSON está en odds -> total -> value
        line = item.get("odds", {}).get("total", {}).get("value")
        if line is None:
            # Respaldo por si viene en 'current'
            line = item.get("current", {}).get("target", {}).get("value")
        
        if line is None: continue

        # 3. Extraer Momio (American Odds)
        american_odds = item.get("odds", {}).get("american", {}).get("value", "-110")
        # Limpiamos el '+' si viene como string
        try:
            american_odds = int(str(american_odds).replace('+', ''))
        except:
            american_odds = -110

        # 4. Obtener Atleta ( displayName )
        athlete_ref = item.get("athlete", {}).get("$ref")
        if not athlete_ref: continue
        
        athlete_info = await fetch_json(athlete_ref)
        player_name = athlete_info.get("displayName")

        if player_name and line:
            results.append({
                "name": player_name,
                "type": prop_type,
                "line": float(line),
                "over_odds": american_odds, # ESPN los separa en items distintos (Over/Under)
                "under_odds": american_odds,
                "source": "DraftKings"
            })

    print(f"✅ DraftKings: {len(results)} props procesados correctamente.")
    return results