from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base_model import BaseModel


class Prediction(BaseModel):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(Integer, ForeignKey("matches.id"))
    market_type = Column(String)

    # 📊 Probabilidades modelo
    model_prob_home = Column(Float)
    model_prob_draw = Column(Float)
    model_prob_away = Column(Float)
    model_prob_over = Column(Float)
    model_prob_under = Column(Float)

    # 💰 Edge y decisión
    edge = Column(Float)
    decision = Column(String)

    # 🧾 NUEVO: tracking real
    result = Column(String, nullable=True)  # WIN / LOSS / PUSH
    stake = Column(Float, default=1.0)
    profit = Column(Float, nullable=True)
    settled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match")
