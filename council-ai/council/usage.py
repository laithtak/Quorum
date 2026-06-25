"""Token usage tracking and cost estimation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token counts and estimated cost for a completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = ""

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
            model=self.model or other.model,
        )


@dataclass
class CounselorUsage:
    """Per-counselor usage summary."""

    counselor_name: str
    model: str
    usage: TokenUsage


# USD per 1M tokens: (input, output)
COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-pro": (1.25, 5.00),
    "llama3.1": (0.0, 0.0),
    "mistral": (0.0, 0.0),
}


def _lookup_pricing(model: str) -> tuple[float, float]:
    if model in COST_TABLE:
        return COST_TABLE[model]
    model_lower = model.lower()
    for key, pricing in COST_TABLE.items():
        if key in model_lower or model_lower in key:
            return pricing
    return (1.0, 3.0)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost from token counts and model pricing table."""
    input_rate, output_rate = _lookup_pricing(model)
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def usage_from_openai_response(model: str, usage_obj) -> TokenUsage | None:
    """Build TokenUsage from an OpenAI-style usage object."""
    if usage_obj is None:
        return None
    prompt = getattr(usage_obj, "prompt_tokens", 0) or 0
    completion = getattr(usage_obj, "completion_tokens", 0) or 0
    total = getattr(usage_obj, "total_tokens", 0) or (prompt + completion)
    cost = calculate_cost(model, prompt, completion)
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        estimated_cost_usd=cost,
        model=model,
    )
