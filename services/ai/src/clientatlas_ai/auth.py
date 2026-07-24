from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

import jwt
from anyio import to_thread
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from clientatlas_ai.settings import Settings, get_settings

BEARER_PATTERN = re.compile(r"^Bearer ([A-Za-z0-9._~-]+)$")
ALLOWED_ALGORITHMS = ("ES256", "RS256", "EdDSA")


@dataclass(frozen=True, slots=True)
class VerifiedClaims:
    audience: str | tuple[str, ...]
    expires_at: int
    issuer: str
    role: str
    subject: UUID

    def database_payload(self) -> dict[str, Any]:
        return {
            "aud": self.audience,
            "exp": self.expires_at,
            "iss": self.issuer,
            "role": self.role,
            "sub": str(self.subject),
        }


class AccessTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._audience = settings.supabase_jwt_audience
        self._issuer = str(settings.supabase_jwt_issuer).rstrip("/")
        self._jwks_client = PyJWKClient(
            str(settings.supabase_jwks_url),
            cache_jwk_set=True,
            lifespan=600,
            timeout=5,
        )

    async def verify(self, token: str) -> VerifiedClaims:
        signing_key = await to_thread.run_sync(
            self._jwks_client.get_signing_key_from_jwt,
            token,
        )
        return decode_verified_claims(
            token,
            signing_key.key,
            audience=self._audience,
            issuer=self._issuer,
        )


def decode_verified_claims(
    token: str,
    key: Any,
    *,
    audience: str,
    issuer: str,
) -> VerifiedClaims:
    payload = jwt.decode(
        token,
        key,
        algorithms=list(ALLOWED_ALGORITHMS),
        audience=audience,
        issuer=issuer,
        options={
            "require": ["aud", "exp", "iss", "role", "sub"],
            "verify_aud": True,
            "verify_exp": True,
            "verify_iss": True,
            "verify_nbf": True,
            "verify_signature": True,
        },
    )

    if payload.get("role") != "authenticated":
        raise jwt.InvalidTokenError("unexpected role")

    raw_audience = payload["aud"]
    normalized_audience: str | tuple[str, ...]
    if isinstance(raw_audience, list):
        normalized_audience = tuple(str(item) for item in raw_audience)
    else:
        normalized_audience = str(raw_audience)

    return VerifiedClaims(
        audience=normalized_audience,
        expires_at=int(payload["exp"]),
        issuer=str(payload["iss"]),
        role="authenticated",
        subject=UUID(str(payload["sub"])),
    )


def extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required"},
        )

    match = BEARER_PATTERN.fullmatch(authorization)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_authorization_header"},
        )
    return match.group(1)


_verifier: AccessTokenVerifier | None = None


def get_access_token_verifier() -> AccessTokenVerifier:
    global _verifier
    if _verifier is None:
        _verifier = AccessTokenVerifier(get_settings())
    return _verifier


async def require_verified_claims(
    authorization: Annotated[str | None, Header()] = None,
) -> VerifiedClaims:
    token = extract_bearer_token(authorization)
    try:
        return await get_access_token_verifier().verify(token)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_access_token"},
        ) from None
