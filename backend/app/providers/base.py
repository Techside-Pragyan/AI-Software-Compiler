"""
Abstract base class for all AI providers.
Every provider must implement this interface.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Type
from pydantic import BaseModel


@dataclass
class ProviderResponse:
    """Typed response from any AI provider."""
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    raw_response: Optional[object] = field(default=None, repr=False)


class AIProvider(ABC):
    """Abstract provider interface — all providers must implement complete()."""

    provider_name: str = "unknown"

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        """
        Execute a completion request.

        Args:
            prompt: The user prompt text
            system: Optional system instruction
            response_schema: Optional Pydantic model class for structured JSON output
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum output tokens

        Returns:
            ProviderResponse with text, token counts, cost, latency
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider has valid credentials configured."""
        return True
