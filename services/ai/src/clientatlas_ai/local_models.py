from __future__ import annotations

import asyncio
import importlib
from collections.abc import Sequence
from functools import lru_cache
from threading import Lock
from typing import Protocol, cast

_embedding_lock = Lock()
_generation_lock = Lock()


class SentenceEncoder(Protocol):
    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object: ...


class TextPipeline(Protocol):
    def __call__(self, prompt: str, **kwargs: object) -> object: ...


@lru_cache
def _load_sentence_encoder(model: str, device: str) -> SentenceEncoder:
    module = importlib.import_module("sentence_transformers")
    constructor = module.SentenceTransformer
    return cast(SentenceEncoder, constructor(model, device=device))


@lru_cache
def _load_text_pipeline(model: str, device: int) -> TextPipeline:
    module = importlib.import_module("transformers")
    factory = module.pipeline
    return cast(
        TextPipeline,
        factory(
            "text2text-generation",
            model=model,
            device=device,
        ),
    )


async def encode_sentences(
    texts: Sequence[str],
    *,
    model: str,
    device: str,
    timeout_seconds: float,
) -> object:
    def run() -> object:
        with _embedding_lock:
            encoder = _load_sentence_encoder(model, device)
            return encoder.encode(
                list(texts),
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

    return await asyncio.wait_for(
        asyncio.to_thread(run),
        timeout=timeout_seconds,
    )


async def generate_text(
    prompt: str,
    *,
    model: str,
    device: int,
    max_input_characters: int,
    max_new_tokens: int,
    timeout_seconds: float,
) -> str:
    bounded_prompt = prompt[:max_input_characters]

    def run() -> object:
        with _generation_lock:
            generator = _load_text_pipeline(model, device)
            return generator(
                bounded_prompt,
                do_sample=False,
                max_new_tokens=max_new_tokens,
                truncation=True,
            )

    raw = await asyncio.wait_for(
        asyncio.to_thread(run),
        timeout=timeout_seconds,
    )
    if not isinstance(raw, list) or len(raw) != 1:
        raise ValueError("invalid local text-generation response")
    candidate = raw[0]
    if not isinstance(candidate, dict):
        raise ValueError("invalid local text-generation candidate")
    generated = candidate.get("generated_text")
    if not isinstance(generated, str) or not generated.strip():
        raise ValueError("empty local text-generation response")
    return generated.strip()
