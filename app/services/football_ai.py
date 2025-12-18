"""
AI-powered football match predictions using Gemini.
"""
import asyncio
import json
from typing import Any, Dict

import google.generativeai as genai

from app.core.config import settings
from app.services import gemini as gemini_service

# Ensure Gemini is configured for this module
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _sanitize_match(match: Any) -> Dict[str, Any]:
    """Reduce match payload to a JSON-safe subset."""
    if isinstance(match, dict):
        return {k: v for k, v in match.items() if not callable(v)}
    return {"match": match}


def _build_prompt(match: Dict[str, Any]) -> str:
    """Create a concise prompt for Gemini with schema instructions."""
    match_json = json.dumps(_sanitize_match(match), ensure_ascii=True)
    if len(match_json) > 6000:
        match_json = match_json[:6000] + "..."

    return (
        "Eres un analista de futbol. Usa solo los datos provistos para predecir el resultado. "
        "Devuelve JSON valido con este esquema:\n"
        "{\n"
        "  \"winner\": \"home|away|draw\",\n"
        "  \"scoreline\": \"2-1\",\n"
        "  \"confidence\": 0-100,\n"
        "  \"reasons\": [\"breve razon 1\", \"breve razon 2\"]\n"
        "}\n"
        "Reglas: no inventes equipos ni fechas, limita las razones a 2-3, usa porcentaje entero.\n"
        f"Datos del partido (JSON):\n{match_json}\n"
        "Respuesta solo con JSON:"
    )


def _predict_sync(prompt: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY no esta configurado")

    model_name = gemini_service._choose_model()  # reuse model selection logic
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    result = json.loads(text)
    # Minimal validation
    for key in ("winner", "scoreline", "confidence"):
        if key not in result:
            raise ValueError("Respuesta incompleta del modelo")
    return result


def _fallback_prediction(match: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Deterministic lightweight fallback when Gemini is unavailable."""
    home_name = match.get("home_name") or match.get("homeTeam") or "Home"
    away_name = match.get("away_name") or match.get("awayTeam") or "Away"
    return {
        "winner": "draw",
        "scoreline": "1-1",
        "confidence": 50,
        "reasons": [
            "Prediccion basica por falta de modelo AI",
            f"Detalles: {reason[:200]}",
        ],
        "summary": f"Pronostico reservado para {home_name} vs {away_name}",
    }


async def predict_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """Predict a match outcome using Gemini with graceful fallback."""
    prompt = _build_prompt(match)
    try:
        return await asyncio.to_thread(_predict_sync, prompt)
    except Exception as exc:  # broad to ensure an answer is always returned
        return _fallback_prediction(match, str(exc))
