"""
Football Router - FootyStats proxy endpoints
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict, Optional
import httpx
from app.services import footystats, football_ai
import httpx
from app.utils.auth import get_current_user
from app.core.config import settings
import os

router = APIRouter()

# --- API-SPORTS Token y constantes desde settings/env ---
API_SPORTS_KEY = getattr(settings, "API_SPORTS_KEY", "")
API_SPORTS_BASE = getattr(settings, "API_SPORTS_BASE", "https://v3.football.api-sports.io")
PERU_LEAGUE_ID = int(getattr(settings, "PERU_LEAGUE_ID", 281))
SEASON = int(getattr(settings, "PERU_SEASON", 2025))

# --- Helper para requests API-SPORTS ---
async def api_sports_get(endpoint: str, params: dict = None):
    headers = {"x-apisports-key": API_SPORTS_KEY}
    url = f"{API_SPORTS_BASE}{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"API-SPORTS error: {resp.text}")
        return resp.json()


# --- Endpoint: Tabla de posiciones Liga Perú (Apertura/Clausura) ---
@router.get("/peru/table", summary="Tabla de posiciones Liga Perú (API-SPORTS)")
async def peru_table(phase: str = Query("Apertura", enum=["Apertura", "Clausura"], description="Fase: Apertura o Clausura")):
    round_param = f"{phase} - 1"
    # Buscar el round actual para la fase
    rounds_data = await api_sports_get("/fixtures/rounds", {"league": PERU_LEAGUE_ID, "season": SEASON})
    rounds = rounds_data.get("response", [])
    # Buscar el último round jugado de la fase
    last_round = next((r for r in reversed(rounds) if phase in r), round_param)
    standings_data = await api_sports_get("/standings", {"league": PERU_LEAGUE_ID, "season": SEASON})
    standings = standings_data.get("response", [{}])[0].get("league", {}).get("standings", [[]])[0]
    return {"phase": phase, "round": last_round, "standings": standings}

# --- Endpoint: Predicción IA Gemini para un partido ---
@router.get("/matches/{match_id}/predict", summary="Predicción IA Gemini para un partido")
async def predict_match_ai(match_id: int):
    # Obtener datos del partido desde API-SPORTS
    fixture_data = await api_sports_get("/fixtures", {"id": match_id})
    fixture = fixture_data.get("response", [{}])[0]
    if not fixture:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    # Llamar a la IA para predecir
    from app.services.football_ai import predict_match
    prediction = await predict_match(fixture)
    return {"match_id": match_id, "fixture": fixture, "prediction": prediction}


# --- Endpoint: Resumen últimos partidos y estadísticas globales Liga Perú ---
@router.get("/peru/summary", summary="Resumen y estadísticas Liga Perú (API-SPORTS)")
async def peru_summary():
    # Últimos partidos
    fixtures_data = await api_sports_get("/fixtures", {"league": PERU_LEAGUE_ID, "season": SEASON, "last": 5})
    last_fixtures = fixtures_data.get("response", [])
    # Estadísticas generales
    stats_data = await api_sports_get("/leagues", {"id": PERU_LEAGUE_ID})
    league_info = stats_data.get("response", [{}])[0]
    return {"last_fixtures": last_fixtures, "league_info": league_info}


@router.get("/presets", summary="List preset leagues")
async def list_presets(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    presets = settings.footystats_presets
    return {"presets": presets}


@router.get("/leagues", summary="League list")
async def league_list(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    return await footystats.get_league_list()


@router.get("/seasons/{season_id}", summary="League season stats")
async def league_season(
    season_id: int,
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_league_season(season_id=season_id)


@router.get("/seasons/{season_id}/teams", summary="Teams in a season")
async def league_teams(
    season_id: int,
    include: Optional[str] = Query("stats", description="Optional include flag, e.g. 'stats'"),
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_league_teams(season_id=season_id, include=include)


@router.get("/presets/{alias}/standings", summary="Standings for preset league")
async def get_preset_standings(
    alias: str,
    season: Optional[int] = Query(None, description="Season year, e.g. 2024"),
    season_id: Optional[int] = Query(None, description="FootyStats season_id override"),
    current_user: str = Depends(get_current_user)
):
    preset = footystats.get_preset_league(alias)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset no encontrado")

    league_id = preset.get("league_id")
    preset_season = season or preset.get("season")
    preset_season_id = season_id or preset.get("season_id")

    if not league_id and not preset_season_id:
        raise HTTPException(status_code=400, detail="Preset requiere league_id o season_id")

    return await footystats.get_league(
        league_id=league_id,
        season=preset_season,
        season_id=preset_season_id,
    )


@router.get("/leagues/{league_id}/standings", summary="League standings")
async def league_standings(
    league_id: int,
    season: Optional[int] = Query(None, description="Season year, e.g. 2024"),
    season_id: Optional[int] = Query(None, description="FootyStats season_id"),
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_league(league_id=league_id, season=season, season_id=season_id)


@router.get("/leagues/{league_id}/fixtures", summary="League fixtures")
async def league_fixtures(
    league_id: int,
    season: Optional[int] = Query(None, description="Season year"),
    season_id: Optional[int] = Query(None, description="FootyStats season_id"),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    page: Optional[int] = Query(None, description="Pagination page if supported"),
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_matches(
        league_id=league_id,
        season=season,
        season_id=season_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
    )


@router.get("/fixtures/upcoming", summary="Upcoming fixtures for a league")
async def upcoming_fixtures(
    league_id: Optional[int] = Query(None, description="League id from FootyStats"),
    season: Optional[int] = Query(None, description="Season year"),
    season_id: Optional[int] = Query(None, description="FootyStats season_id"),
    days_ahead: int = Query(7, ge=1, le=60, description="How many days ahead to look"),
    limit: int = Query(10, ge=1, le=50, description="How many matches to return"),
    current_user: str = Depends(get_current_user)
):
    today = datetime.utcnow().date()
    date_from = today.isoformat()
    date_to = (today + timedelta(days=days_ahead)).isoformat()

    raw = await footystats.get_matches(
        league_id=league_id,
        season=season,
        season_id=season_id,
        date_from=date_from,
        date_to=date_to,
        page=None,
    )

    def _extract_matches(payload: Any):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "matches", "fixtures", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []

    matches = _extract_matches(raw)

    def _sort_key(match: Dict[str, Any]):
        date_value = match.get("date") or match.get("match_date") or match.get("iso_date")
        try:
            return datetime.fromisoformat(str(date_value))
        except Exception:
            return datetime.max

    sorted_matches = sorted(matches, key=_sort_key)[:limit]

    return {
        "date_from": date_from,
        "date_to": date_to,
        "count": len(sorted_matches),
        "items": sorted_matches,
    }


@router.get("/leagues/{league_id}/top-scorers", summary="Top scorers")
async def league_top_scorers(
    league_id: int,
    season: Optional[int] = Query(None, description="Season year"),
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_top_scorers(league_id=league_id, season=season)


@router.get("/matches/{match_id}", summary="Match details")
async def match_detail(
    match_id: int,
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_match(match_id=match_id)


@router.get("/teams/{team_id}", summary="Team details")
async def team_detail(
    team_id: int,
    current_user: str = Depends(get_current_user)
):
    return await footystats.get_team(team_id=team_id)


@router.post("/matches/{match_id}/predict", summary="AI prediction for a match")
async def predict_match(
    match_id: int,
    current_user: str = Depends(get_current_user)
):
    match = await footystats.get_match(match_id=match_id)
    try:
        prediction = await football_ai.predict_match(match)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "match_id": match_id,
        "match": match,
        "prediction": prediction,
    }
