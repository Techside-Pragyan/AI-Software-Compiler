"""
OpenAI provider implementation.
Supports JSON mode and structured output.
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.config.cost_table import compute_cost


class OpenAIProvider(AIProvider):
    """OpenAI provider with JSON mode structured output."""

    provider_name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
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
        client = self._get_client()
        start = time.time()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_schema:
            # Use JSON mode with schema hint in system prompt
            schema_hint = f"\n\nRespond ONLY with valid JSON matching this schema:\n{response_schema.model_json_schema()}"
            if messages and messages[-1]["role"] == "system":
                messages[-1]["content"] += schema_hint
            else:
                messages.insert(0, {"role": "system", "content": schema_hint})
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        latency_ms = (time.time() - start) * 1000
        text = response.choices[0].message.content or ""
        tokens_in  = response.usage.prompt_tokens     if response.usage else 0
        tokens_out = response.usage.completion_tokens if response.usage else 0
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
