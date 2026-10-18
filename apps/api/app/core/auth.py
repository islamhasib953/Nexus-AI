import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx
import jwt
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


class AuthenticationError(ValueError):
    """Safe authentication failure without provider details."""


class OIDCAuthenticator:
    """OIDC JWT verifier with bounded JWKS caching and key-rotation refresh."""

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str,
        algorithms: tuple[str, ...] = ("RS256",),
        *,
        cache_ttl_seconds: float = 300,
        client: httpx.Client | None = None,
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.jwks_url = jwks_url
        self.algorithms = algorithms
        self.cache_ttl_seconds = cache_ttl_seconds
        self._client = client
        self._jwks: dict[str, dict[str, Any]] = {}
        self._jwks_expires_at = 0.0

    def _load_keys(self, *, force: bool = False) -> dict[str, dict[str, Any]]:
        now = monotonic()
        if not force and self._jwks and now < self._jwks_expires_at:
            return self._jwks
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=5.0)
        try:
            response = client.get(self.jwks_url)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise AuthenticationError("Identity provider keys are unavailable.") from error
        finally:
            if owns_client:
                client.close()
        keys = body.get("keys") if isinstance(body, dict) else None
        if not isinstance(keys, list):
            raise AuthenticationError("Identity provider returned invalid JWKS data.")
        self._jwks = {
            item["kid"]: item
            for item in keys
            if isinstance(item, dict) and isinstance(item.get("kid"), str)
        }
        self._jwks_expires_at = now + self.cache_ttl_seconds
        return self._jwks

    def verify(self, token: str) -> Principal:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not isinstance(kid, str):
                raise AuthenticationError("Token key ID is missing.")
            key_data = self._load_keys().get(kid) or self._load_keys(force=True).get(kid)
            if key_data is None:
                raise AuthenticationError("Token signing key is unknown.")
            key = jwt.PyJWK.from_dict(key_data).key
            claims = jwt.decode(
                token,
                key=key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
            organization_id = claims.get("org") or claims.get("organization_id")
            role = claims.get("role")
            workspace = claims.get("workspace")
            if not all(
                isinstance(value, str) and value
                for value in (claims.get("sub"), organization_id, role, workspace)
            ):
                raise AuthenticationError("Token is missing required tenant claims.")
            return Principal(claims["sub"], organization_id, role, workspace)
        except AuthenticationError:
            raise
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise AuthenticationError("Invalid identity token.") from error


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
    if settings.identity_provider == "oidc":
        authenticator: OIDCAuthenticator | None = getattr(request.app.state, "authenticator", None)
        if authenticator is None:
            raise HTTPException(status_code=503, detail="Identity provider is not configured.")
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Authentication is required.")
        try:
            return authenticator.verify(credentials.credentials)
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
    if settings.app_env.lower() != "development" or not settings.dev_auth_enabled:
        raise HTTPException(
            status_code=503,
            detail="A production identity provider is required; development auth is disabled.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication is required.")
    return verify_token(credentials.credentials, settings)
