from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from clientatlas_ai.auth import decode_verified_claims, extract_bearer_token

ISSUER = "https://example.supabase.co/auth/v1"
AUDIENCE = "authenticated"


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def create_token(
    key: rsa.RSAPrivateKey,
    *,
    audience: str = AUDIENCE,
    issuer: str = ISSUER,
    role: str = "authenticated",
    subject: str | None = None,
    expires_delta: timedelta = timedelta(minutes=5),
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "aud": audience,
            "exp": now + expires_delta,
            "iat": now,
            "iss": issuer,
            "role": role,
            "sub": subject or str(uuid4()),
        },
        key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def test_extract_bearer_token() -> None:
    assert extract_bearer_token("Bearer a.b.c") == "a.b.c"


@pytest.mark.parametrize(
    "authorization, expected_status",
    [
        (None, 401),
        ("bearer a.b.c", 403),
        ("Bearer", 403),
        ("Bearer a.b.c extra", 403),
    ],
)
def test_extract_bearer_token_rejects_invalid_header(
    authorization: str | None,
    expected_status: int,
) -> None:
    with pytest.raises(HTTPException) as error:
        extract_bearer_token(authorization)
    assert error.value.status_code == expected_status


def test_decode_verified_claims(rsa_key: rsa.RSAPrivateKey) -> None:
    subject = str(uuid4())
    token = create_token(rsa_key, subject=subject)
    claims = decode_verified_claims(
        token,
        rsa_key.public_key(),
        audience=AUDIENCE,
        issuer=ISSUER,
    )
    assert str(claims.subject) == subject
    assert claims.role == "authenticated"


@pytest.mark.parametrize(
    "overrides",
    [
        {"audience": "wrong"},
        {"issuer": "https://attacker.invalid/auth/v1"},
        {"role": "service_role"},
        {"subject": "not-a-uuid"},
        {"expires_delta": timedelta(seconds=-1)},
    ],
)
def test_decode_verified_claims_rejects_invalid_tokens(
    rsa_key: rsa.RSAPrivateKey,
    overrides: dict[str, object],
) -> None:
    token = create_token(rsa_key, **overrides)  # type: ignore[arg-type]
    with pytest.raises((jwt.InvalidTokenError, ValueError)):
        decode_verified_claims(
            token,
            rsa_key.public_key(),
            audience=AUDIENCE,
            issuer=ISSUER,
        )
