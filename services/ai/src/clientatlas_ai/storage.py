from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from clientatlas_ai.errors import SafeServiceError


def generated_object_path(
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
    version_id: UUID,
    filename: str,
) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise SafeServiceError("unsupported_file_extension")
    return (
        f"{organization_id}/{workspace_id}/{source_id}/{version_id}/source{extension}"
    )


class LocalObjectStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _resolve(self, object_path: str) -> Path:
        candidate = (self._root / object_path).resolve()
        if self._root not in candidate.parents:
            raise SafeServiceError("invalid_object_path")
        return candidate

    async def put(self, object_path: str, content: bytes) -> None:
        target = self._resolve(object_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.partial")
        temporary.write_bytes(content)
        os.replace(temporary, target)

    async def get(self, object_path: str) -> bytes:
        target = self._resolve(object_path)
        try:
            return target.read_bytes()
        except FileNotFoundError as error:
            raise SafeServiceError("source_object_missing", status_code=404) from error

    async def delete(self, object_path: str) -> None:
        target = self._resolve(object_path)
        target.unlink(missing_ok=True)
        parent = target.parent
        while parent != self._root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
