from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.clients.espn import upcoming_matches
from app.schemas.predict import AIPredictRequest
from app.services.predictor import ai_predict

from app.db.session import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from app.clients.espn_scoreboard import get_event_result
from app.services.result_evaluator import evaluate_prediction


router = APIRouter()


# =====================================================
# EXISTENTE
# =====================================================

@router.get("/matches/upcoming")
async def matches_upcoming(sport: str):
    return await upcoming_matches(sport)


@router.post("/ai/predict")
async def predict(req: AIPredictRequest):
    try:
        return await ai_predict(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================
# 🔥 SETTLE AUTOMÁTICO (ESPN)
# =====================================================

@router.post("/settle-matches")
async def settle_matches():

    db: Session = SessionLocal()
    settled_count = 0

    matches = db.query(Match).all()

    for match in matches:

        result = await get_event_result(
            match.league.split("/")[-1],
            match.event_id
        )

        if not result or not result.get("completed"):
            continue

        predictions = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.result == None
        ).all()

        for p in predictions:

            outcome = evaluate_prediction(
                p,
                result["home_score"],
                result["away_score"]
            )

            # 🔥 Guardar resultado
            p.result = outcome
            p.home_score = result["home_score"]
            p.away_score = result["away_score"]
            p.settled_at = datetime.utcnow()

            # 💰 Profit estándar decimal 1.91 (-110)
            decimal_odds = 1.91
            stake = p.stake or 1.0

            if outcome == "WIN":
                p.profit = round(stake * (decimal_odds - 1), 2)
            elif outcome == "LOSS":
                p.profit = -stake
            else:
                p.profit = 0

            settled_count += 1

        db.commit()

    db.close()

    return {"settled_predictions": settled_count}


# =====================================================
# 🧪 SETTLE MANUAL (SIMULACIÓN)
# =====================================================

@router.post("/settle-manual/{match_id}")
async def settle_manual(match_id: int, home_score: int, away_score: int):

    db: Session = SessionLocal()

    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        db.close()
        raise HTTPException(status_code=404, detail="Match not found")

    predictions = db.query(Prediction).filter(
        Prediction.match_id == match.id,
        Prediction.result == None
    ).all()

    if not predictions:
        db.close()
        return {"message": "No open predictions for this match"}

    settled = 0

    for p in predictions:

        outcome = evaluate_prediction(
            p,
            home_score,
            away_score
        )

        p.result = outcome
        stake = p.stake or 1

        if outcome == "WIN":
            p.profit = round(stake * 0.91, 2)  # equivalente -110
        elif outcome == "LOSS":
            p.profit = -stake
        else:
            p.profit = 0

        p.home_score = home_score
        p.away_score = away_score
        p.settled_at = datetime.utcnow()

        settled += 1

    db.commit()
    db.close()

    return {
        "match": f"{match.home_team} vs {match.away_team}",
        "home_score": home_score,
        "away_score": away_score,
        "settled_predictions": settled
    }


# =====================================================
# 📊 SOCCER PROPS TABLE (SoccerProps.cash core)
# =====================================================

@router.get("/soccer/props")
def soccer_props(league: str = None, active_only: bool = True):

    db: Session = SessionLocal()

    try:
        query = db.query(Prediction).join(Match)

        if league:
            query = query.filter(Match.league == f"soccer/{league}")

        if active_only:
            query = query.filter(Prediction.edge > 0)

        predictions = query.all()

        results = []

        for p in predictions:

            results.append({
                "match": f"{p.match.home_team} vs {p.match.away_team}",
                "league": p.match.league,
                "market": p.market_type,
                "model_prob_home": round(p.model_prob_home or 0, 4),
                "model_prob_draw": round(p.model_prob_draw or 0, 4),
                "model_prob_away": round(p.model_prob_away or 0, 4),
                "model_prob_over": round(p.model_prob_over or 0, 4),
                "model_prob_under": round(p.model_prob_under or 0, 4),
                "edge": round(p.edge or 0, 4),
                "decision": p.decision,
                "result": p.result,
                "profit": p.profit
            })

        results.sort(key=lambda x: x["edge"], reverse=True)

        return results

    finally:
        db.close()

