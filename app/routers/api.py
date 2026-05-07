from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services import football_ai

router = APIRouter()


@router.post("/predict")
async def predict_from_frontend(fixture: Dict[str, Any]):
    """Endpoint compatible con frontend: acepta el fixture completo y devuelve la predicción."""
    try:
        prediction = await football_ai.predict_match(fixture)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    response = {"fixture": fixture, "prediction": prediction}
    response.update(prediction)
    return response
