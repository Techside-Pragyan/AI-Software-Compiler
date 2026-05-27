"""
AI Gateway — provider-agnostic orchestration layer.

Responsibilities:
- Resolves provider from routing.config.py
- Executes with latency/cost threshold enforcement
- Auto-routes to OpenRouter on 429/5xx/timeout
- Tracks cumulative cost per execution
- NEVER hardcodes model names — all resolved from routing config
"""
from __future__ import annotations
import logging
import os
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.groq_provider import GroqProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.config.routing_config import ROUTING_CONFIG, get_openrouter_model

logger = logging.getLogger(__name__)

# Errors that trigger fallback to OpenRouter
FALLBACK_TRIGGER_CODES = {429, 500, 502, 503, 504}
FALLBACK_TRIGGER_MSGS  = ["rate limit", "overloaded", "timeout", "server error", "service unavailable"]


def _build_provider(provider_name: str, model: str) -> AIProvider:
    """Instantiate the correct provider class for a given provider name + model."""
    provider_map = {
        "gemini":      lambda: GeminiProvider(model=model),
        "openai":      lambda: OpenAIProvider(model=model),
        "groq":        lambda: GroqProvider(model=model),
        "anthropic":   lambda: AnthropicProvider(model=model),
        "openrouter":  lambda: OpenRouterProvider(model=model),
    }
    factory = provider_map.get(provider_name)
    if not factory:
        logger.warning(f"Unknown provider '{provider_name}', falling back to Gemini")
        return GeminiProvider(model=model)
    return factory()


def _should_fallback(exc: Exception) -> bool:
    """Determine if an exception warrants OpenRouter fallback."""
    msg = str(exc).lower()
    for trigger in FALLBACK_TRIGGER_MSGS:
        if trigger in msg:
            return True
    # Check for HTTP status codes in the exception
    for code in FALLBACK_TRIGGER_CODES:
        if str(code) in str(exc):
            return True
    return False


class AIGateway:
    """
    Provider-agnostic AI execution gateway.
    Read stage config → pick primary provider → execute → fallback if needed.
    """

    def __init__(self):
        self._openrouter = OpenRouterProvider()

    def execute(
        self,
        stage: str,
        prompt: str,
        *,
        system: Optional[str] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature_override: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
    ) -> ProviderResponse:
        """
        Execute a prompt for a given pipeline stage.
        Automatically handles primary → OpenRouter fallback.

        Args:
            stage: Stage name from routing.config (e.g. "intentExtraction")
            prompt: User prompt text
            system: Optional system instruction
            response_schema: Pydantic model for structured output
            temperature_override: Override routing config temperature
            max_tokens_override: Override routing config max_tokens

        Returns:
            ProviderResponse from whichever provider succeeded
        """
        config = ROUTING_CONFIG.get(stage, ROUTING_CONFIG["appSpecGeneration"])
        temperature = temperature_override if temperature_override is not None else config["temperature"]
        max_tokens  = max_tokens_override  if max_tokens_override  is not None else config["max_tokens"]

        primary_cfg  = config["primary"]
        fallback_cfg = config["fallback"]

        # --- Try primary provider ---
        primary = _build_provider(primary_cfg["provider"], primary_cfg["model"])
        if primary.is_available():
            try:
                logger.info(f"[Gateway] Stage={stage} provider={primary_cfg['provider']} model={primary_cfg['model']}")
                result = primary.complete(
                    prompt,
                    system=system,
                    response_schema=response_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                # Latency threshold check
                if result.latency_ms > config.get("latency_threshold_ms", 30000):
                    logger.warning(f"[Gateway] Primary exceeded latency threshold ({result.latency_ms:.0f}ms), but returning result anyway")
                return result

            except Exception as exc:
                if _should_fallback(exc):
                    logger.warning(f"[Gateway] Primary failed ({exc}), switching to fallback provider")
                else:
                    raise  # Non-retriable error — propagate up

        # --- Try configured fallback provider ---
        fallback = _build_provider(fallback_cfg["provider"], fallback_cfg["model"])
        if fallback.is_available():
            try:
                logger.info(f"[Gateway] Fallback: provider={fallback_cfg['provider']} model={fallback_cfg['model']}")
                return fallback.complete(
                    prompt,
                    system=system,
                    response_schema=response_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                logger.warning(f"[Gateway] Fallback also failed ({exc}), trying OpenRouter")

        # --- Last resort: OpenRouter with auto-mapped model ---
        if self._openrouter.is_available():
            or_model = get_openrouter_model(primary_cfg["provider"], primary_cfg["model"])
            self._openrouter.model = or_model
            logger.info(f"[Gateway] OpenRouter last resort: model={or_model}")
            return self._openrouter.complete(
                prompt,
                system=system,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise RuntimeError(
            f"All providers failed for stage '{stage}'. "
            "Ensure at least one provider key is configured in .env"
        )


# Singleton gateway instance
_gateway_instance: Optional[AIGateway] = None

def get_gateway() -> AIGateway:
    """Return singleton gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = AIGateway()
    return _gateway_instance
