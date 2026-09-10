import asyncio
from collections.abc import Awaitable, Callable

from ..config import get_settings
from ..providers.base import TransientProviderError


async def with_retries(operation: Callable[[], Awaitable], *, attempts: int | None = None, sleep: Callable[[float], Awaitable] = asyncio.sleep):
    max_attempts = attempts or get_settings().provider_max_attempts
    backoffs: list[int] = []
    for number in range(1, max_attempts + 1):
        try:
            return await operation(), number, backoffs
        except TransientProviderError:
            if number == max_attempts:
                raise
            delay_ms = get_settings().retry_base_delay_ms * (2 ** (number - 1))
            backoffs.append(delay_ms)
            await sleep(delay_ms / 1000)
