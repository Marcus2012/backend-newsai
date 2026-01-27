"""
Scheduler Router - Endpoints for external schedulers (e.g., Google Cloud Scheduler)
"""
from datetime import datetime
import asyncio
from typing import Optional, List
import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
import google.auth.transport.requests
from google.oauth2 import id_token

from app.core.config import settings
from app.scheduler import scraping_job

router = APIRouter()
logger = logging.getLogger("scheduler")


def _verify_scheduler_oidc(auth_header: Optional[str], audiences: List[str]) -> None:
    audiences = [a.strip() for a in audiences if a and a.strip()]
    audiences = [a.rstrip("/") for a in audiences]
    expected_email = (settings.CLOUD_SCHEDULER_SERVICE_ACCOUNT_EMAIL or "").strip()

    if not audiences:
        logger.error("Scheduler auth: audiencia vacía")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audience no configurado"
        )

    if not auth_header or not auth_header.lower().startswith("bearer "):
        logger.warning("Scheduler auth: falta Authorization Bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization Bearer requerido"
        )

    token = auth_header.split(" ", 1)[1].strip()
    request = google.auth.transport.requests.Request()
    claims = None
    audiences_to_try: List[str] = []
    for aud in audiences:
        audiences_to_try.append(aud)
        audiences_to_try.append(f"{aud}/")

    for aud in audiences_to_try:
        try:
            claims = id_token.verify_oauth2_token(token, request, audience=aud)
            break
        except Exception:
            continue

    if not claims:
        logger.warning("Scheduler auth: OIDC inválido para audiences=%s", audiences_to_try)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC token inválido"
        )

    issuer = claims.get("iss")
    if issuer not in {"https://accounts.google.com", "accounts.google.com"}:
        logger.warning("Scheduler auth: issuer inválido %s", issuer)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Issuer inválido"
        )

    if expected_email:
        token_email = claims.get("email")
        if token_email != expected_email:
            logger.warning(
                "Scheduler auth: service account no autorizado (token=%s, expected=%s)",
                token_email,
                expected_email
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Service account no autorizado"
            )


@router.post("/run")
async def run_scheduled_scrape(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    background: bool = Query(False, description="Ejecutar en segundo plano")
):
    """
    Ejecuta el scraping bajo demanda (pensado para Google Cloud Scheduler).

    - Requiere header X-Scheduler-Token si CLOUD_SCHEDULER_TOKEN está configurado.
    - Si background=true, dispara el job en segundo plano y responde inmediato.
    """
    configured_audience = (settings.CLOUD_SCHEDULER_AUDIENCE or "").strip()
    base_url = str(request.base_url).rstrip("/")
    full_url = str(request.url)
    full_url_no_query = full_url.split("?", 1)[0]
    audiences = [configured_audience, base_url, full_url_no_query, full_url]
    _verify_scheduler_oidc(authorization, audiences)

    if background:
        asyncio.create_task(scraping_job())
        return {
            "status": "started",
            "mode": "background",
            "timestamp": datetime.utcnow().isoformat()
        }

    await scraping_job()
    return {
        "status": "completed",
        "mode": "sync",
        "timestamp": datetime.utcnow().isoformat()
    }
