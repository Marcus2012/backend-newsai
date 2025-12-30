from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.services.easypromo import register_and_get_play_link
import logging

router = APIRouter()

@router.post("/register", tags=["EasyPromo"])
async def easypromo_register(request: Request):
    try:
        data = await request.json()
        logging.info(f"[EasyPromo] Datos recibidos: {data}")
        result = await register_and_get_play_link(user=data)
        logging.info(f"[EasyPromo] Resultado: {result}")
        return JSONResponse(result)
    except Exception as e:
        logging.error(f"[EasyPromo] Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)
