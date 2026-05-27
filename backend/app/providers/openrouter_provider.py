"""
OpenRouter provider — universal fallback gateway.
Routes to equivalent models when primary providers fail (429/5xx/timeout).
Supports all major model families through a single OpenAI-compatible API.
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.config.cost_table import compute_cost


class OpenRouterProvider(AIProvider):
    """
    OpenRouter universal fallback provider.
    Uses OpenAI-compatible API with openrouter.ai base URL.
    """

    provider_name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-flash-1.5"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
                default_headers={
                    "HTTP-Referer": "https://github.com/AI-Software-Compiler",
                    "X-Title": "AI Software Compiler",
                },
            )
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
            system_content += f"\n\nRespond ONLY with valid JSON exactly matching this schema:\n{schema_json}\nDo not include markdown, explanations, or any text outside the JSON object."
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_schema:
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
