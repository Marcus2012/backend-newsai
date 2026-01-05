"""Service: simple Poisson-based scoreline estimator using API-SPORTS data."""
import math
from typing import Dict, Tuple, Any, Optional

import httpx

from app.core.config import settings


API_BASE = getattr(settings, "API_SPORTS_BASE", "https://v3.football.api-sports.io")
API_KEY = getattr(settings, "API_SPORTS_KEY", "")


async def _api_get(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    headers = {"x-apisports-key": API_KEY}
    url = f"{API_BASE}{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


async def _get_fixture_by_id(fixture_id: int) -> Optional[Dict[str, Any]]:
    try:
        data = await _api_get("/fixtures", {"id": fixture_id})
        items = data.get("response", [])
        return items[0] if items else None
    except Exception:
        return None


async def _get_recent_fixtures(team_id: int, last: int = 8):
    data = await _api_get("/fixtures", {"team": team_id, "last": last})
    return data.get("response", [])


def _safe_avg(total: float, count: int, default: float = 1.0) -> float:
    return total / count if count and count > 0 else default


async def compute_team_averages(team_id: int, last: int = 8, venue: Optional[str] = None) -> Dict[str, float]:
    """Compute average goals for and against for a team.

    venue: None (all), 'home', or 'away'
    """
    fixtures = await _get_recent_fixtures(team_id, last=last)
    gf = ga = count = 0
    for f in fixtures:
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        home = teams.get("home", {}).get("id")
        away = teams.get("away", {}).get("id")

        if venue == "home" and home != team_id:
            continue
        if venue == "away" and away != team_id:
            continue

        # Determine if this team was home or away
        if home == team_id:
            g_for = goals.get("home")
            g_against = goals.get("away")
        elif away == team_id:
            g_for = goals.get("away")
            g_against = goals.get("home")
        else:
            continue

        if g_for is None or g_against is None:
            continue

        gf += g_for
        ga += g_against
        count += 1

    return {"avg_for": _safe_avg(gf, count), "avg_against": _safe_avg(ga, count)}


async def estimate_lambdas(home_team_id: int, away_team_id: int, last: int = 8, home_advantage: float = 1.10) -> Tuple[float, float]:
    """Estimate Poisson lambdas for home and away teams.

    Uses recent home avg goals for home team and recent away avg conceded for away team.
    """
    # Home team's home scoring form
    home_home = await compute_team_averages(home_team_id, last=last, venue="home")
    # Away team's away conceded form
    away_away = await compute_team_averages(away_team_id, last=last, venue="away")

    # If any value missing, fallback to neutral 1.0
    lambda_home = (home_home.get("avg_for", 1.0) + away_away.get("avg_against", 1.0)) / 2.0
    lambda_home *= home_advantage

    # For away lambda, use away avg_for and home avg_against
    away_home = await compute_team_averages(away_team_id, last=last, venue="home")
    home_away = await compute_team_averages(home_team_id, last=last, venue="away")
    lambda_away = (away_home.get("avg_for", 1.0) + home_away.get("avg_against", 1.0)) / 2.0

    return lambda_home, lambda_away


def poisson_pmf(k: int, lam: float) -> float:
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def most_likely_score(lambda_home: float, lambda_away: float, max_goals: int = 5) -> Tuple[str, float]:
    best = None
    best_p = 0.0
    for h in range(0, max_goals + 1):
        for a in range(0, max_goals + 1):
            p = poisson_pmf(h, lambda_home) * poisson_pmf(a, lambda_away)
            if p > best_p:
                best_p = p
                best = (h, a)
    return f"{best[0]}-{best[1]}", best_p


async def estimate_scoreline_from_match(match: Dict[str, Any], last: int = 8) -> Tuple[Optional[str], Optional[float]]:
    """Try to extract team ids from a fixture dict and estimate the most likely scoreline.

    If IDs are missing but fixture has `id`, will fetch full fixture from API-SPORTS.
    Returns (scoreline, probability) or (None, None) on failure.
    """
    # Try to find team ids directly
    home_id = None
    away_id = None
    try:
        teams = match.get("teams") or {}
        home_id = teams.get("home", {}).get("id")
        away_id = teams.get("away", {}).get("id")
    except Exception:
        pass

    # If ids missing, try to fetch fixture by match id
    if not home_id or not away_id:
        fid = match.get("id") or match.get("fixture_id")
        if fid:
            full = await _get_fixture_by_id(int(fid))
            if full:
                teams = full.get("teams", {})
                home_id = teams.get("home", {}).get("id")
                away_id = teams.get("away", {}).get("id")

    if not home_id or not away_id:
        return None, None

    try:
        lam_h, lam_a = await estimate_lambdas(int(home_id), int(away_id), last=last)
        scoreline, prob = most_likely_score(lam_h, lam_a)
        return scoreline, prob
    except Exception:
        return None, None
