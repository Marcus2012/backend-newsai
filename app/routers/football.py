import os

"""
Football Router - FootyStats proxy endpoints
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict, Optional

from app.services import footystats, football_ai
import httpx
from app.utils.auth import get_current_user
from app.core.config import settings

router = APIRouter()

# Endpoint tabla de posiciones Liga Perú usando API key de settings
@router.get("/league-table", summary="Tabla de posiciones Liga Perú")
async def peru_league_table(current_user: str = Depends(get_current_user)):
    api_key = getattr(settings, "FOOTBALL_DATA_API_KEY", None)
    if not api_key:
        # Si no está en settings, usar la key hardcodeada como fallback
        api_key = "f37d0d7b03a98882d9a3672336c2a30d89ade024875637d35b5cd5f224149d0e"
    url = f"https://api.football-data-api.com/league-tables?key={api_key}&season_id=14912"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Error consultando API externa")
        return response.json()


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
