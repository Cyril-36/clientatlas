from __future__ import annotations

from uuid import uuid4

import pytest

from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.rate_limit import SlidingWindowRateLimiter


async def test_rate_limiter_is_scoped_by_user_and_operation() -> None:
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
    user_a, user_b = uuid4(), uuid4()
    await limiter.check(user_a, "chat")
    await limiter.check(user_a, "chat")
    await limiter.check(user_a, "artifact")
    await limiter.check(user_b, "chat")
    with pytest.raises(SafeServiceError, match="rate_limit_exceeded"):
        await limiter.check(user_a, "chat")
