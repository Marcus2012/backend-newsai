
import asyncio
import json
from typing import Any, Dict, Optional

import google.generativeai as genai
from app.core.config import settings

# Configurar Gemini si hay API KEY
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def _sanitize_match(match: Any) -> Dict[str, Any]:
    """Reduce el payload del partido a un subconjunto seguro para JSON."""
    if isinstance(match, dict):
        return {k: v for k, v in match.items() if not callable(v)}
    return {"match": match}

def _build_prompt(match: Dict[str, Any], stat_scoreline: Optional[str] = None, stat_prob: Optional[float] = None) -> str:
    """Crea un prompt para Gemini con instrucciones de esquema."""
    match_json = json.dumps(_sanitize_match(match), ensure_ascii=True)
    if len(match_json) > 6000:
        match_json = match_json[:6000] + "..."
    parts = []
    parts.append(
        "Eres un analista de futbol. Usa solo los datos provistos para predecir el resultado. "
        "Devuelve JSON valido con este esquema:\n"
        "{\n"
        "  \"winner\": \"home|away|draw\",\n"
        "  \"scoreline\": \"2-1\",\n"
        "  \"confidence\": 0-100,\n"
        "  \"reasons\": [\"breve razon 1\", \"breve razon 2\"]\n"
        "}\n"
        "Reglas: no inventes equipos ni fechas, limita las razones a 2-3, usa porcentaje entero.\n"
    )
    parts.append(f"Datos del partido (JSON):\n{match_json}\n")
    if stat_scoreline and stat_prob is not None:
        parts.append(f"Prediccion estadistica (Poisson): {stat_scoreline} (p={stat_prob:.3f})\n")
    parts.append("Respuesta solo con JSON:")
    return "".join(parts)

def _predict_sync(prompt: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY no esta configurado")
    # Prefer model name from settings (e.g. "models/gemini-2.5-pro").
    model_name = getattr(settings, "GEMINI_MODEL", None) or "models/gemini-2.5-pro"
    # Normalize model name: accept both "gemini-2.5-pro" and "models/gemini-2.5-pro"
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        # Re-raise with model info to help debugging issues like 404 unsupported model
        raise RuntimeError(f"error generating content with model={model_name}: {exc}") from exc
    text = getattr(response, "text", "") or ""
    text = text.strip()
    if not text:
        raise RuntimeError(f"Empty response text from model={model_name}; full response repr: {repr(response)}")
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    # If the model didn't return pure JSON, try to extract a JSON object from the text.
    try:
        result = json.loads(text)
    except Exception:
        import re

        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            candidate = m.group(0)
            try:
                result = json.loads(candidate)
            except Exception as exc:
                raise RuntimeError(
                    f"failed to parse JSON from model={model_name}. extracted_candidate={candidate!r} full_text={text!r}"
                ) from exc
        else:
            raise RuntimeError(f"failed to parse JSON from model={model_name}. text={text!r}")
    for key in ("winner", "scoreline", "confidence"):
        if key not in result:
            raise ValueError("Respuesta incompleta del modelo")
    return result

def _fallback_prediction(match: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Fallback simple si Gemini no responde."""
    home = match.get("home_name") or match.get("homeTeam") or "Home"
    away = match.get("away_name") or match.get("awayTeam") or "Away"
    return {
        "winner": "draw",
        "scoreline": "1-1",
        "confidence": 50,
        "reasons": [
            "Prediccion basica por falta de modelo IA",
            f"Detalles: {reason[:200]}",
        ],
        "summary": f"Pronostico reservado para {home} vs {away}",
    }

async def predict_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """Predice el resultado de un partido usando Gemini."""
    # Try to compute a statistical scoreline first (if API-SPORTS IDs available)
    stat_scoreline = None
    stat_prob = None
    try:
        from app.services.poisson import estimate_scoreline_from_match

        stat_scoreline, stat_prob = await estimate_scoreline_from_match(match)
    except Exception:
        stat_scoreline, stat_prob = None, None

    prompt = _build_prompt(match, stat_scoreline=stat_scoreline, stat_prob=stat_prob)
    try:
        return await asyncio.to_thread(_predict_sync, prompt)
    except Exception as exc:
        return _fallback_prediction(match, str(exc))
