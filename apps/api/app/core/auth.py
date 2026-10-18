import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    organization_id: str
    role: str
    workspace: str


DEV_PROFILES: dict[str, Principal] = {
    "internal": Principal("dev-internal", "dev-org", "internal_member", "internal"),
    "customer": Principal("dev-customer", "dev-org", "external_customer", "customer"),
    "other": Principal("dev-other", "dev-org", "internal_member", "internal"),
}


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(principal: Principal, settings: Settings) -> str:
    if not settings.dev_auth_enabled or settings.app_env == "production":
        raise HTTPException(status_code=404, detail="Development authentication is disabled.")
    payload = {
        "sub": principal.user_id,
        "org": principal.organization_id,
        "role": principal.role,
        "workspace": principal.workspace,
        "exp": int(time.time()) + 60 * 60 * 8,
    }
    encoded = _encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.dev_auth_secret.encode(), encoded.encode(), hashlib.sha256
    ).digest()
    return f"{encoded}.{_encode(signature)}"


def verify_token(token: str, settings: Settings) -> Principal:
    try:
        encoded, provided_signature = token.split(".", maxsplit=1)
        expected_signature = _encode(
            hmac.new(settings.dev_auth_secret.encode(), encoded.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise ValueError("invalid signature")
        payload = json.loads(_decode(encoded))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired token")
        return Principal(payload["sub"], payload["org"], payload["role"], payload["workspace"])
    except (KeyError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=401, detail="Invalid or expired authentication token."
        ) from error


def require_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    settings: Settings = request.app.state.settings
    if settings.app_env.lower() != "development" or not settings.dev_auth_enabled:
        raise HTTPException(
            status_code=503,
            detail="A production identity provider is required; development auth is disabled.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication is required.")
    return verify_token(credentials.credentials, settings)
