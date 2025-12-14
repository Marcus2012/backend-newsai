"""
FootyStats API client (async) to fetch football data.
"""
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings


class FootyStatsError(Exception):
    """Custom error for FootyStats client"""


def _build_url(endpoint: str) -> str:
    base = settings.FOOTYSTATS_BASE_URL.rstrip("/")
    return f"{base}/{endpoint.lstrip('/')}"


def _build_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def _request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.FOOTYSTATS_API_KEY:
        raise FootyStatsError("FOOTYSTATS_API_KEY is not configured")

    url = _build_url(endpoint)
    full_params = {"key": settings.FOOTYSTATS_API_KEY}
    full_params.update(_build_params(params))

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, params=full_params)
        if resp.status_code >= 400:
            raise FootyStatsError(f"FootyStats error {resp.status_code}: {resp.text}")
        try:
            return resp.json()
        except Exception as exc:
            raise FootyStatsError(f"Invalid JSON from FootyStats: {exc}") from exc


def get_preset_league(alias: str) -> Optional[Dict[str, Any]]:
    presets = settings.footystats_presets
    return presets.get(alias)


async def get_league(
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    season_id: Optional[int] = None,
) -> Dict[str, Any]:
    # FootyStats supports league_id or season_id depending on endpoint version
    return await _request("league", {"league_id": league_id, "season": season, "season_id": season_id})


async def get_matches(
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    season_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: Optional[int] = None,
) -> Dict[str, Any]:
    return await _request(
        "matches",
        {
            "league_id": league_id,
            "season": season,
            "season_id": season_id,
            "from": date_from,
            "to": date_to,
            "page": page,
        },
    )


async def get_match(match_id: int) -> Dict[str, Any]:
    return await _request("match", {"match_id": match_id})


async def get_team(team_id: int) -> Dict[str, Any]:
    return await _request("team", {"team_id": team_id})


async def get_top_scorers(league_id: int, season: Optional[int] = None) -> Dict[str, Any]:
    return await _request("top-scorers", {"league_id": league_id, "season": season})


async def get_countries() -> Dict[str, Any]:
    return await _request("countries", {})


async def get_league_list() -> Dict[str, Any]:
    return await _request("league-list", {})


async def get_league_season(season_id: int) -> Dict[str, Any]:
    return await _request("league-season", {"season_id": season_id})


async def get_league_teams(season_id: int, include: Optional[str] = None) -> Dict[str, Any]:
    return await _request("league-teams", {"season_id": season_id, "include": include})
