"""
Anthropic Claude provider implementation.
Uses tool_use for structured JSON output.
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, Type
from pydantic import BaseModel

from app.providers.base import AIProvider, ProviderResponse
from app.config.cost_table import compute_cost


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider with structured output via tool_use."""

    provider_name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
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

        system_content = system or "You are a helpful AI assistant."

        if response_schema:
            # Use tool_use for structured output
            tool_schema = response_schema.model_json_schema()
            tools = [{
                "name": "structured_output",
                "description": "Return the structured response in the required format",
                "input_schema": tool_schema,
            }]
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_content,
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice={"type": "tool", "name": "structured_output"},
                temperature=temperature,
            )
            # Extract JSON from tool use
            text = ""
            for block in response.content:
                if block.type == "tool_use":
                    text = json.dumps(block.input)
                    break
        else:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_content,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            text = response.content[0].text if response.content else ""

        latency_ms = (time.time() - start) * 1000
        tokens_in  = response.usage.input_tokens  if response.usage else 0
        tokens_out = response.usage.output_tokens if response.usage else 0
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
