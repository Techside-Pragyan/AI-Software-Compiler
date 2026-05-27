"""
Cost table for all supported AI providers and models.
Used by cost tracker to compute estimated USD cost per pipeline run.

Prices in USD per 1,000,000 tokens (input / output).
Updated: May 2025 — verify against provider dashboards for accuracy.
"""

COST_TABLE: dict[str, dict[str, dict[str, float]]] = {
    "gemini": {
        "gemini-2.0-flash": {
            "input_per_1m":  0.10,
            "output_per_1m": 0.40,
        },
        "gemini-1.5-pro": {
            "input_per_1m":  1.25,
            "output_per_1m": 5.00,
        },
        "gemini-1.5-flash": {
            "input_per_1m":  0.075,
            "output_per_1m": 0.30,
        },
    },
    "openai": {
        "gpt-4o": {
            "input_per_1m":  2.50,
            "output_per_1m": 10.00,
        },
        "gpt-4o-mini": {
            "input_per_1m":  0.15,
            "output_per_1m": 0.60,
        },
        "gpt-3.5-turbo": {
            "input_per_1m":  0.50,
            "output_per_1m": 1.50,
        },
    },
    "anthropic": {
        "claude-3-5-haiku-20241022": {
            "input_per_1m":  0.80,
            "output_per_1m": 4.00,
        },
        "claude-3-5-sonnet-20241022": {
            "input_per_1m":  3.00,
            "output_per_1m": 15.00,
        },
    },
    "groq": {
        "llama-3.3-70b-versatile": {
            "input_per_1m":  0.59,
            "output_per_1m": 0.79,
        },
        "llama-3.1-8b-instant": {
            "input_per_1m":  0.05,
            "output_per_1m": 0.08,
        },
        "mixtral-8x7b-32768": {
            "input_per_1m":  0.24,
            "output_per_1m": 0.24,
        },
    },
    "openrouter": {
        "google/gemini-flash-1.5": {
            "input_per_1m":  0.075,
            "output_per_1m": 0.30,
        },
        "meta-llama/llama-3.3-70b-instruct": {
            "input_per_1m":  0.12,
            "output_per_1m": 0.30,
        },
        "mistralai/mistral-7b-instruct": {
            "input_per_1m":  0.055,
            "output_per_1m": 0.055,
        },
        "openai/gpt-4o-mini": {
            "input_per_1m":  0.15,
            "output_per_1m": 0.60,
        },
        "anthropic/claude-3.5-haiku": {
            "input_per_1m":  0.80,
            "output_per_1m": 4.00,
        },
    },
    "mistral": {
        "mistral-small-latest": {
            "input_per_1m":  0.20,
            "output_per_1m": 0.60,
        },
        "mistral-medium-latest": {
            "input_per_1m":  2.70,
            "output_per_1m": 8.10,
        },
    },
    "deepseek": {
        "deepseek-chat": {
            "input_per_1m":  0.14,
            "output_per_1m": 0.28,
        },
        "deepseek-reasoner": {
            "input_per_1m":  0.55,
            "output_per_1m": 2.19,
        },
    },
}


def compute_cost(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Compute estimated USD cost for a given provider/model/token usage.
    Returns 0.0 if provider or model not in table.
    """
    provider_table = COST_TABLE.get(provider, {})
    model_table = provider_table.get(model, {})
    if not model_table:
        return 0.0

    input_cost  = (tokens_in  / 1_000_000) * model_table.get("input_per_1m",  0.0)
    output_cost = (tokens_out / 1_000_000) * model_table.get("output_per_1m", 0.0)
    return round(input_cost + output_cost, 8)
