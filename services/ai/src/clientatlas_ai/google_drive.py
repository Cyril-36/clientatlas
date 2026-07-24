from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

import httpx
import jwt
from anyio import to_thread
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jwt import PyJWKClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.database import with_user_database
from clientatlas_ai.errors import SafeServiceError

GOOGLE_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
GOOGLE_SCOPES = ("openid", "email", GOOGLE_DRIVE_SCOPE)
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class TokenCipher:
    def __init__(self, encoded_key: str) -> None:
        try:
            key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
        except (ValueError, UnicodeError) as error:
            raise SafeServiceError(
                "invalid_token_encryption_key", status_code=500
            ) from error
        if len(key) != 32:
            raise SafeServiceError("invalid_token_encryption_key", status_code=500)
        self._cipher = AESGCM(key)

    def encrypt(self, plaintext: str, associated_data: str) -> bytes:
        nonce = secrets.token_bytes(12)
        ciphertext = self._cipher.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            associated_data.encode("utf-8"),
        )
        return nonce + ciphertext

    def decrypt(self, value: bytes, associated_data: str) -> str:
        if len(value) < 29:
            raise SafeServiceError("invalid_encrypted_credential", status_code=500)
        try:
            plaintext = self._cipher.decrypt(
                value[:12],
                value[12:],
                associated_data.encode("utf-8"),
            )
        except Exception as error:
            raise SafeServiceError(
                "credential_decryption_failed",
                status_code=500,
            ) from error
        return plaintext.decode("utf-8")


def credential_context(
    organization_id: UUID,
    workspace_id: UUID,
    user_id: UUID,
) -> str:
    return f"{organization_id}:{workspace_id}:{user_id}:google-drive"


@dataclass(frozen=True, slots=True)
class OAuthStart:
    authorization_url: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ConsumedOAuthState:
    organization_id: UUID
    pkce_verifier: str
    workspace_id: UUID


@dataclass(frozen=True, slots=True)
class GoogleTokens:
    access_token: str
    id_token: str
    refresh_token: str | None
    scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DriveFile:
    content: bytes
    file_id: str
    filename: str
    mime_type: str


class GoogleOAuthClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        timeout_seconds: float,
    ) -> None:
        self.client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._timeout = timeout_seconds
        self._jwks = PyJWKClient(GOOGLE_JWKS_URL, cache_jwk_set=True, lifespan=600)

    async def exchange_code(self, code: str, verifier: str) -> GoogleTokens:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "code_verifier": verifier,
                        "grant_type": "authorization_code",
                        "redirect_uri": self._redirect_uri,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            scopes = tuple(str(payload.get("scope", "")).split())
            return GoogleTokens(
                access_token=str(payload["access_token"]),
                id_token=str(payload["id_token"]),
                refresh_token=(
                    str(payload["refresh_token"])
                    if payload.get("refresh_token")
                    else None
                ),
                scopes=scopes,
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise SafeServiceError(
                "google_oauth_exchange_failed", status_code=502
            ) from error

    async def verify_identity(self, id_token: str) -> str:
        try:
            signing_key = await to_thread.run_sync(
                self._jwks.get_signing_key_from_jwt,
                id_token,
            )
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer="https://accounts.google.com",
                options={"require": ["aud", "exp", "iss", "sub"]},
            )
            return str(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError) as error:
            raise SafeServiceError(
                "google_identity_invalid", status_code=403
            ) from error

    async def refresh(self, refresh_token: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self._client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )
                response.raise_for_status()
                return str(response.json()["access_token"])
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise SafeServiceError(
                "google_token_refresh_failed", status_code=502
            ) from error

    async def download_selected_file(
        self,
        access_token: str,
        file_id: str,
        *,
        max_bytes: int,
    ) -> DriveFile:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                metadata_response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    headers=headers,
                    params={"fields": "id,name,mimeType,size"},
                )
                metadata_response.raise_for_status()
                metadata = metadata_response.json()
                if str(metadata.get("id")) != file_id:
                    raise SafeServiceError(
                        "google_file_identity_mismatch", status_code=502
                    )
                declared_size = int(metadata.get("size", 0))
                if declared_size > max_bytes:
                    raise SafeServiceError("file_too_large", status_code=413)
                download_response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    headers=headers,
                    params={"alt": "media"},
                )
                download_response.raise_for_status()
                content = download_response.content
            if len(content) > max_bytes:
                raise SafeServiceError("file_too_large", status_code=413)
            return DriveFile(
                content=content,
                file_id=file_id,
                filename=str(metadata["name"]),
                mime_type=str(metadata["mimeType"]),
            )
        except SafeServiceError:
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise SafeServiceError(
                "google_file_download_failed", status_code=502
            ) from error

    async def revoke(self, refresh_token: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    GOOGLE_REVOKE_URL,
                    data={"token": refresh_token},
                )
                if response.status_code not in {200, 400}:
                    response.raise_for_status()
        except httpx.HTTPError as error:
            raise SafeServiceError("google_revoke_failed", status_code=502) from error


