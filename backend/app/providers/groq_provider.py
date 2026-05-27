"""
Groq provider implementation.
Groq uses an OpenAI-compatible API — extremely fast inference.
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.config.cost_table import compute_cost


class GroqProvider(AIProvider):
    """Groq provider — OpenAI-compatible, ultra-low latency."""

    provider_name = "groq"

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
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
        system_content = system or ""
        if response_schema:
            schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
            system_content += f"\n\nYou MUST respond with valid JSON only matching this exact schema:\n{schema_json}\nNo markdown, no explanation — pure JSON."
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if response_schema else None,
        )

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
