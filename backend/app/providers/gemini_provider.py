"""
Google Gemini provider implementation.
Uses google-genai SDK with structured output support.
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.config.cost_table import compute_cost


class GeminiProvider(AIProvider):
    """Google Gemini provider with structured JSON output support."""

    provider_name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        from google.genai import types

        client = self._get_client()
        start = time.time()

        config_kwargs = {
            "response_mime_type": "application/json",
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system:
            config_kwargs["system_instruction"] = system
        if response_schema:
            config_kwargs["response_schema"] = response_schema

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        latency_ms = (time.time() - start) * 1000
        text = response.text or ""

        # Token usage
        tokens_in  = getattr(getattr(response, "usage_metadata", None), "prompt_token_count",     0) or 0
        tokens_out = getattr(getattr(response, "usage_metadata", None), "candidates_token_count",  0) or 0
        cost = compute_cost(self.provider_name, self.model, tokens_in, tokens_out)

        return ProviderResponse(
            text=text,
            provider=self.provider_name,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=cost,
            raw_response=response,
        )
