import httpx
import asyncio
import time
from datetime import datetime, timedelta

BASE = "https://site.api.espn.com/apis/site/v2/sports"

# Cache en memoria para evitar saturar ESPN
_CACHE = {}
CACHE_TTL = 600 # 10 minutos

SPORT_PATHS = {
   "soccer": [
    "soccer/eng.1", "soccer/eng.2", "soccer/esp.1", "soccer/ger.1",
    "soccer/ita.1", "soccer/fra.1", "soccer/usa.1", "soccer/uefa.europa.conf",
    "soccer/uefa.champions", "soccer/uefa.europa", "soccer/mex.1",
    "soccer/ned.1", "soccer/por.1", "soccer/conmebol.libertadores", 
    "soccer/fifa.friendly", "soccer/fifa.worldq.uefa","soccer/fifa.wcq.ply",
],
    "nba": ["basketball/nba"],
    "nfl": ["football/nfl"],
}

# Reducido a 3 días para evitar exceso de datos
def _get_date_range(days=4):
    today = datetime.utcnow().date()
    end = today + timedelta(days=days-1)
    return f"{today.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

async def get_scoreboard(path: str, sport: str):
    cache_key = f"{path}_{sport}"
    now = time.time()

    # 1. Retornar cache si existe y es joven
    if cache_key in _CACHE:
        timestamp, data = _CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            return data

    # 2. Configurar URL con el nuevo rango de 3 días
    url = f"{BASE}/{path}/scoreboard"
    date_range = _get_date_range(days=4)
    url += f"?dates={date_range}"

    async with httpx.AsyncClient(timeout=15) as c:
        try:
            r = await c.get(url)
            r.raise_for_status()
            data = r.json()
            # Guardar en cache
            _CACHE[cache_key] = (now, data)
            return data
        except Exception as e:
            print(f"Error cargando {path}: {e}")
            # Si falla pero hay cache vieja, usarla
            if cache_key in _CACHE: return _CACHE[cache_key][1]
            return {"events": []}

async def upcoming_matches(sport: str):
    paths = SPORT_PATHS.get(sport, [])
    
    # EJECUCIÓN EN PARALELO: Esto es mucho más rápido que el for loop
    tasks = [get_scoreboard(path, sport) for path in paths]
    results = await asyncio.gather(*tasks)

    events = []
    # Procesar resultados
    for i, data in enumerate(results):
        current_path = paths[i]
        for e in data.get("events", []):
            if e.get("status", {}).get("type", {}).get("state") == "pre":
                try:
                    comp = e["competitions"][0]["competitors"]
                    h = next(x for x in comp if x["homeAway"]=="home")
                    a = next(x for x in comp if x["homeAway"]=="away")
                    
                    events.append({
                        "sport": sport,
                        "league": current_path.split('/')[-1].upper(), # Simplifica el nombre de la liga
                        "event_id": e["id"],
                        "home": h["team"]["displayName"],
                        "home_logo": h["team"].get("logo"),
                        "away": a["team"]["displayName"],
                        "away_logo": a["team"].get("logo"),
                        "start_time": e["date"]
                    })
                except (KeyError, StopIteration):
                    continue

    # Ordenar por fecha (más cercanos primero)
    events.sort(key=lambda x: x["start_time"])

    # Fallback si no hay partidos
    if not events:
        return []
        
    return events