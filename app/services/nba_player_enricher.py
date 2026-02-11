from app.clients.espn_player_stats import get_player_stats


async def enrich_players_with_stats(players):

    enriched = []

    for p in players:

        stats = await get_player_stats(p["id"])

        if not stats:
            continue

        player_model = {
            "id": p["id"],
            "name": p["name"],
            "position": p["position"],
            "role": detect_role(stats),
            "base_minutes": stats["minutes"],
            "usage_rate": stats["usage_rate"],
            "points_per_min": stats["points_per_min"],
            "reb_per_min": stats["reb_per_min"],
            "ast_per_min": stats["ast_per_min"],
            "points_std_dev": stats.get("points_std_dev", 4),
            "reb_std_dev": stats.get("reb_std_dev", 2),
            "ast_std_dev": stats.get("ast_std_dev", 2),
            "form_factor": stats.get("form_factor", 1)
        }

        enriched.append(player_model)

    return enriched


def detect_role(stats):

    if stats["usage_rate"] >= 0.27:
        return "Primary"

    if stats["usage_rate"] >= 0.18:
        return "Secondary"

    return "Bench"