# =====================================================
# 🔥 SOCCER VALUE LEADERBOARD
# =====================================================

@router.get("/soccer/leaderboard")
def soccer_leaderboard(min_edge: float = 0.03):

    db: Session = SessionLocal()

    try:
        query = db.query(Prediction).join(Match)

        # Solo VALUE BETS reales
        query = query.filter(
            Prediction.edge >= min_edge,
            Prediction.decision != "PASS"
        )

        predictions = query.all()

        results = []

        for p in predictions:

            # Detectar probabilidad modelo correcta
            model_prob = (
                p.model_prob_over
                or p.model_prob_home
                or 0
            )

            # Decimal odds estimado (simplificado)
            if p.market_type == "total_goals":
                decimal_odds = 2.05  # temporal, luego lo hacemos dinámico
            else:
                decimal_odds = 2.00

            ev = round((model_prob * decimal_odds) - 1, 4)

            confidence_index = round(
                (p.edge * 400) + (model_prob * 50),
                2
            )

            results.append({
                "match": f"{p.match.home_team} vs {p.match.away_team}",
                "league": p.match.league,
                "market": p.market_type,
                "decision": p.decision,
                "model_prob": round(model_prob, 4),
                "edge": round(p.edge or 0, 4),
                "ev": ev,
                "confidence_index": confidence_index,
                "result": p.result
            })

        results.sort(key=lambda x: x["edge"], reverse=True)
        # 🔥 Mantener solo el mejor pick por partido
        best_per_match = {}

        for r in results:
            key = r["match"]

            if key not in best_per_match:
                best_per_match[key] = r
            else:
                if r["confidence_index"] > best_per_match[key]["confidence_index"]:
                    best_per_match[key] = r

        results = list(best_per_match.values())

        return results

    finally:
        db.close()
   
# =====================================================
# 📜 MATCH HISTORY
# =====================================================

@router.get("/match/{event_id}")
def get_match_history(event_id: str):

    db: Session = SessionLocal()

    match = db.query(Match).filter(
        Match.event_id == event_id
    ).first()

    if not match:
        db.close()
        raise HTTPException(status_code=404, detail="Match not found")

    predictions = db.query(Prediction).filter(
        Prediction.match_id == match.id
    ).all()

    response = []

    for p in predictions:
        response.append({
            "match": f"{match.home_team} vs {match.away_team}",
            "league": match.league,
            "market": p.market_type,
            "edge": p.edge,
            "decision": p.decision,
            "result": p.result,
            "profit": p.profit
        })

    db.close()

    return response

# =====================================================
# 🧠 ALL PREDICTIONS HISTORY
# =====================================================

@router.get("/predictions")
def get_predictions(limit: int = 1000):

    db: Session = SessionLocal()

    try:

        predictions = db.query(Prediction)\
            .join(Match)\
            .order_by(Prediction.id.desc())\
            .limit(limit)\
            .all()

        response = []

        for p in predictions:

            response.append({

                "prediction_id":
                    p.id,

                "event_id":
                    p.match.event_id,

                "match":
                    f"{p.match.home_team} vs "
                    f"{p.match.away_team}",

                "league":
                    p.match.league,

                "market":
                    p.market_type,

                "decision":
                    p.decision,

                "edge":
                    round(p.edge or 0, 4),

                "model_prob_home":
                    round(p.model_prob_home or 0, 4),

                "model_prob_draw":
                    round(p.model_prob_draw or 0, 4),

                "model_prob_away":
                    round(p.model_prob_away or 0, 4),

                "model_prob_over":
                    round(p.model_prob_over or 0, 4),

                "model_prob_under":
                    round(p.model_prob_under or 0, 4),

                "stake":
                    p.stake,

                "result":
                    p.result,

                "profit":
                    p.profit,

                "created_at":
                    str(p.created_at)

            })

        return response

    finally:

        db.close()
