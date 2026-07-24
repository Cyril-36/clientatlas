from __future__ import annotations

import io

import pytest
from docx import Document

from clientatlas_ai.chunking import chunk_blocks
from clientatlas_ai.documents import DOCX_MIME, parse_document, validate_document
from clientatlas_ai.errors import SafeServiceError


def make_docx(*paragraphs: str) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def test_validates_and_parses_docx() -> None:
    content = make_docx("Implementation owner is Avery.", "Launch is 15 October.")
    mime = validate_document(
        "onboarding.docx",
        DOCX_MIME,
        content,
        max_bytes=1_000_000,
    )
    parsed = parse_document(mime, content)
    assert len(parsed.blocks) == 2
    assert parsed.blocks[0].locator == {"paragraph": 1}


def test_rejects_mime_extension_mismatch() -> None:
    with pytest.raises(SafeServiceError, match="mime_extension_mismatch"):
        validate_document(
            "onboarding.docx",
            "application/pdf",
            make_docx("text"),
            max_bytes=1_000_000,
        )


def test_rejects_traversal_as_unsupported_extension() -> None:
    with pytest.raises(SafeServiceError, match="unsupported_file_extension"):
        validate_document(
            "../../secret.env",
            "text/plain",
            b"secret",
            max_bytes=1_000_000,
        )


def test_chunking_is_deterministic_and_overlapping() -> None:
    content = make_docx(" ".join(f"word-{index}" for index in range(900)))
    chunks = chunk_blocks(parse_document(DOCX_MIME, content).blocks)
    assert len(chunks) == 2
    assert chunks[0].ordinal == 0
    assert chunks[1].ordinal == 1
    assert chunks[1].locator["word_start"] == 620
