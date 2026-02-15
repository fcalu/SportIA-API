from app.db.session import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from datetime import datetime


def save_prediction(event_payload, prediction_response):

    db = SessionLocal()

    try:
        # 1️⃣ Buscar o crear Match
        match = db.query(Match).filter(
            Match.event_id == event_payload["event_id"]
        ).first()

        if not match:
            match = Match(
                event_id=event_payload["event_id"],
                league=event_payload["league"],
                home_team=event_payload["home_team"],
                away_team=event_payload["away_team"],
                start_time=datetime.utcnow()
            )
            db.add(match)
            db.commit()
            db.refresh(match)

        # 2️⃣ Guardar mercados
        for market in prediction_response.get("player_props", []):

            pred = Prediction(
                match_id=match.id,
                market_type=market.get("type"),
                model_prob_home=market.get("model_prob_home"),
                model_prob_draw=market.get("model_prob_draw"),
                model_prob_away=market.get("model_prob_away"),
                model_prob_over=market.get("model_prob_over"),
                model_prob_under=market.get("model_prob_under"),
                edge=market.get("max_edge") or market.get("edge_over") or 0,
                decision=market.get("bet_decision")
            )

            db.add(pred)

        db.commit()

    except Exception as e:
        db.rollback()
        print("Error guardando predicción:", e)

    finally:
        db.close()
