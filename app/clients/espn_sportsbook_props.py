import httpx
import asyncio

BASE_CORE = "https://sports.core.api.espn.com/v2/sports"

# Mercados normalizados para NBA y NFL
NBA_MARKETS_MAP = {
    "points": "Points",
    "rebounds": "Rebounds",
    "assists": "Assists",
    "three point field goals made": "Three_Pointers_Made",
    "3-pointers made": "Three_Pointers_Made"
}

async def fetch_json(url):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            if r.status_code == 200:
                return r.json()
            return {}
        except Exception as e:
            print(f"⚠️ Error fetching ESPN data: {e}")
            return {}

async def get_sportsbook_player_props(sport, league, event_id):
    """
    Trae los props de DraftKings (Provider 100) desde el endpoint propBets de ESPN Core v2.
    """
    props_url = (
        f"{BASE_CORE}/{sport}/leagues/{league}/events/{event_id}"
        f"/competitions/{event_id}/odds/100/propBets?limit=150"
    )

    data = await fetch_json(props_url)
    results = []
    items = data.get("items", [])
    
    if not items:
        print(f"⚠️ No se encontraron propBets para el evento {event_id}")

    for item in items:
        # 1. Identificar el tipo de apuesta y normalizarlo
        display_name = item.get("displayValue", "").lower()
        
        prop_type = None
        for key, value in NBA_MARKETS_MAP.items():
            if key in display_name:
                prop_type = value
                break
        
        if not prop_type:
            continue

        # 2. Obtener el Atleta
        athlete_ref = item.get("athlete", {}).get("$ref", "")
        if not athlete_ref:
            continue
        
        # Obtenemos nombre del atleta (puedes cachear esto en el futuro para más velocidad)
        athlete_data = await fetch_json(athlete_ref)
        player_name = athlete_data.get("displayName")
        
        if not player_name:
            continue

        # 3. Obtener la Línea (Target Value)
        # En el JSON de ESPN v2, a veces viene como 'value' directo en el item
        line = item.get("value")
        
        # 4. Extraer Momios de los Choices
        over_odds = -110
        under_odds = -110
        
        choices = item.get("choices", [])
        for choice in choices:
            # Buscamos 'Over' o 'Under' en el texto o abreviatura
            choice_text = choice.get("text", "").lower()
            choice_short = choice.get("shortDisplayValue", "").upper()
            
            american_odds = choice.get("odds", {}).get("american", -110)
            
            if choice_short == "O" or "over" in choice_text:
                over_odds = american_odds
                # Si la línea no estaba en el nivel superior, a veces está aquí
                if line is None: line = choice.get("value")
            elif choice_short == "U" or "under" in choice_text:
                under_odds = american_odds

        if line is not None:
            results.append({
                "name": player_name,
                "type": prop_type,
                "line": float(line),
                "over_odds": int(over_odds),
                "under_odds": int(under_odds),
                "source": "DraftKings"
            })

    print(f"✅ Se capturaron {len(results)} líneas reales de DraftKings")
    return results