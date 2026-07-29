from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CLIENTATLAS_",
        extra="ignore",
        frozen=True,
    )

    environment: Literal["development", "test", "production"] = "development"
    user_database_url: PostgresDsn
    supabase_jwt_issuer: AnyHttpUrl
    supabase_jwt_audience: str = "authenticated"
    supabase_jwks_url: AnyHttpUrl
    object_storage_root: Path = Path(".clientatlas/storage")
    max_upload_bytes: int = 25 * 1024 * 1024
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_generation_model: str = "google/flan-t5-small"
    huggingface_embedding_device: str = "cpu"
    huggingface_generation_device: int = -1
    embedding_dimensions: int = 384
    local_model_max_input_characters: int = 8_000
    local_model_max_new_tokens: int = 256
    llm_timeout_seconds: float = 180.0
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash-lite"
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: SecretStr | None = None
    google_oauth_redirect_uri: AnyHttpUrl | None = None
    token_encryption_key: SecretStr | None = None
    otlp_endpoint: AnyHttpUrl | None = None
    telemetry_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
