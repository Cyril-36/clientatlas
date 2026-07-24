from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest

from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.google_drive import (
    GOOGLE_DRIVE_SCOPE,
    GOOGLE_SCOPES,
    TokenCipher,
    credential_context,
)
from clientatlas_ai.routes_google_drive import ImportDriveFileRequest


def encryption_key() -> str:
    return base64.urlsafe_b64encode(bytes(range(32))).decode("ascii")


def test_refresh_token_encryption_is_bound_to_tenant_and_user() -> None:
    cipher = TokenCipher(encryption_key())
    context = credential_context(uuid4(), uuid4(), uuid4())
    encrypted = cipher.encrypt("refresh-secret", context)
    assert b"refresh-secret" not in encrypted
    assert cipher.decrypt(encrypted, context) == "refresh-secret"
    with pytest.raises(SafeServiceError, match="credential_decryption_failed"):
        cipher.decrypt(encrypted, f"{context}:other")


def test_drive_scope_is_narrow_and_fixed() -> None:
    assert GOOGLE_SCOPES == ("openid", "email", GOOGLE_DRIVE_SCOPE)
    assert GOOGLE_DRIVE_SCOPE.endswith("/drive.file")
    assert all(
        scope != "https://www.googleapis.com/auth/drive" for scope in GOOGLE_SCOPES
    )


def test_drive_file_id_validation_rejects_paths_and_urls() -> None:
    assert ImportDriveFileRequest(file_id="abc_123-Z").file_id == "abc_123-Z"
    for value in ("../secret", "https://drive.google.com/file", "a/b"):
        with pytest.raises(ValueError):
            ImportDriveFileRequest(file_id=value)


def test_authorization_url_query_parser_example() -> None:
    parsed = urlparse(
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "scope=openid+email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.file"
    )
    assert GOOGLE_DRIVE_SCOPE in parse_qs(parsed.query)["scope"][0]
