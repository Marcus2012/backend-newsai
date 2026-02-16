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
    "la-liga": {
        "league_id": settings.SPORTMONKS_LALIGA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_LALIGA_SEASON_ID,
    },
    "bundesliga": {
        "league_id": settings.SPORTMONKS_BUNDESLIGA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_BUNDESLIGA_SEASON_ID,
    },
    "ligue-1": {
        "league_id": settings.SPORTMONKS_LIGUE1_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_LIGUE1_SEASON_ID,
    },
    "champions-league": {
        "league_id": settings.SPORTMONKS_CHAMPIONS_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_CHAMPIONS_SEASON_ID,
    },
    "peru-primera": {
        "league_id": settings.SPORTMONKS_PERU_PRIMERA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_PERU_PRIMERA_SEASON_ID,
    },
    "peru-segunda": {
        "league_id": settings.SPORTMONKS_PERU_SEGUNDA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_PERU_SEGUNDA_SEASON_ID,
    },
    "argentina-liga-profesional": {
        "league_id": settings.SPORTMONKS_ARGENTINA_LIGA_PROFESIONAL_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_ARGENTINA_LIGA_PROFESIONAL_SEASON_ID,
    },
    "argentina-copa-argentina": {
        "league_id": settings.SPORTMONKS_ARGENTINA_COPA_ARGENTINA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_ARGENTINA_COPA_ARGENTINA_SEASON_ID,
    },
    "brasil-serie-a": {
        "league_id": settings.SPORTMONKS_BRASIL_SERIE_A_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_BRASIL_SERIE_A_SEASON_ID,
    },
    "colombia-liga-betplay": {
        "league_id": settings.SPORTMONKS_COLOMBIA_LIGA_BETPLAY_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_COLOMBIA_LIGA_BETPLAY_SEASON_ID,
    },
    "ecuador-liga-pro": {
        "league_id": settings.SPORTMONKS_ECUADOR_LIGA_PRO_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_ECUADOR_LIGA_PRO_SEASON_ID,
    },
    "usa-mls": {
        "league_id": settings.SPORTMONKS_USA_MLS_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_USA_MLS_SEASON_ID,
    },
    "mexico-liga-mx": {
        "league_id": settings.SPORTMONKS_MEXICO_LIGA_MX_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_MEXICO_LIGA_MX_SEASON_ID,
    },
    "copa-libertadores": {
        "league_id": settings.SPORTMONKS_CONMEBOL_COPA_LIBERTADORES_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_CONMEBOL_COPA_LIBERTADORES_SEASON_ID,
    },
    "copa-sudamericana": {
        "league_id": settings.SPORTMONKS_CONMEBOL_COPA_SUDAMERICANA_LEAGUE_ID,
        "season_id": settings.SPORTMONKS_CONMEBOL_COPA_SUDAMERICANA_SEASON_ID,
    },
}


def _extract_standing_summary(details: Optional[list]) -> Dict[str, Optional[int]]:
    if not details:
        return {
            "played": None,
            "won": None,
            "draw": None,
            "lost": None,
            "goals_for": None,
            "goals_against": None,
            "goal_difference": None,
            "points": None,
        }

    by_code: Dict[str, int] = {}
    for item in details:
        code = (item.get("type") or {}).get("code")
        value = item.get("value")
        if code is not None and value is not None:
            by_code[code] = value

    return {
        "played": by_code.get("overall-matches-played"),
        "won": by_code.get("overall-won"),
        "draw": by_code.get("overall-draw"),
        "lost": by_code.get("overall-lost"),
        "goals_for": by_code.get("overall-goals-for"),
        "goals_against": by_code.get("overall-goals-against"),
        "goal_difference": by_code.get("goal-difference"),
        "points": by_code.get("overall-points"),
    }


def _summary_to_table(summary: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
    return {
        "pj": summary.get("played"),
        "pg": summary.get("won"),
        "pe": summary.get("draw"),
        "pp": summary.get("lost"),
        "gf": summary.get("goals_for"),
        "gc": summary.get("goals_against"),
        "dg": summary.get("goal_difference"),
        "pts": summary.get("points"),
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
    data = await call_sportmonks(f"standings/seasons/{sid}", {"include": "participant;details.type"})
    standings = data.get("data", [])
    if isinstance(standings, list):
        for item in standings:
            summary = _extract_standing_summary(item.get("details"))
            item["summary"] = summary
            item["table"] = _summary_to_table(summary)
    return data


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
    data = await call_sportmonks(f"standings/seasons/{sid}", {"include": "participant;details.type"})
    standings = data.get("data", [])
    if isinstance(standings, list):
        for item in standings:
            summary = _extract_standing_summary(item.get("details"))
            item["summary"] = summary
            item["table"] = _summary_to_table(summary)
    return data


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


@router.get("/public/{slug}/info", summary="League info (Sportmonks)")
async def league_info(slug: str):
    cfg = _get_slug_config(slug)
    return await call_sportmonks(f"leagues/{cfg['league_id']}", {"include": "currentSeason"})


@router.get("/public/{slug}/standings", summary="League standings (Sportmonks)")
async def league_standings(slug: str, season_id: Optional[int] = None):
    cfg = _get_slug_config(slug)
    sid = season_id or cfg["season_id"]
    if not season_id:
        current = await _get_current_season_id(cfg["league_id"])
        if current:
            sid = current
    data = await call_sportmonks(f"standings/seasons/{sid}", {"include": "participant;details.type"})
    standings = data.get("data", [])
    if isinstance(standings, list):
        for item in standings:
            summary = _extract_standing_summary(item.get("details"))
            item["summary"] = summary
            item["table"] = _summary_to_table(summary)
    return data


@router.get("/public/{slug}/fixtures", summary="League fixtures (Sportmonks)")
async def league_fixtures(
    slug: str,
    date: Optional[date_type] = Query(None, description="Fecha YYYY-MM-DD"),
    next: Optional[int] = Query(None, description="Cantidad de partidos a futuro"),
):
    cfg = _get_slug_config(slug)
    target_date = (date or date_type.today()).isoformat()
    season_id = await _get_current_season_id(cfg["league_id"]) or cfg["season_id"]
    params = {
        "include": "participants;scores",
    }
    payload = await call_sportmonks(f"fixtures/date/{target_date}", params=params)
    filtered = _filter_fixtures_by_league(payload, cfg["league_id"], season_id=season_id)
    if next and isinstance(filtered.get("data"), list):
        new_payload = dict(filtered)
        new_payload["data"] = filtered["data"][:next]
        return new_payload
    return filtered
