from __future__ import annotations

from functools import lru_cache

from clientatlas_ai.embeddings import (
    DeterministicEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
)
from clientatlas_ai.ingestion import IngestionService
from clientatlas_ai.settings import get_settings
from clientatlas_ai.storage import LocalObjectStorage


@lru_cache
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    embeddings = (
        DeterministicEmbeddingProvider(settings.embedding_dimensions)
        if settings.environment == "test"
        else HuggingFaceEmbeddingProvider(
            model=settings.huggingface_embedding_model,
            device=settings.huggingface_embedding_device,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    )
    return IngestionService(
        storage=LocalObjectStorage(settings.object_storage_root),
        embeddings=embeddings,
        max_upload_bytes=settings.max_upload_bytes,
    )
