import asyncio
import json
import re
from typing import Any, Dict, Optional

import google.generativeai as genai
from app.core.config import settings

# Configurar Gemini si hay API KEY
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _clamp_confidence(value: Any, default: int = 50) -> int:
    try:
        confidence = int(round(float(value)))
    except (TypeError, ValueError):
        confidence = default
    return max(0, min(confidence, 100))


def _parse_scoreline(scoreline: Any) -> Optional[tuple[int, int]]:
    if not scoreline:
        return None
    match = re.search(r"(\d+)\s*[-:]\s*(\d+)", str(scoreline))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _format_scoreline(scoreline: Any, default: str = "1-1") -> str:
    parsed = _parse_scoreline(scoreline)
    if not parsed:
        return default
    home_goals, away_goals = parsed
    return f"{home_goals}-{away_goals}"


def _derive_winner(scoreline: str, winner: Any) -> str:
    if winner in {"home", "away", "draw"}:
        return winner

    parsed = _parse_scoreline(scoreline)
    if not parsed:
        return "draw"

    home_goals, away_goals = parsed
    if home_goals > away_goals:
        return "home"
    if away_goals > home_goals:
        return "away"
    return "draw"


def _build_probabilities(winner: str, confidence: int) -> Dict[str, int]:
    remaining = max(0, 100 - confidence)

    if winner == "home":
        draw = round(remaining * 0.6)
        away = remaining - draw
        probabilities = {"home": confidence, "draw": draw, "away": away}
    elif winner == "away":
        draw = round(remaining * 0.6)
        home = remaining - draw
        probabilities = {"home": home, "draw": draw, "away": confidence}
    else:
        home = remaining // 2
        away = remaining - home
        probabilities = {"home": home, "draw": confidence, "away": away}

    total = sum(probabilities.values())
    if total != 100:
        probabilities[winner if winner in probabilities else "draw"] += 100 - total
    return probabilities


def _build_summary(match: Dict[str, Any], winner: str, confidence: int) -> str:
    home = match.get("home") or match.get("home_name") or match.get("homeTeam") or "Local"
    away = match.get("away") or match.get("away_name") or match.get("awayTeam") or "Visitante"

    if winner == "home":
        return f"Gana {home} ({confidence}%)"
    if winner == "away":
        return f"Gana {away} ({confidence}%)"
    return f"Empate ({confidence}%)"


