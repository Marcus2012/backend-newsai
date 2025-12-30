from typing import Any, Dict, Optional
import httpx
from app.core.config import settings


_API_AUTLOGIN = settings.EASYPROMOS_API_AUTLOGIN
_PROMO_BASE = settings.EASYPROMOS_PROMO_BASE


async def _post_autologin(client: httpx.AsyncClient, campaign_id: str, api_token: str, body: Dict[str, Any]) -> Dict[str, Any]:
    url = _API_AUTLOGIN.format(campaign_id=campaign_id)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    resp = await client.post(url, json=body, headers=headers, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


async def register_and_get_play_link(user: Dict[str, Any], campaign_id: Optional[str] = None, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Ejecuta el flujo para EasyPromos:
      1) Auth: POST autologin con {"external_id": "..."}
      2) Register: POST autologin con los datos completos del usuario
      3) Construye la URL de juego concatenando `?lt=<token>` a la URL promocional

    Parámetros:
      - campaign_id: id de la promoción (ej. "1005559")
      - api_token: token Bearer para Authorization
      - user: diccionario con al menos `external_id`. Puede incluir `first_name`,
        `last_name`, `nickname`, `email`, `phone`, `country`.

    Retorna:
      Dict con claves: `register` (bool), `lt` (str|None), `promo_url` (str|None), `raw` (respuesta json completa)
    """
    if "external_id" not in user:
        raise ValueError("user debe contener la clave 'external_id'")
    # Resolve defaults from settings if not provided
    campaign_id = campaign_id or settings.EASYPROMOS_CAMPAIGN_ID
    api_token = api_token or settings.EASYPROMOS_API_TOKEN

    if not campaign_id:
        raise ValueError("campaign_id no proporcionado y EASYPROMOS_CAMPAIGN_ID no está configurado")
    if not api_token:
        raise ValueError("api_token no proporcionado y EASYPROMOS_API_TOKEN no está configurado")

    async with httpx.AsyncClient() as client:
        # Paso 1: auth (intento, no necesariamente crítico si ya existe)
        try:
            await _post_autologin(client, campaign_id, api_token, {"external_id": user["external_id"]})
        except httpx.HTTPStatusError:
            # Ignoramos fallo en auth inicial; seguiremos al registro que devuelve lt
            pass

        # Paso 2: register (o autologin con datos completos)
        try:
            resp_json = await _post_autologin(client, campaign_id, api_token, user)
        except httpx.HTTPStatusError as exc:
            # Devolver estructura con error para que el llamante lo maneje
            return {"register": False, "lt": None, "promo_url": None, "raw": {"error": str(exc), "status_code": exc.response.status_code if exc.response is not None else None}}

        register = resp_json.get("register", False)
        lt = resp_json.get("lt")
        promo_url: Optional[str] = None
        if lt:
            promo_url = f"{_PROMO_BASE.format(campaign_id=campaign_id)}?lt={lt}"

        return {"register": register, "lt": lt, "promo_url": promo_url, "raw": resp_json}
