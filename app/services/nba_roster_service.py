from app.clients.espn_nba_roster_live import get_team_roster


async def get_match_players(home_team_id: str, away_team_id: str):

    home_players = await get_team_roster(home_team_id)
    away_players = await get_team_roster(away_team_id)

    return home_players + away_players
