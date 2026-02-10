from pydantic import BaseModel
from typing import Optional, Dict, Any

class PredictionRequest(BaseModel):
    sport: str
    market: str
    home_team: str
    away_team: str
    odds: Optional[float] = None

class PredictionResponse(BaseModel):
    event: Dict[str, Any]
    market: str
    probability: Dict[str, float]
    ev: Optional[float]
    recommendation: str
    risk: str
    explanation: str
