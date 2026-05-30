from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import MatchPrediction
from app.services import football_ai

router = APIRouter()


@router.post("/predict")
async def predict_from_frontend(fixture: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Endpoint compatible con frontend: acepta el fixture completo y devuelve la predicción.
    La primera predicción se guarda en DB; las siguientes siempre devuelven el mismo resultado.
    """
    fixture_id = str(fixture.get("id") or fixture.get("match", {}).get("id") or "")

    if fixture_id:
        row = await db.get(MatchPrediction, fixture_id)
        if row:
            prediction = row.prediction_data
            return {"fixture": fixture, "prediction": prediction, **prediction}

    try:
        prediction = await football_ai.predict_match(fixture)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if fixture_id:
        db.add(MatchPrediction(fixture_id=fixture_id, prediction_data=prediction))
        await db.commit()

    return {"fixture": fixture, "prediction": prediction, **prediction}