def _normalize_prediction(match: Dict[str, Any], prediction: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(prediction or {})
    scoreline = _format_scoreline(normalized.get("scoreline"))
    winner = _derive_winner(scoreline, normalized.get("winner"))
    confidence = _clamp_confidence(normalized.get("confidence"))
    probabilities = _build_probabilities(winner, confidence)

    reasons = normalized.get("reasons")
    if isinstance(reasons, list):
        reason_list = [str(reason) for reason in reasons if reason]
    elif reasons:
        reason_list = [str(reasons)]
    else:
        reason_list = []

    summary = str(normalized.get("summary") or _build_summary(match, winner, confidence))
    analysis = str(normalized.get("analysis") or " ".join(reason_list[:3]) or summary)

    normalized.update(
        {
            "winner": winner,
            "scoreline": scoreline,
            "score": scoreline,
            "confidence": confidence,
            "summary": summary,
            "analysis": analysis,
            "reasons": reason_list,
            "probabilities": probabilities,
            "homeWinPercentage": probabilities["home"],
            "drawPercentage": probabilities["draw"],
            "awayWinPercentage": probabilities["away"],
            "predictionLabel": summary,
            "probableScore": scoreline,
        }
    )
    return normalized

def _sanitize_match(match: Any) -> Dict[str, Any]:
    """Reduce el payload del partido a un subconjunto seguro para JSON."""
    if isinstance(match, dict):
        return {k: v for k, v in match.items() if not callable(v)}
    return {"match": match}

async def _get_team_stats(team_name: str, league_slug: str, season_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Obtiene las estadisticas de un equipo desde Sportmonks."""
    try:
        from app.routers.sportmonks import call_sportmonks, SPORTMONKS_CONFIG
        
        cfg = SPORTMONKS_CONFIG.get(league_slug)
        if not cfg:
            return None
        
        sid = season_id or cfg.get("season_id")
        if not sid:
            return None
        
        data = await call_sportmonks(
            f"standings/seasons/{sid}",
            {"include": "participant;details.type"}
        )
        
        standings = data.get("data", [])
        if not isinstance(standings, list):
            return None
        
        for item in standings:
            participant = item.get("participant", {})
            participant_name = participant.get("name", "")
            
            if team_name.lower() in participant_name.lower() or participant_name.lower() in team_name.lower():
                details = item.get("details", [])
                by_code = {}
                if isinstance(details, list):
                    for detail in details:
                        code = (detail.get("type") or {}).get("code")
                        value = detail.get("value")
                        if code and value is not None:
                            by_code[code] = value
                
                return {
                    "name": participant_name,
                    "position": item.get("position"),
                    "points": by_code.get("overall-points"),
                    "played": by_code.get("overall-matches-played"),
                    "wins": by_code.get("overall-won"),
                    "draws": by_code.get("overall-draw"),
                    "losses": by_code.get("overall-lost"),
                    "goals_for": by_code.get("overall-goals-for"),
                    "goals_against": by_code.get("overall-goals-against"),
                    "goal_difference": by_code.get("goal-difference"),
                }
        
        return None
    except Exception as exc:
        print(f"Error fetching team stats: {exc}")
        return None

def _build_prompt(match: Dict[str, Any], home_stats: Optional[Dict[str, Any]] = None, away_stats: Optional[Dict[str, Any]] = None) -> str:
    """Crea un prompt para Gemini 2.5 Flash con datos de Sportmonks."""
    parts = []
    
    parts.append(
        "Eres un experto en analisis de futbol. Predice el resultado basandote en los datos provistos.\n"
        "Devuelve SOLO JSON valido en este formato:\n"
        "{\n"
        '  "winner": "home" o "away" o "draw",\n'
        '  "scoreline": "2-1",\n'
        '  "confidence": numero entre 0-100,\n'
        '  "reasons": ["razon 1", "razon 2", "razon 3"]\n'
        "}\n\n"
    )
    
    match_json = json.dumps(_sanitize_match(match), ensure_ascii=True)
    if len(match_json) > 6000:
        match_json = match_json[:6000] + "..."
    parts.append(f"INFORMACION DEL PARTIDO:\n{match_json}\n\n")
    
    if home_stats or away_stats:
        parts.append("ESTADISTICAS DE LOS EQUIPOS (Sportmonks):\n")
        
        if home_stats:
            parts.append(f"LOCAL - {home_stats.get('name')}:\n")
            parts.append(f"  Posicion: #{home_stats.get('position')} | Puntos: {home_stats.get('points')}\n")
            parts.append(f"  Jugados/Ganas/Empates/Perdidas: {home_stats.get('played')}/{home_stats.get('wins')}/{home_stats.get('draws')}/{home_stats.get('losses')}\n")
            parts.append(f"  Goles a favor: {home_stats.get('goals_for')} | Goles en contra: {home_stats.get('goals_against')}\n")
            parts.append(f"  Diferencia de goles: {home_stats.get('goal_difference')}\n\n")
        
        if away_stats:
            parts.append(f"VISITANTE - {away_stats.get('name')}:\n")
            parts.append(f"  Posicion: #{away_stats.get('position')} | Puntos: {away_stats.get('points')}\n")
            parts.append(f"  Jugados/Ganas/Empates/Perdidas: {away_stats.get('played')}/{away_stats.get('wins')}/{away_stats.get('draws')}/{away_stats.get('losses')}\n")
            parts.append(f"  Goles a favor: {away_stats.get('goals_for')} | Goles en contra: {away_stats.get('goals_against')}\n")
            parts.append(f"  Diferencia de goles: {away_stats.get('goal_difference')}\n\n")
    
    parts.append("Proporciona tu prediccion en JSON:")
    return "".join(parts)

def _predict_sync(prompt: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY no esta configurado")
    model_name = getattr(settings, "GEMINI_MODEL", None) or "models/gemini-2.5-flash"
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(prompt)
    except Exception as exc:
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

async def predict_match(fixture: Dict[str, Any]) -> Dict[str, Any]:
    """Predice el resultado de un partido usando Gemini 2.5 Flash con datos de Sportmonks."""
    match = fixture.get("match") if isinstance(fixture.get("match"), dict) else fixture

    home_name = match.get("home") or match.get("home_name") or match.get("homeTeam") or "Home"
    away_name = match.get("away") or match.get("away_name") or match.get("awayTeam") or "Away"

    league_slug = match.get("league_slug") or ""
    
    home_stats = await _get_team_stats(home_name, league_slug)
    away_stats = await _get_team_stats(away_name, league_slug)
    
    prompt = _build_prompt(match, home_stats, away_stats)
    
    try:
        prediction = await asyncio.to_thread(_predict_sync, prompt)
    except Exception as exc:
        prediction = _fallback_prediction(match, str(exc))

    return _normalize_prediction(match, prediction)
