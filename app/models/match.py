from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.base_model import BaseModel

class Match(BaseModel):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    league = Column(String, index=True)
    home_team = Column(String)
    away_team = Column(String)
    start_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
