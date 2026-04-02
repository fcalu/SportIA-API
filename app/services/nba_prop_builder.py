# ==========================================================
# 🏀 NBA PROP BUILDER — FULL ENGINE 2026 (MULTI-MARKET)
# ==========================================================

def build_nba_props_from_roster(players, player_status, odds=None):
    props = []

    # 1. FILTRO DE STATUS — SOLO JUGADORES QUE VAN A JUGAR
    SAFE_STATUSES = {"ACTIVE", "PROBABLE", "QUESTIONABLE"} # Incluimos questionable para análisis previo
    inactive_ids = []

    for pid, status in player_status.items():
        if not status:
            inactive_ids.append(pid)
            continue
        
        normalized_status = str(status).strip().upper()
        if normalized_status not in SAFE_STATUSES:
            inactive_ids.append(pid)

    # 2. CALCULAR RECURSOS LIBERADOS (POR LESIONES)
    freed_minutes, freed_usage, freed_rebounds, freed_assists = \
        calculate_freed_resources(players, inactive_ids)

    spread = abs(float(odds.get("spread", 0))) if odds else 0

    # 3. LOOP PRINCIPAL DE GENERACIÓN
    for p in players:
        if "id" not in p or p["id"] in inactive_ids:
            continue

        # --- REDISTRIBUCIÓN DE MINUTOS ---
        minute_boost = redistribute_minutes(p, inactive_ids, players)
        minutes_projection = min(42.0, p.get("base_minutes", 20) + minute_boost)

        # Filtro de seguridad para evitar jugadores irrelevantes (Garbage time puro)
        if minutes_projection < 12:
            continue

        # --- REDISTRIBUCIÓN DE ESTADÍSTICAS (USAGE/REB/AST) ---
        usage_boost = redistribute_usage(p, freed_usage, players, inactive_ids)
        rebound_boost = redistribute_rebounds(p, freed_rebounds)
        assist_boost = redistribute_assists(p, freed_assists)

        # Ratios ajustados por forma y bajas
        adj_points_rate = p.get("points_per_min", 0.4) * (1 + usage_boost) * p.get("form_factor", 1)
        adj_reb_rate = p.get("reb_per_min", 0.2) * (1 + rebound_boost)
        adj_ast_rate = p.get("ast_per_min", 0.1) * (1 + assist_boost)
        adj_3pt_rate = p.get("three_per_min", 0.05) # Asumiendo que tienes este dato

        # --- AJUSTE POR PALIZA (BLOWOUT) ---
        if spread >= 15:
            adj_factor = 0.82 if spread >= 20 else 0.88
            if p.get("role") == "Primary":
                minutes_projection *= adj_factor
            else:
                minutes_projection *= 1.12 # Los suplentes juegan más

        # ==========================================
        # 🎯 GENERACIÓN DE MERCADOS (SIN RESTRICCIÓN)
        # ==========================================

        # A. PUNTOS
        props.append(build_prop(p, "Points", adj_points_rate * minutes_projection, 
                               minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate, spread))

        # B. REBOTES
        props.append(build_prop(p, "Rebounds", adj_reb_rate * minutes_projection, 
                               minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate, spread))

        # C. ASISTENCIAS
        props.append(build_prop(p, "Assists", adj_ast_rate * minutes_projection, 
                               minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate, spread))

        # D. TRIPLES (Solo si el jugador es tirador activo)
        if adj_3pt_rate > 0.03:
            props.append(build_prop(p, "Three_Pointers_Made", adj_3pt_rate * minutes_projection, 
                                   minutes_projection, adj_points_rate, adj_reb_rate, adj_ast_rate, spread))

    # ORDENAR POR RELEVANCIA (Minutos) Y LIMITAR
    props.sort(key=lambda x: x["projected_minutes"], reverse=True)
    
    return props[:45] # Retornamos suficientes para cubrir ambos equipos


# ==========================================
# FUNCIONES DE APOYO (LÓGICA INTERNA)
# ==========================================

def calculate_freed_resources(players, inactive_ids):
    f_min = f_usg = f_reb = f_ast = 0
    for p in players:
        if p["id"] in inactive_ids:
            f_min += p.get("base_minutes", 25)
            f_usg += p.get("usage_rate", 0.20)
            f_reb += p.get("reb_per_min", 0.2) * p.get("base_minutes", 25)
            f_ast += p.get("ast_per_min", 0.1) * p.get("base_minutes", 25)
    return f_min, f_usg, f_reb, f_ast

def redistribute_minutes(player, inactive_ids, players):
    boost = 0
    active_in_pos = [p for p in players if p["position"] == player["position"] and p["id"] not in inactive_ids]
    for p in players:
        if p["id"] in inactive_ids and p["position"] == player["position"]:
            share = 1.0 / len(active_in_pos) if active_in_pos else 0.4
            boost += p.get("base_minutes", 25) * share
    return boost

def redistribute_usage(player, freed_usage, players, inactive_ids):
    active_primaries = [p for p in players if p.get("role") == "Primary" and p["id"] not in inactive_ids]
    if player.get("role") == "Primary":
        return freed_usage / len(active_primaries) if active_primaries else freed_usage * 0.4
    return freed_usage * 0.10

def redistribute_rebounds(player, freed_rebounds):
    # Centros y Aleros capturan la mayoría de rebotes liberados
    factor = 0.35 if player["position"] in ["C", "PF"] else 0.10
    return (freed_rebounds * factor) / 10

def redistribute_assists(player, freed_assists):
    # Bases y Escoltas distribuyen el juego liberado
    factor = 0.40 if player["position"] in ["PG", "SG"] else 0.08
    return (freed_assists * factor) / 10

# ==========================================
# CREADOR DE OBJETO PROP FINAL
# ==========================================

def build_prop(player, prop_type, projection, min_proj, pts_r, reb_r, ast_r, spread):
    # Definir volatilidad (Std Dev) según el tipo de mercado
    if prop_type == "Points":
        base_std = player.get("points_std_dev", projection * 0.24)
    elif prop_type == "Rebounds":
        base_std = player.get("reb_std_dev", projection * 0.28)
    elif prop_type == "Assists":
        base_std = player.get("ast_std_dev", projection * 0.35)
    elif prop_type == "Three_Pointers_Made":
        base_std = projection * 0.45 # Mayor varianza en triples
    else:
        base_std = projection * 0.25

    # Ajuste por minutos (A menos minutos, más varianza relativa)
    minutes_factor = max(0.10, 1 - (min_proj / 48))
    adjusted_std = base_std * (1 + (minutes_factor * 0.5))

    return {
        "name": player["name"],
        "player_id": player["id"],
        "position": player["position"],
        "role": player.get("role", "Secondary"),
        "type": prop_type,
        "projection_model": {
            "mean": round(max(0, projection), 2),
            "std_dev": round(max(0.1, adjusted_std), 2)
        },
        "projected_minutes": round(min_proj, 2),
        "usage_rate": player.get("usage_rate", 0),
        "points_per_min": round(pts_r, 3),
        "reb_per_min": round(reb_r, 3),
        "ast_per_min": round(ast_r, 3),
        "is_active": True
    }