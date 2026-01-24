"""
Football Router - compatibilidad para frontend usando Sportmonks
"""
from datetime import date as date_type
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.routers.sportmonks import call_sportmonks

router = APIRouter()

SPORTMONKS_CONFIG: Dict[str, Dict[str, int]] = {
    "premier-league": {
        "league_id": settings.SPORTMONKS_PREMIER_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_PREMIER_SEASON_ID,
    },
    "serie-a": {
        "league_id": settings.SPORTMONKS_SERIEA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_SERIEA_SEASON_ID,
    },
}


def _get_slug_config(slug: str) -> Dict[str, int]:
    cfg = SPORTMONKS_CONFIG.get(slug)
    if not cfg:
        raise HTTPException(status_code=404, detail="Liga no configurada")
    return cfg


async def _get_current_season_id(league_id: int) -> Optional[int]:
    data = await call_sportmonks(f"leagues/{league_id}", {"include": "currentSeason"})
    season = (data.get("data") or {}).get("currentseason")
    if isinstance(season, dict):
        return season.get("id")
    return None


def _filter_fixtures_by_league(
    payload: Dict[str, Any],
    league_id: int,
    season_id: Optional[int] = None,
) -> Dict[str, Any]:
    data = payload.get("data")
    if isinstance(data, list):
        filtered = [item for item in data if item.get("league_id") == league_id]
        if season_id is not None:
            filtered = [item for item in filtered if item.get("season_id") == season_id]
        new_payload = dict(payload)
        new_payload["data"] = filtered
        return new_payload
    return payload


@router.get("/public/premier/info", summary="Premier League info (Sportmonks)")
async def premier_info():
    cfg = _get_slug_config("premier-league")
    return await call_sportmonks(f"leagues/{cfg['league_id']}", {"include": "currentSeason"})


@router.get("/public/premier/standings", summary="Premier League standings (Sportmonks)")
async def premier_standings(season_id: Optional[int] = None):
    cfg = _get_slug_config("premier-league")
    sid = season_id or cfg["season_id"]
    return await call_sportmonks(f"standings/seasons/{sid}", {"include": "participant"})


@router.get("/public/premier/fixtures", summary="Premier League fixtures (Sportmonks)")
async def premier_fixtures(
    date: Optional[date_type] = Query(None, description="Fecha YYYY-MM-DD"),
):
    cfg = _get_slug_config("premier-league")
    target_date = (date or date_type.today()).isoformat()
    season_id = await _get_current_season_id(cfg["league_id"]) or cfg["season_id"]
    params = {
        "include": "participants;scores",
    }
    payload = await call_sportmonks(f"fixtures/date/{target_date}", params=params)
    return _filter_fixtures_by_league(payload, cfg["league_id"], season_id=season_id)


@router.get("/public/seriea/info", summary="Serie A info (Sportmonks)")
async def seriea_info():
    cfg = _get_slug_config("serie-a")
    return await call_sportmonks(f"leagues/{cfg['league_id']}", {"include": "currentSeason"})


@router.get("/public/seriea/standings", summary="Serie A standings (Sportmonks)")
async def seriea_standings(season_id: Optional[int] = None):
    cfg = _get_slug_config("serie-a")
    sid = season_id or cfg["season_id"]
    if not season_id:
        current = await _get_current_season_id(cfg["league_id"])
        if current:
            sid = current
    return await call_sportmonks(f"standings/seasons/{sid}", {"include": "participant"})


@router.get("/public/seriea/fixtures", summary="Serie A fixtures (Sportmonks)")
async def seriea_fixtures(
    date: Optional[date_type] = Query(None, description="Fecha YYYY-MM-DD"),
):
    cfg = _get_slug_config("serie-a")
    target_date = (date or date_type.today()).isoformat()
    season_id = await _get_current_season_id(cfg["league_id"]) or cfg["season_id"]
    params = {
        "include": "participants;scores",
    }
    payload = await call_sportmonks(f"fixtures/date/{target_date}", params=params)
    return _filter_fixtures_by_league(payload, cfg["league_id"], season_id=season_id)
