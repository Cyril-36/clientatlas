from __future__ import annotations

from dataclasses import dataclass

from clientatlas_ai.documents import ParsedBlock

MAX_CHUNK_WORDS = 700
CHUNK_OVERLAP_WORDS = 80
MAX_CHUNK_CHARACTERS = 12_000


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    content: str
    locator: dict[str, str | int]
    ordinal: int
    token_count: int


def chunk_blocks(blocks: tuple[ParsedBlock, ...]) -> tuple[DocumentChunk, ...]:
    chunks: list[DocumentChunk] = []
    for block in blocks:
        words = block.text.split()
        start = 0
        while start < len(words):
            end = min(start + MAX_CHUNK_WORDS, len(words))
            content = " ".join(words[start:end])[:MAX_CHUNK_CHARACTERS].strip()
            if content:
                locator = dict(block.locator)
                locator["word_start"] = start
                locator["word_end"] = end
                chunks.append(
                    DocumentChunk(
                        content=content,
                        locator=locator,
                        ordinal=len(chunks),
                        token_count=max(1, (len(content) + 3) // 4),
                    )
                )
            if end == len(words):
                break
            start = end - CHUNK_OVERLAP_WORDS
    return tuple(chunks)