class GoogleDriveConnector:
    def __init__(
        self,
        *,
        oauth: GoogleOAuthClient,
        cipher: TokenCipher,
        redirect_uri: str,
    ) -> None:
        self._oauth = oauth
        self._cipher = cipher
        self._redirect_uri = redirect_uri

    async def begin(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
    ) -> OAuthStart:
        state = _base64url(secrets.token_bytes(32))
        verifier = _base64url(secrets.token_bytes(64))
        challenge = _base64url(hashlib.sha256(verifier.encode("ascii")).digest())
        state_hash = hashlib.sha256(state.encode("ascii")).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        context = credential_context(organization_id, workspace_id, claims.subject)
        encrypted_verifier = self._cipher.encrypt(verifier, context)

        async def persist(session: AsyncSession) -> None:
            await session.execute(
                text(
                    """
                    select app.begin_google_drive_oauth(
                      :organization_id, :workspace_id, :state_hash,
                      :encrypted_verifier, :expires_at
                    )
                    """
                ),
                {
                    "encrypted_verifier": encrypted_verifier,
                    "expires_at": expires_at,
                    "organization_id": organization_id,
                    "state_hash": state_hash,
                    "workspace_id": workspace_id,
                },
            )

        await with_user_database(claims, persist)
        query = urlencode(
            {
                "access_type": "offline",
                "client_id": self._oauth.client_id,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "include_granted_scopes": "false",
                "prompt": "consent",
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": " ".join(GOOGLE_SCOPES),
                "state": state,
            }
        )
        return OAuthStart(
            authorization_url=f"{GOOGLE_AUTHORIZE_URL}?{query}",
            expires_at=expires_at,
        )

    async def complete(
        self,
        *,
        claims: VerifiedClaims,
        expected_organization_id: UUID,
        expected_workspace_id: UUID,
        state: str,
        code: str,
    ) -> UUID:
        state_hash = hashlib.sha256(state.encode("ascii")).hexdigest()

        async def consume(session: AsyncSession) -> tuple[UUID, UUID, bytes] | None:
            result = await session.execute(
                text("select * from app.consume_google_drive_oauth(:state_hash)"),
                {"state_hash": state_hash},
            )
            row = result.first()
            if row is None:
                return None
            return (
                UUID(str(row.organization_id)),
                UUID(str(row.workspace_id)),
                bytes(row.encrypted_pkce_verifier),
            )

        consumed = await with_user_database(claims, consume)
        if consumed is None:
            raise SafeServiceError("oauth_state_invalid_or_used", status_code=403)
        organization_id, workspace_id, encrypted_verifier = consumed
        if (
            organization_id != expected_organization_id
            or workspace_id != expected_workspace_id
        ):
            raise SafeServiceError("oauth_workspace_mismatch", status_code=403)
        context = credential_context(organization_id, workspace_id, claims.subject)
        verifier = self._cipher.decrypt(encrypted_verifier, context)
        tokens = await self._oauth.exchange_code(code, verifier)
        if GOOGLE_DRIVE_SCOPE not in tokens.scopes:
            raise SafeServiceError("google_scope_missing", status_code=403)
        if not set(tokens.scopes).issubset(GOOGLE_SCOPES):
            raise SafeServiceError("google_scope_too_broad", status_code=403)
        if tokens.refresh_token is None:
            raise SafeServiceError("google_refresh_token_missing", status_code=403)
        google_subject = await self._oauth.verify_identity(tokens.id_token)
        encrypted_refresh = self._cipher.encrypt(tokens.refresh_token, context)

        async def save(session: AsyncSession) -> UUID:
            result = await session.execute(
                text(
                    """
                    select app.save_google_drive_connection(
                      :organization_id, :workspace_id, :google_subject,
                      cast(:scopes as text[]), :encrypted_refresh
                    )
                    """
                ),
                {
                    "encrypted_refresh": encrypted_refresh,
                    "google_subject": google_subject,
                    "organization_id": organization_id,
                    "scopes": list(tokens.scopes),
                    "workspace_id": workspace_id,
                },
            )
            return UUID(str(result.scalar_one()))

        return await with_user_database(claims, save)

    async def access_token(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
    ) -> tuple[str, str]:
        async def load(session: AsyncSession) -> tuple[str, bytes] | None:
            result = await session.execute(
                text(
                    """
                    select google_subject, encrypted_refresh_token
                    from app.get_google_drive_credential(
                      :organization_id, :workspace_id
                    )
                    """
                ),
                {
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
                },
            )
            row = result.first()
            if row is None:
                return None
            return str(row.google_subject), bytes(row.encrypted_refresh_token)

        credential = await with_user_database(claims, load)
        if credential is None:
            raise SafeServiceError("google_connection_not_found", status_code=404)
        subject, encrypted_refresh = credential
        context = credential_context(organization_id, workspace_id, claims.subject)
        refresh_token = self._cipher.decrypt(encrypted_refresh, context)
        return subject, await self._oauth.refresh(refresh_token)

    async def download_selected_file(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
        file_id: str,
        max_bytes: int,
    ) -> DriveFile:
        _subject, access_token = await self.access_token(
            claims=claims,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        return await self._oauth.download_selected_file(
            access_token,
            file_id,
            max_bytes=max_bytes,
        )

    async def revoke(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        try:
            _subject, access_token = await self.access_token(
                claims=claims,
                organization_id=organization_id,
                workspace_id=workspace_id,
            )
            await self._oauth.revoke(access_token)
        except SafeServiceError as error:
            if error.code == "google_connection_not_found":
                return False
            raise

        async def remove(session: AsyncSession) -> bool:
            result = await session.execute(
                text(
                    """
                    select app.revoke_google_drive_connection(
                      :organization_id, :workspace_id
                    )
                    """
                ),
                {
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
                },
            )
            return bool(result.scalar_one())

        return await with_user_database(claims, remove)
