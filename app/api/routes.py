from fastapi import APIRouter, HTTPException
from app.clients.espn import upcoming_matches
from app.schemas.predict import AIPredictRequest
from app.services.predictor import ai_predict

router = APIRouter()

@router.get("/matches/upcoming")
async def matches_upcoming(sport: str):
    return await upcoming_matches(sport)

@router.post("/ai/predict")
async def predict(req: AIPredictRequest):
    try:
        return await ai_predict(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
