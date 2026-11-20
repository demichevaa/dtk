import json
from typing import Optional

import dtk
from dtk.connector import http

API_URL = "https://opensky-network.org/api"
AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"


def token(client_id: str, client_secret: str, timeout: int = 10) -> str:
    """OAuth2 client-credentials token, valid ~30 min."""
    data, _ = http.post(
        AUTH_URL,
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=timeout,
    )
    body = json.loads(data)
    dtk.LOG("Token(OpenSky) received, expires in %ss", body.get("expires_in"))
    return body["access_token"]


def headers(access_token: Optional[str]) -> dict:
    """Auth headers for API calls; None = anonymous."""
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}
