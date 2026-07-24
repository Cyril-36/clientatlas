from __future__ import annotations

from uuid import uuid4

import pytest

from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.storage import LocalObjectStorage, generated_object_path


async def test_local_storage_round_trip_and_deletion(tmp_path: object) -> None:
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    storage = LocalObjectStorage(tmp_path)
    path = generated_object_path(uuid4(), uuid4(), uuid4(), uuid4(), "client.pdf")
    await storage.put(path, b"%PDF-1.7")
    assert await storage.get(path) == b"%PDF-1.7"
    await storage.delete(path)
    with pytest.raises(SafeServiceError, match="source_object_missing"):
        await storage.get(path)


async def test_local_storage_rejects_path_escape(tmp_path: object) -> None:
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    storage = LocalObjectStorage(tmp_path)
    with pytest.raises(SafeServiceError, match="invalid_object_path"):
        await storage.put("../../escape", b"no")
