"""
Provider routing configuration.
NEVER hardcode model names inside pipeline stages — always read from here.

Each stage defines:
  primary: preferred provider + model
  fallback: used when primary fails (429/5xx/timeout)
  temperature: generation temperature for determinism
  max_tokens: max token budget
  latency_threshold_ms: switch to fallback if primary exceeds this
  cost_threshold_usd: switch to cheaper model if cost exceeds
"""
from typing import TypedDict, Optional

class ProviderConfig(TypedDict):
    provider: str
    model: str

class StageRoutingConfig(TypedDict):
    primary: ProviderConfig
    fallback: ProviderConfig
    temperature: float
    max_tokens: int
    latency_threshold_ms: int
    cost_threshold_usd: float


ROUTING_CONFIG: dict[str, StageRoutingConfig] = {
    "intentExtraction": {
        "primary":   {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
        "fallback":  {"provider": "gemini", "model": "gemini-2.0-flash"},
        "temperature": 0.1,
        "max_tokens": 1024,
        "latency_threshold_ms": 8000,
        "cost_threshold_usd": 0.002,
    },
    "schemaGeneration": {
        "primary":   {"provider": "gemini", "model": "gemini-2.0-flash"},
        "fallback":  {"provider": "openrouter", "model": "google/gemini-flash-1.5"},
        "temperature": 0.1,
        "max_tokens": 4096,
        "latency_threshold_ms": 15000,
        "cost_threshold_usd": 0.01,
    },
    "appSpecGeneration": {
        "primary":   {"provider": "gemini", "model": "gemini-2.0-flash"},
        "fallback":  {"provider": "openrouter", "model": "google/gemini-flash-1.5"},
        "temperature": 0.2,
        "max_tokens": 8192,
        "latency_threshold_ms": 20000,
        "cost_threshold_usd": 0.02,
    },
    "repair": {
        "primary":   {"provider": "gemini", "model": "gemini-2.0-flash"},
        "fallback":  {"provider": "openrouter", "model": "mistralai/mistral-7b-instruct"},
        "temperature": 0.0,
        "max_tokens": 4096,
        "latency_threshold_ms": 10000,
        "cost_threshold_usd": 0.005,
    },
    "evaluation": {
        "primary":   {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
        "fallback":  {"provider": "gemini", "model": "gemini-2.0-flash"},
        "temperature": 0.1,
        "max_tokens": 2048,
        "latency_threshold_ms": 12000,
        "cost_threshold_usd": 0.005,
    },
}

# OpenRouter model mapping for automatic fallback
# Maps (provider, model) → openrouter model string
OPENROUTER_MODEL_MAP: dict[str, str] = {
    "groq/llama-3.3-70b-versatile":     "meta-llama/llama-3.3-70b-instruct",
    "gemini/gemini-2.0-flash":           "google/gemini-flash-1.5",
    "openai/gpt-4o-mini":               "openai/gpt-4o-mini",
    "openai/gpt-4o":                    "openai/gpt-4o",
    "anthropic/claude-3-5-haiku-20241022": "anthropic/claude-3.5-haiku",
    "mistral/mistral-small-latest":      "mistralai/mistral-small",
}

def get_openrouter_model(provider: str, model: str) -> str:
    """Maps a (provider, model) pair to the equivalent OpenRouter model string."""
    key = f"{provider}/{model}"
    return OPENROUTER_MODEL_MAP.get(key, f"{provider}/{model}")
