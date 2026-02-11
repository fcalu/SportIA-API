from app.services.nba_roster_service import get_match_players
from app.services.nba_player_enricher import enrich_players_with_stats
from app.services.nba_prop_builder import build_nba_props_from_roster


async def generate_nba_match_props(
    home_team_id: str,
    away_team_id: str,
    odds: dict,
    player_status: dict
):

    # 1️⃣ Obtener roster real del partido
    match_players = await get_match_players(home_team_id, away_team_id)

    # 2️⃣ Enriquecer con stats reales
    enriched_players = await enrich_players_with_stats(match_players)

    # 3️⃣ Construir props usando tu modelo PRO + Blowout
    props = build_nba_props_from_roster(
        enriched_players,
        player_status,
        odds
    )

    return props
