from pydantic import BaseModel

class AIPredictRequest(BaseModel):
    sport: str                 # "football" | "basketball" | "soccer"
    league: str                # "football/nfl" | "basketball/nba" | "soccer/uefa.europa"
    event_id: str              # ESPN EVENT ID (OBLIGATORIO)
    home_team: str
    away_team: str
