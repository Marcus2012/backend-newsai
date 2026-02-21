"""
Sportmonks Router - Football endpoints for leagues, standings and fixtures
"""
from datetime import date as date_type
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()

SPORTMONKS_BASE_URL = settings.SPORTMONKS_BASE_URL
SPORTMONKS_API_TOKEN = settings.SPORTMONKS_API_TOKEN

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


async def call_sportmonks(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not SPORTMONKS_API_TOKEN:
        raise HTTPException(status_code=500, detail="SPORTMONKS_API_TOKEN no configurado")

    payload = params.copy() if params else {}
    payload["api_token"] = SPORTMONKS_API_TOKEN

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{SPORTMONKS_BASE_URL}/{endpoint}", params=payload)

    if response.status_code != 200:
        detail = "Error en Sportmonks"
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@router.get("/leagues/{slug}", summary="Info general de liga (Sportmonks)")
async def get_league_info(slug: str):
    cfg = _get_slug_config(slug)
    league_id = cfg["league_id"]
    return await call_sportmonks(f"leagues/{league_id}", {"include": "currentSeason"})


@router.get("/standings/{slug}", summary="Tabla de posiciones (Sportmonks)")
async def get_league_standings(slug: str):
    cfg = _get_slug_config(slug)
    season_id = cfg["season_id"]
    data = await call_sportmonks(
        "standings",
        {"seasons": season_id, "include": "participant;details.type"},
    )

    standings = data.get("data", [])
    if isinstance(standings, list):
        for item in standings:
            summary = _extract_standing_summary(item.get("details"))
            item["summary"] = summary
            item["table"] = _summary_to_table(summary)

    return data


@router.get("/fixtures/{slug}", summary="Partidos por fecha (Sportmonks)")
async def get_fixtures_by_date(
    slug: str,
    date: Optional[date_type] = Query(None, description="Fecha YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Pagina de resultados"),
):
    cfg = _get_slug_config(slug)
    league_id = cfg["league_id"]

    target_date = (date or date_type.today()).isoformat()
    params = {
        "filter": f"league_ids:{league_id}",
        "include": "participants;scores",
        "page": page,
    }

    return await call_sportmonks(f"fixtures/date/{target_date}", params=params)


@router.get("/fixtures/between/{slug}", summary="Partidos por rango de fechas (Sportmonks)")
async def get_fixtures_between(
    slug: str,
    start: date_type = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: date_type = Query(..., description="Fecha fin YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Pagina de resultados"),
):
    cfg = _get_slug_config(slug)
    league_id = cfg["league_id"]

    params = {
        "filter": f"league_ids:{league_id}",
        "include": "participants;scores",
        "page": page,
    }

    return await call_sportmonks(f"fixtures/between/{start}/{end}", params=params)
