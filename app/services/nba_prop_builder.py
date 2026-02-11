# ==========================================
# 🏀 NBA PROP BUILDER — VERSIÓN PRO 2026
# ==========================================

def build_nba_props_from_roster(players, player_status):
    props = []
    
    # IDs de los que NO juegan (Lesionados/Cortados)
    inactive_ids = [pid for pid, st in player_status.items() if st != "ACTIVE"]

    # Calculamos recursos totales que quedan "en el aire"
    freed_minutes, freed_usage, freed_rebounds, freed_assists = \
        calculate_freed_resources(players, inactive_ids)

    for p in players:
        if "id" not in p or p["id"] in inactive_ids:
            continue

        # 1. REDISTRIBUCIÓN DINÁMICA DE MINUTOS
        # Buscamos cuántos sanos hay en su misma posición para repartir
        minute_boost = redistribute_minutes(p, inactive_ids, players)
        
        # Aplicamos un Hard Cap de 40 minutos (máximo físico real en NBA)
        minutes_projection = min(40.0, p["base_minutes"] + minute_boost)

        # 🔥 FILTRO DE ROTACIÓN: Si no llega a 15 mins proyectados, no es viable para apostar
        if minutes_projection < 15:
            continue

        # 2. REDISTRIBUCIÓN DE USAGE (PUNTOS)
        # El usage_boost ahora es más agresivo para los "Primary"
        usage_boost = redistribute_usage(p, freed_usage, players, inactive_ids)
        
        # 3. REDISTRIBUCIÓN DE REBOTES Y ASISTENCIAS
        rebound_boost = redistribute_rebounds(p, freed_rebounds)
        assist_boost = redistribute_assists(p, freed_assists)

        # Aplicamos los multiplicadores a las tasas por minuto
        adj_points_rate = p["points_per_min"] * (1 + usage_boost) * p.get("form_factor", 1)
        adj_reb_rate = p["reb_per_min"] * (1 + rebound_boost)
        adj_ast_rate = p["ast_per_min"] * (1 + assist_boost)

        # 4. CONSTRUCCIÓN DE PROPS SEGÚN PERFIL
        # Guardias: Priorizamos Puntos y Asistencias
        if p["position"] in ["PG", "SG"]:
            props.append(build_prop(p, "Points", adj_points_rate * minutes_projection, minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate))
            props.append(build_prop(p, "Assists", adj_ast_rate * minutes_projection, minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate))
        
        # Forwards/Centers: Priorizamos Puntos y Rebotes
        else:
            props.append(build_prop(p, "Points", adj_points_rate * minutes_projection, minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate))
            props.append(build_prop(p, "Rebounds", adj_reb_rate * minutes_projection, minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate))

    # Retornamos los mejores 16 props (Top 8 jugadores x 2 props cada uno)
    return props[:16]


# ==========================================
# 🔄 LÓGICA DE REDISTRIBUCIÓN AVANZADA
# ==========================================

def calculate_freed_resources(players, inactive_ids):
    f_min = f_usg = f_reb = f_ast = 0
    for p in players:
        if p["id"] in inactive_ids:
            f_min += p["base_minutes"]
            f_usg += p["usage_rate"]
            f_reb += (p["reb_per_min"] * p["base_minutes"])
            f_ast += (p["ast_per_min"] * p["base_minutes"])
    return f_min, f_usg, f_reb, f_ast

def redistribute_minutes(player, inactive_ids, players):
    """Reparte minutos solo entre jugadores de la misma posición."""
    boost = 0
    active_in_pos = [p for p in players if p["position"] == player["position"] and p["id"] not in inactive_ids]
    
    for p in players:
        if p["id"] in inactive_ids and p["position"] == player["position"]:
            # Si eres el único sano en esa posición, te llevas más carga
            share = 1.0 / len(active_in_pos) if active_in_pos else 0.4
            boost += p["base_minutes"] * share
    return boost

def redistribute_usage(player, freed_usage, players, inactive_ids):
    """
    Si falta una estrella, los otros 'Primary' suben mucho más.
    Efecto Egor Demin: Si falta Cam Thomas, Demin absorbe el 40-50% del uso.
    """
    active_primaries = [p for p in players if p["role"] == "Primary" and p["id"] not in inactive_ids]
    
    if player["role"] == "Primary":
        # Se reparte el pastel entre los líderes sanos
        return (freed_usage / len(active_primaries)) if active_primaries else freed_usage * 0.4
    
    if player["role"] == "Secondary":
        return freed_usage * 0.15 # Los reservas solo suben un poco
    
    return freed_usage * 0.05

def redistribute_rebounds(player, freed_rebounds):
    if player["position"] in ["C", "PF"]:
        return (freed_rebounds * 0.30) / 10 # Factor de normalización para rate
    return (freed_rebounds * 0.10) / 10

def redistribute_assists(player, freed_assists):
    if player["position"] in ["PG", "SG"]:
        return (freed_assists * 0.35) / 10
    return (freed_assists * 0.10) / 10


# ==========================================
# 🧠 GENERADOR DE OBJETO PROP
# ==========================================

def build_prop(player, prop_type, projection, min_proj, pts_r, reb_r, ast_r):
    return {
        "name": player["name"],
        "player_id": player["id"],
        "position": player["position"],
        "role": player["role"],
        "type": prop_type,
        "projection_model": {
            "mean": round(projection, 2),
            "std_dev": round(player.get("points_std_dev", projection * 0.18), 2)
        },
        "projected_minutes": round(min_proj, 2),
        "usage_rate": player["usage_rate"],
        "points_per_min": round(pts_r, 3),
        "reb_per_min": round(reb_r, 3),
        "ast_per_min": round(ast_r, 3),
        "is_active": True
    }