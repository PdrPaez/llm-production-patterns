from typing import Protocol

from ..schemas import ProviderRequest, ProviderResponse


class TransientProviderError(Exception):
    """A retryable temporary provider failure."""


class ProviderUnavailableError(Exception):
    """A provider cannot serve this request right now."""


class ProviderConfigurationError(Exception):
    """A provider is incorrectly configured and should not be retried."""


class LLMProvider(Protocol):
    name: str

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        ...
